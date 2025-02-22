import datetime
import os
import time
from datetime import date as Date
from datetime import datetime as Datetime
from datetime import time as Time
from typing import Any

import pytest

from pyrdpdb import pyrdp


def Timestamp(year, month, day, hour, minute, second):
    """Construct an object holding a timestamp value.

    This function is part of the `DBAPI 2.0 specification
    <http://www.python.org/dev/peps/pep-0249/>`_.

    :rtype: :class:`datetime.datetime`
    """
    return Datetime(year, month, day, hour, minute, second)


@pytest.fixture
def has_tzset():
    # Neither Windows nor Jython 2.5.3 have a time.tzset() so skip
    if hasattr(time, "tzset"):
        os.environ["TZ"] = "UTC"
        time.tzset()
        return True
    return False


# DBAPI compatible interface tests
@pytest.fixture
def db_table(con, has_tzset) -> Any:
    cursor: pyrdp.Cursor = con.cursor()

    def insert_rows():
        cursor.execute(
            "INSERT INTO moxe.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (1, 1, None)
        )
        cursor.execute(
            "INSERT INTO moxe.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (2, 10, None)
        )
        cursor.execute(
            "INSERT INTO moxe.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (3, 100, None)
        )
        cursor.execute(
            "INSERT INTO moxe.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (4, 1000, None)
        )
        cursor.execute(
            "INSERT INTO moxe.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (5, 10000, None)
        )

    if not cursor.has_table("t1", schema="moxe"):
        cursor.execute(
            """
            CREATE TABLE moxe.t1 (
                f1 integer primary key,
                f2 integer not null,
                f3 varchar(50) null
            )
    """
        )
        insert_rows()
    else:
        cursor.execute("select count(*) from moxe.t1")
        if cursor.fetchone()[0] != 5:
            cursor.execute("truncate table moxe.t1")
            insert_rows()
    return con


def test_parallel_queries(db_table) -> None:
    c1: pyrdp.Cursor = db_table.cursor()
    c2: pyrdp.Cursor = db_table.cursor()

    c1.execute("SELECT f1, f2, f3 FROM moxe.t1")
    while 1:
        row = c1.fetchone()
        if row is None:
            break
        f1, f2, f3 = row
        c2.execute("SELECT f1, f2, f3 FROM moxe.t1 WHERE f1 > %s", (f1,))
        while 1:
            row = c2.fetchone()
            if row is None:
                break
            f1, f2, f3 = row


# def test_qmark(mocker, db_table):
#     mocker.patch("pyrdp.paramstyle", "qmark")
#     c1 = db_table.cursor()
#     c1.execute("SELECT f1, f2, f3 FROM t1 WHERE f1 > ?", (3,))
#     while 1:
#         row = c1.fetchone()
#         if row is None:
#             break
#         f1, f2, f3 = row


# def test_numeric(mocker, db_table):
#     mocker.patch("pyrdp.paramstyle", "numeric")
#     c1 = db_table.cursor()
#     c1.execute("SELECT f1, f2, f3 FROM t1 WHERE f1 > :1", (3,))
#     while 1:
#         row = c1.fetchone()
#         if row is None:
#             break
#         f1, f2, f3 = row


# def test_named(mocker, db_table):
#     mocker.patch("pyrdp.paramstyle", "named")
#     c1 = db_table.cursor()
#     c1.execute("SELECT f1, f2, f3 FROM t1 WHERE f1 > :f1", {"f1": 3})
#     while 1:
#         row = c1.fetchone()
#         if row is None:
#             break
#         f1, f2, f3 = row


def test_format(mocker, db_table) -> None:
    mocker.patch("pyrdpdb.pyrdp.paramstyle", "format")
    c1: pyrdp.Cursor = db_table.cursor()
    c1.execute("SELECT f1, f2, f3 FROM moxe.t1 WHERE f1 > %s", (3,))
    while 1:
        row = c1.fetchone()
        if row is None:
            break
        f1, f2, f3 = row


# def test_pyformat(mocker, db_table):
#     mocker.patch("pyrdp.paramstyle", "pyformat")
#     c1 = db_table.cursor()
#     c1.execute("SELECT f1, f2, f3 FROM t1 WHERE f1 > %(f1)s", {"f1": 3})
#     while 1:
#         row = c1.fetchone()
#         if row is None:
#             break
#         f1, f2, f3 = row


def test_arraysize(db_table) -> None:
    c1: pyrdp.Cursor = db_table.cursor()
    c1.arraysize = 3
    c1.execute("SELECT * FROM moxe.t1")
    retval = c1.fetchmany()
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


def test_row_count(db_table) -> None:
    c1: pyrdp.Cursor = db_table.cursor()
    c1.execute("SELECT * FROM moxe.t1")

    assert 5 == c1.rowcount

    # c1.execute("UPDATE t1 SET f3 = %s WHERE f2 > 101", ("Hello!",))
    # assert 2 == c1.rowcount

    # c1.execute("DELETE FROM t1")
    # assert 5 == c1.rowcount


def test_fetch_many(db_table) -> None:
    cursor: pyrdp.Cursor = db_table.cursor()
    cursor.arraysize = 2
    cursor.execute("SELECT * FROM moxe.t1")
    assert 2 == len(cursor.fetchmany())
    assert 2 == len(cursor.fetchmany())
    assert 1 == len(cursor.fetchmany())
    assert 0 == len(cursor.fetchmany())


def test_iterator(db_table) -> None:
    cursor: pyrdp.Cursor = db_table.cursor()
    cursor.execute("SELECT * FROM moxe.t1 ORDER BY f1")
    f1 = 0
    for row in cursor.fetchall():
        next_f1 = row[0]
        assert next_f1 > f1
        f1 = next_f1


def test_cursor_type(cursor):
    assert str(type(cursor)) == "<class 'pyrdpdb.pyrdp.cursors.Cursor'>"
