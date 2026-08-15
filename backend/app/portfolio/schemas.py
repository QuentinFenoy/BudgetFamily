"""Schémas Pydantic de l'allocation de portefeuille.

Contrat public : uniquement des classes d'actifs génériques, jamais d'instrument
nominatif (cf. doc d'architecture, section 8). Champs d'avertissement obligatoires.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class LigneAllocationResponse(BaseModel):
    classe: str = Field(..., description="Nom de la classe d'actifs générique")
    categorie: str = Field(..., description="Croissance ou Défensif")
    part: float = Field(..., description="Poids dans le portefeuille, entre 0 et 1")
    montant: float | None = Field(None, description="Montant en euros si un capital a été fourni")


class PortfolioAllocationResponse(BaseModel):
    profil_risque: int | None
    age: int | None
    horizon_annees: int | None
    objectif: str
    methode: str = Field(..., description="Méthode d'allocation intra-classe (hrp | erc)")
    goal_id: int | None = Field(None, description="Objectif d'épargne associé, si fourni")

    part_croissance: float
    part_defensive: float
    allocation: list[LigneAllocationResponse]

    rendement_annuel_espere: float = Field(..., description="Hypothèse long terme, non garantie")
    volatilite_annuelle_estimee: float
    ratio_sharpe_estime: float

    source_donnees: str
    hypotheses: str
    avertissement: str


class AllocationSimulationSummary(BaseModel):
    """Ligne d'historique — sans le détail par classe, pour une liste compacte."""

    model_config = {"from_attributes": True}

    id: int
    methode: str
    goal_id: int | None
    montant: float | None
    part_croissance: float
    part_defensive: float
    rendement_annuel_espere: float
    volatilite_annuelle_estimee: float
    ratio_sharpe_estime: float
    source_donnees: str
    created_at: datetime


class AllocationSimulationDetail(AllocationSimulationSummary):
    """Simulation complète, avec le détail par classe d'actifs."""

    allocation: list[LigneAllocationResponse]


class AssetClassInfoResponse(BaseModel):
    """Fiche pédagogique d'une classe d'actifs générique (définition + exemples)."""

    cle: str
    nom: str
    categorie: str  # "Croissance" | "Défensif"
    definition: str
    exemples: list[str]
