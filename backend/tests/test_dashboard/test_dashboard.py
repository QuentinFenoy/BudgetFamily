"""Tests de l'endpoint GET /v1/dashboard."""

CREDS = {"email": "nina@example.com", "password": "motdepasse123"}

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


def test_dashboard_sans_onboarding_renvoie_404(client):
    token = client.post("/v1/auth/register", json=CREDS).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/v1/dashboard", headers=headers)
    assert r.status_code == 404


def test_dashboard_sans_authentification_renvoie_401(client):
    r = client.get("/v1/dashboard")
    assert r.status_code == 401


def test_dashboard_apres_onboarding_montant_realise_a_zero(client):
    headers = _auth_headers_apres_onboarding(client)

    r = client.get("/v1/dashboard", headers=headers)
    assert r.status_code == 200
    body = r.json()

    assert body["disponible"] == 1800.0  # 2500 - 700
    alimentation = next(c for c in body["categories"] if c["libelle"] == "alimentation")
    assert alimentation["montant_realise"] == 0.0
    assert alimentation["ecart"] == alimentation["montant_recommande"]


def test_dashboard_reflete_les_depenses_du_mois(client):
    headers = _auth_headers_apres_onboarding(client)

    client.post(
        "/v1/expenses",
        json={"categorie": "alimentation", "montant": 40, "date_operation": "2026-08-03"},
        headers=headers,
    )
    client.post(
        "/v1/expenses",
        json={"categorie": "alimentation", "montant": 25, "date_operation": "2026-08-10"},
        headers=headers,
    )
    # dépense hors période demandée, ne doit pas être comptée dans le mois d'août
    client.post(
        "/v1/expenses",
        json={"categorie": "alimentation", "montant": 999, "date_operation": "2026-07-15"},
        headers=headers,
    )

    r = client.get("/v1/dashboard?mois=2026-08", headers=headers)
    assert r.status_code == 200
    body = r.json()

    assert body["periode"] == "2026-08"
    alimentation = next(c for c in body["categories"] if c["libelle"] == "alimentation")
    assert alimentation["montant_realise"] == 65.0  # 40 + 25, sans le 999 de juillet


def test_dashboard_mois_mal_formate_renvoie_422(client):
    headers = _auth_headers_apres_onboarding(client)

    r = client.get("/v1/dashboard?mois=aout-2026", headers=headers)
    assert r.status_code == 422
