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
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = True
    session_secret_key: str = Field(default="change-me", alias="SESSION_SECRET_KEY")
    session_cookie_name: str = Field(default="raspsystem_session", alias="SESSION_COOKIE_NAME")
    session_max_age: int = Field(default=60 * 60 * 24 * 7, alias="SESSION_MAX_AGE")
    session_same_site: str = Field(default="lax", alias="SESSION_SAME_SITE")
    session_cookie_domain: str | None = Field(default=None, alias="SESSION_COOKIE_DOMAIN")
    frontend_origins_raw: str = Field(
        default="http://localhost:4321,http://127.0.0.1:4321",
        alias="FRONTEND_ORIGINS",
    )
    csrf_trusted_origins_raw: str | None = Field(default=None, alias="CSRF_TRUSTED_ORIGINS")
    api_docs_enabled: bool | None = Field(default=None, alias="API_DOCS_ENABLED")
    allow_originless_unsafe_requests: bool | None = Field(default=None, alias="ALLOW_ORIGINLESS_UNSAFE_REQUESTS")
    login_rate_limit_attempts: int = Field(default=5, alias="LOGIN_RATE_LIMIT_ATTEMPTS")
    login_rate_limit_window_seconds: int = Field(default=15 * 60, alias="LOGIN_RATE_LIMIT_WINDOW_SECONDS")
    password_change_rate_limit_attempts: int = Field(default=5, alias="PASSWORD_CHANGE_RATE_LIMIT_ATTEMPTS")
    password_change_rate_limit_window_seconds: int = Field(default=10 * 60, alias="PASSWORD_CHANGE_RATE_LIMIT_WINDOW_SECONDS")
    jwt_secret_key: str = Field(default="change-me", alias="JWT_SECRET_KEY")
    jwt_access_token_expire_minutes: int = Field(default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_days: int = Field(default=30, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")

    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    postgres_server: str = Field(default="postgres", alias="POSTGRES_SERVER")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="rasp_user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="rasp_password", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="rasp_db", alias="POSTGRES_DB")

    redis_host: str = Field(default="redis", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    raspyx_api_base_url: str = Field(default="https://zefixed.ru/raspyx/api/v2", alias="RASPYX_API_BASE_URL")
    raspyx_auth_url: str = Field(default="https://zefixed.ru/auth/api/v1/login", alias="RASPYX_AUTH_URL")
    raspyx_username: str = Field(default="username", alias="RASPYX_USERNAME")
    raspyx_password: str = Field(default="password=", alias="RASPYX_PASSWORD")

    @property
    def sqlalchemy_database_uri(self) -> str:
        # Prefer the discrete Postgres settings when they were provided explicitly.
        # This avoids subtle mismatches when DATABASE_URL and POSTGRES_* drift apart.
        postgres_fields = {
            "postgres_server",
            "postgres_port",
            "postgres_user",
            "postgres_password",
            "postgres_db",
        }
        if postgres_fields.issubset(self.model_fields_set):
            return (
                f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
            )
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

    @property
    def csrf_trusted_origins(self) -> list[str]:
        source = self.csrf_trusted_origins_raw or self.frontend_origins_raw
        return [origin.strip().lower() for origin in source.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() == "production"

    @property
    def session_https_only(self) -> bool:
        return self.is_production

    @property
    def are_api_docs_enabled(self) -> bool:
        if self.api_docs_enabled is not None:
            return self.api_docs_enabled
        return not self.is_production

    @property
    def allow_originless_unsafe_api_requests(self) -> bool:
        if self.allow_originless_unsafe_requests is not None:
            return self.allow_originless_unsafe_requests
        return not self.is_production

    def validate_runtime_settings(self) -> None:
        if not self.is_production:
            return

        weak_session_secret_values = {
            "",
            "change-me",
            "change-me-in-production",
        }
        weak_jwt_secret_values = {
            "",
            "change-me",
            "change-me-in-production",
        }
        if self.session_secret_key.strip() in weak_session_secret_values:
            raise RuntimeError("SESSION_SECRET_KEY must be set to a strong value in production.")
        if self.jwt_secret_key.strip() in weak_jwt_secret_values:
            raise RuntimeError("JWT_SECRET_KEY must be set to a strong value in production.")

        if self.session_same_site.strip().lower() not in {"lax", "strict", "none"}:
            raise RuntimeError("SESSION_SAME_SITE must be one of: lax, strict, none.")

        if self.session_same_site.strip().lower() == "none" and not self.session_https_only:
            raise RuntimeError("SESSION_SAME_SITE=none requires secure HTTPS cookies.")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
