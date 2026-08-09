"""Schémas Pydantic de l'onboarding (contrat public de POST /v1/onboarding)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.budgeting.models import Objectif
from app.budgeting.schemas import ResultatBudgetResponse


class IncomeItem(BaseModel):
    type: Literal["fixe", "variable"]
    libelle: str = Field(..., min_length=1, max_length=120)
    montant: float = Field(..., ge=0, description="Montant mensuel (moyenne pour le variable)")
    frequence: str = Field("mensuel", max_length=20)


class FixedExpenseItem(BaseModel):
    libelle: str = Field(..., min_length=1, max_length=120)
    montant: float = Field(..., ge=0, description="Montant mensuel")
    categorie: str | None = Field(None, max_length=60)


class OnboardingRequest(BaseModel):
    """Situation déclarée à l'installation. Tous les montants sont mensuels."""

    nb_personnes: int = Field(..., ge=1, description="Nombre total d'habitants du foyer")
    nb_enfants: int = Field(0, ge=0)
    situation_familiale: str | None = Field(None, max_length=30)
    age: int | None = Field(None, ge=0, le=120)
    objectif: Objectif = Objectif.AUCUN
    tolerance_risque: int | None = Field(None, ge=1, le=5)
    horizon_annees: int | None = Field(None, ge=0)
    matelas_securite_atteint: bool = False
    revenus: list[IncomeItem] = Field(..., min_length=1)
    charges_fixes: list[FixedExpenseItem] = Field(default_factory=list)

    @model_validator(mode="after")
    def _coherence_foyer(self) -> "OnboardingRequest":
        if self.nb_enfants > self.nb_personnes:
            raise ValueError("nb_enfants ne peut pas dépasser nb_personnes")
        return self


class ProfileSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nb_personnes: int
    nb_enfants: int
    objectif: str


class OnboardingResponse(BaseModel):
    """Profil créé + premier budget calculé."""

    profile: ProfileSummary
    budget: ResultatBudgetResponse
