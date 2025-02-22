# flake8: noqa: F401
import unittest
import pytest

from pyrdpdb import pyrdp
from tests.pyrdp.base import PyRDPTestCase

from .conftest import db_kwargs


class ConnectorTest(unittest.TestCase):

    connector_name = "test_connector"

    def setUp(self):
        db_args, self.connector_ddl = db_kwargs()
        self.conn = pyrdp.connect(**db_args)
        self.test_cursor = self.conn.cursor()

    def tearDown(self):
        self.test_cursor.close()
        self.conn.close()

    def test_create_jdbc_connector(self):
        PyRDPTestCase.create_connector(
            self.test_cursor, self.connector_name, self.connector_ddl
        )
        result = self.test_cursor.execute(
            f"select * from connectors where connector_name='{self.connector_name.upper()}'"
        )
        self.assertEqual(result, 1)
        PyRDPTestCase.drop_connector(self.test_cursor, self.connector_name)

    def test_drop_connector(self):
        PyRDPTestCase.create_connector(
            self.test_cursor, self.connector_name, self.connector_ddl
        )
        PyRDPTestCase.drop_connector(self.test_cursor, self.connector_name)
        result = self.test_cursor.execute(
            "select * from connectors where connector_name='test_connector';"
        )
        self.assertEqual(result, 0)
