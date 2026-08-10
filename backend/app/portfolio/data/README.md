# Snapshot de statistiques par classe d'actifs

Ce dossier accueille `asset_class_stats.json`, produit par
`scripts/refresh_asset_class_stats.py` à partir des proxys réels (hors-ligne, réseau
requis). Tant qu'aucun snapshot n'est présent, l'API se rabat automatiquement sur les
hypothèses de marché long terme calibrées dans `app/portfolio/asset_classes.py`.

Le snapshot ne contient **que** des données agrégées par classe générique (clés,
vecteur de moyennes, matrice de covariance) — jamais de ticker.
