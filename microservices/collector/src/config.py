from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_url: str # "postgresql://trends_user:trends_pass@postgres/trends"
    proxy: str  # 代理配置（如"http://user:pass@proxy:8080"）
    request_delay: float  # Trends API请求间隔
    port: int 
    consul_host: str = "localhost"
    consul_port: int = 8500
    service_tags: List[str] = ["trends_collector"]
    rabbitmq_host: str =  "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_username: str = "admin"
    rabbitmq_password: str = "admin"
    class Config:
        env_file = Path(__file__).parent.parent / ".env"
@lru_cache
def get_settings() -> Settings:
    return Settings()


