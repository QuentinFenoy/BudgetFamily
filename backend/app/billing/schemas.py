"""Schémas Pydantic du module billing (statut d'abonnement, événements webhook)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class BillingStatusResponse(BaseModel):
    tier: str  # "free" | "premium" — reflète toujours User.subscription_tier
    statut: str | None = None  # dernier statut connu (active/cancelled/expired), None si jamais abonné
    provider: str | None = None
    date_debut: datetime | None = None
    date_fin: datetime | None = None


class WebhookEvent(BaseModel):
    """Événement générique reçu du fournisseur de paiement.

    `app_user_id` suit la convention RevenueCat : l'identifiant applicatif (notre
    propre User.id) transmis au fournisseur au moment de l'achat, qui nous permet de
    relier l'événement à l'utilisateur sans dépendre d'un identifiant fournisseur.
    """

    app_user_id: int
    event_type: Literal["INITIAL_PURCHASE", "RENEWAL", "CANCELLATION", "EXPIRATION"]
    provider: Literal["revenuecat", "stripe", "manual"] = "manual"
    provider_ref: str | None = Field(None, max_length=120)
    expires_at: datetime | None = None


class WebhookAck(BaseModel):
    received: bool = True
