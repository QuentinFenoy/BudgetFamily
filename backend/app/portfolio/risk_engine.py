"""Cœur d'allocation basé sur le risque — fonctions pures (numpy/scipy/pandas).

Ces fonctions sont reprises VERBATIM de l'optimiseur QuantFolio v2 d'Émilie
(Hierarchical Risk Parity et Equal Risk Contribution), afin de préserver sa
calibration et ses corrections. Seul le cœur robuste, indépendant des rendements
espérés (« HRP / Risk Parity ignorent mu — leur Sharpe dépend uniquement de Σ »),
est vendoré ici : il ne dépend d'aucun accès réseau (pas de yfinance, pas de
sklearn), ce qui le rend sûr sur le chemin d'une requête API.

La couche vues (Black-Litterman, momentum, analyste, ML) de l'optimiseur d'origine
n'est volontairement pas reprise : elle raisonne sur des instruments nominatifs
(capitalisations, cibles d'analystes) et n'a pas de sens sur des classes d'actifs
génériques (cf. doc d'architecture, section 8). Elle reste disponible dans
app.portfolio.quant_engine pour le rafraîchissement hors-ligne des statistiques.
"""

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage
from scipy.optimize import minimize
from scipy.spatial.distance import squareform


def _hrp_quasi_diagonal_order(link: np.ndarray, n_leaves: int) -> list[int]:
    link = link.astype(int)
    sorted_items = pd.Series([link[-1, 0], link[-1, 1]])
    while sorted_items.max() >= n_leaves:
        sorted_items.index = range(0, sorted_items.shape[0] * 2, 2)
        clusters = sorted_items[sorted_items >= n_leaves]
        idx = clusters.index
        rows = clusters.values - n_leaves
        sorted_items[idx] = link[rows, 0]
        right_children = pd.Series(link[rows, 1], index=idx + 1)
        sorted_items = pd.concat([sorted_items, right_children]).sort_index()
        sorted_items.index = range(sorted_items.shape[0])
    return sorted_items.tolist()


def _hrp_cluster_variance(cov: np.ndarray, items: list[int]) -> float:
    sub_cov = cov[np.ix_(items, items)]
    ivp = 1.0 / np.diag(sub_cov)
    ivp /= ivp.sum()
    return float(ivp @ sub_cov @ ivp)


def hierarchical_risk_parity(cov_matrix: np.ndarray) -> np.ndarray:
    n = cov_matrix.shape[0]
    if n == 1:
        return np.array([1.0])
    std = np.sqrt(np.diag(cov_matrix))
    corr = np.clip(cov_matrix / np.outer(std, std), -1.0, 1.0)
    np.fill_diagonal(corr, 1.0)
    dist = np.sqrt(np.clip(0.5 * (1.0 - corr), 0.0, None))
    link = linkage(squareform(dist, checks=False), method="single")
    order = _hrp_quasi_diagonal_order(link, n)
    weights = pd.Series(1.0, index=order)
    clusters = [order]
    while clusters:
        next_clusters = []
        for items in clusters:
            if len(items) <= 1:
                continue
            mid = len(items) // 2
            left, right = items[:mid], items[mid:]
            var_l = _hrp_cluster_variance(cov_matrix, left)
            var_r = _hrp_cluster_variance(cov_matrix, right)
            alpha = 1.0 - var_l / (var_l + var_r)
            weights[left] *= alpha
            weights[right] *= (1.0 - alpha)
            next_clusters += [left, right]
        clusters = next_clusters
    w = weights.sort_index().values
    return w / w.sum()


def equal_risk_contribution(
    cov_matrix: np.ndarray, min_weight: float = 0.0, max_weight: float = 1.0
) -> np.ndarray:
    n = cov_matrix.shape[0]
    if n == 1:
        return np.array([1.0])

    def obj(w):
        pv = w @ cov_matrix @ w
        rc = w * (cov_matrix @ w) / pv
        return np.sum((rc - 1.0 / n) ** 2)

    result = minimize(
        obj,
        np.ones(n) / n,
        method="SLSQP",
        bounds=[(min_weight, max_weight)] * n,
        constraints=[{"type": "eq", "fun": lambda w: np.sum(w) - 1}],
        options={"ftol": 1e-14, "maxiter": 2000},
    )
    if not result.success:
        raise RuntimeError(f"Risk parity : {result.message}")
    return result.x / result.x.sum()
