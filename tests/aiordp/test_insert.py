import pytest

from pyrdpdb import aiordp

table_name = "moxe.t1"


@pytest.mark.asyncio
async def test_insert_table(t1_table) -> None:
    cursor: aiordp.Cursor = t1_table
    await cursor.execute("truncate table moxe.t1")
    await cursor.execute(
        f"INSERT INTO {table_name} (f1, f2, f3) VALUES (%s, %s, %s)", (1, 1, 1)
    )
    await cursor.execute(
        f"INSERT INTO {table_name} (f1, f2, f3) VALUES (%s, %s, %s)", (2, 2, 2)
    )
    await cursor.execute(
        f"INSERT INTO {table_name} (f1, f2, f3) VALUES (%s, %s, %s)", (3, 3, 3)
    )

    await cursor.execute(f"select * from {table_name}")
    assert cursor.rowcount == 3
