from typing import List
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_url: str  #"postgresql://user:pass@localhost/trends"
    port: int
    consul_host: str = "localhost"
    consul_port: int = 8500
    service_tags: List[str] = ["query"]
    class Config:
        env_file = Path(__file__).parent.parent / ".env"

def get_settings() -> Settings:
    return Settings()
