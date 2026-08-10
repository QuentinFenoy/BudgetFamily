"""Endpoints billing : statut d'abonnement (authentifié) et webhook (secret partagé)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.billing.schemas import BillingStatusResponse, WebhookAck, WebhookEvent
from app.billing.service import get_billing_status, process_webhook_event
from app.core.config import settings
from app.db.session import get_db

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/status", response_model=BillingStatusResponse)
def billing_status(
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> BillingStatusResponse:
    """Palier actuel de l'utilisateur connecté, et dernier événement d'abonnement connu."""
    return get_billing_status(db, current_user)


@router.post("/webhook", response_model=WebhookAck)
def billing_webhook(
    event: WebhookEvent,
    db: Annotated[Session, Depends(get_db)],
    x_webhook_secret: Annotated[str | None, Header()] = None,
) -> WebhookAck:
    """Reçoit les événements d'abonnement du fournisseur de paiement.

    Vérification par secret partagé (en-tête X-Webhook-Secret) : suffisant pour le
    développement, mais À REMPLACER en production par la vérification de signature
    propre au fournisseur réel (Stripe-Signature, ou le mécanisme d'auth de RevenueCat)
    avant tout déploiement.
    """
    if x_webhook_secret != settings.billing_webhook_secret:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Secret webhook invalide")

    process_webhook_event(db, event)
    return WebhookAck()
