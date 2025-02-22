from typing import AsyncGenerator

import pytest
import pytest_asyncio

from pyrdpdb import aiordp

from .base import PyRDPTestCase
from .conftest import db_kwargs

tablename = "test_table"
tableddl = "create table if not exists {} (id Integer, test_colum varchar(20))".format(
    tablename
)


@pytest_asyncio.fixture(loop_scope="class")
async def conn() -> AsyncGenerator[tuple[aiordp.Connection, str], None]:
    db_args, connector_ddl = db_kwargs()
    conn: aiordp.Connection = await aiordp.connect(**db_args)

    yield conn, connector_ddl

    conn.close()


@pytest_asyncio.fixture(loop_scope="function")
async def cursor_(conn) -> AsyncGenerator[aiordp.Cursor, None]:
    _conn: aiordp.Connection
    _conn, _ = conn
    cursor: aiordp.Cursor = await _conn.cursor()
    await PyRDPTestCase().safe_create_table(cursor, "test_table", tableddl)

    yield cursor

    await PyRDPTestCase().drop_table(cursor, tablename)
    await cursor.close()


class TestCursor:

    connectorname = "moxe"
    insert_stmt = f"insert into {tablename} (Id, test_colum) values {{}}"

    @pytest.mark.asyncio
    async def test_execute(self, cursor_: aiordp.Cursor, capsys):
        cursor_.timing()  # turn on cursor timing flag
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)  # stdout: 0 rows

        sql = f"select * from {tablename} where test_colum='test'"
        count = await cursor_.execute(sql)  # stdout: 1 rows
        assert count == 1

        captured_output: str = capsys.readouterr().out
        captured = captured_output.splitlines()

        assert captured[0] == "Timing is ON."
        assert "0 rows" in captured[1]
        assert "1 rows" in captured[2]
        assert "sec)" in captured[2]

        sql = f"insert into {tablename} values(%s, %s)"
        arg = (2, "test")
        await cursor_.execute(sql, arg)
        sql = f"select * from {tablename} where test_colum='test'"
        count = await cursor_.execute(sql)
        assert count == 2

        # update  UPDATE Person SET FirstName = 'Fred' WHERE LastName = 'Wilson'
        # sql = "update test_table  set test_colum = 'update' where test_colum='test'"
        # await cursor.execute(sql)
        # sql = "select * from test_table where test_colum='update'"
        # count = await cursor.execute(sql)
        # assert count == 1

        # delete
        # sql = "delete from test_table where test_colum='test' "
        # await cursor.execute(sql)
        # sql = "select * from test_table"
        # count = await cursor.execute(sql)
        # assert count == 0

    @pytest.mark.asyncio
    async def test_executemany(self, cursor_: aiordp.Cursor):
        cursor = cursor_
        if await cursor.has_table("test_table"):
            await cursor.execute("truncate table test_table")

        sql = f"insert into {tablename} values (%s, %s)"
        args = [(1, "a"), (2, "b"), (3, "c")]
        rcount = await cursor.executemany(sql, args)
        assert rcount == 3  # inserted rows is 3
        await cursor.execute("select * from test_table")
        rset = await cursor.fetchall()
        assert rset == [(1, "a"), (2, "b"), (3, "c")]

        sql = "select test_colum from test_table where test_colum = %s"
        qargs = [("a",), ("b",), ("c",)]
        await cursor.executemany(sql, qargs)
        count = cursor.rowcount
        # executemany() returns sum of affected_rows of each run
        assert count == 3
        # "executemany()" for select query only reserve result of last run
        assert (await cursor.fetchall()) == [("c",)]

    @pytest.mark.asyncio
    async def test_fetchone(self, cursor_: aiordp.Cursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = f"select * from {tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchone()
        res = [res]
        assert len(res) == 1

    @pytest.mark.asyncio
    async def test_fetchone_and_fetchone(self, cursor_: aiordp.Cursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = f"select * from {tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchone()
        res = [res]
        assert len(res), 1
        res = await cursor_.fetchone()
        assert res is None

    @pytest.mark.asyncio
    async def test_fetchone_and_fetchmany(self, cursor_: aiordp.Cursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = f"select * from {tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchone()
        res = [res]
        assert len(res), 1
        res = await cursor_.fetchmany()
        assert len(res) == 0

    @pytest.mark.asyncio
    async def test_fetchone_and_fetchall(self, cursor_: aiordp.Cursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = f"select * from {tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchone()
        res = [res]
        assert len(res) == 1
        res = await cursor_.fetchall()
        assert len(res) == 0

    @pytest.mark.asyncio
    async def test_fetchmany(self, cursor_: aiordp.Cursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = self.insert_stmt.format("(2, 'test2')")
        await cursor_.execute(sql)
        sql = f"select * from {tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchmany(2)
        assert len(res) == 2

    @pytest.mark.asyncio
    async def test_fetchmany_and_fetchone(self, cursor_: aiordp.Cursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = self.insert_stmt.format("(2, 'test2')")
        await cursor_.execute(sql)
        sql = f"select * from {tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchmany(2)
        assert len(res) == 2
        res = await cursor_.fetchone()
        assert res is None

    @pytest.mark.asyncio
    async def test_fetchmany_and_fetchall(self, cursor_: aiordp.Cursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = self.insert_stmt.format("(2, 'test2')")
        await cursor_.execute(sql)
        sql = f"select * from {tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchmany(2)
        assert len(res) == 2
        res = await cursor_.fetchall()
        assert len(res) == 0

    @pytest.mark.asyncio
    async def test_fetchall(self, cursor_: aiordp.Cursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = self.insert_stmt.format("(2, 'test2')")
        await cursor_.execute(sql)
        sql = f"select * from {tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchall()
        assert len(res) == 2

    @pytest.mark.asyncio
    async def test_fetchall_and_fetchone(self, cursor_: aiordp.Cursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = self.insert_stmt.format("(2, 'test2')")
        await cursor_.execute(sql)
        sql = f"select * from {tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchall()
        assert len(res) == 2
        res = await cursor_.fetchone()
        assert res is None
        res = await cursor_.fetchmany()
        assert len(res) == 0
        res = await cursor_.fetchall()
        assert len(res) == 0
