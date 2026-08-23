"""Tests de l'envoi d'e-mail de réinitialisation (sans réseau réel)."""

from email.message import EmailMessage

import app.auth.email as email_mod
from app.core.config import settings


def _configurer_smtp(monkeypatch, port: int = 587) -> None:
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", port)
    monkeypatch.setattr(settings, "smtp_user", "utilisateur")
    monkeypatch.setattr(settings, "smtp_password", "motdepasse")
    monkeypatch.setattr(settings, "smtp_from", "no-reply@example.com")


def test_forgot_password_n_expose_pas_le_jeton_si_email_actif(client, monkeypatch):
    _configurer_smtp(monkeypatch)
    envois = []
    monkeypatch.setattr(email_mod, "_envoyer", lambda message: envois.append(message))

    client.post(
        "/v1/auth/register",
        json={"email": "mailuser@example.com", "password": "motdepasse123"},
    )
    r = client.post("/v1/auth/forgot-password", json={"email": "mailuser@example.com"})

    assert r.status_code == 200
    assert r.json()["reset_token"] is None  # délivré par e-mail, pas dans la réponse
    assert len(envois) == 1
    assert envois[0]["To"] == "mailuser@example.com"


def test_envoi_smtp_utilise_starttls_sur_587(monkeypatch):
    _configurer_smtp(monkeypatch, port=587)

    trace = {"starttls": False, "login": None, "envoye": False}

    class FauxSMTP:
        def __init__(self, host, port):
            trace["hostport"] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self, context=None):
            trace["starttls"] = True

        def login(self, user, password):
            trace["login"] = (user, password)

        def send_message(self, message):
            trace["envoye"] = True

    monkeypatch.setattr(email_mod.smtplib, "SMTP", FauxSMTP)

    message = EmailMessage()
    message["To"] = "x@example.com"
    message.set_content("test")
    email_mod._envoyer(message)

    assert trace["starttls"] is True
    assert trace["login"] == ("utilisateur", "motdepasse")
    assert trace["envoye"] is True


def test_envoi_desactive_si_smtp_non_configure(monkeypatch):
    # Aucun SMTP configuré : ne tente aucun envoi (et ne lève pas).
    appels = []
    monkeypatch.setattr(email_mod, "_envoyer", lambda message: appels.append(message))
    email_mod.envoyer_email_reinitialisation("x@example.com", "jeton")
    assert appels == []
