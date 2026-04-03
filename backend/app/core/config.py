from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "RaspSystem API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api"
    debug: bool = True
    session_secret_key: str = Field(default="change-me", alias="SESSION_SECRET_KEY")
    session_cookie_name: str = Field(default="raspsystem_session", alias="SESSION_COOKIE_NAME")
    session_max_age: int = Field(default=60 * 60 * 24 * 7, alias="SESSION_MAX_AGE")
    frontend_origins_raw: str = Field(
        default="http://localhost:4321,http://127.0.0.1:4321",
        alias="FRONTEND_ORIGINS",
    )

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    postgres_server: str = Field(default="postgres", alias="POSTGRES_SERVER")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="rasp_user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="rasp_password", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="rasp_db", alias="POSTGRES_DB")

    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    @property
    def frontend_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
