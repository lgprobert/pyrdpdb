# mypy: ignore-errors

r"""
.. dialect:: rapidsdb+asyncrdp
    :name: asyncrdp
    :dbapi: asyncrdp
    :connectstring: rapidsdb+asyncrdp://user:password@host:port/dbname[?key=value&key=value...]

The asyncrdp dialect is SQLAlchemy's second Python asyncio dialect.

Using a special asyncio mediation layer, the asyncrdp dialect is usable
as the backend for the :ref:`SQLAlchemy asyncio <asyncio_toplevel>`
extension package.

This dialect should normally be used only with the
:func:`_asyncio.create_async_engine` engine creation function::

    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(
        "rapidsdb+asyncrdp://user:pass@hostname:4333/federation/schema"
    )

"""  # noqa
from typing import TYPE_CHECKING

from sqlalchemy import pool, util
from sqlalchemy.connectors.asyncio import (
    AsyncAdapt_dbapi_connection,
    AsyncAdapt_dbapi_cursor,
    AsyncAdapt_dbapi_ss_cursor,
)
from sqlalchemy.dialects import registry
from sqlalchemy.pool.base import _ConnectionFairy
from sqlalchemy.util.concurrency import await_only

from .base import RDPDialect

if TYPE_CHECKING:
    from ..connections import Connection


class AsyncAdapt_asyncrdp_cursor(AsyncAdapt_dbapi_cursor):
    __slots__ = ()

    def _make_new_cursor(self, connection):
        return connection.cursor(self._adapt_connection.dbapi.Cursor)


class AsyncAdapt_asyncrdp_ss_cursor(
    AsyncAdapt_dbapi_ss_cursor, AsyncAdapt_asyncrdp_cursor
):
    __slots__ = ()

    def _make_new_cursor(self, connection):
        return connection.cursor(self._adapt_connection.dbapi.aiordp.cursors.SSCursor)


class AsyncAdapt_asyncrdp_connection(AsyncAdapt_dbapi_connection):
    __slots__ = ()

    _cursor_cls = AsyncAdapt_asyncrdp_cursor
    _ss_cursor_cls = AsyncAdapt_asyncrdp_ss_cursor

    # def ping(self, reconnect):
    #     assert not reconnect
    #     return await_(self._connection.ping(reconnect))

    def character_set_name(self):
        return self._connection.character_set_name()

    # def autocommit(self, value):
    #     await_(self._connection.autocommit(value))

    def terminate(self):
        # it's not awaitable.
        self._connection.close()

    def close(self) -> None:
        await_only(self._connection.ensure_closed())
        # await self._connection.ensure_closed()


class AsyncAdapt_asyncrdp_dbapi:
    def __init__(self, aiordp, pyrdp):
        self.aiordp = aiordp
        self.pyrdp = pyrdp
        self.paramstyle = "format"
        self._init_dbapi_attributes()
        self.Cursor, self.SSCursor = self._init_cursors_subclasses()

    def _init_dbapi_attributes(self):
        for name in (
            "Warning",
            "Error",
            "InterfaceError",
            "DataError",
            "DatabaseError",
            "OperationalError",
            "InterfaceError",
            "IntegrityError",
            "ProgrammingError",
            "InternalError",
            "NotSupportedError",
        ):
            setattr(self, name, getattr(self.aiordp, name))

        for name in (
            "NUMBER",
            "STRING",
            "DATETIME",
            "BINARY",
            "TIMESTAMP",
            "Binary",
        ):
            setattr(self, name, getattr(self.pyrdp, name))

    def connect(self, *arg, **kw):
        creator_fn = kw.pop("async_creator_fn", self.aiordp.connect)
        conn_ = AsyncAdapt_asyncrdp_connection(
            self,
            await_only(creator_fn(*arg, **kw)),
        )

        return conn_

    def _init_cursors_subclasses(self):
        # suppress unconditional warning emitted by asyncrdp
        class Cursor(self.aiordp.Cursor):
            async def _show_warnings(self, conn):
                pass

        class SSCursor(self.aiordp.SSCursor):
            async def _show_warnings(self, conn):
                pass

        return Cursor, SSCursor


class RDPDialect_asyncrdp(RDPDialect):
    driver = "asyncrdp"
    supports_statement_cache = True
    supports_savepoints = False
    supports_server_side_cursors = True
    _sscursor = AsyncAdapt_asyncrdp_ss_cursor

    is_async = True
    has_terminate = True

    @classmethod
    def import_dbapi(cls):
        try:
            from pyrdpdb import aiordp, pyrdp

            return AsyncAdapt_asyncrdp_dbapi(aiordp, pyrdp)
        except ImportError as e:
            raise ImportError(f"Failed to import required modules: {e}")

    @classmethod
    def get_pool_class(cls, url):
        async_fallback = url.query.get("async_fallback", False)

        if util.asbool(async_fallback):
            return pool.FallbackAsyncAdaptedQueuePool
        else:
            return pool.AsyncAdaptedQueuePool

    def do_terminate(self, dbapi_connection) -> None:
        """Terminate a DBAPI connection.

        Parameters:
        dbapi_connection: a :pep:`249` database connection.
        """
        dbapi_connection.terminate()

    def is_disconnect(self, e, connection: _ConnectionFairy, cursor):
        """Tells whether connection is closed.

        Parameters:
        - error: not used
        - connection: Optional[Connection]
        - cursor: not use

        Return: bool
        """
        conn: "Connection" = connection.connection._connection
        if conn is None:
            return True
        return conn.closed

    def get_driver_connection(self, connection):
        return connection


dialect = RDPDialect_asyncrdp
registry.register(
    "rapidsdb.asyncrdp", "pyrdpdb.aiordp.sa.asyncrapids", "RDPDialect_asyncrdp"
)
