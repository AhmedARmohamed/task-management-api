import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import your models - but we need to import Base directly to avoid async issues
from app.database import Base

# Import models to ensure they're registered with Base.metadata
from app.models import User, Task

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url():
    """Get database URL from environment or config, converted for sync use"""
    # Check for Railway DATABASE_URL environment variable
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Convert async URLs to sync URLs for migrations
        if database_url.startswith("postgresql+asyncpg://"):
            # Convert asyncpg to psycopg2 for sync migrations
            database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)
        elif database_url.startswith("postgres://"):
            # Convert postgres:// to postgresql:// for SQLAlchemy
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        elif database_url.startswith("sqlite+aiosqlite://"):
            # Convert async sqlite to sync sqlite
            database_url = database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
        return database_url

    # Fallback to config file (already sync)
    return config.get_main_option("sqlalchemy.url")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Override the sqlalchemy.url in the config
    config.set_main_option("sqlalchemy.url", get_database_url())

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()