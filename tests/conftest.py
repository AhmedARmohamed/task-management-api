import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from main import app
from app.database import get_db, Base

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="function")
async def db_session():
    """Create test database session"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncTestSession = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncTestSession() as session:
        yield session

@pytest.fixture(scope="function")
async def test_app(db_session):
    """Create test app with test database"""
    app.dependency_overrides[get_db] = lambda: db_session
    yield app
    app.dependency_overrides.clear()