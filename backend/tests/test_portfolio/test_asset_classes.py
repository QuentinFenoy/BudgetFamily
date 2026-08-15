"""Tests de GET /v1/portfolio/asset-classes (catalogue pédagogique)."""

import json

from app.portfolio.asset_classes import ASSET_CLASSES

CREDS = {"email": "emilie@example.com", "password": "motdepasse123"}


def _auth_headers(client) -> dict:
    token = client.post("/v1/auth/register", json=CREDS).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_asset_classes_sans_auth_renvoie_401(client):
    assert client.get("/v1/portfolio/asset-classes").status_code == 401


def test_asset_classes_accessible_sans_premium(client):
    # Un compte gratuit, sans profil, doit pouvoir consulter les définitions.
    r = client.get("/v1/portfolio/asset-classes", headers=_auth_headers(client))
    assert r.status_code == 200
    body = r.json()

    assert len(body) == len(ASSET_CLASSES)
    for fiche in body:
        assert fiche["definition"].strip()
        assert len(fiche["exemples"]) >= 1
        assert fiche["categorie"] in ("Croissance", "Défensif")


def test_asset_classes_ne_contient_aucun_ticker(client):
    r = client.get("/v1/portfolio/asset-classes", headers=_auth_headers(client))
    texte = json.dumps(r.json(), ensure_ascii=False)
    for ac in ASSET_CLASSES:
        for ticker in ac.proxys:
            assert ticker not in texte, f"Le ticker {ticker} ne doit pas apparaître"
