"""Tests du flux de réinitialisation de mot de passe."""

CREDS = {"email": "reset@example.com", "password": "ancienmotdepasse"}


def _register(client) -> None:
    client.post("/v1/auth/register", json=CREDS)


def test_forgot_password_renvoie_le_jeton_en_dev(client):
    _register(client)
    r = client.post("/v1/auth/forgot-password", json={"email": CREDS["email"]})
    assert r.status_code == 200
    assert r.json()["reset_token"]  # présent en développement


def test_forgot_password_email_inconnu_reste_generique(client):
    r = client.post("/v1/auth/forgot-password", json={"email": "inconnu@example.com"})
    assert r.status_code == 200
    # Pas de jeton pour un email inexistant, mais même message (ne révèle rien).
    assert r.json()["reset_token"] is None


def test_reset_password_change_le_mot_de_passe(client):
    _register(client)
    token = client.post(
        "/v1/auth/forgot-password", json={"email": CREDS["email"]}
    ).json()["reset_token"]

    r = client.post(
        "/v1/auth/reset-password",
        json={"token": token, "new_password": "nouveaumotdepasse"},
    )
    assert r.status_code == 204

    # L'ancien mot de passe ne marche plus, le nouveau oui.
    assert client.post("/v1/auth/login", json=CREDS).status_code == 401
    assert (
        client.post(
            "/v1/auth/login",
            json={"email": CREDS["email"], "password": "nouveaumotdepasse"},
        ).status_code
        == 200
    )


def test_reset_password_jeton_invalide_renvoie_400(client):
    r = client.post(
        "/v1/auth/reset-password",
        json={"token": "jeton-bidon", "new_password": "nouveaumotdepasse"},
    )
    assert r.status_code == 400


def test_reset_password_jeton_a_usage_unique(client):
    _register(client)
    token = client.post(
        "/v1/auth/forgot-password", json={"email": CREDS["email"]}
    ).json()["reset_token"]

    ok = client.post(
        "/v1/auth/reset-password", json={"token": token, "new_password": "motdepasse1"}
    )
    assert ok.status_code == 204
    # Réutiliser le même jeton échoue.
    rejeu = client.post(
        "/v1/auth/reset-password", json={"token": token, "new_password": "motdepasse2"}
    )
    assert rejeu.status_code == 400
