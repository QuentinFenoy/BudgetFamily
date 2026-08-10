"""Tests de l'endpoint POST /v1/expenses."""

CREDS = {"email": "leo@example.com", "password": "motdepasse123"}

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


def test_ajout_depense_categorie_existante(client):
    headers = _auth_headers_apres_onboarding(client)

    r = client.post(
        "/v1/expenses",
        json={"categorie": "alimentation", "montant": 45.5, "date_operation": "2026-08-05"},
        headers=headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["categorie"] == "alimentation"
    assert body["montant"] == 45.5
    assert body["date_operation"] == "2026-08-05"


def test_ajout_depense_sans_date_utilise_aujourdhui(client):
    headers = _auth_headers_apres_onboarding(client)

    r = client.post("/v1/expenses", json={"categorie": "loisirs", "montant": 20}, headers=headers)
    assert r.status_code == 201
    assert r.json()["date_operation"] is not None


def test_ajout_depense_categorie_inconnue_renvoie_404(client):
    headers = _auth_headers_apres_onboarding(client)

    r = client.post(
        "/v1/expenses", json={"categorie": "categorie_qui_nexiste_pas", "montant": 10}, headers=headers
    )
    assert r.status_code == 404


def test_ajout_depense_sans_authentification_renvoie_401(client):
    r = client.post("/v1/expenses", json={"categorie": "alimentation", "montant": 10})
    assert r.status_code == 401


def test_ajout_depense_montant_negatif_renvoie_422(client):
    headers = _auth_headers_apres_onboarding(client)

    r = client.post("/v1/expenses", json={"categorie": "alimentation", "montant": -5}, headers=headers)
    assert r.status_code == 422
