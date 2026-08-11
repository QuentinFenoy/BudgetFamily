"""Schémas Pydantic pour l'endpoint de répartition de l'épargne entre objectifs."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ObjectifEpargneRequest(BaseModel):
    id: str
    nom: str
    montant_cible: float = Field(..., gt=0)
    montant_actuel: float = Field(0.0, ge=0)
    priorite: int = Field(1, ge=1)


class RepartitionEpargneRequest(BaseModel):
    objectifs: list[ObjectifEpargneRequest]
    epargne_disponible: float = Field(..., ge=0)
    methode: Literal["cascade", "proportionnelle"] = "cascade"


class AllocationObjectifResponse(BaseModel):
    objectif_id: str
    montant_alloue_ce_mois: float
    mois_restants_estimes: float | None


class ResultatRepartitionResponse(BaseModel):
    epargne_disponible: float
    allocations: list[AllocationObjectifResponse]
    epargne_non_allouee: float


# ── Objectifs d'épargne persistés (CRUD) ─────────────────────────────────────────


class SavingsGoalCreate(BaseModel):
    libelle: str = Field(..., min_length=1, max_length=120)
    montant_cible: float = Field(..., gt=0)
    montant_actuel: float = Field(0.0, ge=0)
    priorite: int = Field(1, ge=1)


class SavingsGoalUpdate(BaseModel):
    """Tous les champs sont optionnels : seuls ceux fournis sont modifiés (PATCH)."""

    libelle: str | None = Field(None, min_length=1, max_length=120)
    montant_cible: float | None = Field(None, gt=0)
    montant_actuel: float | None = Field(None, ge=0)
    priorite: int | None = Field(None, ge=1)


class SavingsGoalResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    libelle: str
    montant_cible: float
    montant_actuel: float
    priorite: int
    montant_restant: float
    est_atteint: bool
    created_at: datetime
    updated_at: datetime


class RepartitionAutoRequest(BaseModel):
    epargne_disponible: float = Field(..., ge=0)
    methode: Literal["cascade", "proportionnelle"] = "cascade"
