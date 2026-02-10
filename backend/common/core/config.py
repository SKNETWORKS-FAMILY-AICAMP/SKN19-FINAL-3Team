from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import computed_field

class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int = 5432
    DB_NAME: str

    REDIS_HOST: str
    REDIS_PORT: int = 6379

    API_HOST: str
    API_PORT: int = 8000

    QUEUE_NAME: str

    HF_TOKEN: Optional[str] = None

    # Auth
    JWT_SECRET_KEY: Optional[str] = None
    ACCESS_TOKEN_EXPIRE_MINUTES: Optional[int] = None
    REFRESH_TOKEN_EXPIRE_DAYS: Optional[int] = 7

    # Crypto
    AES_SECRET_KEY: Optional[str] = None

    # Privacy (JSON List of {"name": "...", "pattern": "..."})
    PRIVACY_PATTERNS_JSON: str = '[]'

    # Document Adaption Thresholds
    THRESHOLD_LEVEL1: float = 0.95 # 0.95
    THRESHOLD_LEVEL2: float = 0.5 # 0.8

    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @computed_field
    @property
    def API_SERVER_URL(self) -> str:
        return f"http://{self.API_HOST}:{self.API_PORT}"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()