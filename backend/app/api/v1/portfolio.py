"""Endpoint d'allocation de portefeuille (classes d'actifs génériques uniquement)."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.db.session import get_db
from app.portfolio.schemas import (
    AllocationSimulationDetail,
    AllocationSimulationSummary,
    PortfolioAllocationResponse,
)
from app.portfolio.service import get_allocation, get_simulation, list_simulations

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("/allocation", response_model=PortfolioAllocationResponse)
def allocation(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    methode: Literal["hrp", "erc"] = "hrp",
    montant: Annotated[float | None, Query(ge=0, description="Capital à répartir, en euros")] = None,
    save: Annotated[bool, Query(description="Enregistrer cette simulation dans l'historique")] = True,
    goal_id: Annotated[int | None, Query(description="Objectif d'épargne associé, si pertinent")] = None,
) -> PortfolioAllocationResponse:
    """Propose une allocation par classe d'actifs générique, adaptée au profil de
    l'utilisateur connecté (tolérance au risque, âge, horizon, objectif).

    Réservé à l'offre payante. Ne renvoie que des classes génériques, jamais
    d'instrument nominatif. Enregistrée dans l'historique par défaut (save=false
    pour un aperçu non conservé). goal_id, optionnel, rattache la simulation à un
    objectif d'épargne persisté (doit appartenir à l'utilisateur connecté).
    """
    return get_allocation(db, current_user, methode=methode, montant=montant, save=save, goal_id=goal_id)


@router.get("/simulations", response_model=list[AllocationSimulationSummary])
def simulations(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[AllocationSimulationSummary]:
    """Historique des simulations d'allocation, les plus récentes en premier."""
    return list_simulations(db, current_user, limit=limit)


@router.get("/simulations/{simulation_id}", response_model=AllocationSimulationDetail)
def simulation_detail(
    simulation_id: int,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AllocationSimulationDetail:
    """Détail complet d'une simulation passée (avec la répartition par classe)."""
    return get_simulation(db, current_user, simulation_id)
