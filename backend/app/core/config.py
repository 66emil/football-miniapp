from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URI: str = "sqlite+aiosqlite:///./app.db"

settings = Settings()  # env-override-friendly
