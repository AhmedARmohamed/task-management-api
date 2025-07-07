from pydantic_settings import BaseSettings
from typing import Optional
import os

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

    # Railway specific
    PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Override with Railway environment variables if present
        if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PORT"):
            self.DEBUG = False
            if os.getenv("PORT"):
                self.PORT = int(os.getenv("PORT"))
            # Generate a secure secret key for production if not set
            if self.SECRET_KEY == "your-secret-key-change-this-in-production":
                import secrets
                self.SECRET_KEY = secrets.token_urlsafe(32)

settings = Settings()