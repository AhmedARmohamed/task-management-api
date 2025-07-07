from logging.config import fileConfig
from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool
from alembic import context
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import after adding to path
from app.models import User, Task  # Import all models
from app.config import settings

# Import Base separately to avoid circular imports
from sqlalchemy.orm import declarative_base
Base = declarative_base()

# Import models to ensure they're registered with Base
from app.models import User, Task

# this is the Alembic Config object
config = context.config

# Get DATABASE_URL and convert async to sync for Alembic
database_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
# Convert async SQLite URL to sync for Alembic
if "sqlite+aiosqlite" in database_url:
    database_url = database_url.replace("sqlite+aiosqlite", "sqlite")

# Set the database URL for Alembic
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Use the actual Base from your models
from app.database import Base
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Create a sync engine for Alembic
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()