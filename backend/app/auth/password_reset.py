"""Réinitialisation de mot de passe : génération d'un jeton à usage unique et expirant,
puis validation lors du changement de mot de passe.

Sécurité : on ne révèle jamais si un email existe (message générique), le jeton n'est
stocké que haché, et il est à usage unique. En développement, le jeton est renvoyé dans
la réponse pour tester sans e-mail ; en production, jamais.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.email import envoyer_email_reinitialisation
from app.auth.schemas import ForgotPasswordResponse
from app.auth.security import hash_password
from app.core.config import settings
from app.db.models import PasswordResetToken, User

_DUREE_VALIDITE = timedelta(hours=1)
_MESSAGE_GENERIQUE = (
    "Si un compte existe pour cet email, un lien de réinitialisation vient d'être envoyé."
)


def _hash_token(token: str) -> str:
    """Le jeton a une forte entropie : un simple SHA-256 suffit (pas besoin de bcrypt)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def demander_reinitialisation(db: Session, email: str) -> ForgotPasswordResponse:
    user = db.scalar(select(User).where(User.email == email))
    jeton_clair = None

    if user is not None:
        # Invalider les éventuels jetons encore actifs de cet utilisateur.
        anciens = db.scalars(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used.is_(False),
            )
        ).all()
        for ancien in anciens:
            ancien.used = True

        jeton_clair = secrets.token_urlsafe(32)
        db.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=_hash_token(jeton_clair),
                expires_at=datetime.now(timezone.utc) + _DUREE_VALIDITE,
            )
        )
        db.commit()
        envoyer_email_reinitialisation(user.email, jeton_clair)

    # En production : message générique, jamais le jeton ni l'existence du compte.
    if settings.environment == "production":
        return ForgotPasswordResponse(message=_MESSAGE_GENERIQUE)
    return ForgotPasswordResponse(message=_MESSAGE_GENERIQUE, reset_token=jeton_clair)


def reinitialiser_mot_de_passe(db: Session, token: str, nouveau_mot_de_passe: str) -> None:
    entree = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == _hash_token(token))
    )

    invalide = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Lien de réinitialisation invalide ou expiré.",
    )
    if entree is None or entree.used:
        raise invalide

    # SQLite renvoie des datetimes naïfs ; on normalise en UTC avant comparaison.
    expiration = entree.expires_at
    if expiration.tzinfo is None:
        expiration = expiration.replace(tzinfo=timezone.utc)
    if expiration <= datetime.now(timezone.utc):
        raise invalide

    user = db.get(User, entree.user_id)
    if user is None:
        raise invalide

    user.password_hash = hash_password(nouveau_mot_de_passe)
    entree.used = True
    db.commit()
