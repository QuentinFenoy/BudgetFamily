"""Rafraîchit le snapshot de statistiques par classe d'actifs à partir des proxys réels.

HORS-LIGNE — nécessite un accès réseau et les dépendances de requirements-quant.txt
(yfinance, scikit-learn). À lancer périodiquement (ex. trimestriellement) :

    pip install -r requirements.txt -r requirements-quant.txt
    python -m scripts.refresh_asset_class_stats            # depuis backend/

Pour chaque classe, on télécharge les rendements (convertis en EUR) de son panier de
proxys, on les MOYENNE en une série de rendements représentative de la classe, puis on
estime la moyenne annualisée et la covariance Ledoit-Wolf via le moteur QuantFolio v2.
Le résultat écrase app/portfolio/data/asset_class_stats.json, que l'API préfère
ensuite aux hypothèses calibrées par défaut.

Aucun ticker n'est écrit dans le snapshot : seules les clés de classes génériques,
le vecteur de moyennes et la matrice de covariance le sont.
"""

import json
from datetime import date
from pathlib import Path

import pandas as pd

from app.portfolio.asset_classes import ASSET_CLASSES, CLES
from app.portfolio.quant_engine import covariance_ledoit_wolf, fetch_returns

PERIOD = "10y"
OUTPUT = Path(__file__).resolve().parent.parent / "app" / "portfolio" / "data" / "asset_class_stats.json"


def _serie_rendements_classe(proxys: tuple[str, ...], period: str) -> pd.Series:
    """Moyenne équipondérée des rendements des proxys d'une classe (colonnes alignées)."""
    returns = fetch_returns(list(proxys), period=period)  # colonnes triées alpha., converties EUR
    return returns.mean(axis=1)


def main() -> None:
    series = {}
    for ac in ASSET_CLASSES:
        print(f"→ {ac.nom} ({', '.join(ac.proxys)})")
        series[ac.cle] = _serie_rendements_classe(ac.proxys, PERIOD)

    # Alignement de toutes les classes sur les dates communes.
    df = pd.concat(series, axis=1).dropna()
    df = df[list(CLES)]  # ordre canonique

    mu = (df.mean() * 252).values
    cov, shrink = covariance_ledoit_wolf(df)

    snapshot = {
        "as_of": date.today().isoformat(),
        "period": PERIOD,
        "source": "yfinance (proxys UCITS moyennés par classe, convertis EUR)",
        "ledoit_wolf_shrinkage": round(float(shrink), 4),
        "cles": list(CLES),
        "mu": [round(float(x), 6) for x in mu],
        "cov": [[round(float(x), 8) for x in row] for row in cov],
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✔ Snapshot écrit : {OUTPUT}  ({len(df)} jours, shrinkage={shrink:.3f})")


if __name__ == "__main__":
    main()
