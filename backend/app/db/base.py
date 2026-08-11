"""Base déclarative SQLAlchemy commune à tous les modèles ORM.

Tous les modèles de persistance (app.db.models) héritent de cette Base.
`Base.metadata` sert de cible unique à Alembic pour l'autogénération des migrations.

La naming_convention est nécessaire pour SQLite : Alembic modifie les tables SQLite
en mode "batch" (recréation de table), qui exige que TOUTE contrainte (FK, index,
unique...) ait un nom explicite. Sans cette convention, SQLAlchemy laisse certaines
contraintes anonymes, et l'autogénération Alembic échoue avec "Constraint must have
a name" dès qu'une migration touche une contrainte sous SQLite (rencontré lors de
l'ajout de la FK allocation_simulations.goal_id -> savings_goals.id).
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=_NAMING_CONVENTION)
