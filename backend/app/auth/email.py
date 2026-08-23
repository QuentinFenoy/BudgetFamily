"""Envoi d'e-mails transactionnels via SMTP.

Volontairement agnostique : on parle SMTP standard (bibliothèque Python), pas de SDK
propriétaire. Il suffit de renseigner SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASSWORD /
SMTP_FROM pour n'importe quel fournisseur (Brevo, Mailtrap, SMTP2GO, Amazon SES…).

Si aucun SMTP n'est configuré, l'envoi est simplement journalisé — et en développement
l'endpoint /auth/forgot-password renvoie le jeton dans la réponse pour rester testable.
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger("budgetfamily.email")


def envoyer_email_reinitialisation(email: str, token: str) -> None:
    """Envoie le code de réinitialisation par e-mail (si un SMTP est configuré)."""
    if not settings.emails_actives:
        logger.info("SMTP non configuré : e-mail de réinitialisation non envoyé pour %s.", email)
        return

    message = EmailMessage()
    message["Subject"] = "Réinitialisation de votre mot de passe BudgetFamily"
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from}>"
    message["To"] = email
    message.set_content(
        "Bonjour,\n\n"
        "Vous avez demandé à réinitialiser votre mot de passe BudgetFamily.\n\n"
        "Votre code de réinitialisation :\n\n"
        f"    {token}\n\n"
        "Saisissez-le dans l'application (« Mot de passe oublié ? » puis « J'ai un code »). "
        "Ce code est valable 1 heure et à usage unique.\n\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez cet e-mail : "
        "votre mot de passe restera inchangé.\n"
    )

    try:
        _envoyer(message)
        logger.info("E-mail de réinitialisation envoyé à %s.", email)
    except Exception:  # noqa: BLE001 — ne jamais faire échouer la requête sur un souci SMTP
        logger.exception("Échec de l'envoi de l'e-mail de réinitialisation à %s.", email)


def _envoyer(message: EmailMessage) -> None:
    """Transport SMTP : SSL implicite sur le port 465, STARTTLS sinon."""
    contexte = ssl.create_default_context()
    if settings.smtp_port == 465:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=contexte) as serveur:
            serveur.login(settings.smtp_user, settings.smtp_password)
            serveur.send_message(message)
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as serveur:
            serveur.starttls(context=contexte)
            serveur.login(settings.smtp_user, settings.smtp_password)
            serveur.send_message(message)
