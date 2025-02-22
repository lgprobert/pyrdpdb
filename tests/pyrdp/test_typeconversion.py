# flake8: noqa: F401
import os
import time
from datetime import date, datetime, timedelta

import pytest

connector_name = "moxe"


def test_date_roundtrip(cursor):
    v = date(2001, 2, 3)
    cursor.execute("SELECT cast(%s as date) as f1", (v,))
    assert cursor.fetchall()[0][0] == v


def test_null_roundtrip(cursor):
    cursor.execute("SELECT %s", (None,))
    assert cursor.fetchall()[0][0] is None


def test_float_roundtrip(cursor):
    val = 1.756e-12
    cursor.execute("SELECT cast(%s as float)", (val,))
    assert cursor.fetchall()[0][0] == val


def test_str_roundtrip(cursor):
    v = "hello world"
    cursor.execute(
        f"create table if not exists {connector_name}.test_str (f character varying(255))"
    )
    cursor.execute(f"INSERT INTO {connector_name}.test_str VALUES (%s)", (v,))
    cursor.execute(f"SELECT * from {connector_name}.test_str")
    assert cursor.fetchall()[0][0] == v
    cursor.execute(f"drop table {connector_name}.test_str")


def test_unicode_roundtrip(cursor):
    v = "hello \u0173 world"
    cursor.execute("SELECT cast(%s as varchar) as f1", (v,))
    assert cursor.fetchall()[0][0] == v


def test_int_execute_many_select(cursor):
    cursor.executemany("SELECT CAST(%s AS INTEGER)", ((1,), (40000,)))
    cursor.fetchall()


def test_int_execute_many_insert(cursor):
    v = ([None], [4])
    cursor.execute(f"create table if not exists {connector_name}.test_int (f integer)")
    cursor.executemany(f"INSERT INTO {connector_name}.test_int VALUES (%s)", v)
    cursor.execute(f"SELECT * from {connector_name}.test_int")
    assert cursor.fetchall() == [tuple(val) for val in v]
    cursor.execute(f"drop table {connector_name}.test_int")


def test_insert_null(cursor):
    v = None
    cursor.execute(f"CREATE TABLE if not exists {connector_name}.test_int (f INTEGER)")
    cursor.execute(f"INSERT INTO {connector_name}.test_int VALUES (%s)", (v,))
    cursor.execute(f"SELECT * FROM {connector_name}.test_int")
    assert cursor.fetchall()[0][0] == v
    cursor.execute(f"drop table {connector_name}.test_int")


def test_timestamp_roundtrip(cursor):
    v = datetime(2001, 2, 3, 4, 5, 6, 170000)
    cursor.execute("SELECT cast(%s as timestamp)", (v,))
    assert cursor.fetchall()[0][0] == v

    # Test that time zone doesn't affect it
    orig_tz = os.environ.get("TZ")
    os.environ["TZ"] = "America/Edmonton"
    time.tzset()

    cursor.execute("SELECT cast(%s as timestamp)", (v,))
    assert cursor.fetchall()[0][0] == v

    if orig_tz is None:
        del os.environ["TZ"]
    else:
        os.environ["TZ"] = orig_tz
    time.tzset()


def test_name_out(cursor):
    # select a field that is of "name" type:
    cursor.execute("SELECT username FROM system.users")
    cursor.fetchall()
    # It is sufficient that no errors were encountered.


def test_boolean_in(cursor):
    cursor.execute("SELECT cast('1' as boolean)")
    assert cursor.fetchall()[0][0]


def test_interval_in_1_day(cursor):
    date_value = "2000-01-01"
    target_date = datetime.strptime(date_value, "%Y-%m-%d").date() + timedelta(days=1)
    cursor.execute(f"select cast('{date_value}' as date) + interval '1 day'")
    assert cursor.fetchall()[0][0] == target_date


def test_interval_in_30_seconds(cursor):
    date_value = "2000-01-01"
    target_date = datetime.strptime(date_value, "%Y-%m-%d")
    cursor.execute(f"select cast('{date_value}' as timestamp) + interval '30 seconds'")
    assert cursor.fetchall()[0][0] == target_date + timedelta(seconds=30)
