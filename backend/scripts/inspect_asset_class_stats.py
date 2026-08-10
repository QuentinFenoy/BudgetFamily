"""Affiche les statistiques historiques RÉELLES par classe d'actifs, et les compare
aux hypothèses calibrées par défaut.

HORS-LIGNE — nécessite un accès réseau et requirements-quant.txt (yfinance, sklearn) :

    pip install -r requirements.txt -r requirements-quant.txt
    python -m scripts.inspect_asset_class_stats                 # depuis backend/
    python -m scripts.inspect_asset_class_stats --period 5y     # autre fenêtre
    python -m scripts.inspect_asset_class_stats --par-proxy     # détail ticker par ticker

Contrairement à refresh_asset_class_stats.py, ce script n'écrit RIEN : il sert à
vérifier la qualité des proxys et à décider si les hypothèses par défaut
(DEFAULT_MU_VOL / DEFAULT_CORRELATIONS) doivent être révisées.

Trois diagnostics utiles :
  1. Historique réellement disponible par proxy (les ETF récents tronquent la fenêtre
     commune : le `dropna` final aligne toutes les classes sur la plus jeune) ;
  2. Corrélation entre proxys d'une même classe — si elle vaut ~0.99, les moyenner
     n'apporte aucune robustesse statistique (les deux suivent le même indice) ;
  3. Écart entre statistiques réalisées et hypothèses par défaut.
"""

import argparse

import numpy as np
import pandas as pd

from app.portfolio.asset_classes import ASSET_CLASSES, CLES, DEFAULT_CORRELATIONS, DEFAULT_MU_VOL
from app.portfolio.quant_engine import covariance_ledoit_wolf, fetch_returns

TRADING_DAYS = 252


def _stats_annualisees(serie: pd.Series) -> tuple[float, float]:
    """Rendement (log, annualisé) et volatilité annualisée d'une série de rendements."""
    return float(serie.mean() * TRADING_DAYS), float(serie.std(ddof=1) * np.sqrt(TRADING_DAYS))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--period", default="10y", help="Fenêtre yfinance (ex. 5y, 10y, max)")
    parser.add_argument("--par-proxy", action="store_true", help="Détail par ticker")
    args = parser.parse_args()

    series: dict[str, pd.Series] = {}
    couverture: list[tuple[str, str, int, str, str]] = []
    correl_intra: dict[str, float | None] = {}

    for ac in ASSET_CLASSES:
        returns = fetch_returns(list(ac.proxys), period=args.period)
        for ticker in returns.columns:
            col = returns[ticker].dropna()
            couverture.append(
                (ac.nom, ticker, len(col), str(col.index[0].date()), str(col.index[-1].date()))
            )
        # Corrélation entre proxys d'une même classe (si panier multiple).
        if returns.shape[1] > 1:
            correl = returns.corr().values
            correl_intra[ac.cle] = float(np.median(correl[np.triu_indices_from(correl, k=1)]))
        else:
            correl_intra[ac.cle] = None
        series[ac.cle] = returns.mean(axis=1)

    print("\n" + "=" * 78)
    print("1. COUVERTURE HISTORIQUE PAR PROXY")
    print("=" * 78)
    print(f"{'Classe':<37}{'Ticker':<11}{'Jours':>7}  {'Début':<12}{'Fin':<12}")
    for nom, ticker, n, debut, fin in couverture:
        print(f"{nom:<37}{ticker:<11}{n:>7}  {debut:<12}{fin:<12}")

    if args.par_proxy:
        print("\n" + "=" * 78)
        print("2b. STATISTIQUES PAR PROXY INDIVIDUEL")
        print("=" * 78)
        for ac in ASSET_CLASSES:
            r = fetch_returns(list(ac.proxys), period=args.period)
            for ticker in r.columns:
                mu, vol = _stats_annualisees(r[ticker].dropna())
                print(f"{ac.nom:<37}{ticker:<11}{mu * 100:>7.2f}%{vol * 100:>9.2f}%")

    print("\n" + "=" * 78)
    print("2. CORRÉLATION ENTRE PROXYS D'UNE MÊME CLASSE")
    print("   (proche de 1.00 => le panier n'apporte pas de diversification)")
    print("=" * 78)
    for ac in ASSET_CLASSES:
        c = correl_intra[ac.cle]
        print(f"{ac.nom:<40}{'—  (proxy unique)' if c is None else f'{c:>6.3f}'}")

    # Fenêtre commune à toutes les classes.
    df = pd.concat(series, axis=1).dropna()
    df = df[list(CLES)]

    print("\n" + "=" * 78)
    print(f"3. FENÊTRE COMMUNE : {len(df)} jours  ({df.index[0].date()} → {df.index[-1].date()})")
    print(f"   ({len(df) / TRADING_DAYS:.1f} an(s) — c'est ce que voit refresh_asset_class_stats)")
    print("=" * 78)

    print("\n" + "=" * 78)
    print("4. RÉALISÉ vs HYPOTHÈSES PAR DÉFAUT")
    print("=" * 78)
    print(f"{'Classe':<37}{'µ réel':>9}{'µ déf.':>9}{'σ réel':>9}{'σ déf.':>9}")
    for ac in ASSET_CLASSES:
        mu_r, vol_r = _stats_annualisees(df[ac.cle])
        mu_d, vol_d = DEFAULT_MU_VOL[ac.cle]
        print(
            f"{ac.nom:<37}{mu_r * 100:>8.2f}%{mu_d * 100:>8.2f}%"
            f"{vol_r * 100:>8.2f}%{vol_d * 100:>8.2f}%"
        )

    print("\n  NB : µ réel est un rendement log annualisé sur la fenêtre commune —")
    print("  très sensible à la période choisie. Les hypothèses par défaut visent le")
    print("  long terme et ne doivent PAS être recalées mécaniquement sur cette colonne.")

    print("\n" + "=" * 78)
    print("5. CORRÉLATIONS RÉALISÉES vs PAR DÉFAUT (écarts > 0.10)")
    print("=" * 78)
    correl_reelle = df.corr()
    ecarts = []
    for (a, b), rho_def in DEFAULT_CORRELATIONS.items():
        rho_reel = float(correl_reelle.loc[a, b])
        if abs(rho_reel - rho_def) > 0.10:
            ecarts.append((abs(rho_reel - rho_def), a, b, rho_reel, rho_def))
    if not ecarts:
        print("  Aucun écart significatif — les corrélations posées tiennent la route.")
    for _, a, b, rho_reel, rho_def in sorted(ecarts, reverse=True):
        print(f"  {a} ↔ {b}\n      réel {rho_reel:+.2f}  |  défaut {rho_def:+.2f}")

    _, shrink = covariance_ledoit_wolf(df)
    print(f"\n  Shrinkage Ledoit-Wolf sur la fenêtre commune : {shrink:.3f}")
    print("\n(Ce script n'écrit rien. Pour mettre à jour le snapshot utilisé par l'API :")
    print(" python -m scripts.refresh_asset_class_stats)\n")


if __name__ == "__main__":
    main()
