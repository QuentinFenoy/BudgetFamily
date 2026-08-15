"""Traduction d'un profil utilisateur en allocation par classe d'actifs.

Logique transparente et explicable (robo-advisor prudent), pilotée par le profil
plutôt que par des prévisions de rendement fragiles :

1. Une fraction « croissance » cible est dérivée du profil — tolérance au risque,
   puis plafonnée par l'âge (glide-path « 110 - âge »), l'horizon et l'objectif.
2. Cette fraction répartit le portefeuille entre le sleeve croissance (actions,
   immobilier) et le sleeve défensif (obligations, or, monétaire).
3. Le monétaire est traité à part, comme un TAMPON DE LIQUIDITÉ plafonné : sans cela,
   la parité de risque (HRP/ERC), qui répartit par risque inverse, s'engouffre dans
   l'actif à volatilité quasi nulle et produit un portefeuille à ~100 % de cash. Le
   reste du défensif (obligations, or) est réparti par HRP/ERC sur les actifs réels.
4. Dans chaque sleeve, les poids viennent de HRP (défaut) ou ERC — le cœur robuste,
   qui ne dépend que de la covariance.

Rendement/Sharpe affichés : calculés avec des hypothèses de rendement LONG TERME
(app.portfolio.asset_classes.LONG_RUN_MU), volontairement distinctes des rendements
réalisés récents (mauvais estimateur du futur). La volatilité, elle, vient de la
covariance de marché. On sépare ainsi le risque (estimé sur données) du rendement
(hypothèse prudente).
"""

from dataclasses import dataclass

import numpy as np

from app.portfolio.asset_classes import ASSET_CLASSES, LONG_RUN_MU, SLEEVE_CROISSANCE
from app.portfolio.data_provider import AssetClassStats
from app.portfolio.risk_engine import equal_risk_contribution, hierarchical_risk_parity

# Fraction croissance de base selon la tolérance au risque déclarée (1..5).
_GROWTH_BY_RISK = {1: 0.20, 2: 0.35, 3: 0.50, 4: 0.68, 5: 0.85}
_DEFAULT_RISK = 3

# Part du sleeve défensif conservée en tampon de liquidité (monétaire). Le reste du
# défensif est investi en actifs réels (obligations, or). Borne le cash pour éviter
# qu'il ne capte tout le sleeve défensif par pur effet de volatilité quasi nulle.
_CASH_CLE = "monetaire_liquidites"
_CASH_PART_OF_DEFENSIVE = 0.20

# Taux sans risque pour le ratio de Sharpe (approx. monétaire euro long terme).
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

    if age is not None:
        plafonds.append(max(0.0, min(0.90, (110 - age) / 100.0)))

    if horizon_annees is not None:
        if horizon_annees < 3:
            plafonds.append(0.20)
        elif horizon_annees < 8:
            plafonds.append(0.60)

    plafonds_objectif = {
        "desendettement": 0.05,
        "matelas_securite": 0.25,
        "moyen_terme": 0.60,
    }
    if objectif in plafonds_objectif:
        plafonds.append(plafonds_objectif[objectif])

    return float(max(0.0, min(base, *plafonds)))


def _poids_sleeve(cov: np.ndarray, indices: list[int], methode: str) -> np.ndarray:
    """Poids intra-sleeve via HRP ou ERC sur la sous-covariance des classes du sleeve."""
    if len(indices) == 1:
        return np.array([1.0])
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
    # Défensif « réel » = sleeve défensif SANS le monétaire (traité en tampon à part).
    idx_defensif_reel = [
        index_par_cle[ac.cle]
        for ac in ASSET_CLASSES
        if ac.sleeve != SLEEVE_CROISSANCE and ac.cle != _CASH_CLE and ac.cle in index_par_cle
    ]
    idx_cash = index_par_cle.get(_CASH_CLE)

    poids = np.zeros(len(stats.cles))

    if idx_croissance and part_croissance > 0:
        poids[idx_croissance] = _poids_sleeve(stats.cov, idx_croissance, methode) * part_croissance

    if part_defensive > 0:
        part_cash = part_defensive * _CASH_PART_OF_DEFENSIVE
        part_defensif_reel = part_defensive - part_cash
        if idx_cash is not None:
            poids[idx_cash] += part_cash
        if idx_defensif_reel and part_defensif_reel > 0:
            poids[idx_defensif_reel] = (
                _poids_sleeve(stats.cov, idx_defensif_reel, methode) * part_defensif_reel
            )

    total = poids.sum()
    if total > 0:
        poids = poids / total  # renormalisation de sûreté

    # Rendement : hypothèses long terme (les rendements réalisés récents sont un mauvais
    # estimateur du futur). Volatilité : covariance de marché.
    mu_long_terme = np.array([LONG_RUN_MU.get(cle, 0.0) for cle in stats.cles])
    vol = float(np.sqrt(max(poids @ stats.cov @ poids, 0.0)))
    rendement = float(poids @ mu_long_terme)
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
