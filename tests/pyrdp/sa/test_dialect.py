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
    select,
)
from sqlalchemy.engine import create_engine
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.sql import text

from .conftest import url


def test_engine_initialization():
    engine = create_engine(url)

    assert engine.dialect.name == "rapidsdb"


def test_engine_connection():
    engine = create_engine(url)

    with engine.connect() as connection:
        assert connection is not None
        assert connection.closed is False


def test_query_execution():
    engine = create_engine(url)

    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))

        row = result.fetchone()
        assert row[0] == 1


# fails because RDP backend does not accept 'show' commands
# def test_show_schemas():
#     engine = create_engine(url)

#     with engine.connect() as connection:
#         result = connection.execute(text("show schemas"))
#         assert result.rowcount == 3


def test_dialect_types(user_table):
    engine = create_engine(url)
    metadata = MetaData()
    users_reflected = Table("users", metadata, autoload_with=engine)
    assert "users" in metadata.tables
    assert set([col.name for col in users_reflected.columns]) == {
        "id",
        "name",
        "age",
        "sex",
        "birthday",
        "popularity",
        "balance",
        "shipdate",
        "arrival",
        "comment",
    }

    assert isinstance(users_reflected.c.id.type, Integer)
    assert isinstance(users_reflected.c.name.type, VARCHAR)
    assert isinstance(users_reflected.c.sex.type, BOOLEAN)
    assert isinstance(users_reflected.c.birthday.type, DATE)
    assert isinstance(users_reflected.c.popularity.type, DECIMAL)
    assert isinstance(users_reflected.c.balance.type, FLOAT)
    assert isinstance(users_reflected.c.shipdate.type, DATE)
    assert isinstance(users_reflected.c.arrival.type, TIMESTAMP)
    assert isinstance(users_reflected.c.comment.type, VARCHAR)


def test_non_existent_table_reflection():
    engine = create_engine(url)

    metadata = MetaData()
    with pytest.raises(NoSuchTableError):
        Table("non_existent_table", metadata, autoload_with=engine)


def test_column_attributes(user_table):
    engine, _ = user_table

    metadata = MetaData()
    users_reflected = Table("users", metadata, autoload_with=engine)

    # assert users_reflected.c.id.primary_key  # RDP does not support primary key yet
    assert not users_reflected.c.name.nullable
    assert users_reflected.c.comment.nullable


def test_empty_database_reflection():
    engine = create_engine(url)
    reflected_metadata = MetaData()

    # ensure database is empty by dropping all existing tables
    table_names = engine.dialect.get_table_names(engine.connect(), engine.url.database)
    with Session(engine) as session:
        for tbl in table_names:
            session.execute(text(f"drop table {tbl}"))
    # reflected_metadata.drop_all(bind=engine)

    reflected_metadata.reflect(bind=engine)

    assert len(reflected_metadata.tables) == 0


def test_metadata_reflection(multi_tables):
    engine = multi_tables
    reflected_metadata = MetaData()
    reflected_metadata.reflect(bind=engine)

    expected_tables = {"users", "posts", "comments"}
    assert set(reflected_metadata.tables.keys()) == expected_tables

    users_table = reflected_metadata.tables["users"]
    assert set([col.name for col in users_table.columns]) == {"id", "name"}

    posts_table = reflected_metadata.tables["posts"]
    assert set([col.name for col in posts_table.columns]) == {"id", "title", "user_id"}

    comments_table = reflected_metadata.tables["comments"]
    assert set([col.name for col in comments_table.columns]) == {
        "id",
        "content",
        "post_id",
    }


def test_orm_select_query(add_user):
    engine, _ = add_user
    # engine, User = add_user
    # Base = automap_base()
    # Base.prepare(autoload_with=engine)
    # User = Base.metadata.tables["users"]

    Base = declarative_base()

    class User(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True)
        name = Column(VARCHAR(50), nullable=False)
        age = Column(Integer, nullable=False)
        sex = Column(BOOLEAN)
        birthday = Column(DATE)
        popularity = Column(DECIMAL)
        balance = Column(FLOAT, default=0)
        shipdate = Column(DATETIME)
        arrival = Column(TIMESTAMP)
        comment = Column(String)

    with Session(engine) as session:
        query = select(User).where(User.age > 25)
        results = session.scalars(query).all()

        assert len(results) == 2
        assert {user.name for user in results} == {"Alice", "Charlie"}
