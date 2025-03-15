from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv
from functools import lru_cache
import os


env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    env_name: str = "Local"
    base_url: str = "http://localhost:8000"
    PROJECT_NAME:str = "First Timers"
    PROJECT_VERSION: str = "1.0.0"

    POSTGRES_USER : str = os.environ.get("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD")
    POSTGRES_SERVER : str = os.environ.get("POSTGRES_SERVER","localhost")
    POSTGRES_PORT : str = os.environ.get("POSTGRES_PORT",5432)
    POSTGRES_DB : str = os.environ.get("POSTGRES_DB")
    DATABASE_URL: str = os.environ.get("DATABASE_URL")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    return settings
