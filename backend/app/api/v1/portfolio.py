"""Endpoint d'allocation de portefeuille (classes d'actifs génériques uniquement)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.db.session import get_db
from app.portfolio.schemas import PortfolioAllocationResponse
from app.portfolio.service import get_allocation

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/allocation", response_model=PortfolioAllocationResponse)
def allocation(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    methode: Literal["hrp", "erc"] = "hrp",
    montant: Annotated[float | None, Query(ge=0, description="Capital à répartir, en euros")] = None,
) -> PortfolioAllocationResponse:
    """Propose une allocation par classe d'actifs générique, adaptée au profil de
    l'utilisateur connecté (tolérance au risque, âge, horizon, objectif).

    Réservé à l'offre payante. Ne renvoie que des classes génériques, jamais
    d'instrument nominatif.
    """
    return get_allocation(db, current_user, methode=methode, montant=montant)
