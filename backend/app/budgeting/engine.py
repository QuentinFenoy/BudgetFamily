"""Moteur de calcul de la répartition budgétaire.

Implémente le modèle décrit dans le document d'architecture (section 10.4) :
1. Disponible = Revenus - Charges fixes
2. Catégories calculées directement sur le Disponible (plafonnées ou dégressives)
3. Épargne_potentielle = résidu, comparée à un taux de référence
4. Ajustement forcé par priorité si une cible d'épargne supérieure est demandée
"""

from .models import ProfilFoyer, ResultatBudget, Priorite
from .rules import (
    CATEGORIES_PLAFONNEES,
    CATEGORIES_ELASTIQUES,
    SEUIL_DEGRESSIVITE_PAR_HAB,
    TRANCHES_EPARGNE_REFERENCE,
    MODIFICATEURS_OBJECTIF,
    TAUX_EPARGNE_MIN,
    TAUX_EPARGNE_MAX,
    REDUCTION_MAX_SEMI_ESSENTIEL,
)


def compute_disponible(profil: ProfilFoyer) -> float:
    disponible = profil.revenus_total - profil.charges_fixes_total
    return max(disponible, 0.0)


def compute_disponible_par_hab(disponible: float, profil: ProfilFoyer) -> float:
    return disponible / profil.nb_personnes


def _montant_categorie_plafonnee(nom: str, cfg: dict, disponible: float, profil: ProfilFoyer) -> float:
    montant_pondere = cfg["poids"] * disponible
    if "plafond_par_enfant" in cfg:
        if profil.nb_enfants == 0:
            return 0.0
        plafond = cfg["plafond_par_enfant"] * profil.nb_enfants
    else:
        plafond = cfg["plafond_par_hab"] * profil.nb_personnes
    return min(montant_pondere, plafond)


def _montant_categorie_elastique(cfg: dict, disponible_par_hab: float, profil: ProfilFoyer) -> float:
    part_pleine = min(disponible_par_hab, SEUIL_DEGRESSIVITE_PAR_HAB)
    part_reduite = max(disponible_par_hab - SEUIL_DEGRESSIVITE_PAR_HAB, 0.0)
    montant_par_hab = cfg["poids_plein"] * part_pleine + cfg["poids_reduit"] * part_reduite
    return montant_par_hab * profil.nb_personnes


def compute_montants_categories(disponible: float, disponible_par_hab: float, profil: ProfilFoyer) -> dict:
    montants = {}
    for nom, cfg in CATEGORIES_PLAFONNEES.items():
        montants[nom] = round(_montant_categorie_plafonnee(nom, cfg, disponible, profil), 2)
    for nom, cfg in CATEGORIES_ELASTIQUES.items():
        montants[nom] = round(_montant_categorie_elastique(cfg, disponible_par_hab, profil), 2)
    return montants


def compute_epargne_potentielle(disponible: float, montants_categories: dict) -> float:
    return round(disponible - sum(montants_categories.values()), 2)


def _priorite_categorie(nom: str) -> Priorite:
    if nom in CATEGORIES_PLAFONNEES:
        return CATEGORIES_PLAFONNEES[nom]["priorite"]
    return CATEGORIES_ELASTIQUES[nom]["priorite"]


def compute_taux_epargne_reference(disponible_par_hab: float, profil: ProfilFoyer) -> float:
    base = None
    for borne_min, borne_max, taux in TRANCHES_EPARGNE_REFERENCE:
        if borne_min <= disponible_par_hab < borne_max:
            base = taux
            break
    if base is None:
        base = TRANCHES_EPARGNE_REFERENCE[-1][2]

    modificateur = MODIFICATEURS_OBJECTIF.get(profil.objectif, 0.0)
    taux = base + modificateur

    # matelas de sécurité : le bonus ne s'applique que s'il n'est pas déjà atteint
    if profil.objectif.value == "matelas_securite" and profil.matelas_securite_atteint:
        taux = base

    return max(TAUX_EPARGNE_MIN, min(TAUX_EPARGNE_MAX, taux))


def forcer_epargne_cible(
    montants_categories: dict,
    disponible: float,
    epargne_potentielle: float,
    epargne_cible_forcee: float,
) -> tuple[dict, float]:
    """Réduit les catégories par ordre de priorité pour atteindre une cible d'épargne
    supérieure à l'épargne potentielle naturelle. Retourne (nouveaux montants, écart non couvert).
    """
    ecart = round(epargne_cible_forcee - epargne_potentielle, 2)
    if ecart <= 0:
        return dict(montants_categories), 0.0

    nouveaux = dict(montants_categories)

    # Niveau 3 : discrétionnaire, réductible jusqu'à 0
    categories_niv3 = [n for n in nouveaux if _priorite_categorie(n) == Priorite.DISCRETIONNAIRE]
    total_niv3 = sum(nouveaux[n] for n in categories_niv3)
    if total_niv3 > 0 and ecart > 0:
        reduction = min(ecart, total_niv3)
        for n in categories_niv3:
            part = nouveaux[n] / total_niv3 if total_niv3 else 0
            nouveaux[n] = round(nouveaux[n] - reduction * part, 2)
        ecart = round(ecart - reduction, 2)

    # Niveau 2 : semi-essentiel, réductible jusqu'à -30% du montant initial
    if ecart > 0:
        categories_niv2 = [n for n in montants_categories if _priorite_categorie(n) == Priorite.SEMI_ESSENTIEL]
        reduction_max_par_cat = {n: montants_categories[n] * REDUCTION_MAX_SEMI_ESSENTIEL for n in categories_niv2}
        total_reduction_max = sum(reduction_max_par_cat.values())
        if total_reduction_max > 0:
            reduction = min(ecart, total_reduction_max)
            for n in categories_niv2:
                part = reduction_max_par_cat[n] / total_reduction_max if total_reduction_max else 0
                nouveaux[n] = round(nouveaux[n] - reduction * part, 2)
            ecart = round(ecart - reduction, 2)

    # Niveau 1 : jamais touché — l'écart résiduel est retourné tel quel
    return nouveaux, max(ecart, 0.0)


def calculer_budget(profil: ProfilFoyer, epargne_cible_forcee: float | None = None) -> ResultatBudget:
    """Point d'entrée principal : calcule la répartition complète pour un profil donné."""
    disponible = compute_disponible(profil)
    disponible_par_hab = compute_disponible_par_hab(disponible, profil)

    montants = compute_montants_categories(disponible, disponible_par_hab, profil)
    epargne_potentielle = compute_epargne_potentielle(disponible, montants)

    taux_reference = compute_taux_epargne_reference(disponible_par_hab, profil)
    montant_reference = round(taux_reference * disponible, 2)

    ajustement_applique = False
    ecart_non_couvert = 0.0
    if epargne_cible_forcee is not None and epargne_cible_forcee > epargne_potentielle:
        montants, ecart_non_couvert = forcer_epargne_cible(
            montants, disponible, epargne_potentielle, epargne_cible_forcee
        )
        epargne_potentielle = compute_epargne_potentielle(disponible, montants)
        ajustement_applique = True

    return ResultatBudget(
        disponible=round(disponible, 2),
        disponible_par_hab=round(disponible_par_hab, 2),
        montants_categories=montants,
        epargne_potentielle=epargne_potentielle,
        epargne_reference_taux=round(taux_reference, 4),
        epargne_reference_montant=montant_reference,
        ajustement_applique=ajustement_applique,
        ecart_non_couvert=ecart_non_couvert,
    )
