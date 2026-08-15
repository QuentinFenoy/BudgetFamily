"""Schémas de lecture du profil (GET /v1/profile).

La mise à jour (PUT /v1/profile) réutilise OnboardingRequest comme corps de requête
et OnboardingResponse comme réponse : même contrat que la création, seule la
sémantique (remplacer au lieu de créer) diffère.
"""

from pydantic import BaseModel


class IncomeItemOut(BaseModel):
    type: str
    libelle: str
    montant: float
    frequence: str


class FixedExpenseItemOut(BaseModel):
    libelle: str
    montant: float
    categorie: str | None = None


class ProfileDetailResponse(BaseModel):
    id: int
    nb_personnes: int
    nb_enfants: int
    situation_familiale: str | None
    age: int | None
    objectif: str
    tolerance_risque: int | None
    horizon_annees: int | None
    matelas_securite_atteint: bool
    revenus: list[IncomeItemOut]
    charges_fixes: list[FixedExpenseItemOut]
