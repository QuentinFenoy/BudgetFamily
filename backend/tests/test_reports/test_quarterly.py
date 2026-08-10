"""Tests de GET /v1/reports/quarterly (fonctionnalité payante)."""

from sqlalchemy import select

from app.db.models import SubscriptionTier, User

CREDS = {"email": "yara@example.com", "password": "motdepasse123"}

ONBOARDING_PAYLOAD = {
    "nb_personnes": 1,
    "nb_enfants": 0,
    "objectif": "aucun",
    "revenus": [{"type": "fixe", "libelle": "Salaire net", "montant": 2500.0}],
    "charges_fixes": [{"libelle": "Loyer", "montant": 700.0}],
}


def _auth_headers_apres_onboarding(client) -> dict:
    token = client.post("/v1/auth/register", json=CREDS).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/v1/onboarding", json=ONBOARDING_PAYLOAD, headers=headers)
    return headers


def _passer_en_premium(db_session, email: str) -> None:
    user = db_session.scalar(select(User).where(User.email == email))
    user.subscription_tier = SubscriptionTier.PREMIUM.value
    db_session.commit()


def test_bilan_trimestriel_refuse_pour_utilisateur_gratuit(client):
    headers = _auth_headers_apres_onboarding(client)

    r = client.get("/v1/reports/quarterly", headers=headers)
    assert r.status_code == 403


def test_bilan_trimestriel_autorise_pour_utilisateur_premium(client, db_session):
    headers = _auth_headers_apres_onboarding(client)
    _passer_en_premium(db_session, CREDS["email"])

    r = client.get("/v1/reports/quarterly?mois=2026-08", headers=headers)
    assert r.status_code == 200
    body = r.json()

    assert body["mois"] == ["2026-06", "2026-07", "2026-08"]
    assert len(body["bilans"]) == 3
    assert len(body["tendances"]) == 3
    # sans dépenses, chaque mois dégage tout le disponible (1800) en épargne
    assert body["epargne_totale_trimestre"] == 1800.0 * 3
    assert body["moyenne_totale_realisee"] == 0.0
    assert body["ecart_mois_courant_vs_moyenne"] == 0.0


def test_bilan_trimestriel_calcule_bien_la_moyenne_avec_depenses(client, db_session):
    headers = _auth_headers_apres_onboarding(client)
    _passer_en_premium(db_session, CREDS["email"])

    # dépenses uniquement sur le dernier mois du trimestre
    client.post(
        "/v1/expenses",
        json={"categorie": "alimentation", "montant": 300, "date_operation": "2026-08-05"},
        headers=headers,
    )

    r = client.get("/v1/reports/quarterly?mois=2026-08", headers=headers)
    body = r.json()

    # juin: 0, juillet: 0, août: 300 -> moyenne = 100
    assert body["moyenne_totale_realisee"] == 100.0
    assert body["ecart_mois_courant_vs_moyenne"] == 200.0  # 300 - 100


def test_bilan_trimestriel_sans_authentification_renvoie_401(client):
    r = client.get("/v1/reports/quarterly")
    assert r.status_code == 401


def test_bilan_trimestriel_mois_mal_formate_renvoie_422(client, db_session):
    headers = _auth_headers_apres_onboarding(client)
    _passer_en_premium(db_session, CREDS["email"])

    r = client.get("/v1/reports/quarterly?mois=aout-2026", headers=headers)
    assert r.status_code == 422
