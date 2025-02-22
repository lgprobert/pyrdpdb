# flake8: noqa: F401
import unittest

import pytest

from pyrdpdb import pyrdp
from pyrdpdb.pyrdp.cursors import SSCursor
from tests.config import connector_name

from .base import PyRDPTestCase
from .conftest import db_kwargs


class SSCursorTest(unittest.TestCase):

    tablename = "test_table"
    connectorname = connector_name
    insert_stmt = f"insert into {connectorname}.{tablename} (Id, test_colum) values {{}}"
    tableddl = (
        "create table if not exists {}.{} (id Integer, test_colum varchar(20))".format(
            connectorname, tablename
        )
    )

    @classmethod
    def setUpClass(cls) -> None:
        db_args, connector_ddl = db_kwargs()
        db_args["cursorclass"] = SSCursor
        cls.conn = pyrdp.connect(**db_args)  # type: ignore
        cursor: pyrdp.SSCursor = cls.conn.cursor()  # type: ignore

        if not cursor.has_connector(cls.connectorname):
            PyRDPTestCase.create_connector(cursor, cls.connectorname, connector_ddl)
        cursor.close()
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        PyRDPTestCase.drop_connector(cls.conn.cursor(), cls.connectorname)  # type: ignore
        cls.conn.close()  # type: ignore
        return super().tearDownClass()

    def setUp(self) -> None:
        self.conn = self.__class__.conn  # type: ignore
        self.cursor: pyrdp.SSCursor = self.conn.cursor()
        PyRDPTestCase.safe_create_table(self.cursor, self.tablename, self.tableddl)

    def tearDown(self):
        PyRDPTestCase.drop_table(self.cursor, self.tablename)
        self.cursor.close()

    def test_cursor_type(self):
        assert isinstance(self.cursor, pyrdp.SSCursor)

    def test_execute(self):
        sql = self.insert_stmt.format("(1, 'test')")
        self.cursor.execute(sql)
        sql = f"select * from {self.tablename} where test_colum='test'"
        count = self.cursor.execute(sql)
        self.assertEqual(count, -1)

    def test_fetchone(self):
        sql = self.insert_stmt.format("(1, 'test')")
        self.cursor.execute(sql)
        sql = f"select * from {self.tablename}"
        self.cursor.execute(sql)
        res = self.cursor.fetchone()
        res = [res]
        self.assertEqual(len(res), 1)

    def test_fetchone_and_fetchone(self):
        sql = self.insert_stmt.format("(1, 'test')")
        self.cursor.execute(sql)
        sql = f"select * from {self.tablename}"
        self.cursor.execute(sql)
        res = self.cursor.fetchone()
        res = [res]
        self.assertEqual(len(res), 1)
        res = self.cursor.fetchone()
        self.assertEqual(res, None)

    def test_fetchone_and_fetchmany(self):
        sql = self.insert_stmt.format("(1, 'test')")
        self.cursor.execute(sql)
        sql = f"select * from {self.tablename}"
        self.cursor.execute(sql)
        res = self.cursor.fetchone()
        res = [res]
        self.assertEqual(len(res), 1)
        res = self.cursor.fetchmany()
        self.assertEqual(len(res), 0)

    def test_fetchone_and_fetchall(self):
        sql = self.insert_stmt.format("(1, 'test')")
        self.cursor.execute(sql)
        sql = f"select * from {self.tablename}"
        self.cursor.execute(sql)
        res = self.cursor.fetchone()
        res = [res]
        self.assertEqual(len(res), 1)
        res = self.cursor.fetchall()
        self.assertEqual(len(res), 0)

    def test_fetchmany(self):
        sql = self.insert_stmt.format("(1, 'test')")
        self.cursor.execute(sql)
        sql = self.insert_stmt.format("(2, 'test2')")
        self.cursor.execute(sql)
        sql = f"select * from {self.tablename}"
        self.cursor.execute(sql)
        res = self.cursor.fetchmany(2)
        self.assertEqual(len(res), 2)

    def test_fetchmany_and_fetchone(self):
        sql = self.insert_stmt.format("(1, 'test')")
        self.cursor.execute(sql)
        sql = self.insert_stmt.format("(2, 'test2')")
        self.cursor.execute(sql)
        sql = f"select * from {self.tablename}"
        self.cursor.execute(sql)
        res = self.cursor.fetchmany(2)
        self.assertEqual(len(res), 2)
        res = self.cursor.fetchone()
        self.assertEqual(res, None)

    def test_fetchmany_and_fetchall(self):
        sql = self.insert_stmt.format("(1, 'test')")
        self.cursor.execute(sql)
        sql = self.insert_stmt.format("(2, 'test2')")
        self.cursor.execute(sql)
        sql = f"select * from {self.tablename}"
        self.cursor.execute(sql)
        res = self.cursor.fetchmany(2)
        self.assertEqual(len(res), 2)
        res = self.cursor.fetchall()
        self.assertEqual(len(res), 0)

    def test_fetchall(self):
        sql = self.insert_stmt.format("(1, 'test')")
        self.cursor.execute(sql)
        sql = self.insert_stmt.format("(2, 'test2')")
        self.cursor.execute(sql)
        # breakpoint()
        sql = f"select * from {self.tablename}"
        self.cursor.execute(sql)
        # breakpoint()
        res = self.cursor.fetchall()
        self.assertEqual(len(res), 2)

    def test_fetchall_and_fetchone(self):
        sql = self.insert_stmt.format("(1, 'test')")
        self.cursor.execute(sql)
        sql = self.insert_stmt.format("(2, 'test2')")
        self.cursor.execute(sql)
        sql = f"select * from {self.tablename}"
        self.cursor.execute(sql)
        res = self.cursor.fetchall()
        self.assertEqual(len(res), 2)
        res = self.cursor.fetchone()
        self.assertEqual(res, None)
        res = self.cursor.fetchmany()
        self.assertEqual(len(res), 0)
        res = self.cursor.fetchall()
        self.assertEqual(len(res), 0)
