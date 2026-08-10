"""Endpoints des bilans périodiques."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.db.session import get_db
from app.reports.schemas import BilanMensuel, BilanTrimestriel
from app.reports.service import build_bilan_mensuel, build_bilan_trimestriel

router = APIRouter(prefix="/reports", tags=["reports"])

_MoisQuery = Annotated[str | None, Query(description="Format YYYY-MM, défaut : mois courant")]


@router.get("/monthly", response_model=BilanMensuel)
def monthly_report(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    mois: _MoisQuery = None,
) -> BilanMensuel:
    """Bilan mensuel : recommandé vs réalisé par catégorie, totaux, épargne réellement dégagée."""
    return build_bilan_mensuel(db, current_user, mois)


@router.get("/quarterly", response_model=BilanTrimestriel)
def quarterly_report(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    mois: _MoisQuery = None,
) -> BilanTrimestriel:
    """Bilan trimestriel avancé [payant] : tendances sur 3 mois, moyenne, écart au mois courant."""
    return build_bilan_trimestriel(db, current_user, mois)
