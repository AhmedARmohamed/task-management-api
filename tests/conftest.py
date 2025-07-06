import pytest
import asyncio
from unittest.mock import patch, AsyncMock

from app.config import settings
from app.database import Base, get_db
import app.database
from main import app

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker


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

    test_database_url = "sqlite+aiosqlite:///:memory:"
    settings.DATABASE_URL = test_database_url

    test_engine = create_async_engine(
        test_database_url,
        echo=False,
        future=True
    )
    test_async_session_local = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    with patch('app.database.engine', new=test_engine) as mock_engine, \
            patch('app.database.AsyncSessionLocal', new=test_async_session_local) as mock_session_local:

        async def mock_create_tables():
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        with patch('app.database.create_tables', new=mock_create_tables):

            async def override_get_db():
                async with mock_session_local() as session:
                    try:
                        yield session
                    finally:
                        await session.close()

            app.dependency_overrides[get_db] = override_get_db

            yield

            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

            await test_engine.dispose()

    settings.DATABASE_URL = original_database_url
    settings.SECRET_KEY = original_secret_key
    settings.API_KEY = original_api_key
    settings.DEBUG = original_debug

    app.dependency_overrides = {}
