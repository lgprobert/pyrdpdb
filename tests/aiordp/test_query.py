# flake8: noqa: F401, E501
from datetime import datetime as Datetime
from datetime import timezone as Timezone

import pytest

from pyrdpdb import aiordp
from tests.config import connector_name


@pytest.mark.asyncio
async def test_database_error(cursor) -> None:
    cur: aiordp.Cursor = cursor
    with pytest.raises(aiordp.RDBError):
        await cur.execute("INSERT INTO t99 VALUES (1, 2, 3)")


@pytest.mark.asyncio
async def test_parallel_queries(t1_table, con) -> None:
    cursor: aiordp.Cursor = t1_table
    conn: aiordp.Connection = con
    await cursor.execute(
        f"INSERT INTO {connector_name}.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (1, 1, None)
    )
    await cursor.execute(
        f"INSERT INTO {connector_name}.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (2, 10, None)
    )
    await cursor.execute(
        f"INSERT INTO {connector_name}.t1 (f1, f2, f3) VALUES (%s, %s, %s)",
        (3, 100, None),
    )
    await cursor.execute(
        f"INSERT INTO {connector_name}.t1 (f1, f2, f3) VALUES (%s, %s, %s)",
        (4, 1000, None),
    )
    await cursor.execute(
        f"INSERT INTO {connector_name}.t1 (f1, f2, f3) VALUES (%s, %s, %s)",
        (5, 10000, None),
    )
    c1: aiordp.Cursor = await conn.cursor()
    c2: aiordp.Cursor = await conn.cursor()
    await c1.execute(f"SELECT f1, f2, f3 FROM {connector_name}.t1")
    rset = await c1.fetchall()
    for row in rset:
        f1, f2, f3 = row
        await c2.execute(
            f"SELECT f1, f2, f3 FROM {connector_name}.t1 WHERE f1 > %s", (f1,)
        )
        c2_rset = await c2.fetchall()
        for row in c2_rset:
            f1, f2, f3 = row


@pytest.mark.asyncio
async def test_create_table(t1_table) -> None:
    cursor: aiordp.Cursor = t1_table
    await cursor.execute(f"select * from {connector_name}.t1")
    await cursor.execute(f"drop table {connector_name}.t1")
    await cursor.execute(f"create table {connector_name}.t1 (f1 integer primary key)")
    await cursor.execute(f"select * from {connector_name}.t1")


@pytest.mark.asyncio
async def test_executemany(t1_table) -> None:
    cursor: aiordp.Cursor = t1_table
    await cursor.executemany(
        f"INSERT INTO {connector_name}.t1 (f1, f2, f3) VALUES (%s, %s, %s)",
        ((1, 1, "Avast ye!"), (2, 1, None)),
    )

    await cursor.executemany(
        "select CAST(%s AS TIMESTAMP)",
        ((Datetime(2014, 5, 7, tzinfo=Timezone.utc),), (Datetime(2014, 5, 7),)),
    )


@pytest.mark.asyncio
async def test_executemany_no_param_sets(con) -> None:
    conn: aiordp.Connection = con
    cursor: aiordp.Cursor = await conn.cursor()
    await cursor.executemany(
        f"INSERT INTO {connector_name}.t1 (f1, f2) VALUES (%s, %s)", []
    )
    assert cursor.rowcount == -1


@pytest.mark.asyncio
async def test_empty_query(cursor) -> None:
    """No exception thrown"""
    cur: aiordp.Cursor = cursor
    await cur.execute("")


@pytest.mark.asyncio
async def test_unexecuted_cursor_rowcount(con) -> None:
    conn: aiordp.Connection = con
    cursor: aiordp.Cursor = await conn.cursor()
    assert cursor.rowcount == -1


@pytest.mark.asyncio
async def test_unexecuted_cursor_description(con) -> None:
    conn: aiordp.Connection = con
    cursor: aiordp.Cursor = await conn.cursor()
    assert cursor.description is None


@pytest.mark.asyncio
async def test_null_result(t1_table) -> None:
    cursor: aiordp.Cursor = t1_table
    await cursor.execute(
        f"INSERT INTO {connector_name}.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (1, 1, "a")
    )
    rset = await cursor.fetchall()
    assert rset == []
