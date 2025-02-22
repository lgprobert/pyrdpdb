import asyncio
from datetime import date, datetime

import pytest
import pytest_asyncio
from sqlalchemy import (
    TIMESTAMP,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    select,
)
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

Base = declarative_base()

url = "rapidsdb+asyncrdp://RAPIDS:rapids@localhost:4333/moxe"
myurl = "mysql+aiomysql://root:rdpadmin@localhost:3310/tpch"


class User(Base):  # type: ignore
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    age = Column(Integer)


class DataTypeTest(Base):  # type: ignore
    __tablename__ = "datatype_test"

    id = Column(Integer, primary_key=True)
    string_col = Column(String(50))
    int_col = Column(Integer)
    float_col = Column(Float)
    date_col = Column(DateTime)
    timestamp_col = Column(TIMESTAMP)


@pytest.fixture(scope="module")
def async_engine():
    engine = create_async_engine(
        url,
        echo=True,  # Enable SQL logging for debug purposes
    )
    yield engine
    asyncio.run(engine.dispose())


@pytest.fixture(scope="module")
def async_myengine():
    engine = create_async_engine(
        myurl,
        echo=True,  # Enable SQL logging for debug purposes
    )
    yield engine
    asyncio.run(engine.dispose())


@pytest_asyncio.fixture
async def setup_tables(request, async_engine):
    engine = async_engine
    print("run fixture setup_tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    def fin():
        async def teardown():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

        current_loop = asyncio.get_event_loop_policy().get_event_loop()
        current_loop.run_until_complete(teardown())

    request.addfinalizer(fin)
    return engine


@pytest.mark.asyncio
async def test_session(setup_tables):
    async with setup_tables.begin() as conn:
        await conn.execute(
            Base.metadata.tables["users"].insert(),
            [{"id": 1, "name": "Alice", "age": 25}],
        )

    async_session = async_sessionmaker(setup_tables, expire_on_commit=False)
    async with async_session() as session:
        session.add(User(id=2, name="Bob", age=30))
        result = await session.execute(select(User).order_by(User.id))
        rset = result.fetchall()
        u1 = rset[0][0]
        u2 = rset[1][0]
        assert u1.age == 25
        assert u2.name == "Bob"


@pytest.mark.asyncio
async def test_create_and_drop_table(async_engine):

    async with async_engine.begin() as conn:
        assert not await conn.run_sync(async_engine.dialect.has_table, "datatype_test")

        await conn.run_sync(Base.metadata.create_all)
        assert await conn.run_sync(async_engine.dialect.has_table, "datatype_test")

        await conn.run_sync(Base.metadata.drop_all)
        assert not await conn.run_sync(async_engine.dialect.has_table, "datatype_test")


@pytest.mark.asyncio
async def test_create_and_drop_one_table(async_engine):

    async with async_engine.begin() as conn:
        assert not await conn.run_sync(async_engine.dialect.has_table, "datatype_test")

        # ensure no table exists by chance
        await conn.run_sync(Base.metadata.drop_all)

        datatype_test_table = Base.metadata.tables["datatype_test"]
        await conn.run_sync(datatype_test_table.create)
        assert await conn.run_sync(async_engine.dialect.has_table, "datatype_test")

        await conn.run_sync(datatype_test_table.drop)
        assert not await conn.run_sync(async_engine.dialect.has_table, "datatype_test")

        # clean up all testing tables
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_basic_crud_operations(setup_tables):

    async with setup_tables.connect() as conn:
        await conn.execute(
            Base.metadata.tables["users"].insert(),
            [{"id": 1, "name": "Alice", "age": 25}, {"id": 2, "name": "Bob", "age": 30}],
        )

    # Query data
    async with setup_tables.connect() as conn:
        rset = await conn.execute(select(User).where(User.name == "Alice"))
        result = rset.fetchone()
        assert result[2] == 25


@pytest.mark.asyncio
async def test_reflect_tables(setup_tables):
    metadata = MetaData()
    async with setup_tables.begin() as conn:
        await conn.run_sync(metadata.reflect)

    assert "users" in metadata.tables
    users_table = metadata.tables["users"]
    assert isinstance(users_table, Table)


@pytest.mark.asyncio
async def test_create_engine(async_engine):
    assert isinstance(async_engine, AsyncEngine)


@pytest.mark.asyncio
async def test_create_connection(async_engine):
    async with async_engine.connect() as connection:
        result = await connection.execute(select(1))
        scalar_result = result.scalar()
        assert scalar_result == 1


@pytest.mark.skip
@pytest.mark.asyncio
async def test_aiomysql_create_connection(async_myengine):
    async with async_myengine.connect() as connection:
        result = await connection.execute(select(1))
        scalar_result = result.scalar()
        assert scalar_result == 1


@pytest.mark.asyncio
async def test_data_type_mappings(setup_tables):
    async_session = async_sessionmaker(setup_tables, expire_on_commit=False)

    # Insert data with various types
    async with async_session() as session:
        async with session.begin():
            test_row = DataTypeTest(
                id=1,
                string_col="test string",
                int_col=42,
                float_col=3.14,
                date_col=datetime(2023, 1, 1, 12, 0, 0),
                timestamp_col=datetime(2023, 1, 1, 12, 0, 0),
            )
            session.add(test_row)

    # Query and validate data types
    async with async_session() as session:
        result = await session.execute(select(DataTypeTest))
        test_row = result.scalar_one()

        assert isinstance(test_row.string_col, str)
        assert test_row.string_col == "test string"

        assert isinstance(test_row.int_col, int)
        assert test_row.int_col == 42

        assert isinstance(test_row.float_col, float)
        assert abs(test_row.float_col - 3.14) < 1e-6

        assert isinstance(test_row.date_col, date)
        assert test_row.date_col == date(2023, 1, 1)

        assert isinstance(test_row.timestamp_col, date)
        assert test_row.timestamp_col == datetime(2023, 1, 1, 12, 0, 0)
