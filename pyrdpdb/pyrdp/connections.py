# -*- coding: utf-8 -*-
# flake8: noqa: E501
import logging
import datetime
import io
import socket
from typing import Optional
import pandas as pd

from pyrdpdb import pyrdp

from . import converters, err
from ._compat import IRONPYTHON, PY2, str_type
from .charset import charset_by_name
from .cursors import Cursor
from .wireline_protocol import WirelineProtocol
from .utils import timeit

log = logging.getLogger("pyrdp.connections")


if PY2 and not IRONPYTHON:
    # read method of file-like returned by sock.makefile() is very slow.
    # So we copy io-based one from Python 3.
    from ._socketio import SocketIO

    def _makefile(sock, mode):
        return io.BufferedReader(SocketIO(sock, mode))

else:

    def _makefile(sock, mode):
        return sock.makefile(mode)


DEFAULT_CHARSET = "utf8"


class Connection(object):
    """
    Representation of a socket with a rapidsdb server.
    The proper way to get an instance of this class is to call
    connect().
    Establish a connection to the rapidsdb database. Accepts several
    arguments:
    :param host: Host where the database server is located
    :param user: Username to log in as
    :param password: Password to use.
    :param database: Database to use, None to not use a particular one.
    :param port: rapidsdb port to use, default is usually OK. (default: 4333)
    :param read_timeout: The timeout for reading from the connection in seconds (default: None - no timeout)
    :param write_timeout: The timeout for writing to the connection in seconds (default: None - no timeout)
    :param charset: Charset you want to use.
    :param conv:
        Conversion dictionary to use instead of the default one.
        This is used to provide custom marshalling and unmarshaling of types.
        See converters.
    :param cursorclass: Custom cursor class to use.
    :param connect_timeout: Timeout before throwing an exception when connecting.
        (default: 10, min: 1, max: 31536000)
    See `Connection <https://www.python.org/dev/peps/pep-0249/#connection-objects>`_ in the
    specification.
    """

    _sock = None
    _closed = False
    _secure = False

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

    def __init__(
        self,
        host=None,
        port=4333,
        cursorclass=Cursor,
        db=None,
        database=None,
        tprotocol=None,
        write_timeout=None,
        read_timeout=None,
        protocol=None,
        user=None,
        password=None,
        # federation=None,
        catalog=None,
        schema=None,
        charset="",
        encoding=None,
        conv=None,
        connect_timeout=20,
        auth_type="PLAIN",
        echo=False,
    ) -> None:
        self.current_execute_time: float = 0
        self.host = host or "localhost"
        self.port = port or 4333
        self.auth_type = auth_type
        self.user = user
        self.password = password
        self.cursorclass = cursorclass
        self.protocol: Optional[WirelineProtocol] = protocol
        self._echo = echo
        if read_timeout is not None and read_timeout <= 0:
            log.error("read_timeout should be >= 0")
            raise ValueError("read_timeout should be >= 0")
        self._read_timeout = read_timeout
        if write_timeout is not None and write_timeout <= 0:
            log.error("write_timeout should be >= 0")
            raise ValueError("write_timeout should be >= 0")
        self._write_timeout = write_timeout

        connect_timeout = int(connect_timeout)
        if not (0 < connect_timeout <= 31536000):
            raise ValueError("connect_timeout should be >0 and <=31536000")
        self.connect_timeout = connect_timeout or None

        if charset:
            self.charset = charset
        else:
            self.charset = DEFAULT_CHARSET

        self.encoding = charset_by_name(self.charset).encoding

        if conv is None:
            conv = converters.conversions
        self._result: Optional[ResultSet] = None

        self.encoders = {k: v for (k, v) in conv.items() if type(k) is not int}
        self.decoders = {k: v for (k, v) in conv.items() if type(k) is int}

        self.connect()

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            print(f"Error occurred when exit connection, exception: {exc_value}")
        self.close()

    def __enter__(self):
        """Context manager that returns a Cursor"""
        return self

    def connect(self, sock=None):
        self._closed = False
        if sock is None:
            sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.connect_timeout)
            sock.connect((self.host, self.port))
        self._sock = sock
        self._rfile = _makefile(sock, "rb")
        if self.protocol is None:
            self.protocol = WirelineProtocol(self)
        self._login()

    def _login(self):
        self.protocol.login()

    def _set_catalog(self, catalog_name):
        maxlength = 128

        if catalog_name and (len(catalog_name) > maxlength or len(catalog_name) < 1):
            # TODO: raise execption
            pass

        with self.cursor() as cursor:
            sql = f"SET CATALOG {catalog_name};"
            cursor.execute(sql, quiet=True)

    def _set_schema(self, schema_name):
        maxlength = 128

        if schema_name and (len(schema_name) > maxlength or len(schema_name) < 1):
            # TODO: raise execption
            pass

        with self.cursor() as cursor:
            sql = f"SET SCHEMA {schema_name};"
            cursor.execute(sql, quiet=True)

    def escape(self, obj, mapping=None):
        """
        Escape whatever value you pass to it.
        Non-standard, for internal use; do not use this in your applications.
        """
        if isinstance(obj, str_type):
            return "'" + converters.escape_string(obj) + "'"
        if isinstance(obj, (bytes, bytearray)):
            return converters.escape_bytes(obj)
        return converters.escape_item(obj, self.charset, mapping=mapping)

    def literal(self, obj):
        """
        Alias for escape()
        Non-standard, for internal use; do not use this in your applications.
        """
        return self.escape(obj, self.encoders)

    def close(self):
        """
        Close connection .
        """
        if self._closed:
            raise err.Error("Already closed")
        self._closed = True
        if self._sock is None:
            return

        self._force_close()

    def _force_close(self):
        if self._sock:
            try:
                self._sock.close()
            except:
                pass
        self._sock = None
        self._rfile = None

    def commit(self):
        """
        Does nothing, required by DB API.
        """
        pass

    def rollback(self):
        """
        Does nothing, required by DB API.
        """
        pass

    def begin(self):
        """
        Does nothing, required by DB API.
        """
        pass

    @timeit
    def to_pandas(self, sql) -> pd.DataFrame:
        dfs = []
        self.protocol.query(sql)

        while self.protocol.to_pandas():
            dfs.append(self.protocol._df)
        if self.protocol._df:
            dfs.append(self.protocol._df)
        df = pd.concat(dfs, ignore_index=True)

        return df

    @timeit
    def to_pandas2(self, sql) -> pd.DataFrame:
        dfs = []
        self.protocol.query(sql)

        result = ResultSet(self.protocol)
        row_generator = result.read_generator()
        columns = [desc[0] for desc in self.protocol.description]
        for block in row_generator:
            df = pd.DataFrame(block, columns=columns)
            dfs.append(df)

        df = pd.concat(dfs, ignore_index=True)

        return df

    # @timeit
    def query(self, sql, unbuffered=False, generator=False):
        start = datetime.datetime.now()
        self.protocol.query(sql)
        end = datetime.datetime.now()
        self.current_execute_time = round((end - start).total_seconds(), 2)

        if not generator:
            self._affected_rows = self._read_query_result(unbuffered)
        else:
            self._affected_rows = self._read_query_result_generator(unbuffered)

    def next_result(self, unbuffered=False):
        self._affected_rows = self._read_query_result(unbuffered=unbuffered)
        return self._affected_rows

    # # This is for testing base request, will delete later
    # def query_demo(self, sql):
    #     request = QueryExecuteRequest(sql)
    #     self.protocol._send_message(request, 51)
    #     while True:
    #         message = self.protocol._read_message()
    #         print(message)

    def cursor(self, cursor=None):
        if cursor:
            return cursor(self)
        return self.cursorclass(self)

    def _read_query_result(self, unbuffered=False) -> Optional[int]:
        self._result = None
        if unbuffered is True:
            try:
                result = ResultSet(self.protocol)
                result.init_unbuffered_query()
            except:
                result.unbuffered_active = False
                result.protocol = None
                raise
        else:
            result = ResultSet(self.protocol)
            result.read()

        self._result = result
        return result.affected_rows

    def _read_query_result_generator(self, unbuffered=False) -> Optional[int]:
        self._result = None

        try:
            result = ResultSet(self.protocol)

            if unbuffered:
                result.init_unbuffered_query()
            else:
                row_generator = result.read_generator()

                for block in row_generator:
                    # print("generating block")
                    current_chunk = []
                    for row in block:
                        current_chunk.append(row)
                    result.rows = current_chunk

                    self._result = result
            return result.affected_rows
        except Exception as e:
            if unbuffered:
                result.unbuffered_active = False
                result.protocol = None
            raise e


class ResultSet(object):
    def __init__(self, protocol: WirelineProtocol) -> None:
        self.protocol: Optional[WirelineProtocol] = protocol
        self.affected_rows = None
        self.rows = None
        self.unbuffered = False
        self.description = None
        self.field_count = 0
        self.err = None
        self.has_next = None
        self.unbuffered_active = False

        if isinstance(self.protocol, WirelineProtocol):
            self.has_next = self.protocol.has_next

    # buffered result, cache all the data to the client
    # @timeit
    def read(self) -> None:
        rows = []

        try:
            while self.protocol.get_next_set():
                rows.extend(self.protocol.chunk)

            if self.protocol.chunk:
                rows.extend(self.protocol.chunk)

            self.has_next = self.protocol.has_next
        except Exception:
            log.debug("No more data")
            self.has_next = False

        self.affected_rows = len(rows)
        self.rows = rows
        self.description = self.protocol.description
        self.field_count = self.protocol.numColumns
        self.err = self.protocol.errstr
        # self.protocol = None

    def read_generator(self):

        def merge_chunk():
            nonlocal count
            _chunk = self.protocol.chunk
            if _chunk:
                count += len(_chunk)
                self.affected_rows = count
                log.debug(
                    "affected_rows: {}, count: {}".format(self.affected_rows, count)
                )
                yield _chunk

        try:
            self.description = self.protocol.description
            self.field_count = self.protocol.numColumns
            self.err = self.protocol.errstr

            count = 0

            yield from merge_chunk()

            while self.protocol.get_next_set():
                yield from merge_chunk()

            yield from merge_chunk()

            self.has_next = self.protocol.has_next

        except Exception as e:
            log.debug("No more data: %s", str(e))
            self.has_next = False

    def init_unbuffered_query(self):
        """Initialize Unbuffered result set.

        Note: MySQL represents the "row count" as an unsigned integer in its protocol.
        When -1 is assigned to the row count to indicate "unknown," it is internally
        converted to 2^64 - 1 (the maximum value of an unsigned 64-bit integer).
        """
        self.description = self.protocol.description
        self.field_count = self.protocol.numColumns
        self.err = self.protocol.errstr
        self.affected_rows = -1  # 18446744073709551615
        self.unbuffered = True
        if self.err:
            raise pyrdp.ProgrammingError(self.err)

    def read_next_row_unbuffered(self):
        if not self.unbuffered:
            return

        if self.protocol and self.protocol.get_next_row():
            row = self.protocol.row
        else:
            self.protocol = None
            row = None

        self.rows = (row,)

        if row is not None:
            self.affected_rows = 1

        return row
