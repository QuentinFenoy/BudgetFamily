"""Endpoint du tableau de bord (recommandé vs réalisé par catégorie)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.dashboard.schemas import DashboardResponse
from app.dashboard.service import get_dashboard
from app.db.session import get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def dashboard(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    mois: Annotated[str | None, Query(description="Format YYYY-MM, défaut : mois courant")] = None,
) -> DashboardResponse:
    """Renvoie la répartition recommandée vs réalisée par catégorie pour le mois demandé,
    ainsi que le potentiel d'épargne recalculé à chaud."""
    return get_dashboard(db, current_user, mois)
