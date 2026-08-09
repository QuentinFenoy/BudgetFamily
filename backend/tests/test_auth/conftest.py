"""Fixtures de test pour l'auth : base SQLite en mémoire, isolée par test.

On surcharge la dépendance `get_db` de l'application par une session pointant sur une
base SQLite en mémoire (StaticPool = une seule connexion partagée, indispensable pour
que le schéma persiste le temps du test). Les tables sont créées via les modèles ORM
(`Base.metadata.create_all`) — les migrations Alembic sont testées séparément.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app

# Importer les modèles pour les enregistrer sur Base.metadata.
# NB : ce `import app.db.models` lie le nom `app` au package, d'où l'alias
# `fastapi_app` ci-dessus pour ne pas masquer l'instance FastAPI.
import app.db.models  # noqa: F401,E402


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()
