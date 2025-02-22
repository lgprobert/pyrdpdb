#!/usr/bin/env python
import sys
from typing import Optional

from sqlalchemy import MetaData, Table, create_engine, select
from sqlalchemy.orm import Session


def main(table: str, host: str) -> None:
    engine = create_engine(f"rapidsdb+pyrdp://RAPIDS:rapids@{host}:4333/sf1", echo=False)
    meta = MetaData()
    session = Session(engine)
    t1: Optional[Table]
    if "." in table:
        schema, table = table.split(".")
        meta.reflect(bind=engine, schema=schema)
        t1 = meta.tables.get(table)
    else:
        table = table
        meta.reflect(bind=engine)
        t1 = meta.tables.get(table)
    if t1 is None:
        print("table not found")
        sys.exit(1)

    print("ready to run query")
    for r in session.execute(select(t1)):
        print(r)


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        table = sys.argv[1]
        host = sys.argv[2]
    elif len(sys.argv) == 2:
        host = "localhost"
        table = sys.argv[1]
    else:
        print("Usage: python -m pyrdp.example.query <table> <host>", file=sys.stderr)
        sys.exit(-1)

    print("Connect to", host)
    main(table=table, host=host)
