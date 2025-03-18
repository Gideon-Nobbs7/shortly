from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv
from functools import lru_cache
import os


# env_path = Path("..") / ".env"
# load_dotenv(dotenv_path=env_path)

current_dir = Path(__file__).parent
root_dir = current_dir.parent
env_path = root_dir / ".env"

load_dotenv(dotenv_path=env_path)

# print(f"Loading .env from: {env_path}")
# print(f".env exists: {env_path.exists()}")
# print(f"POSTGRES_PASSWORD found: {os.environ.get("POSTGRES_PASSWORD")}")


class Settings(BaseSettings):
    env_name: str = "Local"
    base_url: str = "http://localhost:8000"
    PROJECT_NAME:str = "Turtle Link Shortener"
    PROJECT_VERSION: str = "1.0.0"

    POSTGRES_USER : str = os.environ.get("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.environ.get("POSTGRES_PASSWORD")
    POSTGRES_SERVER : str = os.environ.get("POSTGRES_SERVER","localhost")
    POSTGRES_PORT : str = os.environ.get("POSTGRES_PORT")   
    POSTGRES_DB : str = os.environ.get("POSTGRES_DB")
    DATABASE_URL: str = os.environ.get("DATABASE_URL")

    class Config:
        env_file = str(env_path)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    return settings
