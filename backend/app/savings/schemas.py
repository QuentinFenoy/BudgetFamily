"""Schémas Pydantic pour l'endpoint de répartition de l'épargne entre objectifs."""

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
