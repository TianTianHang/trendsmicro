from functools import lru_cache
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    health_check_interval:int
    service_timeout:int
    port:int
    class Config:
        env_file = Path(__file__).parent.parent / ".env"
@lru_cache
def get_settings() -> Settings:
    return Settings()
