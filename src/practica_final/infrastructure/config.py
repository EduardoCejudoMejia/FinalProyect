"""Configuración centralizada, inyectable y basada en variables de entorno."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    database_url: str = "sqlite:///./bicycle_orders.db"
    jwt_secret: str = "development-only-secret"
    access_token_expire_minutes: int = 30
    cors_origins: str = "http://localhost:3000"


settings = Settings()
