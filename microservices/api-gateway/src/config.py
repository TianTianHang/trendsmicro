from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    debug:bool=True
    health_check_interval: int
    service_timeout: int
    port: int
    consul_host: str = "localhost"
    consul_port: int = 8500
    service_check_interval: str = "10s"
    service_check_timeout: str = "1s"
    service_tags: List[str] = ["api-gateway"]
   
    class Config:
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = 'utf-8'

@lru_cache
def get_settings() -> Settings:
    return Settings()
