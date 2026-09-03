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
    initial_supervisor_nik: str = "supervisor"
    initial_supervisor_name: str = "Supervisor STATCHECK"
    initial_supervisor_password: str = "Supervisor123!"
    initial_ka_bps_nik: str = "kabps"
    initial_ka_bps_name: str = "Kepala BPS"
    initial_ka_bps_password: str = "KaBPS123!"
    initial_humas_nik: str = "humas"
    initial_humas_name: str = "Humas STATCHECK"
    initial_humas_password: str = "Humas123!"
    upload_dir: str = "uploads"
    max_upload_size_mb: int = 25

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.backend_cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
