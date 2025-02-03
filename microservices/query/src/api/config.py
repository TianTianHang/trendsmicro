from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_url: str  #"postgresql://user:pass@localhost/trends"
    port: int
    class Config:
        env_file = Path(__file__).parent.parent / ".env"

def get_settings() -> Settings:
    return Settings()
