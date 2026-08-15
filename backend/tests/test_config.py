"""Tests de la configuration : normalisation d'URL PostgreSQL et garde-fou de production."""

import pytest

from app.core.config import _DEV_JWT_SECRET, _DEV_WEBHOOK_SECRET, Settings


def _dev(**kwargs) -> Settings:
    return Settings(_env_file=None, environment="development", **kwargs)


def test_normalise_les_schemas_postgres_vers_psycopg():
    assert _dev(database_url="postgres://u:p@h/db").database_url == "postgresql+psycopg://u:p@h/db"
    assert (
        _dev(database_url="postgresql://u:p@h:5432/db").database_url
        == "postgresql+psycopg://u:p@h:5432/db"
    )


def test_laisse_inchangees_les_urls_deja_normalisees_ou_sqlite():
    assert (
        _dev(database_url="postgresql+psycopg://u:p@h/db").database_url
        == "postgresql+psycopg://u:p@h/db"
    )
    assert _dev(database_url="sqlite:///./x.db").database_url == "sqlite:///./x.db"


def test_production_refuse_les_secrets_de_dev():
    # URL PostgreSQL valide, mais secrets restés sur les valeurs de développement.
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            environment="production",
            database_url="postgresql://u:p@h/db",
            jwt_secret_key=_DEV_JWT_SECRET,
            billing_webhook_secret=_DEV_WEBHOOK_SECRET,
        )


def test_production_refuse_sqlite():
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            environment="production",
            database_url="sqlite:///./x.db",
            jwt_secret_key="un-vrai-secret",
            billing_webhook_secret="un-autre-secret",
        )


def test_production_valide_quand_tout_est_fourni():
    s = Settings(
        _env_file=None,
        environment="production",
        database_url="postgresql://u:p@h/db",
        jwt_secret_key="un-vrai-secret",
        billing_webhook_secret="un-autre-secret",
    )
    assert s.environment == "production"
    assert s.database_url.startswith("postgresql+psycopg://")


def test_developpement_accepte_les_defauts():
    s = _dev()
    assert s.environment == "development"
    assert s.database_url.startswith("sqlite")
