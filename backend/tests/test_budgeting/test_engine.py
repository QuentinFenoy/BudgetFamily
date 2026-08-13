import math

from app.budgeting.models import ProfilFoyer, Objectif
from app.budgeting.engine import calculer_budget


def test_celibataire_haut_revenu_logement_paye():
    """Célibataire, 10 000€/mois, charges fixes quasi nulles -> tranche >5000€/hab."""
    profil = ProfilFoyer(
        revenus_total=10000,
        charges_fixes_total=0,
        nb_personnes=1,
        nb_enfants=0,
        objectif=Objectif.RETRAITE_LONG_TERME,
    )
    resultat = calculer_budget(profil)

    assert resultat.disponible == 10000
    # catégories plafonnées : 330+250+110+100 = 790 (enfants = 0)
    assert resultat.montants_categories["alimentation"] == 330.0
    assert resultat.montants_categories["transport"] == 250.0
    assert resultat.montants_categories["enfants"] == 0.0
    # loisirs dégressif : 13%*3000 + 6%*7000 = 390+420 = 810
    assert math.isclose(resultat.montants_categories["loisirs"], 810.0, abs_tol=0.01)
    # imprevus dégressif : 9%*3000 + 4%*7000 = 270+280 = 550
    assert math.isclose(resultat.montants_categories["imprevus"], 550.0, abs_tol=0.01)
    # épargne potentielle largement > 50%
    assert resultat.epargne_potentielle > 5000
    assert resultat.epargne_potentielle / resultat.disponible > 0.7
    # taux de référence : base 50% (tranche >5000) + 5pts (retraite) = 55%
    assert math.isclose(resultat.epargne_reference_taux, 0.55, abs_tol=0.001)


def test_famille_revenu_moyen():
    """Couple + 2 enfants, revenu moyen -> tranche 1000-3000€/hab."""
    profil = ProfilFoyer(
        revenus_total=4500,
        charges_fixes_total=1500,  # loyer/crédit + assurances
        nb_personnes=4,
        nb_enfants=2,
        objectif=Objectif.AUCUN,
    )
    resultat = calculer_budget(profil)

    assert resultat.disponible == 3000
    assert resultat.disponible_par_hab == 750.0  # tranche 500-1000€/hab
    # enfants : 12%*3000=360, plafond 200*2=400 -> 360 (pas plafonné)
    assert resultat.montants_categories["enfants"] == 360.0
    # aucune catégorie plafonnée ne doit dépasser son plafond
    assert resultat.montants_categories["alimentation"] <= 450.0 * 4
    # somme des montants + épargne doit reconstituer le disponible
    total = sum(resultat.montants_categories.values()) + resultat.epargne_potentielle
    assert math.isclose(total, resultat.disponible, abs_tol=0.01)


def test_revenu_tres_faible_desendettement():
    """Personne seule sous le seuil, objectif désendettement -> taux plancher."""
    profil = ProfilFoyer(
        revenus_total=1400,
        charges_fixes_total=1100,
        nb_personnes=1,
        nb_enfants=0,
        objectif=Objectif.DESENDETTEMENT,
    )
    resultat = calculer_budget(profil)

    assert resultat.disponible == 300
    assert resultat.disponible_par_hab == 300.0  # tranche <500€/hab -> base 5%
    # 5% - 5pts (désendettement) = 0%, mais borné au plancher 5%
    assert resultat.epargne_reference_taux == 0.05


def test_ajustement_force_reduit_discretionnaire_avant_semi_essentiel():
    profil = ProfilFoyer(
        revenus_total=3500,
        charges_fixes_total=1000,
        nb_personnes=2,
        nb_enfants=0,
        objectif=Objectif.AUCUN,
    )
    resultat_libre = calculer_budget(profil)
    cible_forcee = resultat_libre.epargne_potentielle + 200  # +200€ au-delà du potentiel naturel

    resultat_force = calculer_budget(profil, epargne_cible_forcee=cible_forcee)

    assert resultat_force.ajustement_applique is True
    # essentiels inchangés
    assert resultat_force.montants_categories["alimentation"] == resultat_libre.montants_categories["alimentation"]
    assert resultat_force.montants_categories["sante"] == resultat_libre.montants_categories["sante"]
    # discrétionnaires réduits
    assert resultat_force.montants_categories["loisirs"] < resultat_libre.montants_categories["loisirs"]
    assert resultat_force.montants_categories["imprevus"] < resultat_libre.montants_categories["imprevus"]
    # épargne effective proche de la cible (à l'écart non couvert près)
    assert math.isclose(
        resultat_force.epargne_potentielle + resultat_force.ecart_non_couvert,
        cible_forcee,
        abs_tol=0.5,
    )


def test_ajustement_force_signale_ecart_non_couvert_si_cible_irrealiste():
    profil = ProfilFoyer(
        revenus_total=1600,
        charges_fixes_total=1000,
        nb_personnes=1,
        nb_enfants=0,
        objectif=Objectif.AUCUN,
    )
    resultat_libre = calculer_budget(profil)
    # cible délirante : demander plus que le disponible total
    resultat_force = calculer_budget(profil, epargne_cible_forcee=resultat_libre.disponible * 2)

    assert resultat_force.ecart_non_couvert > 0
    # les essentiels ne sont jamais réduits, même dans ce cas extrême
    assert resultat_force.montants_categories["alimentation"] == resultat_libre.montants_categories["alimentation"]


def test_override_categorie_a_zero_nest_pas_gere_par_le_moteur_de_base():
    """Le moteur ne gère pas encore l'override manuel utilisateur (ex: transport=0
    car pris en charge par l'employeur) -> à implémenter dans la couche API (Phase suivante).
    Ce test documente explicitement la limite actuelle."""
    profil = ProfilFoyer(revenus_total=3000, charges_fixes_total=1000, nb_personnes=1)
    resultat = calculer_budget(profil)
    assert resultat.montants_categories["transport"] > 0
