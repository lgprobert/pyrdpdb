import pytest

from pyrdpdb import aiordp
from pyrdpdb.aiordp import OperationalError, __version__

from .conftest import db_kwargs


@pytest.mark.asyncio
async def test_internet_socket_connection_refused():
    conn_params = {"port": 0, "user": "doesn't-matter"}

    with pytest.raises(
        OperationalError,
        match="Lost connection to RapidDB server during query",
    ):
        async with aiordp.connect(**conn_params):
            pass


@pytest.mark.asyncio
async def test_connection(con) -> None:
    """Test with manual created cursor and should be closed manually."""
    # rdp_args, _ = db_kwargs()
    # conn = await aiordp.connect(**rdp_args)
    conn: aiordp.Connection = con
    cur: aiordp.Cursor = await conn.cursor()

    await cur.execute("SELECT 1")
    res = await cur.fetchall()
    assert res[0][0] == 1
    await cur.close()


@pytest.mark.asyncio
async def test_database_missing() -> None:
    rdp_args, _ = db_kwargs()
    rdp_args["database"] = "missing-db"
    await aiordp.connect(**rdp_args)


def test_version():
    try:
        from importlib.metadata import version
    except ImportError:
        from importlib_metadata import version  # type: ignore

    ver = version("pyrdpdb")

    assert __version__ == ver
