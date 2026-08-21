"""Moteur de projection d'un objectif d'épargne (calcul pur, sans dépendance DB).

À partir du montant cible, du déjà-épargné, de la mensualité allouée et de l'échéance,
on résout le **rendement brut annuel** nécessaire pour atteindre l'objectif dans les
temps, puis on le traduit en niveau de risque (via la frontière rendement/volatilité de
l'allocateur) et en message de faisabilité. Un utilitaire indique aussi le rendement net
indicatif selon l'enveloppe fiscale.

Hypothèses : cotisations mensuelles en fin de période (annuité ordinaire), rendement
constant. C'est une projection indicative, pas une garantie.
"""

from __future__ import annotations

from dataclasses import dataclass

# Rendement annuel plafond exploré : au-delà, l'objectif est jugé hors de portée.
_RENDEMENT_ANNUEL_MAX = 3.0  # 300 %/an


def _valeur_future(pv: float, pmt: float, taux_mensuel: float, n: int) -> float:
    """Valeur future d'un capital initial pv + n versements mensuels pmt au taux mensuel."""
    if abs(taux_mensuel) < 1e-12:
        return pv + pmt * n
    croissance = (1 + taux_mensuel) ** n
    return pv * croissance + pmt * (croissance - 1) / taux_mensuel


def rendement_brut_annuel_requis(
    montant_cible: float,
    montant_actuel: float,
    mensualite: float,
    horizon_mois: int | None,
) -> float | None:
    """Rendement brut ANNUEL nécessaire pour atteindre montant_cible en horizon_mois.

    Renvoie :
    - 0.0 si l'objectif est atteignable par la seule épargne (aucun rendement requis) ;
    - le rendement annuel (ex. 0.055 = 5,5 %/an) sinon ;
    - None si l'objectif reste hors de portée même à un rendement irréaliste.
    """
    if horizon_mois is None or horizon_mois <= 0:
        return None
    if montant_actuel >= montant_cible:
        return 0.0

    pv = max(montant_actuel, 0.0)
    pmt = max(mensualite, 0.0)
    n = horizon_mois

    # Atteignable sans aucun rendement ?
    if _valeur_future(pv, pmt, 0.0, n) >= montant_cible:
        return 0.0

    taux_mensuel_max = (1 + _RENDEMENT_ANNUEL_MAX) ** (1 / 12) - 1
    if _valeur_future(pv, pmt, taux_mensuel_max, n) < montant_cible:
        return None  # hors de portée même à 300 %/an

    # Recherche par dichotomie du taux mensuel (fonction croissante du taux).
    bas, haut = 0.0, taux_mensuel_max
    for _ in range(200):
        milieu = (bas + haut) / 2
        if _valeur_future(pv, pmt, milieu, n) < montant_cible:
            bas = milieu
        else:
            haut = milieu
    taux_mensuel = (bas + haut) / 2
    return round((1 + taux_mensuel) ** 12 - 1, 4)


def message_faisabilite(rendement_annuel: float | None) -> str:
    """Phrase qualifiant la difficulté du projet selon le rendement requis."""
    if rendement_annuel is None:
        return (
            "Objectif hors de portée avec l'épargne allouée sur cette durée : "
            "augmentez la mensualité, allongez l'échéance ou revoyez le montant."
        )
    r = rendement_annuel
    if r <= 0.0:
        return "Objectif atteignable par la seule épargne, sans aucun rendement à aller chercher."
    if r <= 0.02:
        return "Très facilement réalisable : un placement très prudent suffit."
    if r <= 0.04:
        return "Réalisable avec un placement prudent."
    if r <= 0.07:
        return "Réaliste avec un portefeuille équilibré."
    if r <= 0.10:
        return "Ambitieux : suppose une part d'actions importante et de la constance dans la durée."
    if r <= 0.15:
        return "Difficile : le rendement requis implique un risque élevé, sans garantie de l'atteindre."
    return (
        "Très difficile : le rendement requis dépasse ce qu'un portefeuille diversifié "
        "vise raisonnablement. Mieux vaut ajuster montant, durée ou mensualité."
    )


# Fiscalité indicative des gains selon l'enveloppe (France). Simplification : le taux
# est appliqué au rendement, pour donner un ordre de grandeur du net — la fiscalité
# réelle porte sur les gains à la sortie et dépend de la situation de chacun.
_ENVELOPPES = [
    ("Livret A / LDDS", 0.0),
    ("PEA (après 5 ans)", 0.172),
    ("Assurance-vie (après 8 ans)", 0.247),
    ("Compte-titres (flat tax)", 0.30),
]

NOTE_RENDEMENT_NET = (
    "Rendements nets indicatifs : le taux brut requis est diminué de la fiscalité des "
    "gains propre à chaque enveloppe. Estimation d'ordre de grandeur, la fiscalité réelle "
    "s'applique aux gains à la sortie et dépend de votre situation."
)


@dataclass(frozen=True)
class RendementNetEnveloppe:
    enveloppe: str
    taux_imposition: float
    rendement_net_indicatif: float


def nets_par_enveloppe(rendement_brut_annuel: float) -> list[RendementNetEnveloppe]:
    return [
        RendementNetEnveloppe(
            enveloppe=nom,
            taux_imposition=taux,
            rendement_net_indicatif=round(rendement_brut_annuel * (1 - taux), 4),
        )
        for nom, taux in _ENVELOPPES
    ]


@dataclass(frozen=True)
class RisqueEstime:
    note_sur_5: int
    volatilite_annuelle: float
    au_dela_frontiere: bool  # True si le rendement requis dépasse le profil le plus risqué


def risque_pour_rendement(
    points_frontiere: list[tuple[int, float, float]],
    rendement_requis: float,
) -> RisqueEstime:
    """Traduit un rendement requis en (note de risque 1-5, volatilité) par interpolation
    sur la frontière rendement/volatilité fournie.

    points_frontiere : liste de (note 1..5, rendement_espere, volatilite), une par
    niveau de tolérance, telle que produite par l'allocateur.
    """
    pts = sorted(points_frontiere, key=lambda p: p[1])  # tri par rendement croissant

    if rendement_requis <= pts[0][1]:
        return RisqueEstime(pts[0][0], round(pts[0][2], 4), False)
    if rendement_requis >= pts[-1][1]:
        return RisqueEstime(pts[-1][0], round(pts[-1][2], 4), True)

    for k in range(len(pts) - 1):
        r0, r1 = pts[k][1], pts[k + 1][1]
        if r0 <= rendement_requis <= r1:
            frac = (rendement_requis - r0) / (r1 - r0) if r1 > r0 else 0.0
            note = round(pts[k][0] + frac * (pts[k + 1][0] - pts[k][0]))
            vol = pts[k][2] + frac * (pts[k + 1][2] - pts[k][2])
            return RisqueEstime(int(note), round(vol, 4), False)

    return RisqueEstime(pts[-1][0], round(pts[-1][2], 4), True)
