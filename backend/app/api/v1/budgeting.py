"""Endpoints liés à la répartition budgétaire."""

from fastapi import APIRouter

from app.budgeting.engine import calculer_budget
from app.budgeting.models import ProfilFoyer
from app.budgeting.schemas import ProfilFoyerRequest, ResultatBudgetResponse

router = APIRouter(prefix="/budgeting", tags=["budgeting"])


@router.post("/calculate", response_model=ResultatBudgetResponse)
def calculate_budget(payload: ProfilFoyerRequest) -> ResultatBudgetResponse:
    """Calcule la répartition budgétaire recommandée pour un profil de foyer donné."""
    profil = ProfilFoyer(
        revenus_total=payload.revenus_total,
        charges_fixes_total=payload.charges_fixes_total,
        nb_personnes=payload.nb_personnes,
        nb_enfants=payload.nb_enfants,
        objectif=payload.objectif,
        matelas_securite_atteint=payload.matelas_securite_atteint,
    )
    resultat = calculer_budget(profil, epargne_cible_forcee=payload.epargne_cible_forcee)
    return ResultatBudgetResponse(**resultat.__dict__)
