"""Tests de GET /v1/savings/plan (plan d'épargne + projection premium)."""

from sqlalchemy import select

from app.db.models import SubscriptionTier, User

CREDS = {"email": "leo@example.com", "password": "motdepasse123"}

ONBOARDING_PAYLOAD = {
    "nb_personnes": 1,
    "nb_enfants": 0,
    "objectif": "aucun",
    "revenus": [{"type": "fixe", "libelle": "Salaire net", "montant": 2500.0}],
    "charges_fixes": [{"libelle": "Loyer", "montant": 700.0}],
}


def _auth_headers(client) -> dict:
    token = client.post("/v1/auth/register", json=CREDS).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _auth_headers_apres_onboarding(client) -> dict:
    headers = _auth_headers(client)
    client.post("/v1/onboarding", json=ONBOARDING_PAYLOAD, headers=headers)
    return headers


def _passer_en_premium(db_session, email: str) -> None:
    user = db_session.scalar(select(User).where(User.email == email))
    user.subscription_tier = SubscriptionTier.PREMIUM.value
    db_session.commit()


def _creer_objectif(client, headers, **champs) -> None:
    client.post("/v1/savings/goals", json=champs, headers=headers)


def test_plan_sans_profil_renvoie_404(client):
    headers = _auth_headers(client)  # pas d'onboarding
    _creer_objectif(client, headers, libelle="X", montant_cible=1000, horizon_mois=12)
    assert client.get("/v1/savings/plan", headers=headers).status_code == 404


def test_horizon_mois_persiste_dans_le_crud(client):
    headers = _auth_headers_apres_onboarding(client)
    r = client.post(
        "/v1/savings/goals",
        json={"libelle": "Voyage", "montant_cible": 3000, "horizon_mois": 18},
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["horizon_mois"] == 18


def test_plan_gratuit_repartit_sans_champs_premium(client):
    headers = _auth_headers_apres_onboarding(client)
    _creer_objectif(client, headers, libelle="Urgence", montant_cible=3000, priorite=1, horizon_mois=24)

    r = client.get("/v1/savings/plan", headers=headers)
    assert r.status_code == 200
    body = r.json()

    assert body["premium"] is False
    assert body["capacite_epargne_mensuelle"] >= 0
    obj = body["objectifs"][0]
    assert obj["horizon_mois"] == 24
    assert "mensualite_attribuee" in obj
    # Champs premium non calculés pour un compte gratuit.
    assert obj["rendement_net_annuel_requis"] is None
    assert obj["bruts_par_enveloppe"] == []


def test_plan_premium_rendement_positif_et_nets(client, db_session):
    headers = _auth_headers_apres_onboarding(client)
    _passer_en_premium(db_session, CREDS["email"])
    # A (prioritaire) absorbe toute la capacité ; B ne reçoit rien et doit donc
    # compter sur un rendement (PV proche de la cible) -> rendement fini positif.
    _creer_objectif(client, headers, libelle="Prioritaire", montant_cible=1_000_000_000, priorite=1, horizon_mois=12)
    _creer_objectif(client, headers, libelle="Retraite", montant_cible=10000, montant_actuel=9500, priorite=2, horizon_mois=24)

    body = client.get("/v1/savings/plan", headers=headers).json()
    assert body["premium"] is True
    assert body["note_rendement_brut"]

    retraite = next(o for o in body["objectifs"] if o["libelle"] == "Retraite")
    assert retraite["mensualite_attribuee"] == 0.0
    assert retraite["rendement_net_annuel_requis"] is not None
    assert retraite["rendement_net_annuel_requis"] > 0.0
    assert 1 <= retraite["risque_note"] <= 5
    assert len(retraite["bruts_par_enveloppe"]) == 4
    assert retraite["realisable"]


def test_plan_premium_objectif_hors_de_portee(client, db_session):
    headers = _auth_headers_apres_onboarding(client)
    _passer_en_premium(db_session, CREDS["email"])
    _creer_objectif(client, headers, libelle="Villa", montant_cible=100000, priorite=1, horizon_mois=12)

    body = client.get("/v1/savings/plan", headers=headers).json()
    villa = body["objectifs"][0]
    assert villa["rendement_net_annuel_requis"] is None
    assert "hors de portée" in villa["realisable"]
