"""Tests du moteur de projection (calcul pur, sans base de données)."""

from app.savings.projection import (
    bruts_par_enveloppe,
    message_faisabilite,
    rendement_net_annuel_requis,
    risque_pour_rendement,
)


def test_rendement_zero_quand_epargne_seule_suffit():
    # 500 €/mois pendant 24 mois = 12 000 € > 10 000 € cible.
    assert rendement_net_annuel_requis(10000, 0, 500, 24) == 0.0


def test_rendement_zero_quand_objectif_deja_atteint():
    assert rendement_net_annuel_requis(5000, 5000, 0, 12) == 0.0


def test_rendement_positif_quand_epargne_insuffisante():
    r = rendement_net_annuel_requis(10000, 0, 300, 24)  # 7 200 € épargnés < 10 000 €
    assert r is not None and r > 0.0


def test_pv_seul_doublement_en_un_an_donne_100_pct():
    # 3 000 -> 6 000 en 12 mois sans versement : ~100 %/an.
    r = rendement_net_annuel_requis(6000, 3000, 0, 12)
    assert r is not None and abs(r - 1.0) < 0.01


def test_objectif_hors_de_portee_renvoie_none():
    assert rendement_net_annuel_requis(100000, 0, 100, 12) is None


def test_horizon_absent_renvoie_none():
    assert rendement_net_annuel_requis(10000, 0, 300, None) is None


def test_messages_faisabilite_par_bande():
    assert "seule épargne" in message_faisabilite(0.0)
    assert "prudent" in message_faisabilite(0.03)
    assert "équilibré" in message_faisabilite(0.055)
    assert "Difficile" in message_faisabilite(0.13)
    assert "Très difficile" in message_faisabilite(0.25)
    assert "hors de portée" in message_faisabilite(None)


def test_bruts_par_enveloppe_croissants_avec_la_fiscalite():
    # Pour NET 6 %, le brut à viser augmente avec la fiscalité de l'enveloppe.
    bruts = bruts_par_enveloppe(0.06)
    par_nom = {b.enveloppe: b.rendement_brut_indicatif for b in bruts}
    assert par_nom["Livret A / LDDS"] == 0.06  # exonéré : brut = net
    assert par_nom["Compte-titres (flat tax)"] > par_nom["PEA (après 5 ans)"]
    assert all(b.rendement_brut_indicatif >= 0.06 for b in bruts)


def test_risque_croit_avec_le_rendement_requis():
    frontiere = [
        (1, 0.025, 0.03),
        (2, 0.035, 0.05),
        (3, 0.047, 0.08),
        (4, 0.058, 0.11),
        (5, 0.067, 0.14),
    ]
    faible = risque_pour_rendement(frontiere, 0.02)
    fort = risque_pour_rendement(frontiere, 0.09)
    assert faible.note_sur_5 < fort.note_sur_5
    assert fort.au_dela_frontiere is True  # 9 % dépasse le profil le plus risqué
    assert faible.au_dela_frontiere is False
