"""Logique d'ajout d'une dépense sur une catégorie de l'utilisateur connecté."""

from datetime import date as date_type, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ExpenseEntry, User, VariableExpenseCategory
from app.expenses.schemas import ExpenseEntryRequest, ExpenseEntryResponse


def add_expense_entry(db: Session, user: User, payload: ExpenseEntryRequest) -> ExpenseEntryResponse:
    categorie = db.scalar(
        select(VariableExpenseCategory).where(
            VariableExpenseCategory.user_id == user.id,
            VariableExpenseCategory.libelle == payload.categorie,
        )
    )
    if categorie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Catégorie {payload.categorie!r} introuvable pour cet utilisateur "
                "(complétez d'abord l'onboarding, qui crée les catégories)."
            ),
        )

    entry = ExpenseEntry(
        category_id=categorie.id,
        montant=payload.montant,
        date_operation=payload.date_operation or datetime.now(timezone.utc).date(),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return ExpenseEntryResponse(
        id=entry.id,
        montant=entry.montant,
        date_operation=entry.date_operation,
        categorie=categorie.libelle,
    )
