"""Tests de GET /v1/reports/monthly."""

CREDS = {"email": "sami@example.com", "password": "motdepasse123"}

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


def test_bilan_mensuel_sans_depenses(client):
    headers = _auth_headers_apres_onboarding(client)

    r = client.get("/v1/reports/monthly", headers=headers)
    assert r.status_code == 200
    body = r.json()

    assert body["disponible"] == 1800.0  # 2500 - 700
    assert body["total_realise"] == 0.0
    # rien dépensé -> épargne réellement dégagée = tout le disponible
    assert body["epargne_realisee_estimee"] == 1800.0


def test_bilan_mensuel_avec_depenses(client):
    headers = _auth_headers_apres_onboarding(client)

    client.post(
        "/v1/expenses",
        json={"categorie": "alimentation", "montant": 200, "date_operation": "2026-08-05"},
        headers=headers,
    )
    client.post(
        "/v1/expenses",
        json={"categorie": "loisirs", "montant": 50, "date_operation": "2026-08-10"},
        headers=headers,
    )

    r = client.get("/v1/reports/monthly?mois=2026-08", headers=headers)
    assert r.status_code == 200
    body = r.json()

    assert body["periode"] == "2026-08"
    assert body["total_realise"] == 250.0
    assert body["epargne_realisee_estimee"] == 1800.0 - 250.0
    assert body["ecart_epargne_vs_reference"] == round(
        body["epargne_realisee_estimee"] - body["epargne_reference_montant"], 2
    )


def test_bilan_mensuel_sans_onboarding_renvoie_404(client):
    token = client.post("/v1/auth/register", json=CREDS).json()["access_token"]
    r = client.get("/v1/reports/monthly", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404


def test_bilan_mensuel_sans_authentification_renvoie_401(client):
    r = client.get("/v1/reports/monthly")
    assert r.status_code == 401
