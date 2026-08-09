"""Moteur SQLAlchemy, fabrique de sessions et dépendance FastAPI `get_db`.

Le moteur est créé paresseusement à l'import (aucune connexion n'est ouverte tant
qu'une requête n'est pas exécutée), ce qui laisse les endpoints purement calculatoires
(budgeting, savings) fonctionner sans base de données.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# check_same_thread=False est requis uniquement pour SQLite (dev/tests) afin que la
# session puisse être partagée entre threads par le serveur ASGI. Sans effet sur PostgreSQL.
_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=_connect_args, future=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    """Fournit une session de base de données par requête, fermée automatiquement."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
