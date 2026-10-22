from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./edtech.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_alg: str = "HS256"
    access_token_ttl_minutes: int = 60 * 24 * 7
    storage_dir: str = "./storage"
    cors_origins: str = "http://localhost:3000"
    dev_mode: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
