# flake8: noqa: F401
import os
import time
from datetime import date, datetime, timedelta

import pytest

from pyrdpdb import aiordp

connector_name = "moxe"


@pytest.mark.asyncio
async def test_date_roundtrip(cursor: aiordp.Cursor):
    v = date(2001, 2, 3)
    await cursor.execute("SELECT cast(%s as date) as f1", (v,))
    assert (await cursor.fetchall())[0][0] == v


@pytest.mark.asyncio
async def test_null_roundtrip(cursor: aiordp.Cursor):
    await cursor.execute("SELECT %s", (None,))
    assert (await cursor.fetchall())[0][0] is None


@pytest.mark.asyncio
async def test_float_roundtrip(cursor: aiordp.Cursor):
    val = 1.756e-12
    await cursor.execute("SELECT cast(%s as float)", (val,))
    assert (await cursor.fetchall())[0][0] == val


@pytest.mark.asyncio
async def test_str_roundtrip(cursor: aiordp.Cursor):
    v = "hello world"
    await cursor.execute(
        f"create table if not exists {connector_name}.test_str (f character varying(255))"
    )
    await cursor.execute(f"INSERT INTO {connector_name}.test_str VALUES (%s)", (v,))
    await cursor.execute(f"SELECT * from {connector_name}.test_str")
    assert (await cursor.fetchall())[0][0] == v


@pytest.mark.asyncio
async def test_unicode_roundtrip(cursor: aiordp.Cursor):
    v = "hello \u0173 world"
    await cursor.execute("SELECT cast(%s as varchar) as f1", (v,))
    assert (await cursor.fetchall())[0][0] == v


@pytest.mark.asyncio
async def test_int_execute_many_select(cursor: aiordp.Cursor):
    await cursor.executemany("SELECT CAST(%s AS INTEGER)", ((1,), (40000,)))
    await cursor.fetchall()
    assert True


@pytest.mark.asyncio
async def test_int_execute_many_insert(cursor: aiordp.Cursor):
    v = ([None], [4])
    await cursor.execute(
        f"create table if not exists {connector_name}.test_int (f integer)"
    )
    await cursor.executemany(f"INSERT INTO {connector_name}.test_int VALUES (%s)", v)
    await cursor.execute(f"SELECT * from {connector_name}.test_int")
    assert (await cursor.fetchall()) == [tuple(val) for val in v]
    await cursor.execute(f"drop table {connector_name}.test_int")


@pytest.mark.asyncio
async def test_insert_null(cursor: aiordp.Cursor):
    v = None
    await cursor.execute(
        f"CREATE TABLE if not exists {connector_name}.test_int (f INTEGER)"
    )
    await cursor.execute(f"INSERT INTO {connector_name}.test_int VALUES (%s)", (v,))
    await cursor.execute(f"SELECT * FROM {connector_name}.test_int")
    assert (await cursor.fetchall())[0][0] == v
    await cursor.execute(f"drop table {connector_name}.test_int")


@pytest.mark.asyncio
async def test_timestamp_roundtrip(cursor: aiordp.Cursor):
    v = datetime(2001, 2, 3, 4, 5, 6, 170000)
    await cursor.execute("SELECT cast(%s as timestamp)", (v,))
    assert (await cursor.fetchall())[0][0] == v

    # Test that time zone doesn't affect it
    orig_tz = os.environ.get("TZ")
    os.environ["TZ"] = "America/Edmonton"
    time.tzset()

    await cursor.execute("SELECT cast(%s as timestamp)", (v,))
    assert (await cursor.fetchall())[0][0] == v

    if orig_tz is None:
        del os.environ["TZ"]
    else:
        os.environ["TZ"] = orig_tz
    time.tzset()


@pytest.mark.asyncio
async def test_name_out(cursor: aiordp.Cursor):
    # select a field that is of "name" type:
    await cursor.execute("SELECT username FROM system.users")
    await cursor.fetchall()
    # It is sufficient that no errors were encountered.


@pytest.mark.asyncio
async def test_boolean_in(cursor: aiordp.Cursor):
    await cursor.execute("SELECT cast('1' as boolean)")
    assert (await cursor.fetchall())[0][0]


@pytest.mark.asyncio
async def test_interval_in_1_day(cursor: aiordp.Cursor):
    date_value = "2000-01-01"
    target_date = datetime.strptime(date_value, "%Y-%m-%d").date() + timedelta(days=1)
    await cursor.execute(f"select cast('{date_value}' as date) + interval '1 day'")
    assert (await cursor.fetchall())[0][0] == target_date


@pytest.mark.asyncio
async def test_interval_in_30_seconds(cursor: aiordp.Cursor):
    date_value = "2000-01-01"
    target_date = datetime.strptime(date_value, "%Y-%m-%d")
    await cursor.execute(
        f"select cast('{date_value}' as timestamp) + interval '30 seconds'"
    )
    assert (await cursor.fetchall())[0][0] == target_date + timedelta(seconds=30)
