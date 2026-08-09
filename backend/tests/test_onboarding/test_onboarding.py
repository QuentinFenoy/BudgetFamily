"""Tests de l'endpoint POST /v1/onboarding."""

from sqlalchemy import select

from app.db.models import FixedExpense, Income, Profile, User, VariableExpenseCategory

CREDS = {"email": "emilie@example.com", "password": "motdepasse123"}

PAYLOAD = {
    "nb_personnes": 4,
    "nb_enfants": 2,
    "situation_familiale": "couple",
    "age": 38,
    "objectif": "matelas_securite",
    "tolerance_risque": 3,
    "horizon_annees": 5,
    "matelas_securite_atteint": False,
    "revenus": [
        {"type": "fixe", "libelle": "Salaire net", "montant": 3200.0},
        {"type": "variable", "libelle": "Primes (moyenne)", "montant": 300.0},
    ],
    "charges_fixes": [
        {"libelle": "Loyer", "montant": 1100.0, "categorie": "logement"},
        {"libelle": "Assurances", "montant": 150.0},
    ],
}


def _register_and_token(client) -> str:
    return client.post("/v1/auth/register", json=CREDS).json()["access_token"]


def _auth_headers(client) -> dict:
    return {"Authorization": f"Bearer {_register_and_token(client)}"}


def test_onboarding_cree_profil_et_retourne_budget(client):
    r = client.post("/v1/onboarding", json=PAYLOAD, headers=_auth_headers(client))
    assert r.status_code == 201
    body = r.json()

    assert body["profile"]["nb_personnes"] == 4
    assert body["profile"]["nb_enfants"] == 2
    assert body["profile"]["objectif"] == "matelas_securite"

    budget = body["budget"]
    # Disponible = revenus (3200 + 300) - charges (1100 + 150) = 2250
    assert budget["disponible"] == 2250.0
    assert budget["disponible_par_hab"] == 2250.0 / 4
    assert set(budget["montants_categories"]) >= {"alimentation", "transport", "enfants", "loisirs"}
    assert isinstance(budget["epargne_potentielle"], float)


def test_onboarding_persiste_les_donnees(client, db_session):
    client.post("/v1/onboarding", json=PAYLOAD, headers=_auth_headers(client))

    user = db_session.scalar(select(User).where(User.email == CREDS["email"]))
    assert user is not None

    profils = db_session.scalars(select(Profile).where(Profile.user_id == user.id)).all()
    assert len(profils) == 1

    revenus = db_session.scalars(select(Income).where(Income.user_id == user.id)).all()
    assert len(revenus) == 2

    charges = db_session.scalars(select(FixedExpense).where(FixedExpense.user_id == user.id)).all()
    assert len(charges) == 2

    categories = db_session.scalars(
        select(VariableExpenseCategory).where(VariableExpenseCategory.user_id == user.id)
    ).all()
    # Une catégorie recommandée par catégorie renvoyée par le moteur.
    assert len(categories) >= 4
    assert all(c.montant_recommande >= 0 for c in categories)


def test_onboarding_sans_auth_renvoie_401(client):
    r = client.post("/v1/onboarding", json=PAYLOAD)
    assert r.status_code == 401


def test_onboarding_deux_fois_renvoie_409(client):
    headers = _auth_headers(client)
    assert client.post("/v1/onboarding", json=PAYLOAD, headers=headers).status_code == 201
    r = client.post("/v1/onboarding", json=PAYLOAD, headers=headers)
    assert r.status_code == 409


def test_onboarding_nb_enfants_incoherent_renvoie_422(client):
    payload = {**PAYLOAD, "nb_personnes": 2, "nb_enfants": 3}
    r = client.post("/v1/onboarding", json=payload, headers=_auth_headers(client))
    assert r.status_code == 422


def test_onboarding_sans_revenus_renvoie_422(client):
    payload = {**PAYLOAD, "revenus": []}
    r = client.post("/v1/onboarding", json=payload, headers=_auth_headers(client))
    assert r.status_code == 422
