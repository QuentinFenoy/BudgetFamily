"""Configuration centrale de l'application."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BudgetFamily API"
    api_v1_prefix: str = "/v1"
    environment: str = "development"

    # --- Base de données ---
    # SQLite par défaut pour le dev/local et les tests ; en production, surcharger
    # via la variable d'environnement DATABASE_URL avec une URL PostgreSQL
    # (ex. postgresql+psycopg://user:pass@host:5432/budgetfamily).
    database_url: str = "sqlite:///./budgetfamily.db"

    # --- Authentification JWT ---
    # ATTENTION : jwt_secret_key DOIT etre surchargee en production via l'environnement.
    # Cette valeur par defaut n'est la que pour le dev/local et les tests.
    jwt_secret_key: str = "dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 h

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
