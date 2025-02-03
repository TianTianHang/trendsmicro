from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_url: str = "sqlite:///trends.db" #"postgresql://user:pass@localhost/trends"
    proxy: str = ""  # 代理配置（如"http://user:pass@proxy:8080"）
    request_delay: float = 10.0  # Trends API请求间隔

    class Config:
        env_file = Path(__file__).parent.parent.parent / ".env"
def get_settings() -> Settings:
    return Settings()
