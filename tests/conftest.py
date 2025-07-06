import pytest
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import get_db, Base
import app.database
from main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    Set up a clean in-memory SQLite database for the test session.
    This fixture runs once per test session.
    """
    
    original_database_url = settings.DATABASE_URL
    original_secret_key = settings.SECRET_KEY
    original_api_key = settings.API_KEY
    original_debug = settings.DEBUG

    settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    settings.SECRET_KEY = "test-secret-key-for-testing-only-must-be-long-enough-32-chars"
    settings.API_KEY = "test-api-key"
    settings.DEBUG = True

    app.database.engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        future=True
    )
    app.database.AsyncSessionLocal = sessionmaker(
        app.database.engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with app.database.AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    async with app.database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with app.database.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await app.database.engine.dispose()

    settings.DATABASE_URL = original_database_url
    settings.SECRET_KEY = original_secret_key
    settings.API_KEY = original_api_key
    settings.DEBUG = original_debug

    app.dependency_overrides = {}
