# config.py
import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    secret_key: str = os.getenv("SECRET_KEY")
    database_url: str = os.getenv("DATABASE_URL")
    refresh_secret_key: str = os.getenv("REFRESH_SECRET_KEY")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY")

    class Config:
        env_file = ".env"


settings = Settings()
