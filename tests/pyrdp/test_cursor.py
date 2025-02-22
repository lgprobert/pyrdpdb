import unittest
from io import StringIO

from pyrdpdb import pyrdp

from .base import PyRDPTestCase
from .conftest import db_kwargs


class CursorTest(unittest.TestCase):

    tablename = "test_table"
    connectorname = "moxe"
    insert_stmt = f"insert into {tablename} (id, test_colum) values {{}}"
    tableddl = (
        "create table if not exists {} (id Integer, test_colum varchar(20))".format(
            tablename
        )
    )

    @classmethod
    def setUpClass(cls) -> None:
        db_args, connector_ddl = db_kwargs()
        cls.conn = pyrdp.connect(**db_args)
        cursor = cls.conn.cursor()

        if not cursor.has_connector(cls.connectorname):
            PyRDPTestCase.create_connector(cursor, cls.connectorname, connector_ddl)
        cursor.close()
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        PyRDPTestCase.drop_connector(cls.conn.cursor(), cls.connectorname)
        cls.conn.close()
        return super().tearDownClass()

    def setUp(self):
        self.conn = self.__class__.conn
        self.cursor = self.conn.cursor()

        PyRDPTestCase().safe_create_table(self.cursor, "test_table", self.tableddl)

    def tearDown(self):
        PyRDPTestCase().drop_table(self.cursor, self.tablename)
        self.cursor.close()

    def test_execute(self):
        captured_output = StringIO()
        with unittest.mock.patch("sys.stdout", new=captured_output):
            self.cursor.timing()  # turn on cursor timing flag
            sql = self.insert_stmt.format("(1, 'test')")
            self.cursor.execute(sql)

            sql = f"select * from {self.tablename} where test_colum='test'"
            count = self.cursor.execute(sql)
            self.assertEqual(count, 1)

        # splitlines() strips new line character
        captured = captured_output.getvalue().splitlines()

        self.assertEqual(captured[0], "Timing is ON.")
        self.assertIn("0 rows", captured[1])
        self.assertIn("1 rows", captured[2])
        self.assertIn("sec)", captured[2])

        sql = f"insert into {self.tablename} values(%s, %s)"
        arg = (2, "test")
        self.cursor.execute(sql, arg)
        sql = f"select * from {self.tablename} where test_colum='test'"
        count = self.cursor.execute(sql)
        self.assertEqual(count, 2)

        # update  UPDATE Person SET FirstName = 'Fred' WHERE LastName = 'Wilson'
        # sql = "update test_table  set test_colum = 'update' where test_colum='test'"
        # cursor.execute(sql)
        # sql = "select * from test_table where test_colum='update'"
        # count = cursor.execute(sql)
        # self.assertEqual(count,1)

        # delete
        # sql = "delete from test_table where test_colum='test' "
        # cursor.execute(sql)
        # sql = "select * from test_table"
        # count = cursor.execute(sql)
        # self.assertEqual(count,0)

    def test_executemany(self):
        if self.cursor.has_table("test_table"):
            self.cursor.execute("truncate table test_table")

        sql = f"insert into {self.tablename} values (%s, %s)"
        args = [(1, "a"), (2, "b"), (3, "c")]
        rcount = self.cursor.executemany(sql, args)
        self.assertEqual(rcount, 3)  # inserted rows is 3
        self.cursor.execute("select * from test_table")
        self.assertEqual(self.cursor.fetchall(), [(1, "a"), (2, "b"), (3, "c")])

        sql = "select test_colum from test_table where test_colum = %s"
        args = [("a"), ("b"), ("c")]
        self.cursor.executemany(sql, args)
        count = self.cursor.rowcount
        # executemany() returns sum of affected_rows of each run
        self.assertEqual(count, 3)
        # "executemany()" for select query only reserve result of last run
        self.assertEqual(self.cursor.fetchall(), [("c",)])

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
        sql = f"select * from {self.tablename}"
        self.cursor.execute(sql)
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
