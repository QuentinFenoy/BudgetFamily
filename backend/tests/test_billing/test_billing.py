"""Tests des endpoints billing (statut + webhook)."""

from sqlalchemy import select

from app.core.config import settings
from app.db.models import User

CREDS = {"email": "omar@example.com", "password": "motdepasse123"}


def _register(client) -> dict:
    r = client.post("/v1/auth/register", json=CREDS)
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _user_id(client, headers) -> int:
    me = client.get("/v1/auth/me", headers=headers).json()
    return me["id"]


def test_statut_par_defaut_est_gratuit(client, db_session):
    headers = _register(client)
    user_id = _user_id(client, headers)

    r = client.get("/v1/billing/status", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["tier"] == "free"
    assert body["statut"] is None


def test_statut_sans_authentification_renvoie_401(client):
    r = client.get("/v1/billing/status")
    assert r.status_code == 401


def test_webhook_sans_bon_secret_renvoie_401(client, db_session):
    headers = _register(client)
    user_id = _user_id(client, headers)

    r = client.post(
        "/v1/billing/webhook",
        json={"app_user_id": user_id, "event_type": "INITIAL_PURCHASE", "provider": "revenuecat"},
        headers={"X-Webhook-Secret": "mauvais-secret"},
    )
    assert r.status_code == 401


def test_webhook_achat_initial_passe_utilisateur_en_premium(client, db_session):
    headers = _register(client)
    user_id = _user_id(client, headers)

    r = client.post(
        "/v1/billing/webhook",
        json={
            "app_user_id": user_id,
            "event_type": "INITIAL_PURCHASE",
            "provider": "revenuecat",
            "provider_ref": "sub_abc123",
            "expires_at": "2026-09-10T00:00:00Z",
        },
        headers={"X-Webhook-Secret": settings.billing_webhook_secret},
    )
    assert r.status_code == 200

    statut = client.get("/v1/billing/status", headers=headers).json()
    assert statut["tier"] == "premium"
    assert statut["statut"] == "active"
    assert statut["provider"] == "revenuecat"

    user = db_session.scalar(select(User).where(User.email == CREDS["email"]))
    assert user.subscription_tier == "premium"


def test_webhook_expiration_repasse_utilisateur_en_gratuit(client, db_session):
    headers = _register(client)
    user_id = _user_id(client, headers)

    client.post(
        "/v1/billing/webhook",
        json={"app_user_id": user_id, "event_type": "INITIAL_PURCHASE", "provider": "manual"},
        headers={"X-Webhook-Secret": settings.billing_webhook_secret},
    )
    client.post(
        "/v1/billing/webhook",
        json={"app_user_id": user_id, "event_type": "EXPIRATION", "provider": "manual"},
        headers={"X-Webhook-Secret": settings.billing_webhook_secret},
    )

    statut = client.get("/v1/billing/status", headers=headers).json()
    assert statut["tier"] == "free"
    assert statut["statut"] == "expired"


def test_webhook_utilisateur_inconnu_est_ignore_sans_erreur(client, db_session):
    r = client.post(
        "/v1/billing/webhook",
        json={"app_user_id": 999999, "event_type": "INITIAL_PURCHASE", "provider": "manual"},
        headers={"X-Webhook-Secret": settings.billing_webhook_secret},
    )
    assert r.status_code == 200


def test_webhook_puis_acces_bilan_trimestriel_debloque(client, db_session):
    """Test d'intégration : le webhook billing débloque bien la fonctionnalité payante
    déjà en place dans reports/ (plus besoin d'écrire en base à la main dans les tests)."""
    headers = _register(client)
    user_id = _user_id(client, headers)

    onboarding_payload = {
        "nb_personnes": 1,
        "nb_enfants": 0,
        "objectif": "aucun",
        "revenus": [{"type": "fixe", "libelle": "Salaire net", "montant": 2000.0}],
        "charges_fixes": [],
    }
    client.post("/v1/onboarding", json=onboarding_payload, headers=headers)

    # avant l'abonnement : accès refusé
    r = client.get("/v1/reports/quarterly", headers=headers)
    assert r.status_code == 403

    client.post(
        "/v1/billing/webhook",
        json={"app_user_id": user_id, "event_type": "INITIAL_PURCHASE", "provider": "manual"},
        headers={"X-Webhook-Secret": settings.billing_webhook_secret},
    )

    # après l'abonnement : accès autorisé
    r = client.get("/v1/reports/quarterly", headers=headers)
    assert r.status_code == 200
