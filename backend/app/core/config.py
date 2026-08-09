"""Configuration centrale de l'application."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BudgetFamily API"
    api_v1_prefix: str = "/v1"
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
