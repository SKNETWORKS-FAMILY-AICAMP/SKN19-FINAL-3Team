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

    QUEUE_NAME: str = "llm_work_queue"

    HF_TOKEN: Optional[str] = None

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

        extra = "ignore"
    class Config:
        env_file = ".env"

settings = Settings()