"""Fourniture des statistiques par classe d'actifs (moyennes annualisées + covariance).

Deux sources, dans l'ordre de préférence :
1. Un snapshot de marché `data/asset_class_stats.json`, produit hors-ligne à partir
   des proxys réels (scripts/refresh_asset_class_stats.py) ;
2. À défaut, les hypothèses de marché long terme calibrées (app.portfolio.asset_classes).

Aucun accès réseau sur ce chemin : le snapshot est un fichier local, et le repli
calibré est en dur. La covariance renvoyée est toujours symétrisée et rendue
semi-définie positive (clip des valeurs propres négatives), pour que HRP/ERC opèrent
sur une matrice valide quelle que soit la source.
"""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from app.portfolio.asset_classes import (
    CLES,
    DEFAULT_CORRELATIONS,
    DEFAULT_MU_VOL,
)

_SNAPSHOT_PATH = Path(__file__).parent / "data" / "asset_class_stats.json"


@dataclass(frozen=True)
class AssetClassStats:
    cles: tuple[str, ...]        # ordre canonique des classes
    mu: np.ndarray               # rendements annuels espérés (aligné sur cles)
    cov: np.ndarray              # covariance annualisée (aligné sur cles)
    source: str                  # "snapshot:<date>" | "hypotheses_calibrees"


def _nearest_psd(cov: np.ndarray, epsilon: float = 1e-10) -> np.ndarray:
    """Symétrise et rend la matrice semi-définie positive (clip des valeurs propres)."""
    sym = 0.5 * (cov + cov.T)
    vals, vecs = np.linalg.eigh(sym)
    vals = np.clip(vals, epsilon, None)
    return (vecs * vals) @ vecs.T


def _cov_from_calibration() -> tuple[np.ndarray, np.ndarray]:
    n = len(CLES)
    mu = np.array([DEFAULT_MU_VOL[c][0] for c in CLES], dtype=float)
    vol = np.array([DEFAULT_MU_VOL[c][1] for c in CLES], dtype=float)

    corr = np.eye(n)
    index = {c: i for i, c in enumerate(CLES)}
    for (a, b), rho in DEFAULT_CORRELATIONS.items():
        i, j = index[a], index[b]
        corr[i, j] = corr[j, i] = rho

    cov = corr * np.outer(vol, vol)
    return mu, _nearest_psd(cov)


def load_asset_class_stats() -> AssetClassStats:
    if _SNAPSHOT_PATH.exists():
        raw = json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))
        cles = tuple(raw["cles"])
        mu = np.array(raw["mu"], dtype=float)
        cov = _nearest_psd(np.array(raw["cov"], dtype=float))
        return AssetClassStats(cles=cles, mu=mu, cov=cov, source=f"snapshot:{raw.get('as_of', 'inconnu')}")

    mu, cov = _cov_from_calibration()
    return AssetClassStats(cles=CLES, mu=mu, cov=cov, source="hypotheses_calibrees")
