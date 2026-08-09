"""Schémas Pydantic pour l'endpoint de calcul budgétaire.

Séparés volontairement des dataclasses internes (app.budgeting.models) : les schémas
Pydantic définissent le contrat public de l'API, les dataclasses définissent la logique
métier interne. Les deux évoluent pour des raisons différentes.
"""

from pydantic import BaseModel, Field

from app.budgeting.models import Objectif


class ProfilFoyerRequest(BaseModel):
    revenus_total: float = Field(..., gt=0, description="Revenus mensuels totaux du foyer")
    charges_fixes_total: float = Field(..., ge=0, description="Charges fixes mensuelles totales")
    nb_personnes: int = Field(..., ge=1, description="Nombre total d'habitants du foyer")
    nb_enfants: int = Field(0, ge=0, description="Nombre d'enfants à charge")
    objectif: Objectif = Objectif.AUCUN
    matelas_securite_atteint: bool = False
    epargne_cible_forcee: float | None = Field(
        None, description="Optionnel : cible d'épargne à forcer si supérieure au potentiel calculé"
    )


class ResultatBudgetResponse(BaseModel):
    disponible: float
    disponible_par_hab: float
    montants_categories: dict[str, float]
    epargne_potentielle: float
    epargne_reference_taux: float
    epargne_reference_montant: float
    ajustement_applique: bool
    ecart_non_couvert: float
