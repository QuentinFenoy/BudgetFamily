from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_savings_repartition_endpoint_cascade():
    payload = {
        "objectifs": [
            {"id": "urgence", "nom": "Fonds urgence", "montant_cible": 3000, "montant_actuel": 2800, "priorite": 1},
            {"id": "voyage", "nom": "Voyage", "montant_cible": 2000, "montant_actuel": 0, "priorite": 2},
        ],
        "epargne_disponible": 500,
        "methode": "cascade",
    }
    response = client.post("/v1/savings/repartition", json=payload)
    assert response.status_code == 200

    data = response.json()
    allocations = {a["objectif_id"]: a for a in data["allocations"]}
    assert allocations["urgence"]["montant_alloue_ce_mois"] == 200.0
    assert allocations["voyage"]["montant_alloue_ce_mois"] == 300.0
