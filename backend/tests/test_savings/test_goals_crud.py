"""Tests du CRUD des objectifs d'épargne persistés (SavingsGoal)."""

CREDS = {"email": "leon@example.com", "password": "motdepasse123"}


def _auth_headers(client) -> dict:
    token = client.post("/v1/auth/register", json=CREDS).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_creation_objectif(client):
    headers = _auth_headers(client)

    r = client.post(
        "/v1/savings/goals",
        json={"libelle": "Fonds d'urgence", "montant_cible": 3000, "montant_actuel": 500, "priorite": 1},
        headers=headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["libelle"] == "Fonds d'urgence"
    assert body["montant_restant"] == 2500.0
    assert body["est_atteint"] is False


def test_creation_objectif_sans_authentification_renvoie_401(client):
    r = client.post("/v1/savings/goals", json={"libelle": "Test", "montant_cible": 100})
    assert r.status_code == 401


def test_liste_objectifs_triee_par_priorite(client):
    headers = _auth_headers(client)
    client.post("/v1/savings/goals", json={"libelle": "B", "montant_cible": 100, "priorite": 2}, headers=headers)
    client.post("/v1/savings/goals", json={"libelle": "A", "montant_cible": 100, "priorite": 1}, headers=headers)

    r = client.get("/v1/savings/goals", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert [g["libelle"] for g in body] == ["A", "B"]


def test_recuperer_un_objectif(client):
    headers = _auth_headers(client)
    goal_id = client.post(
        "/v1/savings/goals", json={"libelle": "Voiture", "montant_cible": 8000}, headers=headers
    ).json()["id"]

    r = client.get(f"/v1/savings/goals/{goal_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["libelle"] == "Voiture"


def test_recuperer_objectif_inexistant_renvoie_404(client):
    headers = _auth_headers(client)
    r = client.get("/v1/savings/goals/999999", headers=headers)
    assert r.status_code == 404


def test_modifier_partiellement_un_objectif(client):
    headers = _auth_headers(client)
    goal_id = client.post(
        "/v1/savings/goals", json={"libelle": "Voyage", "montant_cible": 2000, "montant_actuel": 0}, headers=headers
    ).json()["id"]

    r = client.patch(f"/v1/savings/goals/{goal_id}", json={"montant_actuel": 500}, headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["montant_actuel"] == 500.0
    assert body["libelle"] == "Voyage"  # inchangé, non fourni dans le PATCH
    assert body["montant_restant"] == 1500.0


def test_modifier_montant_actuel_au_dela_de_la_cible_renvoie_422(client):
    headers = _auth_headers(client)
    goal_id = client.post(
        "/v1/savings/goals", json={"libelle": "Test", "montant_cible": 1000}, headers=headers
    ).json()["id"]

    r = client.patch(f"/v1/savings/goals/{goal_id}", json={"montant_actuel": 1500}, headers=headers)
    assert r.status_code == 422


def test_objectif_atteint_quand_montant_actuel_egale_la_cible(client):
    headers = _auth_headers(client)
    goal_id = client.post(
        "/v1/savings/goals", json={"libelle": "Test", "montant_cible": 1000}, headers=headers
    ).json()["id"]

    r = client.patch(f"/v1/savings/goals/{goal_id}", json={"montant_actuel": 1000}, headers=headers)
    assert r.json()["est_atteint"] is True
    assert r.json()["montant_restant"] == 0.0


def test_suppression_objectif(client):
    headers = _auth_headers(client)
    goal_id = client.post(
        "/v1/savings/goals", json={"libelle": "À supprimer", "montant_cible": 100}, headers=headers
    ).json()["id"]

    r = client.delete(f"/v1/savings/goals/{goal_id}", headers=headers)
    assert r.status_code == 204

    r = client.get(f"/v1/savings/goals/{goal_id}", headers=headers)
    assert r.status_code == 404


def test_isolation_entre_utilisateurs(client):
    headers_a = _auth_headers(client)
    goal_id = client.post(
        "/v1/savings/goals", json={"libelle": "Privé", "montant_cible": 100}, headers=headers_a
    ).json()["id"]

    token_b = client.post(
        "/v1/auth/register", json={"email": "mia@example.com", "password": "motdepasse123"}
    ).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    assert client.get(f"/v1/savings/goals/{goal_id}", headers=headers_b).status_code == 404
    assert client.patch(f"/v1/savings/goals/{goal_id}", json={"montant_actuel": 50}, headers=headers_b).status_code == 404
    assert client.delete(f"/v1/savings/goals/{goal_id}", headers=headers_b).status_code == 404
