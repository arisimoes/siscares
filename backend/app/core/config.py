from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "SisCarEs"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    DATABASE_URL: str = "postgresql://siscares:siscares@localhost:5432/siscares"
    CRYPTO_KEY: str = "change-me-32-bytes-long-key!!"  # Must be 32 url-safe base64-encoded bytes for Fernet
    UPLOAD_DIR: str = "../frontend/static/uploads"
    MAX_UPLOAD_SIZE_MB: int = 5
    CORS_ORIGINS: str = "*"

    @property
    def cors_origins_list(self):
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
