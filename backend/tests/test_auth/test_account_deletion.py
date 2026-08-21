"""Tests de la suppression de compte (DELETE /v1/auth/me)."""

CREDS = {"email": "delete@example.com", "password": "motdepasse123"}

ONBOARDING_PAYLOAD = {
    "nb_personnes": 1,
    "nb_enfants": 0,
    "objectif": "aucun",
    "revenus": [{"type": "fixe", "libelle": "Salaire", "montant": 2000.0}],
    "charges_fixes": [{"libelle": "Loyer", "montant": 600.0}],
}


def _auth_headers(client) -> dict:
    token = client.post("/v1/auth/register", json=CREDS).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_suppression_sans_auth_renvoie_401(client):
    assert client.delete("/v1/auth/me").status_code == 401


def test_suppression_efface_le_compte_et_ses_donnees(client):
    headers = _auth_headers(client)
    client.post("/v1/onboarding", json=ONBOARDING_PAYLOAD, headers=headers)
    client.post(
        "/v1/savings/goals",
        json={"libelle": "Voyage", "montant_cible": 3000, "horizon_mois": 12},
        headers=headers,
    )

    r = client.delete("/v1/auth/me", headers=headers)
    assert r.status_code == 204

    # Le jeton ne donne plus accès (utilisateur supprimé).
    assert client.get("/v1/auth/me", headers=headers).status_code == 401
    # L'email est libéré : on peut recréer un compte.
    assert client.post("/v1/auth/register", json=CREDS).status_code == 201
