"""Application configuration using Pydantic BaseSettings."""
from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/finora"

    # Security
    SECRET_KEY: str = "finora-super-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    # App
    PROJECT_NAME: str = "Finora"
    API_V1_STR: str = "/api/v1"
    DEFAULT_CURRENCY: str = "INR"
    DEFAULT_CURRENCY_SYMBOL: str = "\u20b9"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
