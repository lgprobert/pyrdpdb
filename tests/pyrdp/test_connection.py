import pytest

from pyrdpdb import pyrdp
from pyrdpdb.pyrdp import OperationalError, connect

from .conftest import db_kwargs


def test_internet_socket_connection_refused():
    conn_params = {"port": 0, "user": "doesn't-matter"}

    with pytest.raises(
        OperationalError,
        match="Lost connection to RapidDB server during query",
    ):
        with connect(**conn_params):
            pass


def test_connection():
    rdp_args, _ = db_kwargs()
    conn = pyrdp.connect(**rdp_args)
    cur = conn.cursor()

    cur.execute("SELECT 1")
    res = cur.fetchall()
    assert res[0][0] == 1


def test_database_missing():
    rdp_args, _ = db_kwargs()
    rdp_args["database"] = "missing-db"
    pyrdp.connect(**rdp_args)


# def test_version():
#     try:
#         from importlib.metadata import version
#     except ImportError:
#         from importlib_metadata import version  # type: ignore

#     ver = version("pyrdp")

#     assert __version__ == ver
