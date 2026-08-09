"""Tests des endpoints d'authentification et des primitives de sécurité."""

from app.auth.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

VALID = {"email": "emilie@example.com", "password": "motdepasse123"}


# --- Primitives de sécurité (unitaires, sans DB) ---


def test_hash_verify_password_roundtrip():
    h = hash_password("motdepasse123")
    assert h != "motdepasse123"
    assert verify_password("motdepasse123", h) is True
    assert verify_password("mauvais", h) is False


def test_jwt_roundtrip():
    token = create_access_token(subject="42")
    assert decode_access_token(token) == "42"


def test_decode_rejette_jeton_invalide():
    assert decode_access_token("pas.un.jwt") is None


# --- Endpoints (avec DB en mémoire) ---


def test_register_retourne_un_jeton(client):
    r = client.post("/v1/auth/register", json=VALID)
    assert r.status_code == 201
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_register_email_deja_pris_renvoie_409(client):
    assert client.post("/v1/auth/register", json=VALID).status_code == 201
    r = client.post("/v1/auth/register", json=VALID)
    assert r.status_code == 409


def test_register_mot_de_passe_trop_court_renvoie_422(client):
    r = client.post("/v1/auth/register", json={"email": "x@example.com", "password": "court"})
    assert r.status_code == 422


def test_login_ok_apres_register(client):
    client.post("/v1/auth/register", json=VALID)
    r = client.post("/v1/auth/login", json=VALID)
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_login_mauvais_mot_de_passe_renvoie_401(client):
    client.post("/v1/auth/register", json=VALID)
    r = client.post("/v1/auth/login", json={"email": VALID["email"], "password": "faux"})
    assert r.status_code == 401


def test_login_email_inconnu_renvoie_401(client):
    r = client.post("/v1/auth/login", json=VALID)
    assert r.status_code == 401


def test_me_avec_jeton_valide(client):
    token = client.post("/v1/auth/register", json=VALID).json()["access_token"]
    r = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == VALID["email"]
    assert body["subscription_tier"] == "free"
    assert "id" in body and "created_at" in body


def test_me_sans_jeton_renvoie_401(client):
    # HTTPBearer sans en-tête Authorization -> 401 (non authentifié).
    assert client.get("/v1/auth/me").status_code == 401


def test_me_jeton_invalide_renvoie_401(client):
    r = client.get("/v1/auth/me", headers={"Authorization": "Bearer pas.un.jwt"})
    assert r.status_code == 401
