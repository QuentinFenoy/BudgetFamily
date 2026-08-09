"""Moteur de répartition de l'épargne disponible entre plusieurs objectifs.

Ce module est volontairement découplé de app.budgeting : il prend en entrée un montant
d'épargne disponible (typiquement Épargne_potentielle calculée par le module budgeting),
sans dépendre directement de son moteur de calcul.
"""

import math

from .models import ObjectifEpargne, AllocationObjectif, ResultatRepartitionEpargne


def _mois_restants(objectif: ObjectifEpargne, montant_mensuel_alloue: float) -> float | None:
    if objectif.est_atteint:
        return 0.0
    if montant_mensuel_alloue <= 0:
        return None
    return math.ceil(objectif.montant_restant / montant_mensuel_alloue)


def repartir_epargne_cascade(
    objectifs: list[ObjectifEpargne], epargne_disponible: float
) -> ResultatRepartitionEpargne:
    """Méthode 'cascade' : remplit les objectifs par ordre de priorité (1 = le plus
    prioritaire d'abord), jusqu'à épuisement de l'épargne disponible du mois.
    """
    objectifs_tries = sorted(objectifs, key=lambda o: o.priorite)
    reste = round(epargne_disponible, 2)
    allocations = []

    for objectif in objectifs_tries:
        montant_alloue = round(max(min(reste, objectif.montant_restant), 0.0), 2)
        allocations.append(
            AllocationObjectif(
                objectif_id=objectif.id,
                montant_alloue_ce_mois=montant_alloue,
                mois_restants_estimes=_mois_restants(objectif, montant_alloue),
            )
        )
        reste = round(reste - montant_alloue, 2)

    return ResultatRepartitionEpargne(
        epargne_disponible=epargne_disponible,
        allocations=allocations,
        epargne_non_allouee=max(reste, 0.0),
    )


def repartir_epargne_proportionnelle(
    objectifs: list[ObjectifEpargne], epargne_disponible: float
) -> ResultatRepartitionEpargne:
    """Méthode 'proportionnelle' : répartit l'épargne disponible au prorata du montant
    restant de chaque objectif non encore atteint, sans jamais dépasser son besoin réel.

    Limitation connue : une seule passe de redistribution du surplus est effectuée. Dans
    de rares cas avec plusieurs objectifs proches simultanément de leur saturation, un
    petit reliquat peut rester non alloué (visible dans epargne_non_allouee) plutôt que
    d'être redistribué de façon parfaitement itérative — jugé suffisant pour le MVP.
    """
    objectifs_actifs = [o for o in objectifs if not o.est_atteint]

    if not objectifs_actifs:
        allocations = [
            AllocationObjectif(objectif_id=o.id, montant_alloue_ce_mois=0.0, mois_restants_estimes=0.0)
            for o in objectifs
        ]
        return ResultatRepartitionEpargne(
            epargne_disponible=epargne_disponible, allocations=allocations, epargne_non_allouee=epargne_disponible
        )

    total_restant = sum(o.montant_restant for o in objectifs_actifs)
    montants = {}
    for o in objectifs_actifs:
        part = o.montant_restant / total_restant if total_restant > 0 else 0.0
        montants[o.id] = min(part * epargne_disponible, o.montant_restant)

    total_alloue = sum(montants.values())
    surplus = epargne_disponible - total_alloue
    if surplus > 0.01:
        objectifs_non_satures = [o for o in objectifs_actifs if montants[o.id] < o.montant_restant - 0.01]
        besoin_non_sature = sum(o.montant_restant - montants[o.id] for o in objectifs_non_satures)
        if besoin_non_sature > 0:
            for o in objectifs_non_satures:
                part = (o.montant_restant - montants[o.id]) / besoin_non_sature
                montants[o.id] = min(montants[o.id] + part * surplus, o.montant_restant)

    allocations = []
    for o in objectifs:
        montant_alloue = round(montants.get(o.id, 0.0), 2)
        allocations.append(
            AllocationObjectif(
                objectif_id=o.id,
                montant_alloue_ce_mois=montant_alloue,
                mois_restants_estimes=_mois_restants(o, montant_alloue),
            )
        )

    total_alloue_final = round(sum(montants.values()), 2)
    return ResultatRepartitionEpargne(
        epargne_disponible=epargne_disponible,
        allocations=allocations,
        epargne_non_allouee=round(max(epargne_disponible - total_alloue_final, 0.0), 2),
    )


METHODES_REPARTITION = {
    "cascade": repartir_epargne_cascade,
    "proportionnelle": repartir_epargne_proportionnelle,
}


def repartir_epargne(
    objectifs: list[ObjectifEpargne], epargne_disponible: float, methode: str = "cascade"
) -> ResultatRepartitionEpargne:
    """Point d'entrée principal du module."""
    if methode not in METHODES_REPARTITION:
        raise ValueError(f"Méthode inconnue : {methode!r}. Attendu : {list(METHODES_REPARTITION)}")
    return METHODES_REPARTITION[methode](objectifs, epargne_disponible)
