"""Endpoint d'ajout d'une dépense."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.db.session import get_db
from app.expenses.schemas import ExpenseEntryRequest, ExpenseEntryResponse
from app.expenses.service import add_expense_entry

router = APIRouter(prefix="/expenses", tags=["expenses"])


@router.post("", response_model=ExpenseEntryResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseEntryRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ExpenseEntryResponse:
    """Ajoute une dépense sur une catégorie existante de l'utilisateur connecté."""
    return add_expense_entry(db, current_user, payload)
