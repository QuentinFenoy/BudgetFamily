"""Tests de GET /v1/portfolio/allocation (fonctionnalité payante, classes génériques)."""

import json

from sqlalchemy import select

from app.db.models import SubscriptionTier, User
from app.portfolio.asset_classes import ASSET_CLASSES

CREDS = {"email": "emilie@example.com", "password": "motdepasse123"}

# Profil renseigné (risque/âge/horizon/objectif servent à l'allocation).
ONBOARDING_PAYLOAD = {
    "nb_personnes": 2,
    "nb_enfants": 0,
    "age": 35,
    "objectif": "retraite_long_terme",
    "tolerance_risque": 4,
    "horizon_annees": 25,
    "revenus": [{"type": "fixe", "libelle": "Salaire net", "montant": 3000.0}],
    "charges_fixes": [{"libelle": "Loyer", "montant": 900.0}],
}


def _auth_headers_apres_onboarding(client, creds=CREDS, payload=ONBOARDING_PAYLOAD) -> dict:
    token = client.post("/v1/auth/register", json=creds).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/v1/onboarding", json=payload, headers=headers)
    return headers


def _passer_en_premium(db_session, email: str) -> None:
    user = db_session.scalar(select(User).where(User.email == email))
    user.subscription_tier = SubscriptionTier.PREMIUM.value
    db_session.commit()


def test_allocation_refuse_pour_utilisateur_gratuit(client):
    headers = _auth_headers_apres_onboarding(client)
    r = client.get("/v1/portfolio/allocation", headers=headers)
    assert r.status_code == 403


def test_allocation_sans_auth_renvoie_401(client):
    assert client.get("/v1/portfolio/allocation").status_code == 401


def test_allocation_premium_sans_profil_renvoie_404(client, db_session):
    # Inscription sans onboarding, puis passage premium.
    client.post("/v1/auth/register", json=CREDS)
    _passer_en_premium(db_session, CREDS["email"])
    token = client.post("/v1/auth/login", json=CREDS).json()["access_token"]
    r = client.get("/v1/portfolio/allocation", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404


def test_allocation_premium_ok(client, db_session):
    headers = _auth_headers_apres_onboarding(client)
    _passer_en_premium(db_session, CREDS["email"])

    r = client.get("/v1/portfolio/allocation", headers=headers)
    assert r.status_code == 200
    body = r.json()

    assert body["methode"] == "hrp"
    assert body["profil_risque"] == 4
    # Croissance + défensif couvrent tout le portefeuille.
    assert abs(body["part_croissance"] + body["part_defensive"] - 1.0) < 1e-6
    # Les parts somment à ~1.
    assert abs(sum(l["part"] for l in body["allocation"]) - 1.0) < 0.01
    # Une ligne par classe d'actifs générique.
    assert len(body["allocation"]) == len(ASSET_CLASSES)
    # Avertissement réglementaire présent et explicite.
    assert "conseil en investissement" in body["avertissement"].lower()


def test_allocation_ne_contient_aucun_ticker(client, db_session):
    """Réglementaire (section 8) : aucun instrument nominatif ne doit fuiter."""
    headers = _auth_headers_apres_onboarding(client)
    _passer_en_premium(db_session, CREDS["email"])

    r = client.get("/v1/portfolio/allocation", headers=headers)
    texte = json.dumps(r.json(), ensure_ascii=False)

    for ac in ASSET_CLASSES:
        for ticker in ac.proxys:
            assert ticker not in texte, f"Le ticker {ticker} ne doit jamais apparaître dans la réponse"


def test_allocation_avec_montant(client, db_session):
    headers = _auth_headers_apres_onboarding(client)
    _passer_en_premium(db_session, CREDS["email"])

    r = client.get("/v1/portfolio/allocation?montant=10000", headers=headers)
    assert r.status_code == 200
    body = r.json()
    montants = [l["montant"] for l in body["allocation"]]
    assert all(m is not None for m in montants)
    assert abs(sum(montants) - 10000.0) < 5.0  # tolérance d'arrondi


def test_allocation_methode_invalide_renvoie_422(client, db_session):
    headers = _auth_headers_apres_onboarding(client)
    _passer_en_premium(db_session, CREDS["email"])
    r = client.get("/v1/portfolio/allocation?methode=xyz", headers=headers)
    assert r.status_code == 422


def test_profil_prudent_alloue_moins_de_croissance_que_profil_dynamique(client, db_session):
    # Utilisateur prudent : risque faible, âgé, horizon court, objectif matelas.
    prudent_creds = {"email": "prudent@example.com", "password": "motdepasse123"}
    prudent_payload = {
        **ONBOARDING_PAYLOAD,
        "age": 63,
        "tolerance_risque": 1,
        "horizon_annees": 2,
        "objectif": "matelas_securite",
    }
    h_prudent = _auth_headers_apres_onboarding(client, prudent_creds, prudent_payload)
    _passer_en_premium(db_session, prudent_creds["email"])
    part_prudent = client.get("/v1/portfolio/allocation", headers=h_prudent).json()["part_croissance"]

    # Utilisateur dynamique : profil de base (risque 4, jeune, horizon long).
    h_dyn = _auth_headers_apres_onboarding(client)
    _passer_en_premium(db_session, CREDS["email"])
    part_dyn = client.get("/v1/portfolio/allocation", headers=h_dyn).json()["part_croissance"]

    assert part_prudent < part_dyn
