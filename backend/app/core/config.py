from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "STATCHECK API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./statcheck.db"
    jwt_secret_key: str = "development-only-secret-change-this-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    backend_cors_origins: str = "http://localhost:3000"
    initial_admin_nik: str = "admin"
    initial_admin_name: str = "Administrator STATCHECK"
    initial_admin_password: str = "Admin123!"

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.backend_cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
