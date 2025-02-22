import pytest
from sqlalchemy import (
    BOOLEAN,
    DATE,
    DATETIME,
    DECIMAL,
    FLOAT,
    TIMESTAMP,
    VARCHAR,
    Column,
    Integer,
    MetaData,
    String,
    Table,
    insert,
)
from sqlalchemy.engine import create_engine

# from sqlalchemy.orm import sessionmaker

url = "rapidsdb+asyncrdp://RAPIDS:rapids@asr1:4333/moxe"


@pytest.fixture(scope="function")
def user_table(request):
    engine = create_engine(url)
    metadata = MetaData()
    users = Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", VARCHAR(50), nullable=False),
        Column("age", Integer, nullable=False),
        Column("sex", BOOLEAN),
        Column("birthday", DATE),
        Column("popularity", DECIMAL),
        Column("balance", FLOAT, default=0),
        Column("shipdate", DATETIME),
        Column("arrival", TIMESTAMP),
        Column("comment", String),
    )
    users.create(bind=engine, checkfirst=True)

    def fin():
        users.drop(bind=engine)

    request.addfinalizer(fin)
    return engine, users


@pytest.fixture(scope="function")
def add_user(user_table):
    engine, users = user_table
    with engine.connect() as conn:
        conn.execute(
            insert(users),
            [
                {"id": 1, "name": "Alice", "age": 30, "sex": True},
                {"id": 2, "name": "Bob", "age": 25, "sex": False},
                {"id": 3, "name": "Charlie", "age": 35, "sex": None},
            ],
        )
    return engine, users


@pytest.fixture(scope="function")
def multi_tables(request):
    engine = create_engine(url)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    metadata.drop_all(bind=engine)

    Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(50), nullable=False),
    )

    Table(
        "posts",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("title", String(100), nullable=False),
        Column("user_id", Integer),
        # Column("user_id", Integer, ForeignKey("users.id")),
    )

    Table(
        "comments",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("content", String, nullable=False),
        Column("post_id", Integer),
        # Column("post_id", Integer, ForeignKey("posts.id")),
    )

    metadata.create_all(engine)

    def fin():
        metadata.drop_all(bind=engine)

    request.addfinalizer(fin)
    return engine
