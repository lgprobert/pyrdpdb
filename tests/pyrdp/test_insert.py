from typing import Any

import pytest

from pyrdpdb import pyrdp

from .base import PyRDPTestCase

table_name = "moxe.t1"


@pytest.fixture
def db_table(request, con: pyrdp.Connection) -> Any:
    cursor: pyrdp.Cursor = con.cursor()
    ddl = (
        """
            CREATE TABLE %s (
                f1 integer primary key,
                f2 integer not null,
                f3 varchar(50) null
            )
        """
        % table_name
    )
    PyRDPTestCase.safe_create_table(cursor, table_name, ddl)

    def teardown():
        PyRDPTestCase.drop_table(cursor, table_name)
        cursor.close()

    request.addfinalizer(teardown)
    return cursor


def test_insert_table(db_table) -> None:
    cursor: pyrdp.Cursor = db_table
    cursor.execute(
        f"INSERT INTO {table_name} (f1, f2, f3) VALUES (%s, %s, %s)", (1, 1, 1)
    )
    cursor.execute(
        f"INSERT INTO {table_name} (f1, f2, f3) VALUES (%s, %s, %s)", (2, 2, 2)
    )
    cursor.execute(
        f"INSERT INTO {table_name} (f1, f2, f3) VALUES (%s, %s, %s)", (3, 3, 3)
    )

    cursor.execute(f"select * from {table_name}")
    assert cursor.rowcount == 3
