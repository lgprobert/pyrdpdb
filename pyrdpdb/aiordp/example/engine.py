import asyncio
import sys

import aiordp


async def start(engine):
    async with engine.acquire() as conn:

        async for r in await conn.execute("select * from region"):
            print(r)


async def example(loop, host: str):

    engine = await aiordp.create_engine(
        host=host,
        port=4333,
        user="RAPIDS",
        password="rapids",
        db="sf1",
        loop=loop,
    )
    await start(engine)


def main(host: str):
    loop = asyncio.new_event_loop()
    print("Connect to", host)
    asyncio.run(example(loop, host=host))


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    main(host)
