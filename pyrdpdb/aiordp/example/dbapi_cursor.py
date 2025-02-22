import asyncio
import sys

import aiordp


async def test_example(loop, host: str):
    rdp = await aiordp.connect(
        host=host,
        port=4333,
        user="RAPIDS",
        password="rapids",
        database="moxe",
        loop=loop,
    )
    print("Using Async cursor:")
    async with rdp.cursor() as cursor:
        await cursor.execute("select 1")
        rset = await cursor.fetchall()
        for r in rset:
            print(r)


async def test_sscursor(loop, host: str):
    rdp = await aiordp.connect(
        host=host,
        port=4333,
        user="RAPIDS",
        password="rapids",
        database="sf1",
        cursorclass=aiordp.cursors.Cursor,
        loop=loop,
    )
    print("\nUsing Async SSCursor:\n")
    async with rdp.cursor() as cursor:
        await cursor.execute("select * from nation limit 10")
        rset = await cursor.fetchall()
        for r in rset:
            print(r)


def main(host: str):
    loop = asyncio.new_event_loop()
    print("Connect to", host)
    asyncio.run(test_example(loop, host))
    asyncio.run(test_sscursor(loop, host))


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    main(host)
