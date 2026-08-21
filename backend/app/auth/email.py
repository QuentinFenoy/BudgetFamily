"""Envoi d'e-mails transactionnels.

Point d'ancrage volontairement minimal : l'envoi réel (SendGrid, Mailgun, SMTP…) sera
branché ici lors de la mise en place de l'hébergement d'e-mails. En attendant, on
journalise seulement — et l'endpoint /auth/forgot-password renvoie le jeton en
développement pour permettre les tests de bout en bout sans e-mail.
"""

import logging

logger = logging.getLogger("budgetfamily.email")


def envoyer_email_reinitialisation(email: str, token: str) -> None:
    """Envoie (à terme) le lien de réinitialisation. Aujourd'hui : journalisation seule."""
    logger.info("Demande de réinitialisation de mot de passe pour %s (jeton généré).", email)
    # TODO: intégrer un fournisseur d'e-mail et envoyer le lien contenant `token`.
