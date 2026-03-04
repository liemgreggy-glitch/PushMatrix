from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Telegram API
    telegram_api_id: Optional[int] = None
    telegram_api_hash: Optional[str] = None

    # Database
    database_url: str = "sqlite:///./pushmatrix.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Rate limiting
    default_send_interval: int = 30
    default_daily_limit: int = 100
    max_random_delay: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
