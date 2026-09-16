"""Application configuration using Pydantic BaseSettings."""
from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./finora.db"

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
    APP_VERSION: str = "1.0.0"
    DEFAULT_CURRENCY: str = "INR"
    DEFAULT_CURRENCY_SYMBOL: str = "\u20b9"

    # ── Google Drive persistence (opt-in) ─────────────────────────────────────
    # Set GOOGLE_DRIVE_ENABLED=true to activate cloud persistence.
    # When false, Finora runs entirely locally using only SQLite.
    GOOGLE_DRIVE_ENABLED: bool = False
    GOOGLE_DRIVE_ROOT: str = "Finora"
    GOOGLE_CREDENTIALS_FILE: str = "credentials.json"
    GOOGLE_TOKEN_FILE: str = ".finora/token.json"

    # ── Persistence tuning ────────────────────────────────────────────────────
    # Maximum number of permanent numbered versions to keep in Google Drive.
    MAX_VERSIONS: int = 5
    # Autosave interval in seconds (updates current/ without creating a new version).
    AUTOSAVE_INTERVAL: int = 300  # 5 minutes

    # ── Local cache / working directory ───────────────────────────────────────
    FINORA_CACHE_DIR: str = ".finora"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
