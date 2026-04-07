import os
from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    DB_HOST: str = "postgres"
    DB_USER: str
    DB_PASS: str
    DB_NAME: str = "warsim"
    REDIS_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    @property
    def db_dsn(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}/{self.DB_NAME}"
settings = Settings()
