import asyncio
import sys

import aiordp  # type: ignore

from pyrdpdb import pyrdp

args = [(1, "a"), (2, "b"), (3, "c")]
ddl = "create table tbl (id integer, name varchar(50))"


def many_pyrdp() -> None:
    rdp = pyrdp.connect(
        host="localhost", port=4333, user="RAPIDS", password="rapids", db="moxe"
    )

    cursor: pyrdp.Cursor = rdp.cursor()

    print("create table tbl")
    if cursor.has_table("tbl"):
        cursor.execute("drop table tbl")
    cursor.execute(ddl)

    print("\nRun executemany() for insert")
    cursor.timing()  # turn on execution timing

    rcount = cursor.executemany("insert into tbl (id, name) VALUES (%s, %s)", args)

    print("\nInsert many count:", rcount)

    cursor.execute("select * from tbl")
    print("\nQuery result set:")
    print(cursor.fetchall())


async def many_aio(loop) -> None:
    rdp = await aiordp.connect(
        host="localhost",
        port=4333,
        user="RAPIDS",
        password="rapids",
        database="moxe",
        loop=loop,
    )
    cursor: aiordp.Cursor
    async with rdp.cursor() as cursor:
        if await cursor.has_table("tbl"):
            await cursor.execute("drop table tbl")
        await cursor.execute(ddl)

        print("\nRun async executemany() for insert")
        cursor.timing()  # turn on execution timing

        rcount = await cursor.executemany(
            "insert into tbl (id, name) VALUES (%s, %s)", args
        )
        print("\nAsync insert many count:", rcount)

        await cursor.execute("select * from tbl")
        print("\nQuery result set:")
        print(await cursor.fetchall())


def main(mode: str):
    print("Run mode:", mode)
    if mode == "pyrdp":
        many_pyrdp()
    else:
        loop = asyncio.new_event_loop()
        asyncio.run(many_aio(loop))


def usage():
    print("Usage: python many.py [pyrdp | aiordp]", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["pyrdp", "aiordp"]:
        usage()
    main(sys.argv[1])
