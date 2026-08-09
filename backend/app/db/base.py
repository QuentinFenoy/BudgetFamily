"""Base déclarative SQLAlchemy commune à tous les modèles ORM.

Tous les modèles de persistance (app.db.models) héritent de cette Base.
`Base.metadata` sert de cible unique à Alembic pour l'autogénération des migrations.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
