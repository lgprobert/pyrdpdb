import pytest
from typing import Any

from pyrdpdb import pyrdp
from tests import config

from .base import PyRDPTestCase

connector_name = config.connector_name
jdbc_connector = "test_connector"


def db_kwargs() -> tuple[dict[str, Any], str]:
    conn_args = {
        "user": config.user,
        "password": config.password,
        "database": config.database,
        "host": config.host,
        "port": int(config.port),
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
        f"url='jdbc:{external_args['db_type']}://{external_args['host']}:{external_args['port']};databaseName={external_args['db']}', "  # noqa
        f"user='{external_args['user']}', password ='{external_args['password']}' NODE * ;"  # noqa
    )

    return conn_args, connector_ddl


@pytest.fixture(scope="class")
def con(request) -> pyrdp.Connection:
    conn_args, connector_ddl = db_kwargs()
    conn: pyrdp.Connection = pyrdp.connect(**conn_args)
    cursor = conn.cursor()

    if not cursor.has_connector(connector_name):
        cursor.execute(connector_ddl)

    def teardown() -> None:
        cursor = conn.cursor()
        if cursor.has_connector(connector_name):
            PyRDPTestCase.drop_connector(cursor, connector_name)
        conn.close()

    request.addfinalizer(teardown)
    if request.cls:
        request.cls.con = conn
    return conn


@pytest.fixture
def cursor(request, con) -> pyrdp.Cursor:
    cursor = con.cursor()

    def fin():
        cursor.close()

    request.addfinalizer(fin)
    return cursor


@pytest.fixture
def rdp_version(cursor):
    cursor.execute("select version()")
    retval = cursor.fetchall()
    major_version = retval[0][0].split()[1]
    return major_version
