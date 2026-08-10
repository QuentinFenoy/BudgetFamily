"""Schémas Pydantic de GET /v1/dashboard."""

from pydantic import BaseModel


class CategorieBudgetStatus(BaseModel):
    libelle: str
    montant_recommande: float
    montant_realise: float
    ecart: float  # montant_recommande - montant_realise (positif = marge restante)


class DashboardResponse(BaseModel):
    periode: str  # format "YYYY-MM"
    disponible: float
    categories: list[CategorieBudgetStatus]
    epargne_potentielle: float
    epargne_reference_taux: float
    epargne_reference_montant: float
