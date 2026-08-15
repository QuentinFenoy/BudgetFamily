"""Tests unitaires de l'allocateur (sans base de données).

Verrouillent les corrections apportées : le monétaire est un tampon plafonné (et ne
capte plus tout le sleeve défensif), les actifs défensifs réels reçoivent du poids, et
le rendement affiché s'appuie sur les hypothèses long terme.
"""

from app.portfolio.allocator import _CASH_PART_OF_DEFENSIVE, construire_allocation
from app.portfolio.data_provider import load_asset_class_stats


def _part(allocation, cle: str) -> float:
    return next(l.part for l in allocation.lignes if l.cle == cle)


def test_monetaire_est_un_tampon_plafonne():
    stats = load_asset_class_stats()
    alloc = construire_allocation(stats, tolerance_risque=3, age=35, horizon_annees=15, objectif="aucun")

    monetaire = _part(alloc, "monetaire_liquidites")
    # Part défensive = 50 % ; le cash ne doit être qu'une fraction de ce sleeve,
    # pas sa quasi-totalité comme avant (~50 % du portefeuille).
    assert monetaire <= alloc.part_defensive * _CASH_PART_OF_DEFENSIVE + 1e-6
    assert monetaire < 0.15


def test_les_obligations_recoivent_du_poids():
    stats = load_asset_class_stats()
    alloc = construire_allocation(stats, tolerance_risque=3, age=35, horizon_annees=15, objectif="aucun")

    obligations = _part(alloc, "obligations_souveraines_euro") + _part(
        alloc, "obligations_entreprises_euro"
    )
    # Le défensif réel (obligations) doit être substantiel, plus que le tampon cash.
    assert obligations > 0.20
    assert obligations > _part(alloc, "monetaire_liquidites")


def test_poids_somment_a_un_et_rendement_positif():
    stats = load_asset_class_stats()
    alloc = construire_allocation(stats, tolerance_risque=3, age=35, horizon_annees=15, objectif="aucun")

    assert abs(sum(l.part for l in alloc.lignes) - 1.0) < 0.01
    # Avec les hypothèses long terme, un profil équilibré vise nettement plus que le
    # taux sans risque monétaire.
    assert alloc.rendement_annuel_espere > 0.035


def test_profil_prudent_moins_de_croissance_et_moins_de_rendement():
    stats = load_asset_class_stats()
    prudent = construire_allocation(stats, tolerance_risque=1, age=63, horizon_annees=3, objectif="matelas_securite")
    dynamique = construire_allocation(stats, tolerance_risque=5, age=30, horizon_annees=25, objectif="aucun")

    assert prudent.part_croissance < dynamique.part_croissance
    assert prudent.rendement_annuel_espere < dynamique.rendement_annuel_espere
    assert prudent.volatilite_annuelle_estimee < dynamique.volatilite_annuelle_estimee
