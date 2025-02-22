# flake8: noqa: F401
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio

from pyrdpdb import aiordp
from pyrdpdb.aiordp.cursors import SSCursor
from tests.config import connector_name

from .base import PyRDPTestCase
from .conftest import db_kwargs

tablename = "test_table"
tableddl = "create table if not exists {}.{} (id Integer, test_colum varchar(20))".format(
    connector_name, tablename
)


@pytest_asyncio.fixture(loop_scope="class")
async def rdpconn() -> AsyncGenerator[tuple[aiordp.Connection, str], None]:
    db_args, connector_ddl = db_kwargs()
    db_args["cursorclass"] = SSCursor
    rdpconn: aiordp.Connection = await aiordp.connect(**db_args)
    try:
        yield rdpconn, connector_ddl
    finally:
        rdpconn.close()


@pytest_asyncio.fixture(loop_scope="function")
async def cursor_(rdpconn) -> AsyncGenerator[aiordp.SSCursor, None]:
    _conn: aiordp.Connection
    _conn, _ = rdpconn
    cursor: aiordp.SSCursor = await _conn.cursor()
    await PyRDPTestCase().safe_create_table(cursor, "test_table", tableddl)

    try:
        yield cursor
    finally:
        await PyRDPTestCase().drop_table(cursor, tablename)
        await cursor.close()


class TestSSCursor:

    tablename = "test_table"
    insert_stmt = f"insert into {connector_name}.{tablename} (Id, test_colum) values {{}}"

    @pytest.mark.asyncio
    async def test_cursor_type(self, rdpconn) -> None:
        _conn: aiordp.Connection
        _conn, _ = rdpconn
        async with _conn.cursor() as cursor:
            assert isinstance(cursor, SSCursor)

    @pytest.mark.asyncio
    async def test_execute(self, cursor_: aiordp.SSCursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = f"select * from {self.tablename} where test_colum='test'"
        count = await cursor_.execute(sql)
        assert count == -1

    @pytest.mark.asyncio
    async def test_fetchone(self, cursor_: aiordp.SSCursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = f"select * from {self.tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchone()
        res = [res]
        assert len(res) == 1

    @pytest.mark.asyncio
    async def test_fetchone_and_fetchone(self, cursor_: aiordp.SSCursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = f"select * from {self.tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchone()
        res = [res]
        assert len(res) == 1
        res = await cursor_.fetchone()
        assert res is None

    @pytest.mark.asyncio
    async def test_fetchone_and_fetchmany(self, cursor_: aiordp.SSCursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = f"select * from {self.tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchone()
        res = [res]
        assert len(res) == 1
        res = await cursor_.fetchmany()
        assert len(res) == 0

    @pytest.mark.asyncio
    async def test_fetchone_and_fetchall(self, cursor_: aiordp.SSCursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = f"select * from {self.tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchone()
        res = [res]
        assert len(res) == 1
        # res = await cursor_.fetchall()
        # assert len(res) == 0

    @pytest.mark.asyncio
    async def test_fetchmany(self, cursor_: aiordp.SSCursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = self.insert_stmt.format("(2, 'test2')")
        await cursor_.execute(sql)
        sql = f"select * from {self.tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchmany(2)
        assert len(res) == 2

    @pytest.mark.asyncio
    async def test_fetchmany_and_fetchone(self, cursor_: aiordp.SSCursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = self.insert_stmt.format("(2, 'test2')")
        await cursor_.execute(sql)
        sql = f"select * from {self.tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchmany(2)
        assert len(res) == 2
        res = await cursor_.fetchone()
        assert res is None

    @pytest.mark.asyncio
    async def test_fetchmany_and_fetchall(self, cursor_: aiordp.SSCursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = self.insert_stmt.format("(2, 'test2')")
        await cursor_.execute(sql)
        sql = f"select * from {self.tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchmany(2)
        assert len(res) == 2
        # res = await cursor_.fetchall()
        # assert len(res) == 0

    @pytest.mark.asyncio
    async def test_fetchall(self, cursor_: aiordp.SSCursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = self.insert_stmt.format("(2, 'test2')")
        await cursor_.execute(sql)
        sql = f"select * from {self.tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchall()
        assert len(res) == 2

    @pytest.mark.asyncio
    async def test_fetchall_and_fetchone(self, cursor_: aiordp.SSCursor):
        sql = self.insert_stmt.format("(1, 'test')")
        await cursor_.execute(sql)
        sql = self.insert_stmt.format("(2, 'test2')")
        await cursor_.execute(sql)
        sql = f"select * from {self.tablename}"
        await cursor_.execute(sql)
        res = await cursor_.fetchall()
        assert len(res) == 2
        res = await cursor_.fetchone()
        assert res is None
        res = await cursor_.fetchmany()
        assert len(res) == 0
        res = await cursor_.fetchall()
        assert len(res) == 0
