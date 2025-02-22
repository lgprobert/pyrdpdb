import gc

from pyrdpdb import aiordp
from pyrdpdb.aiordp._compat import CPYTHON


class PyRDPTestCase:
    _connections = None
    connector_name = "test_connector"

    @classmethod
    async def safe_create_table(
        self, cursor: aiordp.Cursor, tablename: str, ddl: str, cleanup=True
    ) -> None:
        await cursor.execute("DROP TABLE IF EXISTS %s" % (tablename,), quiet=True)
        await cursor.execute(ddl, quiet=True)

    @classmethod
    async def drop_table(self, cursor: aiordp.Cursor, tablename: str) -> None:
        await cursor.execute("DROP TABLE IF EXISTS %s" % (tablename,), quiet=True)

    @classmethod
    async def create_connector(
        self, cursor: aiordp.Cursor, connector_name: str, ddl: str
    ) -> None:
        if connector_name == "moxe":
            print("built-in connector 'moxe' don't need to be created.")
            return
        if not await cursor.has_connector(connector_name):
            await cursor.execute(ddl, quiet=True)

    @classmethod
    async def drop_connector(self, cursor: aiordp.Cursor, connectorname: str) -> None:
        connector = connectorname.upper()
        if connector == "MOXE":
            print("Built-in connector 'moxe' can't be dropped.")
            return
        await cursor.execute("DROP CONNECTOR %s" % (connector,), quiet=True)

    @classmethod
    async def create_federation(
        self, cursor: aiordp.Cursor, federationname: str, ddl: str
    ) -> None:
        if not cursor.has_federation(federationname):
            await cursor.execute(ddl)

    @classmethod
    async def drop_federation(self, cursor: aiordp.Cursor, federationname: str) -> None:
        await cursor.execute("DROP federation %s" % (federationname,), quiet=True)

    def safe_gc_collect(self):
        gc.collect()
        if not CPYTHON:
            gc.collect()
