import pytest
import asyncio
import os
from app.database import create_tables
from app.config import settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Ensure database tables exist before any test runs"""
    # Set test environment variables
    os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-must-be-long-enough-32-chars"
    os.environ["API_KEY"] = "test-api-key"
    os.environ["DEBUG"] = "True"

    # Update settings
    settings.SECRET_KEY = "test-secret-key-for-testing-only-must-be-long-enough-32-chars"
    settings.API_KEY = "test-api-key"
    settings.DEBUG = True

    # Make sure database tables exist
    await create_tables()
    yield