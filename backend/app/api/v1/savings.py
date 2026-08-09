"""Endpoints liés à la gestion des objectifs d'épargne."""

from fastapi import APIRouter

from app.savings.engine import repartir_epargne
from app.savings.models import ObjectifEpargne
from app.savings.schemas import (
    RepartitionEpargneRequest,
    ResultatRepartitionResponse,
    AllocationObjectifResponse,
)

router = APIRouter(prefix="/savings", tags=["savings"])


@router.post("/repartition", response_model=ResultatRepartitionResponse)
def calculate_repartition(payload: RepartitionEpargneRequest) -> ResultatRepartitionResponse:
    """Répartit un montant d'épargne disponible entre plusieurs objectifs,
    selon la méthode choisie (cascade par priorité, ou proportionnelle)."""
    objectifs = [
        ObjectifEpargne(
            id=o.id,
            nom=o.nom,
            montant_cible=o.montant_cible,
            montant_actuel=o.montant_actuel,
            priorite=o.priorite,
        )
        for o in payload.objectifs
    ]
    resultat = repartir_epargne(objectifs, payload.epargne_disponible, methode=payload.methode)
    return ResultatRepartitionResponse(
        epargne_disponible=resultat.epargne_disponible,
        allocations=[AllocationObjectifResponse(**a.__dict__) for a in resultat.allocations],
        epargne_non_allouee=resultat.epargne_non_allouee,
    )
