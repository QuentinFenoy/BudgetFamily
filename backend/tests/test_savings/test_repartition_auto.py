"""Tests de POST /v1/savings/repartition-auto (répartition sur objectifs persistés)."""

CREDS = {"email": "nadia@example.com", "password": "motdepasse123"}


def _auth_headers(client) -> dict:
    token = client.post("/v1/auth/register", json=CREDS).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_repartition_auto_sans_objectif_renvoie_404(client):
    headers = _auth_headers(client)
    r = client.post("/v1/savings/repartition-auto", json={"epargne_disponible": 500}, headers=headers)
    assert r.status_code == 404


def test_repartition_auto_utilise_les_objectifs_persistes(client):
    headers = _auth_headers(client)
    client.post(
        "/v1/savings/goals",
        json={"libelle": "Urgence", "montant_cible": 3000, "montant_actuel": 2800, "priorite": 1},
        headers=headers,
    )
    client.post(
        "/v1/savings/goals",
        json={"libelle": "Voyage", "montant_cible": 2000, "montant_actuel": 0, "priorite": 2},
        headers=headers,
    )

    r = client.post(
        "/v1/savings/repartition-auto",
        json={"epargne_disponible": 500, "methode": "cascade"},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()

    goals = client.get("/v1/savings/goals", headers=headers).json()
    urgence_id = str(next(g["id"] for g in goals if g["libelle"] == "Urgence"))
    voyage_id = str(next(g["id"] for g in goals if g["libelle"] == "Voyage"))

    allocations = {a["objectif_id"]: a["montant_alloue_ce_mois"] for a in body["allocations"]}
    assert allocations[urgence_id] == 200.0  # comble le besoin restant (3000-2800)
    assert allocations[voyage_id] == 300.0  # reçoit le reste


def test_repartition_auto_sans_authentification_renvoie_401(client):
    r = client.post("/v1/savings/repartition-auto", json={"epargne_disponible": 100})
    assert r.status_code == 401
