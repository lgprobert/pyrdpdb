import time
from os import environ
from typing import AsyncGenerator

import pytest
import pytest_asyncio

from pyrdpdb import aiordp
from tests import config

from .base import PyRDPTestCase

connector_name = config.connector_name
jdbc_connector = "test_connector"


def db_kwargs():
    conn_args = {
        "user": config.user,
        "password": config.password,
        "database": config.database,
    }
    external_args = {
        "host": config.external_host,
        "port": config.external_port,
        "db_type": config.external_dbtype,
        "user": config.external_user,
        "password": config.external_password,
        "db": config.external_db,
    }
    connector_ddl = (
        f"create connector {jdbc_connector} type jdbc with "
        f"url='jdbc:{external_args['db_type']}://{external_args['host']}:{external_args['port']}/{external_args['db']}', "  # noqa
        f"user='{external_args['user']}', password ='{external_args['password']}' NODE * ;"  # noqa
    )

    for kw, var, f in [
        ("host", "RDP_HOST", str),
        ("password", "RDP_PASSWORD", str),
        ("port", "RDP_PORT", int),
    ]:
        try:
            conn_args[kw] = f(environ[var])
        except KeyError:
            pass

    return conn_args, connector_ddl


@pytest_asyncio.fixture(scope="module")
async def con() -> AsyncGenerator[aiordp.Connection, None]:
    conn_args, connector_ddl = db_kwargs()
    conn: aiordp.Connection = await aiordp.connect(**conn_args)

    cursor: aiordp.Cursor
    async with conn.cursor() as cursor:
        if not await cursor.has_connector(connector_name):
            await cursor.execute(connector_ddl)

    yield conn

    async with conn.cursor() as cursor:
        if await cursor.has_connector(connector_name):
            await PyRDPTestCase.drop_connector(cursor, connector_name)
    conn.close()


@pytest_asyncio.fixture
async def cursor(con) -> AsyncGenerator[aiordp.Cursor, None]:
    conn: aiordp.Connection = con
    cursor: aiordp.Cursor = await conn.cursor()

    yield cursor

    await cursor.close()


@pytest.fixture
def has_tzset():
    if hasattr(time, "tzset"):
        environ["TZ"] = "UTC"
        time.tzset()
        return True
    return False


@pytest_asyncio.fixture(loop_scope="function")
async def t1_table(cursor, has_tzset) -> AsyncGenerator[aiordp.Cursor, None]:
    c: aiordp.Cursor = cursor

    async def insert_rows():
        await c.execute(
            "INSERT INTO moxe.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (1, 1, None)
        )
        await c.execute(
            "INSERT INTO moxe.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (2, 10, None)
        )
        await c.execute(
            "INSERT INTO moxe.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (3, 100, None)
        )
        await c.execute(
            "INSERT INTO moxe.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (4, 1000, None)
        )
        await c.execute(
            "INSERT INTO moxe.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (5, 10000, None)
        )

    t1_ddl = """
            CREATE TABLE t1 (
                f1 integer primary key,
                f2 integer not null,
                f3 varchar(50) null
            )
        """
    if not await c.has_table("t1"):
        await PyRDPTestCase.safe_create_table(c, "t1", t1_ddl)
    else:
        await c.execute("select count(*) from moxe.t1")
        rset = await c.fetchone()
        if rset[0] != 5:
            await c.execute("truncate table moxe.t1")
    await insert_rows()

    yield c

    await PyRDPTestCase.drop_table(c, "t1")


@pytest_asyncio.fixture
async def rdp_version(cursor) -> str:
    _cursor: aiordp.Cursor = cursor
    await _cursor.execute("select version()")
    retval = _cursor.fetchall()
    major_version = retval[0][0].split()[1]
    return major_version
