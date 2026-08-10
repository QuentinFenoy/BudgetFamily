"""Tests de l'historique des simulations d'allocation (AllocationSimulation)."""

from sqlalchemy import select

from app.db.models import AllocationSimulation, SubscriptionTier, User

CREDS = {"email": "hugo@example.com", "password": "motdepasse123"}

ONBOARDING_PAYLOAD = {
    "nb_personnes": 1,
    "nb_enfants": 0,
    "age": 40,
    "objectif": "retraite_long_terme",
    "tolerance_risque": 3,
    "horizon_annees": 15,
    "revenus": [{"type": "fixe", "libelle": "Salaire net", "montant": 3000.0}],
    "charges_fixes": [{"libelle": "Loyer", "montant": 900.0}],
}


def _auth_headers_premium(client, db_session) -> dict:
    token = client.post("/v1/auth/register", json=CREDS).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/v1/onboarding", json=ONBOARDING_PAYLOAD, headers=headers)
    user = db_session.scalar(select(User).where(User.email == CREDS["email"]))
    user.subscription_tier = SubscriptionTier.PREMIUM.value
    db_session.commit()
    return headers


def test_allocation_enregistre_une_simulation_par_defaut(client, db_session):
    headers = _auth_headers_premium(client, db_session)

    client.get("/v1/portfolio/allocation?montant=5000", headers=headers)

    user = db_session.scalar(select(User).where(User.email == CREDS["email"]))
    simulations = db_session.scalars(
        select(AllocationSimulation).where(AllocationSimulation.user_id == user.id)
    ).all()
    assert len(simulations) == 1
    assert simulations[0].montant == 5000.0
    assert simulations[0].methode == "hrp"
    assert len(simulations[0].allocation_json) > 0


def test_allocation_save_false_nenregistre_rien(client, db_session):
    headers = _auth_headers_premium(client, db_session)

    client.get("/v1/portfolio/allocation?save=false", headers=headers)

    user = db_session.scalar(select(User).where(User.email == CREDS["email"]))
    simulations = db_session.scalars(
        select(AllocationSimulation).where(AllocationSimulation.user_id == user.id)
    ).all()
    assert len(simulations) == 0


def test_liste_simulations_ordre_plus_recent_dabord(client, db_session):
    headers = _auth_headers_premium(client, db_session)

    client.get("/v1/portfolio/allocation?methode=hrp", headers=headers)
    client.get("/v1/portfolio/allocation?methode=erc", headers=headers)

    r = client.get("/v1/portfolio/simulations", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    assert body[0]["methode"] == "erc"  # la plus récente en premier
    assert body[1]["methode"] == "hrp"
    # le résumé ne contient pas le détail par classe
    assert "allocation" not in body[0]


def test_liste_simulations_refuse_pour_utilisateur_gratuit(client):
    token = client.post("/v1/auth/register", json=CREDS).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/v1/portfolio/simulations", headers=headers)
    assert r.status_code == 403


def test_liste_simulations_sans_authentification_renvoie_401(client):
    r = client.get("/v1/portfolio/simulations")
    assert r.status_code == 401


def test_detail_simulation_contient_lallocation_complete(client, db_session):
    headers = _auth_headers_premium(client, db_session)

    client.get("/v1/portfolio/allocation?montant=8000", headers=headers)
    simulation_id = client.get("/v1/portfolio/simulations", headers=headers).json()[0]["id"]

    r = client.get(f"/v1/portfolio/simulations/{simulation_id}", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["montant"] == 8000.0
    assert len(body["allocation"]) > 0
    assert abs(sum(l["part"] for l in body["allocation"]) - 1.0) < 0.01


def test_detail_simulation_inexistante_renvoie_404(client, db_session):
    headers = _auth_headers_premium(client, db_session)
    r = client.get("/v1/portfolio/simulations/999999", headers=headers)
    assert r.status_code == 404


def test_detail_simulation_dun_autre_utilisateur_renvoie_404(client, db_session):
    headers_a = _auth_headers_premium(client, db_session)
    client.get("/v1/portfolio/allocation", headers=headers_a)
    simulation_id = client.get("/v1/portfolio/simulations", headers=headers_a).json()[0]["id"]

    creds_b = {"email": "iris@example.com", "password": "motdepasse123"}
    token_b = client.post("/v1/auth/register", json=creds_b).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    user_b = db_session.scalar(select(User).where(User.email == creds_b["email"]))
    user_b.subscription_tier = SubscriptionTier.PREMIUM.value
    db_session.commit()

    r = client.get(f"/v1/portfolio/simulations/{simulation_id}", headers=headers_b)
    assert r.status_code == 404


def test_detail_simulation_ne_contient_aucun_ticker(client, db_session):
    """Réglementaire (section 8) : l'historique stocké et renvoyé ne doit jamais
    contenir d'instrument nominatif, même en base."""
    import json

    from app.portfolio.asset_classes import ASSET_CLASSES

    headers = _auth_headers_premium(client, db_session)
    client.get("/v1/portfolio/allocation", headers=headers)
    simulation_id = client.get("/v1/portfolio/simulations", headers=headers).json()[0]["id"]

    r = client.get(f"/v1/portfolio/simulations/{simulation_id}", headers=headers)
    texte = json.dumps(r.json(), ensure_ascii=False)

    for ac in ASSET_CLASSES:
        for ticker in ac.proxys:
            assert ticker not in texte
