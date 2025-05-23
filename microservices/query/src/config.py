from typing import List
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_url: str #"postgresql://trends_user:trends_pass@postgres/trends"
    port: int
    consul_host: str = "localhost"
    consul_port: int = 8500
    service_tags: List[str] = ["query"]
    rabbitmq_host: str =  "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_username: str = "admin"
    rabbitmq_password: str = "admin"
    debug:bool=True
    
    class Config:
        env_file = Path(__file__).parent.parent / ".env"

def get_settings() -> Settings:
    return Settings()
