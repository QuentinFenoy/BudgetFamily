"""Traduction d'un profil utilisateur en allocation par classe d'actifs.

Logique volontairement transparente et explicable (robo-advisor prudent), pilotée
par le profil plutôt que par des prévisions de rendement fragiles :

1. Une fraction « croissance » cible est dérivée du profil — tolérance au risque,
   puis plafonnée par l'âge (glide-path type « 110 - âge »), l'horizon de placement
   et l'objectif (désendettement/matelas => très défensif).
2. Cette fraction répartit le portefeuille entre le sleeve croissance (actions,
   immobilier) et le sleeve défensif (obligations, or, monétaire).
3. À l'intérieur de chaque sleeve, les poids sont fixés par HRP (défaut) ou ERC —
   le cœur robuste de l'optimiseur, qui ne dépend que de la covariance.

Résultat : une allocation diversifiée, cohérente avec le profil, sur des classes
génériques uniquement.
"""

from dataclasses import dataclass

import numpy as np

from app.portfolio.asset_classes import ASSET_CLASSES, SLEEVE_CROISSANCE
from app.portfolio.data_provider import AssetClassStats
from app.portfolio.risk_engine import equal_risk_contribution, hierarchical_risk_parity

# Fraction croissance de base selon la tolérance au risque déclarée (1..5).
_GROWTH_BY_RISK = {1: 0.20, 2: 0.35, 3: 0.50, 4: 0.68, 5: 0.85}
_DEFAULT_RISK = 3

# Taux sans risque pour le ratio de Sharpe estimé (approx. monétaire euro long terme).
_RISK_FREE = 0.020

METHODES = ("hrp", "erc")


@dataclass(frozen=True)
class LigneAllocation:
    cle: str
    nom: str
    sleeve: str
    part: float          # 0..1


@dataclass(frozen=True)
class Allocation:
    part_croissance: float
    part_defensive: float
    lignes: list[LigneAllocation]
    rendement_annuel_espere: float
    volatilite_annuelle_estimee: float
    ratio_sharpe_estime: float


def fraction_croissance_cible(
    tolerance_risque: int | None,
    age: int | None,
    horizon_annees: int | None,
    objectif: str,
) -> float:
    """Fraction du portefeuille allouée au sleeve croissance, dans [0, 0.90].

    Part de la tolérance au risque, puis applique une série de PLAFONDS (on retient
    le plus contraignant) : glide-path âge, horizon court, et objectif prudent.
    """
    base = _GROWTH_BY_RISK.get(tolerance_risque or _DEFAULT_RISK, _GROWTH_BY_RISK[_DEFAULT_RISK])

    plafonds = [0.90]  # jamais 100 % croissance : on garde toujours du lest

    # Glide-path âge : règle empirique « 110 - âge » en actions.
    if age is not None:
        plafonds.append(max(0.0, min(0.90, (110 - age) / 100.0)))

    # Horizon court => capital à préserver.
    if horizon_annees is not None:
        if horizon_annees < 3:
            plafonds.append(0.20)
        elif horizon_annees < 8:
            plafonds.append(0.60)

    # Objectif : certains imposent la prudence quelle que soit la tolérance déclarée.
    plafonds_objectif = {
        "desendettement": 0.05,     # rembourser la dette avant d'investir en risqué
        "matelas_securite": 0.25,   # l'épargne de précaution doit rester liquide/sûre
        "moyen_terme": 0.60,
    }
    if objectif in plafonds_objectif:
        plafonds.append(plafonds_objectif[objectif])

    return float(max(0.0, min(base, *plafonds)))


def _poids_sleeve(cov: np.ndarray, indices: list[int], methode: str) -> np.ndarray:
    """Poids intra-sleeve via HRP ou ERC sur la sous-covariance des classes du sleeve."""
    sous_cov = cov[np.ix_(indices, indices)]
    if methode == "erc":
        return equal_risk_contribution(sous_cov)
    return hierarchical_risk_parity(sous_cov)


def construire_allocation(
    stats: AssetClassStats,
    tolerance_risque: int | None,
    age: int | None,
    horizon_annees: int | None,
    objectif: str,
    methode: str = "hrp",
) -> Allocation:
    if methode not in METHODES:
        raise ValueError(f"Méthode inconnue : {methode!r} (attendu : {METHODES})")

    part_croissance = fraction_croissance_cible(tolerance_risque, age, horizon_annees, objectif)
    part_defensive = 1.0 - part_croissance

    index_par_cle = {cle: i for i, cle in enumerate(stats.cles)}
    idx_croissance = [
        index_par_cle[ac.cle]
        for ac in ASSET_CLASSES
        if ac.sleeve == SLEEVE_CROISSANCE and ac.cle in index_par_cle
    ]
    idx_defensif = [
        index_par_cle[ac.cle]
        for ac in ASSET_CLASSES
        if ac.sleeve != SLEEVE_CROISSANCE and ac.cle in index_par_cle
    ]

    poids = np.zeros(len(stats.cles))
    if idx_croissance and part_croissance > 0:
        poids[idx_croissance] = _poids_sleeve(stats.cov, idx_croissance, methode) * part_croissance
    if idx_defensif and part_defensive > 0:
        poids[idx_defensif] = _poids_sleeve(stats.cov, idx_defensif, methode) * part_defensive

    total = poids.sum()
    if total > 0:
        poids = poids / total  # renormalisation de sûreté

    # Statistiques de portefeuille (rendement = hypothèse, pas une promesse).
    vol = float(np.sqrt(max(poids @ stats.cov @ poids, 0.0)))
    rendement = float(poids @ stats.mu)
    sharpe = (rendement - _RISK_FREE) / vol if vol > 1e-9 else 0.0

    lignes = []
    for ac in ASSET_CLASSES:
        i = index_par_cle.get(ac.cle)
        if i is None:
            continue
        lignes.append(
            LigneAllocation(cle=ac.cle, nom=ac.nom, sleeve=ac.sleeve, part=round(float(poids[i]), 4))
        )

    return Allocation(
        part_croissance=round(part_croissance, 4),
        part_defensive=round(part_defensive, 4),
        lignes=lignes,
        rendement_annuel_espere=round(rendement, 4),
        volatilite_annuelle_estimee=round(vol, 4),
        ratio_sharpe_estime=round(sharpe, 2),
    )
