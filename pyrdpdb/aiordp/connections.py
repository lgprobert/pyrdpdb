# -*- coding: utf-8 -*-
# flake8: noqa: E501
import logging
import asyncio
import datetime
import io
import socket
from typing import Optional
import pandas as pd

from pyrdpdb import aiordp
from pyrdpdb.messages.v4.QueryExecuteRequest.ttypes import QueryExecuteRequest

from . import converters, err
from ._compat import IRONPYTHON, PY2, str_type
from .charset import charset_by_name
from .cursors import Cursor
from .utils import _ConnectionContextManager, _ContextManager
from .wireline_protocol import WirelineProtocol
from .utils import timeit

log = logging.getLogger("aiordp.connections")

MAX_PACKET_LEN = 2**24 - 1

if PY2 and not IRONPYTHON:
    # read method of file-like returned by sock.makefile() is very slow.
    # So we copy io-based one from Python 3.
    from ._socketio import SocketIO

    def _makefile(sock, mode):
        return io.BufferedReader(SocketIO(sock, mode))

else:
    # socket.makefile in Python 3 is nice.
    def _makefile(sock, mode):
        return sock.makefile(mode)


DEFAULT_CHARSET = "utf8"


def connect(
    host="localhost",
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
    connect_timeout=10,
    auth_type="PLAIN",
    echo=False,
    loop=None,
):
    """See connections.Connection.__init__() for information about
    defaults."""
    coro = _connect(
        host=host,
        port=port,
        cursorclass=cursorclass,
        user=user,
        password=password,
        db=db,
        database=database,
        tprotocol=tprotocol,
        write_timeout=write_timeout,
        read_timeout=read_timeout,
        protocol=protocol,
        # federation=federation,
        catalog=catalog,
        schema=schema,
        charset=charset,
        encoding=encoding,
        conv=conv,
        connect_timeout=connect_timeout,
        auth_type=auth_type,
        echo=echo,
        loop=loop,
    )
    return _ConnectionContextManager(coro)


async def _connect(*args, **kwargs):
    conn = Connection(*args, **kwargs)
    await conn._connect()

    # if kwargs.get("catalog"):
    #     await conn._set_catalog(kwargs.get("catalog"))
    # if kwargs.get("schema"):
    #     await conn._set_schema(kwargs.get("schema"))
    return conn


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
    :param read_timeout: The timeout for reading from the connection in seconds
        (default: None - no timeout)
    :param write_timeout: The timeout for writing to the connection in seconds
        (default: None - no timeout)
    :param charset: Charset you want to use.
    :param conv:
        Conversion dictionary to use instead of the default one.
        This is used to provide custom marshalling and unmarshaling of types.
        See converters.
    :param cursorclass: Custom cursor class to use.
    :param connect_timeout: Timeout before throwing an exception when
        connecting. (default: 10, min: 1, max: 31536000)
    See `Connection
        <https://www.python.org/dev/peps/pep-0249/#connection-objects>`_ in the
        specification.
    """

    _sock = None
    closed = False
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

    # AUTH_TYPE PLAIN / KERBORS
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
        connect_timeout=10,
        auth_type="PLAIN",
        echo=False,
        loop=None,
    ):
        self._loop = loop or asyncio.get_event_loop()
        self._last_usage = self._loop.time()
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

    @property
    def loop(self):
        return self._loop

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.close()
        else:
            self.ensure_closed()
        return

    async def _connect(self, sock=None):
        self.closed = False
        if sock is None:
            sock: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.connect_timeout)
            sock.connect((self.host, self.port))
        self._sock = sock
        self._rfile = _makefile(sock, "rb")
        if self.protocol is None:
            self.protocol = WirelineProtocol(self)
        self.connected_time = self._loop.time()
        await self._login()

    async def _login(self):
        await self.protocol.login()

    async def _set_catalog(self, catalog_name):
        maxlength = 128

        if catalog_name and (len(catalog_name) > maxlength or len(catalog_name) < 1):
            # TODO: raise execption
            pass

        async with self.cursor() as cursor:
            stmt = f"SET CATALOG {catalog_name};"
            await cursor.execute(stmt, quiet=True)

    async def _set_schema(self, schema_name):
        maxlength = 128

        if schema_name and (len(schema_name) > maxlength or len(schema_name) < 1):
            # TODO: raise execption
            pass

        async with self.cursor() as cursor:
            sql = f"SET SCHEMA {schema_name};"
            await cursor.execute(sql, quiet=True)

    def ensure_closed(self):
        """Send quit command and then close socket connection"""
        if self._sock is None:
            # connection has been closed
            return
        self.close()

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

    def __del__(self):
        if self._sock:
            self.close()
        if self._sock:
            log.warning(f"Unclosed connection {self!r}", ResourceWarning)

    def close(self):
        """
        Close connection .
        """
        if self.closed:
            raise err.Error("Already closed")
        self.closed = True
        if self._sock is None:
            return
        self._force_close()

    def _force_close(self):
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
        self._sock = None
        self._rfile = None

    async def commit(self):
        """
        Does nothing, required by DB API.
        """
        pass

    async def rollback(self):
        """
        Does nothing, required by DB API.
        """
        pass

    async def begin(self):
        """
        Does nothing, required by DB API.
        """
        pass

    @timeit
    async def to_pandas(self, sql) -> pd.DataFrame:
        dfs = []
        await self.protocol.query(sql)

        while await self.protocol.to_pandas():
            dfs.append(self.protocol._df)
        if self.protocol._df:
            dfs.append(self.protocol._df)
        df = pd.concat(dfs, ignore_index=True)

        return df

    @timeit
    async def to_pandas2(self, sql) -> pd.DataFrame:
        dfs = []
        await self.protocol.query(sql)

        result = ResultSet(self.protocol)
        row_generator = await result.read_generator()
        columns = [desc[0] for desc in self.protocol.description]
        for block in row_generator:
            df = pd.DataFrame(block, columns=columns)
            dfs.append(df)

        df = pd.concat(dfs, ignore_index=True)

        return df

    # @timeit
    async def query(self, sql, unbuffered=False, generator=False):
        start = datetime.datetime.now()
        await self.protocol.query(sql)
        end = datetime.datetime.now()
        self.current_execute_time = round((end - start).total_seconds(), 2)

        if not generator:
            self._affected_rows = await self._read_query_result(unbuffered)
        else:
            self._affected_rows = self._read_query_result_generator(unbuffered)

    async def next_result(self, unbuffered=False):
        self._affected_rows = await self._read_query_result(unbuffered=unbuffered)
        return self._affected_rows

    def cursor(self, *cursors):
        """Instantiates and returns a cursor

        By default, :class:`Cursor` is returned. It is possible to also give a
        custom cursor through the cursor_class parameter, but it needs to
        be a subclass  of :class:`Cursor`.

        Note: this function should be treated as async function. Otherwise,
        it would just return a '_ContextManager' object.

        :param cursor: custom cursor class.
        :returns: instance of cursor, by default :class:`Cursor`
        :raises TypeError: cursor_class is not a subclass of Cursor.
        """
        # self._ensure_alive()
        self._last_usage = self._loop.time()
        try:
            if cursors and any(not issubclass(cursor, Cursor) for cursor in cursors):
                raise TypeError("Custom cursor must be subclass of Cursor")
        except TypeError:
            raise TypeError("Custom cursor must be subclass of Cursor")
        if cursors and len(cursors) == 1:
            cur = cursors[0](self, self._echo)
        elif cursors:
            cursor_name = (
                "".join(map(lambda x: x.__name__, cursors)).replace("Cursor", "")
                + "Cursor"
            )
            cursor_class = type(cursor_name, cursors, {})
            cur = cursor_class(self, self._echo)
        else:
            cur = self.cursorclass(self, self._echo)
        fut = self._loop.create_future()
        fut.set_result(cur)
        return _ContextManager(fut)

    async def _read_query_result(self, unbuffered=False):
        self._result = None
        if unbuffered:
            try:
                result = ResultSet(self.protocol)
                result.init_unbuffered_query()
            except:
                result.unbuffered_active = False
                result.protocol = None
                raise
        else:
            result = ResultSet(self.protocol)
            await result.read()

        self._result = result
        return result.affected_rows

    async def _read_query_result_generator(self, unbuffered=False) -> Optional[int]:
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
    def __init__(self, protocol: WirelineProtocol):
        self.protocol: Optional[WirelineProtocol] = protocol
        self.affected_rows = None
        self.rows = None
        self.unbuffered = False
        self.description = None
        self.field_count = 0
        self.err = None
        self.has_next = None  # should be bool, decide if there is next row

        if isinstance(self.protocol, WirelineProtocol):
            self.has_next = self.protocol.has_next

    # buffered result, cache all the data to the client
    async def read(self):
        rows = []

        try:
            while await self.protocol.get_next_set():
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

    async def read_generator(self):

        async def merge_chunk():
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

            async for _chunk in merge_chunk():
                yield _chunk

            while await self.protocol.get_next_set():
                async for _chunk in merge_chunk():
                    yield _chunk

            async for _chunk in merge_chunk():
                yield _chunk

            self.has_next = self.protocol.has_next

        except Exception as e:
            log.debug("No more data: %s", str(e))
            self.has_next = False

    def init_unbuffered_query(self):
        self.description = self.protocol.description
        self.field_count = self.protocol.numColumns
        self.err = self.protocol.errstr
        self.affected_rows = -1
        self.unbuffered = True
        if self.err:
            raise aiordp.ProgrammingError(self.err)

    async def _finish_unbuffered_query(self):
        while self.has_next:
            await self.read()
        self.protocol = None

    async def read_next_row(self):
        if not self.unbuffered or self.protocol is None:
            return

        has_next = await self.protocol.get_next_row()
        if self.protocol and has_next:
            row = self.protocol.row
        else:
            self.protocol = None
            row = None

        self.rows = (row,)

        if row is not None:
            self.affected_rows = 1

        return row
