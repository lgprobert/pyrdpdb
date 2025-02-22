# flake8: noqa: F401, E501
from datetime import datetime as Datetime
from datetime import timezone as Timezone

import pytest

from pyrdpdb import pyrdp
from tests.config import connector_name

from .base import PyRDPTestCase


@pytest.fixture(scope="function")
def db_table(request, con) -> pyrdp.Connection:
    con.paramstyle = "format"
    cursor: pyrdp.Cursor = con.cursor()
    ddl = (
        f"CREATE TABLE {connector_name}.t1 (f1 integer primary key, "
        "f2 integer not null, f3 varchar(50) null) "
    )
    PyRDPTestCase.safe_create_table(cursor, connector_name + ".t1", ddl)

    def fin():
        # cursor = con.cursor()
        cursor.execute(f"drop table {connector_name}.t1")
        cursor.close()

    request.addfinalizer(fin)
    return con


def test_database_error(cursor) -> None:
    with pytest.raises(pyrdp.RDBError):
        cursor.execute("INSERT INTO t99 VALUES (1, 2, 3)")


def test_parallel_queries(db_table) -> None:
    cursor: pyrdp.Cursor = db_table.cursor()
    cursor.execute(
        f"INSERT INTO {connector_name}.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (1, 1, None)
    )
    cursor.execute(
        f"INSERT INTO {connector_name}.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (2, 10, None)
    )
    cursor.execute(
        f"INSERT INTO {connector_name}.t1 (f1, f2, f3) VALUES (%s, %s, %s)",
        (3, 100, None),
    )
    cursor.execute(
        f"INSERT INTO {connector_name}.t1 (f1, f2, f3) VALUES (%s, %s, %s)",
        (4, 1000, None),
    )
    cursor.execute(
        f"INSERT INTO {connector_name}.t1 (f1, f2, f3) VALUES (%s, %s, %s)",
        (5, 10000, None),
    )
    c1: pyrdp.cursors.Cursor = db_table.cursor()
    c2: pyrdp.cursors.Cursor = db_table.cursor()
    c1.execute(f"SELECT f1, f2, f3 FROM {connector_name}.t1")
    for row in c1.fetchall():
        f1, f2, f3 = row
        c2.execute(f"SELECT f1, f2, f3 FROM {connector_name}.t1 WHERE f1 > %s", (f1,))
        for row in c2.fetchall():
            f1, f2, f3 = row


def test_create_table(db_table) -> None:
    cursor: pyrdp.cursors.Cursor = db_table.cursor()
    cursor.execute(f"select * from {connector_name}.t1")
    cursor.execute(f"drop table {connector_name}.t1")
    cursor.execute(f"create table {connector_name}.t1 (f1 integer primary key)")
    cursor.execute(f"select * from {connector_name}.t1")


def test_executemany(db_table) -> None:
    cursor: pyrdp.cursors.Cursor = db_table.cursor()
    cursor.executemany(
        f"INSERT INTO {connector_name}.t1 (f1, f2, f3) VALUES (%s, %s, %s)",
        ((1, 1, "Avast ye!"), (2, 1, None)),
    )

    cursor.executemany(
        "select CAST(%s AS TIMESTAMP)",
        ((Datetime(2014, 5, 7, tzinfo=Timezone.utc),), (Datetime(2014, 5, 7),)),
    )


def test_executemany_no_param_sets(cursor):
    cursor.executemany(f"INSERT INTO {connector_name}.t1 (f1, f2) VALUES (%s, %s)", [])
    assert cursor.rowcount == -1


def test_empty_query(cursor):
    """No exception thrown"""
    cursor.execute("")


def test_unexecuted_cursor_rowcount(con):
    """Unexecuted cursor should have rowcount value as -1."""
    cursor = con.cursor()
    assert cursor.rowcount == -1


def test_unexecuted_cursor_description(con):
    """Unexecuted cursor should have none description."""
    cursor = con.cursor()
    assert cursor.description is None


def test_null_result(db_table):
    cur = db_table.cursor()
    cur.execute(
        f"INSERT INTO {connector_name}.t1 (f1, f2, f3) VALUES (%s, %s, %s)", (1, 1, "a")
    )
    cur.fetchall() is None
