from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_url: str  #"postgresql://user:pass@localhost/trends"
    port: int
    public_key_path: str
    private_key_path: str
    algorithm: str
    access_token_expire_minutes: int
    consul_host: str = "localhost"
    consul_port: int = 8500
    
    rabbitmq_host: str =  "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_username: str = "admin"
    rabbitmq_password: str = "admin"
    class Config:
        env_file = Path(__file__).parent.parent / ".env"

def get_settings() -> Settings:
    return Settings()
