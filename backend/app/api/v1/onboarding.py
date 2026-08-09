"""Endpoint d'onboarding : crée le profil du foyer et renvoie le premier budget."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.db.session import get_db
from app.onboarding.schemas import OnboardingRequest, OnboardingResponse
from app.onboarding.service import run_onboarding

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("", response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
def onboarding(
    payload: OnboardingRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OnboardingResponse:
    """Persiste profil + revenus + charges de l'utilisateur connecté, puis renvoie
    la répartition budgétaire recommandée et le potentiel d'épargne."""
    return run_onboarding(db, current_user, payload)
