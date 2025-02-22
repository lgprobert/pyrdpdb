import datetime
from datetime import date as Date
from datetime import datetime as Datetime
from datetime import time as Time

import pytest

from pyrdpdb import aiordp


def Timestamp(year, month, day, hour, minute, second):
    """Construct an object holding a timestamp value.

    This function is part of the `DBAPI 2.0 specification
    <http://www.python.org/dev/peps/pep-0249/>`_.

    :rtype: :class:`datetime.datetime`
    """
    return Datetime(year, month, day, hour, minute, second)


@pytest.mark.asyncio
async def test_parallel_queries(con, t1_table) -> None:
    conn: aiordp.Connection = con
    c1: aiordp.Cursor = await conn.cursor()
    c2: aiordp.Cursor = await conn.cursor()

    await c1.execute("SELECT f1, f2, f3 FROM moxe.t1")
    while 1:
        row = await c1.fetchone()
        if row is None:
            break
        f1, f2, f3 = row
        await c2.execute("SELECT f1, f2, f3 FROM moxe.t1 WHERE f1 > %s", (f1,))
        while 1:
            row = await c2.fetchone()
            if row is None:
                break
            f1, f2, f3 = row


@pytest.mark.asyncio
async def test_format(mocker, t1_table) -> None:
    mocker.patch("pyrdpdb.aiordp.paramstyle", "format")
    c1: aiordp.Cursor = t1_table
    await c1.execute("SELECT f1, f2, f3 FROM moxe.t1 WHERE f1 > %s", (3,))
    while 1:
        row = await c1.fetchone()
        if row is None:
            break
        f1, f2, f3 = row


@pytest.mark.asyncio
async def test_arraysize(t1_table) -> None:
    c1: aiordp.Cursor = t1_table
    c1.arraysize = 3
    await c1.execute("SELECT * FROM moxe.t1")
    retval = await c1.fetchmany()
    assert len(retval) == c1.arraysize


def test_date():
    val = Date(2001, 2, 3)
    assert val == datetime.date(2001, 2, 3)


def test_time():
    val = Time(4, 5, 6)
    assert val == datetime.time(4, 5, 6)


def test_timestamp():
    val = Timestamp(2001, 2, 3, 4, 5, 6)
    assert val == datetime.datetime(2001, 2, 3, 4, 5, 6)


@pytest.mark.asyncio
async def test_rowcount(t1_table) -> None:
    c1: aiordp.Cursor = t1_table
    await c1.execute("SELECT * FROM moxe.t1")

    assert c1.rowcount == 5


@pytest.mark.asyncio
async def test_fetch_many(t1_table) -> None:
    cursor: aiordp.Cursor = t1_table
    cursor.arraysize = 2
    await cursor.execute("SELECT * FROM moxe.t1")
    assert 2 == len(await cursor.fetchmany())
    assert 2 == len(await cursor.fetchmany())
    assert 1 == len(await cursor.fetchmany())
    assert 0 == len(await cursor.fetchmany())


@pytest.mark.asyncio
async def test_iterator(t1_table) -> None:
    cursor: aiordp.Cursor = t1_table
    await cursor.execute("SELECT * FROM moxe.t1 ORDER BY f1")
    f1 = 0
    rset = await cursor.fetchall()
    for row in rset:
        next_f1 = row[0]
        assert next_f1 > f1
        f1 = next_f1


def test_cursor_type(cursor):
    assert isinstance(cursor, aiordp.Cursor)
