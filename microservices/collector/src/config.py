from functools import lru_cache
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_url: str  #"postgresql://user:pass@localhost/trends"
    proxy: str  # 代理配置（如"http://user:pass@proxy:8080"）
    request_delay: float  # Trends API请求间隔
    port: int 
    api_gateway:str
    class Config:
        env_file = Path(__file__).parent.parent / ".env"
@lru_cache
def get_settings() -> Settings:
    return Settings()


