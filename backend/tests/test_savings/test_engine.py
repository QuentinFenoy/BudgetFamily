import math

from app.savings.models import ObjectifEpargne
from app.savings.engine import repartir_epargne_cascade, repartir_epargne_proportionnelle, repartir_epargne


def _get_allocation(resultat, objectif_id):
    return next(a for a in resultat.allocations if a.objectif_id == objectif_id)


def test_cascade_priorite_1_rempli_avant_priorite_2():
    objectifs = [
        ObjectifEpargne(id="urgence", nom="Fonds urgence", montant_cible=3000, montant_actuel=2800, priorite=1),
        ObjectifEpargne(id="voyage", nom="Voyage", montant_cible=2000, montant_actuel=0, priorite=2),
    ]
    resultat = repartir_epargne_cascade(objectifs, epargne_disponible=500)

    # urgence a besoin de 200 -> reçoit exactement 200, le reste (300) va au voyage
    assert _get_allocation(resultat, "urgence").montant_alloue_ce_mois == 200.0
    assert _get_allocation(resultat, "urgence").mois_restants_estimes == 1
    assert _get_allocation(resultat, "voyage").montant_alloue_ce_mois == 300.0
    assert resultat.epargne_non_allouee == 0.0


def test_cascade_epargne_insuffisante_pour_second_objectif():
    objectifs = [
        ObjectifEpargne(id="a", nom="A", montant_cible=1000, montant_actuel=0, priorite=1),
        ObjectifEpargne(id="b", nom="B", montant_cible=1000, montant_actuel=0, priorite=2),
    ]
    resultat = repartir_epargne_cascade(objectifs, epargne_disponible=300)

    assert _get_allocation(resultat, "a").montant_alloue_ce_mois == 300.0
    assert _get_allocation(resultat, "b").montant_alloue_ce_mois == 0.0
    # b ne reçoit rien ce mois -> mois_restants_estimes doit être None (pas de division par 0)
    assert _get_allocation(resultat, "b").mois_restants_estimes is None


def test_cascade_tous_objectifs_atteints_epargne_non_allouee():
    objectifs = [ObjectifEpargne(id="a", nom="A", montant_cible=100, montant_actuel=100, priorite=1)]
    resultat = repartir_epargne_cascade(objectifs, epargne_disponible=500)

    assert _get_allocation(resultat, "a").montant_alloue_ce_mois == 0.0
    assert _get_allocation(resultat, "a").mois_restants_estimes == 0.0
    assert resultat.epargne_non_allouee == 500.0


def test_proportionnelle_repartit_au_prorata_du_restant():
    objectifs = [
        ObjectifEpargne(id="a", nom="A", montant_cible=1000, montant_actuel=0, priorite=1),  # restant 1000
        ObjectifEpargne(id="b", nom="B", montant_cible=3000, montant_actuel=0, priorite=2),  # restant 3000
    ]
    resultat = repartir_epargne_proportionnelle(objectifs, epargne_disponible=400)

    # a doit recevoir 1/4 (1000/4000), b 3/4 (3000/4000)
    assert math.isclose(_get_allocation(resultat, "a").montant_alloue_ce_mois, 100.0, abs_tol=0.01)
    assert math.isclose(_get_allocation(resultat, "b").montant_alloue_ce_mois, 300.0, abs_tol=0.01)
    assert resultat.epargne_non_allouee == 0.0


def test_proportionnelle_plafonne_quand_epargne_depasse_le_besoin_total():
    """Avec une pondération strictement proportionnelle au montant restant, un objectif ne
    peut être plafonné individuellement que si TOUS les objectifs le sont simultanément
    (le ratio épargne/besoin_total s'applique uniformément). Le cas réel de plafonnement
    est donc : l'épargne disponible dépasse la somme des besoins restants.
    """
    objectifs = [
        ObjectifEpargne(id="petit", nom="Petit", montant_cible=100, montant_actuel=90, priorite=1),  # restant 10
        ObjectifEpargne(id="grand", nom="Grand", montant_cible=5000, montant_actuel=0, priorite=2),  # restant 5000
    ]
    resultat = repartir_epargne_proportionnelle(objectifs, epargne_disponible=6000)  # > 5010 (besoin total)

    # les deux objectifs doivent être exactement comblés, jamais dépassés
    assert _get_allocation(resultat, "petit").montant_alloue_ce_mois == 10.0
    assert _get_allocation(resultat, "grand").montant_alloue_ce_mois == 5000.0
    # le surplus (6000 - 5010) doit apparaître comme non alloué, pas perdu ni sur-attribué
    assert math.isclose(resultat.epargne_non_allouee, 990.0, abs_tol=0.01)


def test_proportionnelle_repartition_fine_sous_le_besoin_total():
    """En dessous du besoin total, chaque objectif reçoit exactement sa part au prorata
    de son propre besoin, sans plafonnement ni redistribution nécessaire."""
    objectifs = [
        ObjectifEpargne(id="petit", nom="Petit", montant_cible=100, montant_actuel=90, priorite=1),  # restant 10
        ObjectifEpargne(id="grand", nom="Grand", montant_cible=5000, montant_actuel=0, priorite=2),  # restant 5000
    ]
    resultat = repartir_epargne_proportionnelle(objectifs, epargne_disponible=1000)  # < 5010

    # 10/5010 et 5000/5010 de 1000€
    assert math.isclose(_get_allocation(resultat, "petit").montant_alloue_ce_mois, 1.996, abs_tol=0.01)
    assert math.isclose(_get_allocation(resultat, "grand").montant_alloue_ce_mois, 998.004, abs_tol=0.01)
    assert resultat.epargne_non_allouee == 0.0


def test_repartir_epargne_dispatch_par_methode():
    objectifs = [ObjectifEpargne(id="a", nom="A", montant_cible=1000, priorite=1)]
    resultat = repartir_epargne(objectifs, 200, methode="cascade")
    assert _get_allocation(resultat, "a").montant_alloue_ce_mois == 200.0


def test_repartir_epargne_methode_inconnue_leve_erreur():
    objectifs = [ObjectifEpargne(id="a", nom="A", montant_cible=1000, priorite=1)]
    try:
        repartir_epargne(objectifs, 200, methode="au_hasard")
        assert False, "devrait lever une ValueError"
    except ValueError:
        pass
