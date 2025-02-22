# flake8: noqa: F401
from typing import AsyncGenerator

import pytest
import pytest_asyncio

from pyrdpdb import aiordp
from tests.aiordp.base import PyRDPTestCase

from .conftest import db_kwargs


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

    yield cursor

    await cursor.close()


class TestConnector:

    connector_name = "test_connector"

    @pytest.mark.asyncio
    async def test_create_jdbc_connector(self, conn, cursor_) -> None:
        _, connector_ddl = conn
        cur: aiordp.Cursor = cursor_
        await PyRDPTestCase.create_connector(cur, self.connector_name, connector_ddl)
        result = await cur.execute(
            f"select * from connectors where connector_name='{self.connector_name.upper()}'"
        )
        assert result == 1
        await PyRDPTestCase.drop_connector(cur, self.connector_name)

    @pytest.mark.asyncio
    async def test_drop_connector(self, conn, cursor_) -> None:
        _, connector_ddl = conn
        cur: aiordp.Cursor = cursor_
        await PyRDPTestCase.create_connector(cur, self.connector_name, connector_ddl)

        await PyRDPTestCase.drop_connector(cur, self.connector_name)
        result = await cur.execute(
            f"select * from connectors where connector_name='{self.connector_name.upper()}'"
        )
        assert result == 0
