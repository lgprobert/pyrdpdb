# ported from:
# https://github.com/aio-libs/aiopg/blob/master/aiopg/sa/connection.py
import weakref

from sqlalchemy.sql import ClauseElement
from sqlalchemy.sql.ddl import DDLElement
from sqlalchemy.sql.dml import UpdateBase

from ..utils import _SAConnectionContextManager, _TransactionContextManager
from . import exc
from .result import create_result_proxy


def noop(k):
    return k


# class SAConnection(Connection):
class SAConnection:

    def __init__(self, connection, engine, compiled_cache=None):
        self._connection = connection
        # self._transaction = None
        # self._savepoint_seq = 0
        self._weak_results = weakref.WeakSet()
        self._engine = engine
        self.dialect = engine.dialect
        self._compiled_cache = compiled_cache

    def execute(self, query, quiet: bool = False, *multiparams, **params):
        """Executes a SQL query with optional parameters.

        query - a SQL query string or any sqlalchemy expression.

        *multiparams/**params - represent bound parameter values to be
        used in the execution.  Typically, the format is a dictionary
        passed to *multiparams:

            await conn.execute(
                table.insert(),
                {"id":1, "value":"v1"},
            )

        ...or individual key/values interpreted by **params::

            await conn.execute(
                table.insert(), id=1, value="v1"
            )

        In the case that a plain SQL string is passed, a tuple or
        individual values in *multiparams may be passed::

            await conn.execute(
                "INSERT INTO table (id, value) VALUES (%d, %s)",
                (1, "v1")
            )

            await conn.execute(
                "INSERT INTO table (id, value) VALUES (%s, %s)",
                1, "v1"
            )

        Returns ResultProxy instance with results of SQL query
        execution.

        """
        coro = self._execute(query, quiet, *multiparams, **params)
        return _SAConnectionContextManager(coro)

    def _base_params(self, query, dp, compiled, is_update):
        """
        handle params
        """
        if dp and isinstance(dp, (list, tuple)):
            if is_update:
                dp = {c.key: pval for c, pval in zip(query.table.c, dp)}
            else:
                raise exc.ArgumentError(
                    "Don't mix sqlalchemy SELECT " "clause with positional " "parameters"
                )
        compiled_params = compiled.construct_params(dp)
        processors = compiled._bind_processors
        params = [
            {
                key: processors.get(key, noop)(compiled_params[key])
                for key in compiled_params
            }
        ]
        post_processed_params = self.dialect.execute_sequence_format(params)
        return post_processed_params[0]

    async def _executemany(self, query, dps, cursor, quiet):
        """
        executemany
        """
        result_map = None
        if isinstance(query, str):
            await cursor.executemany(query, dps, quiet)
        elif isinstance(query, DDLElement):
            raise exc.ArgumentError(
                "Don't mix sqlalchemy DDL clause and execution with parameters"
            )
        elif isinstance(query, ClauseElement):
            compiled = query.compile(dialect=self.dialect)
            params = []
            is_update = isinstance(query, UpdateBase)
            for dp in dps:
                params.append(
                    self._base_params(
                        query,
                        dp,
                        compiled,
                        is_update,
                    )
                )
            await cursor.executemany(str(compiled), params)
            result_map = compiled._result_columns
        else:
            raise exc.ArgumentError(
                "sql statement should be str or "
                "SQLAlchemy data "
                "selection/modification clause"
            )
        ret = await create_result_proxy(self, cursor, self.dialect, result_map)
        self._weak_results.add(ret)
        return ret

    async def _execute(self, query, quiet: bool = False, *multiparams, **params):
        cursor = await self._connection.cursor()
        dp = _distill_params(multiparams, params)
        if len(dp) > 1:
            return await self._executemany(query, dp, cursor, quiet=quiet)
        elif dp:
            dp = dp[0]

        result_map = None
        if isinstance(query, str):
            await cursor.execute(query, dp or None, quiet=quiet)
        elif isinstance(query, ClauseElement):
            if self._compiled_cache is not None:
                key = query
                compiled = self._compiled_cache.get(key)
                if not compiled:
                    compiled = query.compile(dialect=self.dialect)
                    if (
                        dp
                        and dp.keys() == compiled.params.keys()
                        or not (dp or compiled.params)
                    ):
                        # we only want queries with bound params in cache
                        self._compiled_cache[key] = compiled
            else:
                compiled = query.compile(
                    dialect=self.dialect(),
                    compile_kwargs={"literal_binds": True},
                )

            if not isinstance(query, DDLElement):
                # post_processed_params = self._base_params(
                #     query, dp, compiled, isinstance(query, UpdateBase)
                # )
                result_map = compiled._result_columns
            else:
                if dp:
                    raise exc.ArgumentError(
                        "Don't mix sqlalchemy DDL clause and execution with parameters"
                    )
                # post_processed_params = compiled.construct_params()
                result_map = None

            # hard remove catalog 'RAPIDS.' from entity name in query
            fixed_sql = str(compiled).replace("RAPIDS.", "")
            await cursor.execute(fixed_sql, quiet=quiet)
            # await cursor.execute(str(compiled), post_processed_params)
        else:
            raise exc.ArgumentError(
                "sql statement should be str or "
                "SQLAlchemy data "
                "selection/modification clause"
            )
        ret = await create_result_proxy(self, cursor, self.dialect, result_map)
        self._weak_results.add(ret)
        return ret

    async def scalar(self, query, *multiparams, **params):
        """Executes a SQL query and returns a scalar value."""
        res = await self.execute(query, *multiparams, **params)
        return await res.scalar()

    @property
    def closed(self):
        """The readonly property that returns True if connections is closed."""
        return self._connection is None or self._connection.closed

    @property
    def connection(self):
        return self._connection

    async def begin(self):
        coro = self._begin()
        return _TransactionContextManager(coro)

    async def _begin(self):
        if self._transaction is None:
            self._transaction = RootTransaction(self)
            return self._transaction
        else:
            return Transaction(self, self._transaction)

    async def close(self):
        """Close this SAConnection.

        This results in a release of the underlying database
        resources, that is, the underlying connection referenced
        internally. The underlying connection is typically restored
        back to the connection-holding Pool referenced by the Engine
        that produced this SAConnection. Any transactional state
        present on the underlying connection is also unconditionally
        released via calling Transaction.rollback() method.

        After .close() is called, the SAConnection is permanently in a
        closed state, and will allow no further operations.
        """
        if self._connection is None:
            return

        # if self._transaction is not None:
        #     await self._transaction.rollback()
        #     self._transaction = None
        # don't close underlying connection, it can be reused by pool
        # conn.close()
        self._engine.release(self)
        self._connection = None
        self._engine = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class Transaction:

    def __init__(self, connection, parent):
        self._connection = connection
        self._parent = parent or self
        self._is_active = True

    @property
    def is_active(self):
        """Return ``True`` if a transaction is active."""
        return self._is_active

    @property
    def connection(self):
        """Return transaction's connection (SAConnection instance)."""
        return self._connection

    async def close(self):
        """Close this transaction.

        If this transaction is the base transaction in a begin/commit
        nesting, the transaction will rollback().  Otherwise, the
        method returns.

        This is used to cancel a Transaction without affecting the scope of
        an enclosing transaction.
        """
        if not self._parent._is_active:
            return
        if self._parent is self:
            await self.rollback()
        else:
            self._is_active = False

    # async def rollback(self):
    #     """Roll back this transaction."""
    #     if not self._parent._is_active:
    #         return
    #     await self._do_rollback()
    #     self._is_active = False

    # async def _do_rollback(self):
    #     await self._parent.rollback()

    # async def commit(self):
    #     """Commit this transaction."""

    #     if not self._parent._is_active:
    #         raise exc.InvalidRequestError("This transaction is inactive")
    #     await self._do_commit()
    #     self._is_active = False

    # async def _do_commit(self):
    #     pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        else:
            if self._is_active:
                await self.commit()


class RootTransaction(Transaction):

    def __init__(self, connection):
        super().__init__(connection, None)

    # async def _do_rollback(self):
    #     await self._connection._rollback_impl()

    # async def _do_commit(self):
    #     await self._connection._commit_impl()


def _distill_params(multiparams, params):
    """Given arguments from the calling form *multiparams, **params,
    return a list of bind parameter structures, usually a list of
    dictionaries.

    In the case of 'raw' execution which accepts positional parameters,
    it may be a list of tuples or lists.

    """

    if not multiparams:
        if params:
            return [params]
        else:
            return []
    elif len(multiparams) == 1:
        zero = multiparams[0]
        if isinstance(zero, (list, tuple)):
            if not zero or hasattr(zero[0], "__iter__") and not hasattr(zero[0], "strip"):
                # execute(stmt, [{}, {}, {}, ...])
                # execute(stmt, [(), (), (), ...])
                return zero
            else:
                # execute(stmt, ("value", "value"))
                return [zero]
        elif hasattr(zero, "keys"):
            # execute(stmt, {"key":"value"})
            return [zero]
        else:
            # execute(stmt, "value")
            return [[zero]]
    else:
        if hasattr(multiparams[0], "__iter__") and not hasattr(multiparams[0], "strip"):
            return multiparams
        else:
            return [multiparams]
