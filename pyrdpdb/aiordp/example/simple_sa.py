import asyncio
import sys

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

metadata = sa.MetaData()

tbl = sa.Table(
    "TBL",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("val", sa.String(255)),
    schema="MOXE",
)


async def create_table(engine):
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS MOXE.tbl"))
        await conn.execute(
            text(
                """CREATE TABLE MOXE.tbl (
                              id integer PRIMARY KEY,
                              val varchar(255))"""
            )
        )


async def go(host: str):
    engine = create_async_engine(f"rapidsdb+asyncrdp://RAPIDS:rapids@{host}:4333/moxe")
    await create_table(engine)
    async with engine.begin() as conn:
        await conn.execute(tbl.insert().values(id=1, val="abc"))
        await conn.execute(tbl.insert().values(id=2, val="xyz"))

        result = await conn.execute(tbl.select())
        for row in result:
            print(row[0], row[1])

        await conn.execute(text("drop table MOXE.tbl"))


def main(host: str):
    print("Connect to", host)
    asyncio.run(go(host))


if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    main(host)
