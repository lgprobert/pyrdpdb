# flake8: noqa: E501
import warnings
from typing import Any

import pytest

from pyrdpdb import pyrdp

from .base import PyRDPTestCase
from .conftest import db_kwargs

__rcs_id__ = "$Id: dbapi20.py,v 2.0 2024/12/19"
__version__ = "$Revision: 2.0 $"[11:-2]
__author__ = "Robert Li <laigp@hotmail.com>"

driver = pyrdp
default_schema = "moxe"
table_prefix = "dbapi20test_"  # If you need to specify a prefix for tables

ddl1 = "create table if not exists %s.%sbooze (name varchar(20))" % (
    default_schema,
    table_prefix,
)
ddl2 = "create table if not exists  %s.%sbarflys (name varchar(20))" % (
    default_schema,
    table_prefix,
)
xddl1 = "drop table IF EXISTS %s.%sbooze" % (default_schema, table_prefix)
xddl2 = "drop table IF EXISTS %s.%sbarflys" % (default_schema, table_prefix)

# Name of stored procedure to convert
# string->lowercase
lowerfunc = "lower"

orig_val = "Cooper's"
alter_val = "Coopers"
bang_val = "Boag's"

valid_val = alter_val
valid_bang = "Boags"

samples = [
    "Carlton Cold",
    "Carlton Draft",
    "Mountain Goat",
    "Redback",
    "Victoria Bitter",
    "XXXX",
]


def _populate():
    """Return a list of sql commands to setup the DB for the fetch
    tests.
    """
    populate = [
        "insert into %s.%sbooze values ('%s')" % (default_schema, table_prefix, s)
        for s in samples
    ]
    return populate


# Some drivers may need to override these helpers, for example adding
# a 'commit' after the execute.
def executeDDL1(cursor: pyrdp.Cursor) -> Any:
    table_name = table_prefix + "booze"
    PyRDPTestCase.safe_create_table(cursor, table_name, ddl1)


def executeDDL2(cursor: pyrdp.Cursor) -> Any:
    table_name = table_prefix + "barflys"
    PyRDPTestCase.safe_create_table(cursor, table_name, ddl2)


@pytest.fixture(scope="function")
def cursor_(request, con):
    cursor = con.cursor()

    def fin():
        for tbl in ["booze", "barflys"]:
            table_name = table_prefix + tbl
            if cursor.has_table(table_name, default_schema):
                cursor.execute("drop table {}".format(table_name))
        cursor.close()

    request.addfinalizer(fin)
    return cursor


@pytest.fixture
def ddl1_table(cursor_) -> pyrdp.cursors.Cursor:
    _cursor: pyrdp.cursors.Cursor = cursor_
    table_name = table_prefix + "booze"
    if not _cursor.has_table(table_name, default_schema):
        _cursor.execute(ddl1)
    else:
        _cursor.execute("truncate table %s.%s" % (default_schema, table_name))
    return _cursor


def test_apilevel():
    apilevel = driver.apilevel

    assert apilevel == "2.0"


def test_threadsafety():
    try:
        threadsafety = driver.threadsafety
        assert threadsafety in (0, 1, 2, 3)
    except AttributeError:
        assert False, "Driver doesn't define threadsafety"


def test_paramstyle():
    try:
        # Must exist
        paramstyle = driver.paramstyle
        # Must be a valid value
        assert paramstyle in ("qmark", "numeric", "named", "format", "pyformat")
    except AttributeError:
        assert False, "Driver doesn't define paramstyle"


def test_exceptions():
    # Make sure required exceptions exist, and are in the
    # defined hierarchy.
    assert issubclass(driver.Warning, Exception)
    assert issubclass(driver.Error, Exception)
    assert issubclass(driver.InterfaceError, driver.Error)
    assert issubclass(driver.DatabaseError, driver.Error)
    assert issubclass(driver.OperationalError, driver.Error)
    assert issubclass(driver.IntegrityError, driver.Error)
    assert issubclass(driver.InternalError, driver.Error)
    assert issubclass(driver.ProgrammingError, driver.Error)
    assert issubclass(driver.NotSupportedError, driver.Error)


def test_ExceptionsAsConnectionAttributes(con):
    # OPTIONAL EXTENSION
    # Test for the optional DB API 2.0 extension, where the exceptions
    # are exposed as attributes on the Connection object
    # I figure this optional extension will be implemented by any
    # driver author who is using this test suite, so it is enabled
    # by default.
    warnings.simplefilter("ignore")
    drv = driver
    assert con.Warning is drv.Warning
    assert con.Error is drv.Error
    assert con.InterfaceError is drv.InterfaceError
    assert con.DatabaseError is drv.DatabaseError
    assert con.OperationalError is drv.OperationalError
    assert con.IntegrityError is drv.IntegrityError
    assert con.InternalError is drv.InternalError
    assert con.ProgrammingError is drv.ProgrammingError
    assert con.NotSupportedError is drv.NotSupportedError
    warnings.resetwarnings()


# def test_commit(con):
#     # Commit must work, even if it doesn't do anything
#     con.commit()


# def test_rollback(con):
#     # If rollback is defined, it should either work or throw
#     # the documented exception
#     if hasattr(con, "rollback"):
#         try:
#             con.rollback()
#         except driver.NotSupportedError:
#             pass


def test_cursor(cursor_):
    assert isinstance(cursor_, pyrdp.cursors.Cursor)


def test_cursor_isolation(con: pyrdp.Connection) -> None:
    # Make sure cursors created from the same connection have
    # the documented transaction isolation level
    cursor1: pyrdp.Cursor = con.cursor()
    cursor2: pyrdp.Cursor = con.cursor()
    executeDDL1(cursor1)
    cursor1.execute(
        "insert into %s.%sbooze values ('Victoria Bitter')"
        % ((default_schema, table_prefix))
    )
    cursor2.execute("select name from %s.%sbooze" % (default_schema, table_prefix))
    booze = cursor2.fetchall()
    assert len(booze) == 1
    assert len(booze[0]) == 1
    assert booze[0][0] == "Victoria Bitter"

    # clean up test table
    cursor1.execute(xddl1)


def test_description(ddl1_table) -> None:
    cur: pyrdp.Cursor = ddl1_table
    assert cur.description is None, (
        "cursor.description should be none after executing a "
        "statement that can return no rows (such as DDL)"
    )
    cur.execute("select name from %s.%sbooze" % (default_schema, table_prefix))
    assert len(cur.description) == 1, "cursor.description describes too many columns"  # type: ignore
    assert (
        len(cur.description[0]) == 6  # type: ignore
    ), "cursor.description[x] tuples must have 6 elements"
    assert (
        cur.description[0][0].lower() == "name"  # type: ignore
    ), "cursor.description[x][0] must return column name"
    assert cur.description[0][1] == driver.STRING, (  # type: ignore
        "cursor.description[x][1] must return column type. Got %r" % cur.description[0][1]  # type: ignore
    )

    # Make sure self.description gets reset
    executeDDL2(cur)
    assert cur.description is None, (
        "cursor.description not being set to None when executing "
        "no-result statements (eg. DDL)"
    )
    cur.execute(xddl2)


def test_rowcount(ddl1_table) -> None:
    cursor: pyrdp.cursors.Cursor = ddl1_table
    assert cursor.rowcount == 0, (
        "cursor.rowcount should be 0 after executing no-result " "statements"
    )
    cursor.execute(
        "insert into %s.%sbooze values ('Victoria Bitter')"
        % (default_schema, table_prefix)
    )
    # insert statement does not return
    assert cursor.rowcount in (-1, 0), (
        "cursor.rowcount should equal to number of rows inserted, or "
        "set to -1 after executing an insert statement"
    )
    cursor.execute("select name from %s.%sbooze" % (default_schema, table_prefix))
    assert cursor.rowcount in (-1, 1), "cursor.rowcount should be number of rows returned"
    executeDDL2(cursor)
    assert cursor.rowcount == 0, (
        "cursor.rowcount not being reset to 0 after executing " "no-result statements"
    )


def test_close():
    """Can't use 'con' fixture its teardown() will fail because it is closed by test case."""
    conn_args, _ = db_kwargs()
    con = pyrdp.connect(**conn_args)
    cur = con.cursor()
    con.close()

    # cursor.execute should raise an Error if called after connection
    # closed
    with pytest.raises(driver.Error):
        executeDDL1(cur)

    # connection.commit should raise an Error if called after connection'
    # closed.'
    # with pytest.raises(driver.Error):
    #     con.commit()

    # connection.close should raise an Error if called more than once
    with pytest.raises(driver.Error):
        con.close()


def test_execute(ddl1_table) -> None:
    cur: pyrdp.cursors.Cursor = ddl1_table

    cur.execute(
        "insert into %s.%sbooze values ('Victoria Bitter')"
        % (default_schema, table_prefix)
    )
    assert cur.rowcount in (-1, 0)

    if driver.paramstyle == "qmark":
        cur.execute(
            "insert into %s.%sbooze values (?)" % (default_schema, table_prefix),
            (valid_val,),
        )
    elif driver.paramstyle == "numeric":
        cur.execute(
            "insert into %s.%sbooze values (:1)" % (default_schema, table_prefix),
            (valid_val,),
        )
    elif driver.paramstyle == "named":
        cur.execute(
            "insert into %s.%sbooze values (:beer)" % (default_schema, table_prefix),
            {"beer": valid_val},
        )
    elif driver.paramstyle == "format":
        cur.execute(
            "insert into %s.%sbooze values (%%s)" % (default_schema, table_prefix),
            (valid_val,),
        )
    elif driver.paramstyle == "pyformat":
        cur.execute(
            "insert into %s.%sbooze values (%%(beer)s)" % (default_schema, table_prefix),
            {"beer": valid_val},
        )
    else:
        assert False, "Invalid paramstyle"

    assert cur.rowcount in (-1, 0)

    cur.execute("select name from %s.%sbooze" % (default_schema, table_prefix))
    res = cur.fetchall()
    assert len(res) == 2, "cursor.fetchall returned too few rows"
    beers = [res[0][0], res[1][0]]
    beers.sort()
    assert beers[0] == valid_val, (
        "cursor.fetchall retrieved incorrect data, or data inserted " "incorrectly"
    )
    assert beers[1] == "Victoria Bitter", (
        "cursor.fetchall retrieved incorrect data, or data inserted " "incorrectly"
    )


def test_executemany(ddl1_table) -> None:
    cursor: pyrdp.cursors.Cursor = ddl1_table
    largs = [(valid_val,), (valid_bang,)]
    margs = [{"beer": valid_val}, {"beer": valid_bang}]
    if driver.paramstyle == "qmark":
        cursor.executemany(
            "insert into %s.%sbooze values (?)" % (default_schema, table_prefix), largs
        )
    elif driver.paramstyle == "numeric":
        cursor.executemany(
            "insert into %s.%sbooze values (:1)" % (default_schema, table_prefix), largs
        )
    elif driver.paramstyle == "named":
        cursor.executemany(
            "insert into %s.%sbooze values (:beer)" % (default_schema, table_prefix),
            margs,
        )
    elif driver.paramstyle == "format":
        cursor.executemany(
            "insert into %s.%sbooze values (%%s)" % (default_schema, table_prefix), largs
        )
    elif driver.paramstyle == "pyformat":
        cursor.executemany(
            "insert into %s.%sbooze values (%%(beer)s)" % (default_schema, table_prefix),
            margs,
        )
    else:
        assert False, "Unknown paramstyle"

    assert cursor.rowcount in (-1, 1, 2), (
        "insert using cursor.executemany set cursor.rowcount to "
        "incorrect value %r" % cursor.rowcount
    )

    cursor.execute("select name from %s.%sbooze" % (default_schema, table_prefix))
    res = cursor.fetchall()
    assert len(res) == 2, "cursor.fetchall retrieved incorrect number of rows"
    beers = [res[0][0], res[1][0]]
    beers.sort()
    assert beers[0] == valid_bang, "incorrect data retrieved"
    assert beers[1] == valid_val, "incorrect data retrieved"


def test_fetchone(cursor_):
    # cursor.fetchone should raise an Error if called before
    # executing a select-type query
    tablename = table_prefix + "booze"
    with pytest.raises(driver.Error):
        cursor_.fetchone()

    executeDDL1(cursor_)

    cursor_.execute("select name from %s.%s" % (default_schema, tablename))
    assert cursor_.fetchone() is None, (
        "cursor.fetchone should return None if a query retrieves " "no rows"
    )
    assert cursor_.rowcount in (-1, 0)

    cursor_.execute(
        "insert into %s.%sbooze values ('Victoria Bitter')"
        % (default_schema, table_prefix)
    )
    cursor_.execute("select name from %s.%s" % (default_schema, tablename))
    r = cursor_.fetchone()
    assert len(r) == 1, "cursor.fetchone should have retrieved a single row"
    assert r[0] == "Victoria Bitter", "cursor.fetchone retrieved incorrect data"
    assert (
        cursor_.fetchone() is None
    ), "cursor.fetchone should return None if no more rows available"
    assert cursor_.rowcount in (-1, 1)


def test_fetchmany(cursor_):
    # cursor.fetchmany should raise an Error if called without
    # issuing a query
    with pytest.raises(driver.Error):
        cursor_.fetchmany(4)

    executeDDL1(cursor_)
    for sql in _populate():
        cursor_.execute(sql)

    cursor_.execute("select name from %s.%sbooze" % (default_schema, table_prefix))
    r = cursor_.fetchmany()
    assert len(r) == 1, (
        "cursor.fetchmany retrieved incorrect number of rows, "
        "default of arraysize is one."
    )
    cursor_.arraysize = 10
    r = cursor_.fetchmany(3)  # Should get 3 rows
    assert len(r) == 3, "cursor.fetchmany retrieved incorrect number of rows"
    r = cursor_.fetchmany(4)  # Should get 2 more
    assert len(r) == 2, "cursor.fetchmany retrieved incorrect number of rows"
    r = cursor_.fetchmany(4)  # Should be an empty sequence
    assert len(r) == 0, (
        "cursor.fetchmany should return an empty sequence after " "results are exhausted"
    )
    assert cursor_.rowcount in (-1, 6)

    # Same as above, using cursor.arraysize
    cursor_.arraysize = 4
    cursor_.execute("select name from %s.%sbooze" % (default_schema, table_prefix))
    r = cursor_.fetchmany()  # Should get 4 rows
    assert len(r) == 4, "cursor.arraysize not being honoured by fetchmany"
    r = cursor_.fetchmany()  # Should get 2 more
    assert len(r) == 2
    r = cursor_.fetchmany()  # Should be an empty sequence
    assert len(r) == 0
    assert cursor_.rowcount in (-1, 6)

    cursor_.arraysize = 6
    cursor_.execute("select name from %s.%sbooze" % (default_schema, table_prefix))
    rows = cursor_.fetchmany()  # Should get all rows
    assert cursor_.rowcount in (-1, 6)
    assert len(rows) == 6
    assert len(rows) == 6
    rows = [row[0] for row in rows]
    rows.sort()

    # Make sure we get the right data back out
    for i in range(0, 6):
        assert rows[i] == samples[i], "incorrect data retrieved by cursor.fetchmany"

    rows = cursor_.fetchmany()  # Should return an empty list
    assert len(rows) == 0, (
        "cursor.fetchmany should return an empty sequence if "
        "called after the whole result set has been fetched"
    )
    assert cursor_.rowcount in (-1, 6)

    executeDDL2(cursor_)
    cursor_.execute("select name from %s.%sbarflys" % (default_schema, table_prefix))
    r = cursor_.fetchmany()  # Should get empty sequence
    assert len(r) == 0, (
        "cursor.fetchmany should return an empty sequence if " "query retrieved no rows"
    )
    assert cursor_.rowcount in (-1, 0)


def test_fetchall(cursor_):
    # cursor.fetchall should raise an Error if called
    # without executing a query that may return rows (such
    # as a select)
    with pytest.raises(driver.Error):
        cursor_.fetchall()

    executeDDL1(cursor_)
    for sql in _populate():
        cursor_.execute(sql)

    cursor_.execute("select name from %s.%sbooze" % (default_schema, table_prefix))
    rows = cursor_.fetchall()
    assert cursor_.rowcount in (-1, len(samples))
    assert len(rows) == len(samples), "cursor.fetchall did not retrieve all rows"
    rows = [r[0] for r in rows]
    rows.sort()
    for i in range(0, len(samples)):
        assert rows[i] == samples[i], "cursor.fetchall retrieved incorrect rows"
    rows = cursor_.fetchall()
    assert len(rows) == 0, (
        "cursor.fetchall should return an empty list if called "
        "after the whole result set has been fetched"
    )
    assert cursor_.rowcount in (-1, len(samples))

    executeDDL2(cursor_)
    cursor_.execute("select name from %s.%sbarflys" % (default_schema, table_prefix))
    rows = cursor_.fetchall()
    assert cursor_.rowcount in (-1, 0)
    assert len(rows) == 0, (
        "cursor.fetchall should return an empty list if " "a select query returns no rows"
    )


def test_mixedfetch(cursor_):
    executeDDL1(cursor_)
    for sql in _populate():
        cursor_.execute(sql)

    cursor_.execute("select name from %s.%sbooze" % (default_schema, table_prefix))
    rows1 = cursor_.fetchone()
    rows23 = cursor_.fetchmany(2)
    rows4 = cursor_.fetchone()
    rows56 = cursor_.fetchall()
    assert cursor_.rowcount in (-1, 6)
    assert len(rows23) == 2, "fetchmany returned incorrect number of rows"
    assert len(rows56) == 2, "fetchall returned incorrect number of rows"

    rows = [rows1[0]]
    rows.extend([rows23[0][0], rows23[1][0]])
    rows.append(rows4[0])
    rows.extend([rows56[0][0], rows56[1][0]])
    rows.sort()
    for i in range(0, len(samples)):
        assert rows[i] == samples[i], "incorrect data retrieved or inserted"


def help_nextset_setUp():
    """Should create a procedure called deleteme
    that returns two result sets, first the
    number of rows in booze then "name from booze"
    """
    raise NotImplementedError("Helper not implemented")


def help_nextset_tearDown():
    "If cleaning up is needed after nextSetTest"
    raise NotImplementedError("Helper not implemented")


def test_arraysize(cursor_):
    # Not much here - rest of the tests for this are in test_fetchmany
    assert hasattr(cursor_, "arraysize"), "cursor.arraysize must be defined"


def test_setinputsizes(cursor_):
    cursor_.setinputsizes(25)


# should fails because cursor.setoutputsizes() not implemented yet
# def test_setoutputsize_basic(cursor, cleanup_tbl):
#     # Basic test is to make sure setoutputsize doesn't blow up
#     cursor.setoutputsizes(1000)
#     cursor.setoutputsizes(2000, 0)
#     _paraminsert(cursor)  # Make sure the cursor still works


def test_none(cursor_):
    executeDDL1(cursor_)
    cursor_.execute(
        "insert into %s.%sbooze values (NULL)" % (default_schema, table_prefix)
    )
    cursor_.execute("select name from %s.%sbooze" % (default_schema, table_prefix))
    r = cursor_.fetchall()
    assert len(r) == 1
    assert len(r[0]) == 1
    assert r[0][0] is None, "NULL value not returned as None"


def test_binary():
    driver.Binary(b"Something")
    driver.Binary(b"")


def test_string():
    assert hasattr(driver, "STRING"), "module.STRING must be defined"


def test_number():
    assert hasattr(driver, "NUMBER"), "module.NUMBER must be defined."


def test_datetime():
    assert hasattr(driver, "DATETIME"), "module.DATETIME must be defined."
