import pytest
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.config import settings
from main import app

# Don't override if already set by CI
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
if "SECRET_KEY" not in os.environ:
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-must-be-long-enough-32-chars"
if "API_KEY" not in os.environ:
    os.environ["API_KEY"] = "123456"
if "DEBUG" not in os.environ:
    os.environ["DEBUG"] = "true"

# Use the actual DATABASE_URL from environment/settings
test_engine = create_async_engine(
    settings.DATABASE_URL,  # Use settings instead of hardcoding!
    echo=False,
    future=True
)

TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Create test database tables once per session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await test_engine.dispose()

@pytest.fixture(autouse=True)
async def override_db():
    """Override database dependency for each test."""
    async def get_test_db():
        async with TestSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    # Override the dependency
    app.dependency_overrides[get_db] = get_test_db
    yield

    # Clean up after each test - delete all data but keep tables
    async with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.run_sync(lambda sync_conn, t=table: sync_conn.execute(t.delete()))

    # Clear overrides
    app.dependency_overrides.clear()