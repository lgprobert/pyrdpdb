# flake8: noqa: E501
# -*- coding: utf-8 -*-
import re
from datetime import datetime
from itertools import count
from typing import TYPE_CHECKING, Any, Iterable, Optional, Union
import pandas as pd

from pyrdpdb import aiordp

from . import err
from ._compat import range_type
from .utils import timeit
import logging

log = logging.getLogger("aiordp.cursors")

RE_INSERT_VALUES = re.compile(
    r"\s*((?:INSERT|REPLACE)\b.+\bVALUES?\s*)(\(\s*(?:%s|%\(.+\)s)\s*(?:,\s*(?:%s|%\(.+\)s)\s*)*\))(\s*(?:ON DUPLICATE.*)?);?\s*\Z",
    re.IGNORECASE | re.DOTALL,
)


if TYPE_CHECKING:
    from .connections import Connection, ResultSet


class Cursor(object):
    """
    This is the object you use to interact with the database.
    Do not create an instance of a Cursor yourself. Call
    connections.Connection.cursor().
    See `Cursor <https://www.python.org/dev/peps/pep-0249/#cursor-objects>`_ in
    the specification.
    """

    Warning = err.Warning
    Error = err.Error
    InterfaceError = err.InterfaceError
    DatabaseError = err.DatabaseError
    DataError = err.DataError
    OperationalError = err.OperationalError
    IntegrityError = err.IntegrityError
    InternalError = err.InternalError
    ProgrammingError = err.ProgrammingError
    NotSupportedError = err.NotSupportedError

    def __init__(self, connection: "Connection", echo=False):
        self._connection: Optional["Connection"] = connection
        self.description = None
        self.rownumber = 0
        # specifies the number of rows that the last .execute*() produced  or affected
        self.rowcount = -1
        # specifies the number of rows to fetch at a time with .fetchmany()
        self.arraysize = 1
        self._executed: Optional[str] = None
        self._result: Optional[ResultSet] = None  # response result of executed query
        self._rows = None  # all data rows
        self._timing = False
        self._loop = self._connection.loop
        # self._warnings_handled = False
        self._echo = echo

    @property
    def connection(self):
        """This read-only attribute return a reference to the Connection
        object on which the cursor was created."""
        return self._connection

    async def close(self):
        """
        Close cursor .
        """
        conn = self._connection
        if conn is None:
            return
        try:
            while await self.nextset():
                pass
        finally:
            self._connection = None

    def __aiter__(self):
        return self

    async def __anext__(self):
        result = await self.fetchone()
        if result is None:
            raise StopAsyncIteration
        else:
            return result

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        log.debug("enter __aexit__")
        await self.close()
        return

    def _get_db(self):
        if not self._connection:
            raise err.ProgrammingError("Cursor closed")
        return self._connection

    # cursor.execute("insert into user values(1, 80, 'zhang')"
    # cursor.execute("insert into user values(%s, %s, %s)",(1,80,"zhang"))
    async def execute(
        self,
        query,
        query_args=None,
        quiet: bool = True,
        internal: bool = False,
        generator: bool = False,
    ) -> int:
        """
        execute SQL statment.
        :param str query : query .
        :param tuple|dict|set query_args : query args.
        :return : affected row of this execute
        """
        if self._connection and self._connection.closed:
            raise aiordp.Error("Already closed")
        aa = query.upper().replace(" ", "")
        if aa.startswith("CREATEINDEX"):
            return 0

        while await self.nextset():
            pass

        stmt = self.mogrify(query, query_args)

        log.debug("generated query to run: " + stmt)
        await self._query(stmt)
        self._executed = stmt

        if not quiet or self._timing and not internal:
            self._execute_stdout()
        return self.rowcount

    def _execute_stdout(self, start: Optional[datetime] = None):
        """Show rowcount and execution time if cursor.timing is True."""
        if self._timing:
            print(f"{self.rowcount} rows ({self._get_execute_time(start)} sec)")
        else:
            print(f"{self.rowcount} rows")

    def timing(self) -> None:
        """Flip show execution time flag setting."""
        self._timing = not self._timing
        print(f"Timing is {'ON' if self._timing else 'OFF'}.")

    def mogrify(self, query: str, args=None):
        """Returns real query that will be sent to database.
        :param str query : query .
        :param tuple|dict|set args : query args.
        :return : real sql .
        """
        if args is not None:
            query = query % self._escape_args(args)

        if not query.endswith(";"):
            query += ";"

        return query

    def _escape_args(self, query_args: Any) -> Any:
        """Formalize query by escaping all objects in query."""
        conn: "Connection" = self._get_conn()
        if isinstance(query_args, (tuple, list)):
            return tuple(conn.literal(arg) for arg in query_args)
        elif isinstance(query_args, dict):
            return {key: conn.literal(val) for (key, val) in query_args.items()}
        else:
            return conn.escape(query_args)

    async def executemany(
        self,
        query: str,
        query_args: Iterable[Union[tuple, list, dict]],
        quiet: bool = True,
    ) -> int:
        """Execute query with sequence of arg for multiple times.

        :param query: query statement.
        :param args : query args.
        :return : affected row (rowcount) of this execute
        """
        if not query_args:
            return 0

        m = RE_INSERT_VALUES.match(query)
        if m:
            q_prefix = m.group(1) % ()
            q_values = m.group(2).rstrip()
            q_postfix = m.group(3) or ""
            assert q_values[0] == "(" and q_values[-1] == ")"
            return await self._do_execute_many(
                q_prefix, q_values, q_postfix, query_args, quiet
            )

        start = datetime.now()
        self.rowcount = sum(
            [await self.execute(query, arg, quiet=True) for arg in query_args]
        )

        if not quiet:
            self._execute_stdout(start)
        return self.rowcount

    async def _do_execute_many(
        self,
        prefix: str,
        placeholders: str,
        postfix: str,
        qargs: Iterable[Union[tuple, list, dict]],
        quiet: bool = True,
    ):
        sql = prefix
        start = datetime.now()
        num_placeholders = placeholders.count("%s")

        self._validate_args(qargs, num_placeholders)
        for arg in qargs:
            formatted_args = self._escape_args(arg)
            if num_placeholders < len(formatted_args):
                raise ValueError(
                    "Number of elements in values tuple does not match number of placeholders"
                )
            v = placeholders % formatted_args
            sql += v
            sql += ","
        sql = sql[:-1]  # remove the trailing ',' from generated query

        log.debug(f"[executemany] query: {sql}")
        await self.execute(sql + postfix, quiet=True, internal=True)
        self.rowcount = len(qargs)  # type: ignore

        if not quiet and self._timing:
            self._execute_stdout(start)

        return self.rowcount

    def _validate_args(self, qargs, num_placeholders) -> bool:
        """Validate args for executemany() are in supported structure."""
        if not isinstance(qargs, (list, tuple)):
            raise ValueError(
                "The 'qargs' argument must be a list or tuple of parameter sets."
            )
        for i, param_set in enumerate(qargs):
            if not isinstance(param_set, (tuple, list)):
                raise ValueError(f"Parameter set at index {i} must be a tuple or list.")
            if len(param_set) != num_placeholders:
                raise ValueError(
                    f"Parameter set at index {i} has {len(param_set)} elements; "
                    f"expected {num_placeholders}."
                )
            # Check for nested lists or tuples
            if any(isinstance(item, (tuple, list)) for item in param_set):
                raise ValueError(
                    f"Parameter set at index {i} contains nested structures, which are not allowed: {param_set}"
                )

        return True

    async def _query(self, stmt, generator: bool = False):
        """Execute query.
        : return : the row count in resultset.
        """
        conn = self._get_conn()
        self._executed = stmt
        self._clear_result()
        await conn.query(stmt, generator=generator)
        await self._do_get_result()
        return self.rowcount

    async def fetchone(self):
        """Fetch one row data.
        : return : one row data.
        """
        try:
            self._check_executed()
            fut = self._loop.create_future()

            if self._rows is None or self.rownumber >= len(self._rows):
                return None
            result = self._rows[self.rownumber]
            self.rownumber += 1
        except TypeError:
            raise aiordp.ProgrammingError("attempting to use unexecuted cursor")
        return result

    async def fetchmany(self, size=None):
        """
        Fetch number of the result rows.
        : return : size or arraysize data rows.
        """
        self._check_executed()
        if self._rows is None:
            return ()
        end = self.rownumber + (size or self.arraysize)
        result = self._rows[self.rownumber : end]
        self.rownumber = min(end, len(self._rows))
        return result

    async def fetchall(self):
        """
        Fetch all the rows.
        : return : all the result set.
        """
        self._check_executed()
        if self._rows is None:
            return ()

        if self.rownumber:
            result = self._rows[self.rownumber :]
        else:
            result = self._rows

        self.rownumber = len(result)
        return result

    async def fetchall2(self):
        """
        Fetch all the rows.
        :return: A list containing all the rows in the result set.
        """
        self._check_executed()

        # If no rows are available, return an empty tuple
        if self._rows is None:
            return ()

        # If _rows is a generator, convert it to a list and store it
        if isinstance(self._rows, (list, tuple)):
            result = self._rows[self.rownumber :]
        else:
            # Consume the generator into a list
            result = list(self._rows)
            self._rows = result  # Cache the results for subsequent fetches

        # Update the current row pointer
        self.rownumber = len(result)

        return result

    @timeit
    async def to_pandas(self, sql) -> pd.DataFrame:
        await self.execute(sql, quiet=True)
        columns = [desc[0] for desc in self.description]
        return pd.DataFrame(self._rows, columns=columns)

    def scroll(self, value, mode="relative"):
        self._check_executed()
        if mode == "relative":
            r = self.rownumber + value
        elif mode == "absolute":
            r = value
        else:
            raise err.ProgrammingError("unknown scroll mode %s" % mode)

        if not (0 <= r < len(self._rows)):
            raise IndexError("out of range")
        self.rownumber = r

    def _get_execute_time(self, start: Optional[datetime]) -> float:
        if start:
            end = datetime.now()
            runtime = round((end - start).total_seconds(), 2)
        elif self.connection is not None:
            runtime = self.connection.current_execute_time
        else:
            runtime = -1  # executime unknown
        return runtime

    async def _nextset(self, unbuffered=False):
        """Get the next query set."""
        conn = self._get_db()
        current_result = self._result
        if current_result is None or current_result is not conn._result:
            return None
        if not current_result.has_next:
            return None

        self._result = None
        self._clear_result()
        await conn.next_result(unbuffered=unbuffered)
        if conn._result:
            await self._do_get_result()
        return True

    async def nextset(self, unbuffered=False):
        return await self._nextset(unbuffered)

    async def _do_get_result(self):
        """
        Get result after execute.
        """
        conn = self._get_conn()
        self._result = result = conn._result
        self.rowcount = result.affected_rows
        self.description = result.description
        self.err = result.err
        self._rows = result.rows
        if self.err:
            if (
                self.err.find("Got more than one row returned for the internal query")
                != -1
            ):
                pass
            else:
                err_msg = f"Exception: {self.err}, original query: {self._executed}"
                print(err_msg)
                raise aiordp.RDBError(err_msg)

    def _trim(self, s):
        if s is None or s == "":
            return ""
        # 左侧空格
        while s[:1] == " ":
            s = s[1:]
        # 右侧空格
        while s[-1:] == " ":
            s = s[:-1]
        return s

    def _get_conn(self) -> "Connection":
        """Get the connection to execute query operation.

        Return : connection.
        """
        if not self._connection:
            raise aiordp.ProgrammingError("Cursor closed")
        return self._connection

    def _check_executed(self):
        """Check if query is executed."""
        if not self._executed:
            raise aiordp.ProgrammingError("execute() first")

    def _clear_result(self):
        """
        Clear last result info.
        """
        self.rownumber = 0
        self._result = None
        self.rowcount = 0
        self.description = None
        self.lastrowid = None
        self._rows = None

    def set_arraysize(self, size):
        """Set cursor arraysize.

        :param number size : arraysize of the cursor.
        """
        self.arraysize = size

    def get_arraysize(self):
        """Get cursor arraysize.

        Return : arraysize of the cursor.
        """
        return self.arraysize

    def callproc(self, procname, args=()):
        """Does nothing, required by DB API."""
        log.warning("callproc not implemented yet.")

    def setinputsizes(self, *args):
        """Does nothing, required by DB API."""
        log.warning("setinputsizes not implemented yet.")

    def setoutputsizes(self, *args):
        """Does nothing, required by DB API."""
        log.warning("setoutputsizes not implemented yet.")

    async def _federation_exists(self, name: str, unbuffered: bool = False) -> bool:
        """Check if a federation name exists."""
        fed_name = name.upper()
        stmt = f"select * from FEDERATIONS where FEDERATION_NAME='{fed_name}';"
        await self.execute(stmt, quiet=True)
        if not unbuffered:
            if self.rowcount == 1:
                return True
        else:
            self.fetchall()
            if self.rownumber == 1:
                return True
        return False

    async def has_federation(self, name: str) -> bool:
        """Check if a federation name exists."""
        return await self._federation_exists(name)

    async def _connector_exists(self, name: str, unbuffered: bool = False) -> bool:
        """Check if a named connector exists."""
        connector_name = name.upper()
        stmt = "select connector_name from system.connectors where connector_name='{}';".format(
            connector_name
        )
        await self.execute(stmt, quiet=True)
        if not unbuffered:
            if self.rowcount == 1:
                return True
        else:
            self.fetchall()
            if self.rownumber == 1:
                return True
        return False

    async def has_connector(self, name: str) -> bool:
        """Check if a named connector exists."""
        return await self._connector_exists(name)

    async def _table_exists(
        self, table: str, schema: Optional[str] = None, unbuffered: bool = False
    ) -> bool:
        """Generic helper method to check if a named table exists."""
        tbl = table.upper()
        stmt = "select count(*) from tables where table_name='{}'".format(tbl)
        if schema:
            stmt += f" and schema_name = '{schema.upper()}'"
        await self.execute(stmt, quiet=True)
        result = await self.fetchone()
        table_count = result[0]
        if table_count == 1:
            return True
        return False

    async def has_table(self, table: str, schema: Optional[str] = None) -> bool:
        """Check if a named table exists."""
        return await self._table_exists(table, schema)


class SSCursor(Cursor):
    """
    Unbuffered Cursor, mainly useful for queries that return a lot of data,
    or for connections to remote servers over a slow network.
    Instead of copying every row of data into a buffer, this will fetch
    rows as needed. The upside of this is the client uses much less memory,
    and rows are returned much faster when traveling over a slow network
    or if the result set is very big.
    There are limitations, though. The wireline protocol doesn't support
    returning the total number of rows, so the only way to tell how many rows
    there are is to iterate over every row returned. Also, it currently isn't
    possible to scroll backwards, as only the current row is held in memory.
    """

    async def close(self) -> None:
        conn = self._connection
        if conn is None:
            return

        if self._result is not None and self._result is conn._result:
            await self._result._finish_unbuffered_query()

        try:
            while await self.nextset():
                pass
        finally:
            self._connection = None

    async def _query(self, q):
        conn = self._get_conn()
        self._last_executed = q
        self._clear_result()
        await conn.query(q, unbuffered=True)
        await self._do_get_result()
        return self.rowcount

    async def nextset(self):
        return await self._nextset(unbuffered=True)

    async def _read_next(self):
        """
        Read next row
        """
        return await self._result.read_next_row()

    async def fetchone(self):
        """Fetch next row"""
        self._check_executed()
        row = await self._read_next()
        if row is None:
            return
        self.rownumber += 1
        return row

    async def fetchall(self):
        """
        Fetch all, as per MySQLdb. Pretty useless for large queries, as
        it is buffered. See fetchall_unbuffered(), if you want an unbuffered
        generator version of this method.
        """
        return [row async for row in self.fetchall_unbuffered()]

    async def fetchall_unbuffered(self):
        while True:
            row = await self.fetchone()
            if row is None:
                break
            yield row

    async def scroll(self, value, mode="relative"):
        self._check_executed()

        if mode == "relative":
            if value < 0:
                raise err.NotSupportedError(
                    "Backwards scrolling not supported by this cursor"
                )

            for _ in range(value):
                await self._read_next()
            self.rownumber += value
        elif mode == "absolute":
            if value < self.rownumber:
                raise err.NotSupportedError(
                    "Backwards scrolling not supported by this cursor"
                )

            end = value - self.rownumber
            for _ in range(end):
                await self._read_next()
            self.rownumber = value
        else:
            raise err.ProgrammingError("unknown scroll mode %s" % mode)

    async def fetchmany(self, size=None):
        """Fetch many"""
        self._check_executed()
        if size is None:
            size = self.arraysize

        rows = []
        for _ in range_type(size):
            row = await self._read_next()
            if row is None:
                # self._show_warnings()
                break
            rows.append(row)
            self.rownumber += 1
        return rows

    async def has_federation(self, name: str) -> bool:
        """Check if a federation name exists."""
        return await self._federation_exists(name, unbuffered=True)

    async def has_connector(self, name: str) -> bool:
        """Check if a named connector exists."""
        return await self._connector_exists(name, unbuffered=True)

    async def has_table(self, table: str, schema: Optional[str] = None) -> bool:
        """Check if a named table exists."""
        return await self._table_exists(table, schema, unbuffered=True)


def convert_paramstyle(style, query, args):
    # I don't see any way to avoid scanning the query string char by char,
    # so we might as well take that careful approach and create a
    # state-based scanner.  We'll use int variables for the state.
    OUTSIDE = 0  # outside quoted string
    INSIDE_SQ = 1  # inside single-quote string '...'
    INSIDE_QI = 2  # inside quoted identifier   "..."
    INSIDE_ES = 3  # inside escaped single-quote string, E'...'
    INSIDE_PN = 4  # inside parameter name eg. :name
    INSIDE_CO = 5  # inside inline comment eg. --
    INSIDE_DQ = 6  # inside escaped dollar-quote string, $$...$$

    in_quote_escape = False
    in_param_escape = False
    placeholders = []
    output_query = []
    param_idx = map(lambda x: "$" + str(x), count(1))
    state = OUTSIDE
    prev_c = None
    for i, c in enumerate(query):
        next_c = query[i + 1] if i + 1 < len(query) else None

        if state == OUTSIDE:
            if c == "'":
                output_query.append(c)
                if prev_c == "E":
                    state = INSIDE_ES
                else:
                    state = INSIDE_SQ
            elif c == '"':
                output_query.append(c)
                state = INSIDE_QI
            elif c == "-":
                output_query.append(c)
                if prev_c == "-":
                    state = INSIDE_CO
            elif c == "$":
                output_query.append(c)
                if prev_c == "$":
                    state = INSIDE_DQ
            elif style == "qmark" and c == "?":
                output_query.append(next(param_idx))
            elif style == "numeric" and c == ":" and next_c not in ":=" and prev_c != ":":
                # Treat : as beginning of parameter name if and only
                # if it's the only : around
                # Needed to properly process type conversions
                # i.e. sum(x)::float
                output_query.append("$")
            elif style == "named" and c == ":" and next_c not in ":=" and prev_c != ":":
                # Same logic for : as in numeric parameters
                state = INSIDE_PN
                placeholders.append("")
            elif style == "pyformat" and c == "%" and next_c == "(":
                state = INSIDE_PN
                placeholders.append("")
            elif style in ("format", "pyformat") and c == "%":
                style = "format"
                if in_param_escape:
                    in_param_escape = False
                    output_query.append(c)
                else:
                    if next_c == "%":
                        in_param_escape = True
                    elif next_c == "s":
                        state = INSIDE_PN
                        output_query.append(next(param_idx))
                    else:
                        raise err.InterfaceError(
                            "Only %s and %% are supported in the query."
                        )
            else:
                output_query.append(c)

        elif state == INSIDE_SQ:
            if c == "'":
                if in_quote_escape:
                    in_quote_escape = False
                else:
                    if next_c == "'":
                        in_quote_escape = True
                    else:
                        state = OUTSIDE
            output_query.append(c)

        elif state == INSIDE_QI:
            if c == '"':
                state = OUTSIDE
            output_query.append(c)

        elif state == INSIDE_ES:
            if c == "'" and prev_c != "\\":
                # check for escaped single-quote
                state = OUTSIDE
            output_query.append(c)

        elif state == INSIDE_DQ:
            if c == "$" and prev_c == "$":
                state = OUTSIDE
            output_query.append(c)

        elif state == INSIDE_PN:
            if style == "named":
                placeholders[-1] += c
                if next_c is None or (not next_c.isalnum() and next_c != "_"):
                    state = OUTSIDE
                    try:
                        pidx = placeholders.index(placeholders[-1], 0, -1)
                        output_query.append("$" + str(pidx + 1))
                        del placeholders[-1]
                    except ValueError:
                        output_query.append("$" + str(len(placeholders)))
            elif style == "pyformat":
                if prev_c == ")" and c == "s":
                    state = OUTSIDE
                    try:
                        pidx = placeholders.index(placeholders[-1], 0, -1)
                        output_query.append("$" + str(pidx + 1))
                        del placeholders[-1]
                    except ValueError:
                        output_query.append("$" + str(len(placeholders)))
                elif c in "()":
                    pass
                else:
                    placeholders[-1] += c
            elif style == "format":
                state = OUTSIDE

        elif state == INSIDE_CO:
            output_query.append(c)
            if c == "\n":
                state = OUTSIDE

        prev_c = c

    if style in ("numeric", "qmark", "format"):
        vals = args
    else:
        vals = tuple(args[p] for p in placeholders)

    return "".join(output_query), vals
