# Déploiement — Neon (base) + Render (backend)

Backend FastAPI sur **Render** (offre gratuite), base **PostgreSQL sur Neon**
(gratuit permanent). Les deux en région Francfort (UE).

## 1. Base de données — Neon
1. Créer un compte sur neon.tech (région **EU / Frankfurt**), sans carte bancaire.
2. Créer un projet : une base PostgreSQL est provisionnée.
3. Copier la **connection string** (`postgresql://user:pass@host/db`).

## 2. Backend — Render
1. Pousser le dépôt sur GitHub.
2. Sur render.com : **New > Blueprint**, sélectionner le dépôt (Render lit `render.yaml`).
3. Renseigner la variable **`DATABASE_URL`** = la connection string Neon.
   `JWT_SECRET_KEY` et `BILLING_WEBHOOK_SECRET` sont générés automatiquement.
4. Déployer. Le `startCommand` applique les migrations Alembic puis lance l'API.
5. Vérifier : ouvrir `https://<service>.onrender.com/health` → `{"status":"ok"}`.

## 3. Application mobile
Pointer l'app Flutter sur l'API déployée :
```
flutter run --dart-define=API_BASE_URL=https://<service>.onrender.com/v1
```

## Bon à savoir
- **Sécurité** : l'app refuse de démarrer en production si un secret est resté sur sa
  valeur de développement (garde-fou dans `app/core/config.py`).
- **Cold start** : sur l'offre gratuite Render, la première requête après ~15 min
  d'inactivité peut prendre 30-60 s (réveil du service). Normal à ce stade.
- **Sauvegardes** : limitées sur les offres gratuites. Avant d'avoir de vrais
  utilisateurs payants, prévoir un petit palier payant pour la base (sauvegardes fiables).
- **Bande passante** : surveiller les dépassements côté Render (facturables même en gratuit).
