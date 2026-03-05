from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram API 凭据
    # 默认值为 Telegram Desktop 公开客户端凭据（api_id=2040），适用于大多数账号检查场景。
    # 如需使用自己的凭据，请通过环境变量 TELEGRAM_API_ID / TELEGRAM_API_HASH 或 .env 文件覆盖。
    telegram_api_id: int = 2040
    telegram_api_hash: str = "b18441a1ff607e10a989891a5462e627"

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
