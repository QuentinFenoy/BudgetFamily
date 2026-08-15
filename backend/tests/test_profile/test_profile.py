"""Tests de GET /v1/profile et PUT /v1/profile."""

from sqlalchemy import select

from app.db.models import ExpenseEntry, Income, User, VariableExpenseCategory

CREDS = {"email": "emilie@example.com", "password": "motdepasse123"}

ONBOARDING_PAYLOAD = {
    "nb_personnes": 2,
    "nb_enfants": 0,
    "age": 35,
    "objectif": "matelas_securite",
    "tolerance_risque": 3,
    "horizon_annees": 10,
    "revenus": [{"type": "fixe", "libelle": "Salaire", "montant": 3000.0}],
    "charges_fixes": [{"libelle": "Loyer", "montant": 900.0}],
}


def _auth_headers(client) -> dict:
    token = client.post("/v1/auth/register", json=CREDS).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _auth_headers_apres_onboarding(client) -> dict:
    headers = _auth_headers(client)
    client.post("/v1/onboarding", json=ONBOARDING_PAYLOAD, headers=headers)
    return headers


def test_get_profile_sans_auth_renvoie_401(client):
    assert client.get("/v1/profile").status_code == 401


def test_get_profile_sans_profil_renvoie_404(client):
    headers = _auth_headers(client)
    assert client.get("/v1/profile", headers=headers).status_code == 404


def test_get_profile_retourne_le_detail(client):
    headers = _auth_headers_apres_onboarding(client)
    r = client.get("/v1/profile", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["nb_personnes"] == 2
    assert body["objectif"] == "matelas_securite"
    assert body["tolerance_risque"] == 3
    assert len(body["revenus"]) == 1
    assert body["revenus"][0]["libelle"] == "Salaire"
    assert len(body["charges_fixes"]) == 1


def test_update_profile_sans_profil_renvoie_404(client):
    headers = _auth_headers(client)
    r = client.put("/v1/profile", json=ONBOARDING_PAYLOAD, headers=headers)
    assert r.status_code == 404


def test_update_profile_incoherent_renvoie_422(client):
    headers = _auth_headers_apres_onboarding(client)
    payload = {**ONBOARDING_PAYLOAD, "nb_personnes": 2, "nb_enfants": 3}
    r = client.put("/v1/profile", json=payload, headers=headers)
    assert r.status_code == 422


def test_update_profile_recalcule_et_persiste(client):
    headers = _auth_headers_apres_onboarding(client)

    payload = {
        **ONBOARDING_PAYLOAD,
        "revenus": [
            {"type": "fixe", "libelle": "Salaire", "montant": 3500.0},
            {"type": "variable", "libelle": "Primes", "montant": 0.0},
        ],
        "objectif": "retraite_long_terme",
    }
    r = client.put("/v1/profile", json=payload, headers=headers)
    assert r.status_code == 200
    # disponible = 3500 - 900 = 2600
    assert r.json()["budget"]["disponible"] == 2600.0

    # La lecture reflète la mise à jour.
    detail = client.get("/v1/profile", headers=headers).json()
    assert detail["objectif"] == "retraite_long_terme"
    assert len(detail["revenus"]) == 2


def test_update_profile_preserve_les_depenses(client, db_session):
    headers = _auth_headers_apres_onboarding(client)

    # Une dépense saisie sur une catégorie existante.
    assert (
        client.post(
            "/v1/expenses",
            json={"categorie": "alimentation", "montant": 50.0},
            headers=headers,
        ).status_code
        == 201
    )

    user = db_session.scalar(select(User).where(User.email == CREDS["email"]))
    cat_avant = db_session.scalar(
        select(VariableExpenseCategory).where(
            VariableExpenseCategory.user_id == user.id,
            VariableExpenseCategory.libelle == "alimentation",
        )
    )
    assert db_session.scalar(select(ExpenseEntry).where(ExpenseEntry.category_id == cat_avant.id)) is not None

    # Mise à jour du profil.
    r = client.put("/v1/profile", json={**ONBOARDING_PAYLOAD, "nb_personnes": 3}, headers=headers)
    assert r.status_code == 200

    # La catégorie alimentation a gardé le même id -> la dépense est toujours là.
    cat_apres = db_session.scalar(
        select(VariableExpenseCategory).where(
            VariableExpenseCategory.user_id == user.id,
            VariableExpenseCategory.libelle == "alimentation",
        )
    )
    assert cat_apres.id == cat_avant.id
    entries = db_session.scalars(
        select(ExpenseEntry).where(ExpenseEntry.category_id == cat_apres.id)
    ).all()
    assert len(entries) == 1
    assert entries[0].montant == 50.0

    # Le nombre de revenus reflète bien le remplacement (payload = 1 revenu).
    revenus = db_session.scalars(select(Income).where(Income.user_id == user.id)).all()
    assert len(revenus) == 1
