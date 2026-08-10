"""Schémas Pydantic de POST /v1/expenses (ajout d'une dépense sur une catégorie)."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ExpenseEntryRequest(BaseModel):
    categorie: str = Field(..., min_length=1, max_length=60, description="Libellé de la catégorie (ex: alimentation)")
    montant: float = Field(..., gt=0)
    date_operation: date | None = Field(None, description="Défaut : aujourd'hui")


class ExpenseEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    montant: float
    date_operation: date
    categorie: str
