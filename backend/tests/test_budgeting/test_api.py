from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_calculate_budget_celibataire_haut_revenu():
    payload = {
        "revenus_total": 10000,
        "charges_fixes_total": 0,
        "nb_personnes": 1,
        "nb_enfants": 0,
        "objectif": "retraite_long_terme",
    }
    response = client.post("/v1/budgeting/calculate", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["disponible"] == 10000
    assert data["epargne_potentielle"] > 5000
    assert data["montants_categories"]["alimentation"] == 330.0


def test_calculate_budget_validation_erreur_si_revenus_negatifs():
    payload = {"revenus_total": -100, "charges_fixes_total": 0, "nb_personnes": 1}
    response = client.post("/v1/budgeting/calculate", json=payload)
    assert response.status_code == 422
