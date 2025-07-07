from pydantic_settings import BaseSettings
from typing import Optional
import os
import secrets

class Settings(BaseSettings):
    """Application settings"""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/tasks.db"

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    API_KEY: str = "123456"

    # App
    APP_NAME: str = "Task Management API"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Auto-generate secure secret key if using default
        if self.SECRET_KEY == "your-secret-key-change-this-in-production":
            self.SECRET_KEY = secrets.token_urlsafe(32)

        # Handle Railway PostgreSQL URL if provided
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            # Convert postgres:// to postgresql+asyncpg:// for async support
            if database_url.startswith("postgres://"):
                self.DATABASE_URL = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
            elif database_url.startswith("postgresql://"):
                self.DATABASE_URL = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            else:
                self.DATABASE_URL = database_url

        # Set production mode if PORT is set (Railway environment)
        if os.getenv("PORT"):
            self.DEBUG = False

settings = Settings()