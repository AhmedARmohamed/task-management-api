import pytest
import asyncio
import os
from subprocess import run, PIPE
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.config import settings
from main import app

# Force test database for all tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Override settings before importing anything else
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-must-be-long-enough-32-chars"
os.environ["API_KEY"] = "123456"
os.environ["DEBUG"] = "true"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=True,  # Set to False to reduce output
    future=True
)

TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Setup test database with migrations."""
    # Remove test database if exists
    if os.path.exists("test.db"):
        os.remove("test.db")

    # Run migrations using alembic
    env = os.environ.copy()
    env["DATABASE_URL"] = "sqlite:///./test.db"

    result = run(
        ["alembic", "upgrade", "head"],
        env=env,
        stdout=PIPE,
        stderr=PIPE,
        text=True
    )

    if result.returncode != 0:
        print(f"Migration failed!")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")

        # Fallback: create tables directly if migrations fail
        print("Falling back to direct table creation...")
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    else:
        print("Migrations applied successfully")

    yield

    # Cleanup
    await test_engine.dispose()

    # Remove test database after all tests
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture
async def db_session():
    """Get a test database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(autouse=True)
async def setup_test(db_session):
    # Override the get_db dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    yield

    # Cleanup after each test - clear all data but keep schema
    for table in reversed(Base.metadata.sorted_tables):
        await db_session.execute(table.delete())
    await db_session.commit()

    # Clear dependency overrides
    app.dependency_overrides.clear()
