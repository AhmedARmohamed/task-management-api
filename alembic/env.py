from logging.config import fileConfig
from sqlalchemy import engine_from_config, create_engine
from sqlalchemy import pool
from alembic import context
import os

# this is the Alembic Config object
config = context.config

# Get DATABASE_URL from environment
database_url = os.environ.get("DATABASE_URL", "sqlite:///./tasks.db")
# Ensure it's sync SQLite for Alembic
if "sqlite+aiosqlite" in database_url:
    database_url = database_url.replace("sqlite+aiosqlite", "sqlite")

config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import your models' Base metadata
# This is a simple approach that doesn't import the whole app
from sqlalchemy import MetaData, Table, Column, Integer, String, DateTime, ForeignKey, Enum
import sqlalchemy as sa

target_metadata = MetaData()

# Define tables directly for migrations
users_table = Table(
    'users',
    target_metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('username', String, unique=True, index=True, nullable=False),
    Column('hashed_password', String, nullable=False),
    Column('created_at', DateTime, default=sa.func.now()),
)

tasks_table = Table(
    'tasks',
    target_metadata,
    Column('id', Integer, primary_key=True, index=True),
    Column('title', String, nullable=False),
    Column('description', String, nullable=True),
    Column('status', Enum('PENDING', 'COMPLETED', name='taskstatus'), default='PENDING'),
    Column('user_id', Integer, ForeignKey('users.id'), nullable=False),
    Column('created_at', DateTime, default=sa.func.now()),
)

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