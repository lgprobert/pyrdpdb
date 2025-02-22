import gc
import unittest

from pyrdpdb import pyrdp
from pyrdpdb.pyrdp._compat import CPYTHON


class PyRDPTestCase(unittest.TestCase):
    _connections = None
    connector_name = "test_connector"

    @classmethod
    def safe_create_table(
        self, cursor: pyrdp.Cursor, tablename, ddl, cleanup=True
    ) -> None:
        cursor.execute("DROP TABLE IF EXISTS %s" % (tablename,), quiet=True)
        cursor.execute(ddl, quiet=True)

    @classmethod
    def drop_table(self, cursor: pyrdp.Cursor, tablename) -> None:
        cursor.execute("DROP TABLE IF EXISTS %s" % (tablename,), quiet=True)

    @classmethod
    def create_connector(self, cursor: pyrdp.Cursor, connector_name: str, ddl) -> None:
        if connector_name == "moxe":
            print("built-in connector 'moxe' don't need to be created.")
            return
        cursor.execute(ddl, quiet=True)

    @classmethod
    def drop_connector(self, cursor: pyrdp.Cursor, connectorname) -> None:
        if connectorname == "moxe":
            print("Built-in connector 'moxe' can't be dropped.")
            return
        cursor.execute("DROP CONNECTOR %s" % (connectorname,), quiet=True)

    @classmethod
    def create_federation(self, cursor: pyrdp.Cursor, federationname, ddl) -> None:
        if not cursor.has_federation(federationname):
            cursor.execute(ddl)

    @classmethod
    def drop_federation(self, cursor: pyrdp.Cursor, federationname) -> None:
        cursor.execute("DROP federation %s" % (federationname,), quiet=True)

    def safe_gc_collect(self):
        gc.collect()
        if not CPYTHON:
            gc.collect()
