"""Logique de gestion des abonnements : lecture du statut, traitement des webhooks.

Conçu volontairement agnostique du fournisseur (RevenueCat/Stripe/autre) : le contrat
d'entrée (WebhookEvent) est un événement générique. Faire le lien avec le format réel
d'un fournisseur (vérification de signature, mapping de son schéma d'événements vers
WebhookEvent) est un adaptateur à écrire au moment de l'intégration réelle — non fait
ici en l'absence de compte fournisseur actif.

Limitation connue (documentée, pas un oubli) : l'expiration d'un abonnement n'est
prise en compte que sur réception explicite d'un événement EXPIRATION. Il n'y a pas
de tâche planifiée qui dégraderait automatiquement un utilisateur dont `date_fin` est
dépassée mais dont aucun événement n'a été reçu — à ajouter si le produit dépend d'un
fournisseur qui n'envoie pas cet événement de façon fiable.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Subscription, SubscriptionStatus, SubscriptionTier, User
from app.billing.schemas import BillingStatusResponse, WebhookEvent

_EVENT_TO_STATUS = {
    "INITIAL_PURCHASE": SubscriptionStatus.ACTIVE,
    "RENEWAL": SubscriptionStatus.ACTIVE,
    "CANCELLATION": SubscriptionStatus.CANCELLED,
    "EXPIRATION": SubscriptionStatus.EXPIRED,
}


def get_billing_status(db: Session, user: User) -> BillingStatusResponse:
    derniere = db.scalar(
        select(Subscription)
        .where(Subscription.user_id == user.id)
        .order_by(Subscription.updated_at.desc())
        .limit(1)
    )
    return BillingStatusResponse(
        tier=user.subscription_tier,
        statut=derniere.statut if derniere else None,
        provider=derniere.provider if derniere else None,
        date_debut=derniere.date_debut if derniere else None,
        date_fin=derniere.date_fin if derniere else None,
    )


def process_webhook_event(db: Session, event: WebhookEvent) -> None:
    user = db.get(User, event.app_user_id)
    if user is None:
        # Un événement pour un utilisateur inconnu n'est pas une erreur côté fournisseur :
        # on l'ignore silencieusement plutôt que de faire échouer le webhook (le
        # fournisseur réessaierait indéfiniment un événement qui ne se résoudra jamais).
        return

    nouveau_statut = _EVENT_TO_STATUS[event.event_type]
    nouveau_tier = (
        SubscriptionTier.PREMIUM if nouveau_statut == SubscriptionStatus.ACTIVE else SubscriptionTier.FREE
    )

    subscription = Subscription(
        user_id=user.id,
        tier=nouveau_tier.value,
        statut=nouveau_statut.value,
        provider=event.provider,
        provider_ref=event.provider_ref,
        date_fin=event.expires_at,
    )
    db.add(subscription)

    user.subscription_tier = nouveau_tier.value
    db.commit()
