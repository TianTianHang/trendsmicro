from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_url: str
    port: int
    algorithm: str = "HS256"
    consul_host: str = "localhost"
    consul_port: int = 8500
    service_tags: List[str] = ["permission"]

    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = 'utf-8'

@lru_cache
def get_settings() -> Settings:
    return Settings()
