"""Endpoints d'authentification : inscription, connexion, profil courant."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.auth.password_reset import demander_reinitialisation, reinitialiser_mot_de_passe
from app.auth.schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.auth.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DbSession) -> TokenResponse:
    """Crée un compte et retourne directement un jeton d'accès (auto-connexion)."""
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte existe déjà avec cet email",
        )
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(subject=str(user.id)))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DbSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )
    return TokenResponse(access_token=create_access_token(subject=str(user.id)))


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: CurrentUser) -> User:
    return current_user


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: DbSession) -> ForgotPasswordResponse:
    """Demande de réinitialisation. Répond toujours par un message générique (ne révèle
    pas si l'email existe). En développement, renvoie le jeton pour tester sans e-mail."""
    return demander_reinitialisation(db, payload.email)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(payload: ResetPasswordRequest, db: DbSession) -> None:
    """Définit un nouveau mot de passe à partir d'un jeton valide (usage unique)."""
    reinitialiser_mot_de_passe(db, payload.token, payload.new_password)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_current_user(current_user: CurrentUser, db: DbSession) -> None:
    """Supprime définitivement le compte et toutes les données associées (RGPD).
    La cascade ORM efface profil, revenus, charges, catégories, dépenses, objectifs,
    simulations et abonnements."""
    db.delete(current_user)
    db.commit()
