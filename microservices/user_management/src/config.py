from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_url: str  #"postgresql://user:pass@localhost/trends"
    api_gateway:str
    port: int
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    class Config:
        env_file = Path(__file__).parent.parent / ".env"

def get_settings() -> Settings:
    return Settings()
