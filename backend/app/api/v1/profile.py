"""Endpoints de lecture et de mise à jour du profil."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.db.session import get_db
from app.onboarding.schemas import OnboardingRequest, OnboardingResponse
from app.profile.schemas import ProfileDetailResponse
from app.profile.service import get_profile_detail, update_profile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileDetailResponse)
def read_profile(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ProfileDetailResponse:
    """Renvoie le profil de l'utilisateur connecté (foyer, revenus, charges)."""
    return get_profile_detail(db, current_user)


@router.put("", response_model=OnboardingResponse)
def replace_profile(
    payload: OnboardingRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> OnboardingResponse:
    """Remplace le profil existant, recalcule le budget et met à jour les montants
    recommandés par catégorie (les dépenses déjà saisies sont conservées)."""
    return update_profile(db, current_user, payload)
