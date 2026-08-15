"""Configuration centrale de l'application."""

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Valeurs par défaut de DÉVELOPPEMENT uniquement. En production, elles doivent être
# surchargées par l'environnement — sinon l'application refuse de démarrer (voir
# _valider_config_production).
_DEV_JWT_SECRET = "dev-secret-change-me-in-production"
_DEV_WEBHOOK_SECRET = "dev-webhook-secret-change-me-in-production"
_DEV_DATABASE_URL = "sqlite:///./budgetfamily.db"


class Settings(BaseSettings):
    app_name: str = "BudgetFamily API"
    api_v1_prefix: str = "/v1"
    environment: str = "development"  # "development" | "production"

    # --- Base de données ---
    # SQLite par défaut pour le dev/local et les tests ; en production, surcharger via
    # DATABASE_URL avec une URL PostgreSQL. Les schémas `postgres://` et `postgresql://`
    # (fournis par Neon, Render, etc.) sont automatiquement normalisés vers le driver
    # psycopg 3 (`postgresql+psycopg://`).
    database_url: str = _DEV_DATABASE_URL

    # --- Authentification JWT ---
    jwt_secret_key: str = _DEV_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 h

    # --- Billing ---
    # Secret partagé vérifiant l'authenticité des appels au webhook (app.billing).
    # En prod, remplacer à terme par la validation de signature du fournisseur
    # (Stripe-Signature, mécanisme d'auth webhook de RevenueCat, etc.).
    billing_webhook_secret: str = _DEV_WEBHOOK_SECRET

    model_config = SettingsConfigDict(env_file=".env")

    @field_validator("database_url")
    @classmethod
    def _normaliser_url_postgres(cls, valeur: str) -> str:
        """Force le driver psycopg 3 pour PostgreSQL, quel que soit le schéma fourni."""
        for prefixe in ("postgres://", "postgresql://"):
            if valeur.startswith(prefixe):
                return "postgresql+psycopg://" + valeur[len(prefixe):]
        return valeur

    @model_validator(mode="after")
    def _valider_config_production(self) -> "Settings":
        """En production, refuse de démarrer si les secrets ou la base sont restés sur
        les valeurs de développement — un garde-fou contre un déploiement non sécurisé."""
        if self.environment != "production":
            return self

        problemes = []
        if self.database_url.startswith("sqlite"):
            problemes.append("DATABASE_URL doit pointer vers PostgreSQL (SQLite détecté)")
        if self.jwt_secret_key == _DEV_JWT_SECRET:
            problemes.append("JWT_SECRET_KEY doit être défini (valeur de développement détectée)")
        if self.billing_webhook_secret == _DEV_WEBHOOK_SECRET:
            problemes.append(
                "BILLING_WEBHOOK_SECRET doit être défini (valeur de développement détectée)"
            )
        if problemes:
            raise ValueError("Configuration de production invalide — " + " ; ".join(problemes))
        return self


settings = Settings()
