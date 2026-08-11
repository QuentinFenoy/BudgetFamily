"""Tests du lien entre AllocationSimulation et SavingsGoal (goal_id)."""

from sqlalchemy import select

from app.db.models import SubscriptionTier, User

CREDS = {"email": "priya@example.com", "password": "motdepasse123"}

ONBOARDING_PAYLOAD = {
    "nb_personnes": 1,
    "nb_enfants": 0,
    "age": 35,
    "objectif": "retraite_long_terme",
    "tolerance_risque": 4,
    "horizon_annees": 20,
    "revenus": [{"type": "fixe", "libelle": "Salaire net", "montant": 3500.0}],
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


def test_allocation_avec_goal_id_valide_est_liee_a_lobjectif(client, db_session):
    headers = _auth_headers_premium(client, db_session)
    goal_id = client.post(
        "/v1/savings/goals",
        json={"libelle": "Apport immobilier", "montant_cible": 50000},
        headers=headers,
    ).json()["id"]

    r = client.get(f"/v1/portfolio/allocation?montant=10000&goal_id={goal_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["goal_id"] == goal_id

    historique = client.get("/v1/portfolio/simulations", headers=headers).json()
    assert historique[0]["goal_id"] == goal_id


def test_allocation_avec_goal_id_dun_autre_utilisateur_renvoie_404(client, db_session):
    headers_a = _auth_headers_premium(client, db_session)
    goal_id = client.post(
        "/v1/savings/goals", json={"libelle": "Privé", "montant_cible": 1000}, headers=headers_a
    ).json()["id"]

    creds_b = {"email": "quentin.b@example.com", "password": "motdepasse123"}
    token_b = client.post("/v1/auth/register", json=creds_b).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    client.post("/v1/onboarding", json=ONBOARDING_PAYLOAD, headers=headers_b)
    user_b = db_session.scalar(select(User).where(User.email == creds_b["email"]))
    user_b.subscription_tier = SubscriptionTier.PREMIUM.value
    db_session.commit()

    r = client.get(f"/v1/portfolio/allocation?goal_id={goal_id}", headers=headers_b)
    assert r.status_code == 404


def test_allocation_sans_goal_id_a_goal_id_nul_dans_lhistorique(client, db_session):
    headers = _auth_headers_premium(client, db_session)
    r = client.get("/v1/portfolio/allocation", headers=headers)
    assert r.json()["goal_id"] is None

    historique = client.get("/v1/portfolio/simulations", headers=headers).json()
    assert historique[0]["goal_id"] is None
