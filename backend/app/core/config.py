# backend/app/core/config.py
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]  # football-miniapp/

class Settings(BaseSettings):
    DATABASE_URI: str = "sqlite+aiosqlite:///./app.db"

    YK_SHOP_ID: Optional[str] = None
    YK_API_KEY: Optional[str] = None
    BASE_URL:   Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),  # корневой .env
        extra="ignore",                   # игнорировать лишние переменные
    )

settings = Settings()

