from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    rate_limit_window_seconds: int = 60
    rate_limit_max_requests: int = 3

    data_file_path: str = "ad_exchange_auction/data/data.json"


settings = Settings()
