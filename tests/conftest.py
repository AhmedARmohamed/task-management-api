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
    # Store original values
    original_database_url = settings.DATABASE_URL
    original_secret_key = settings.SECRET_KEY
    original_api_key = settings.API_KEY
    original_debug = settings.DEBUG

    # Set test values
    test_database_url = "sqlite+aiosqlite:///:memory:"
    settings.DATABASE_URL = test_database_url
    settings.SECRET_KEY = "test-secret-key-for-testing-only-must-be-long-enough-32-chars"
    settings.API_KEY = "123456"
    settings.DEBUG = True

    # Create test engine and session
    test_engine = create_async_engine(
        test_database_url,
        echo=False,
        future=True
    )

    test_async_session_local = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create tables in test database
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Mock the database components
    with patch('app.database.engine', new=test_engine), \
         patch('app.database.AsyncSessionLocal', new=test_async_session_local), \
         patch('app.database.create_tables') as mock_create_tables:

        # Make create_tables do nothing since we already created them
        mock_create_tables.return_value = AsyncMock()

        # Override the dependency
        async def override_get_db():
            async with test_async_session_local() as session:
                try:
                    yield session
                finally:
                    await session.close()

        app.dependency_overrides[get_db] = override_get_db

        yield

        # Cleanup
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await test_engine.dispose()

    # Restore original values
    settings.DATABASE_URL = original_database_url
    settings.SECRET_KEY = original_secret_key
    settings.API_KEY = original_api_key
    settings.DEBUG = original_debug
    app.dependency_overrides = {}