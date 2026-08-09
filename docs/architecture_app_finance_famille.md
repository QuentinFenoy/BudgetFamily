# Architecture — App d'optimisation financière pour familles

**Statut** : Document de cadrage v1
**Auteur** : Quentin
**Date** : Août 2026

---

## 1. Vision produit

Une application mobile (Flutter) qui aide les familles et la classe moyenne à :
- structurer leur budget à partir de leurs revenus et charges fixes,
- obtenir une répartition recommandée pour leurs dépenses variables,
- visualiser leur potentiel d'épargne,
- comprendre où orienter cette épargne (version gratuite : pédagogique par grandes classes d'actifs ; version payante : simulation avancée via moteur d'optimisation propriétaire),
- suivre leur situation dans le temps via des bilans périodiques.

**Positionnement** : outil de pilotage budgétaire et de simulation pédagogique — **pas** un service de conseil en investissement financier (CIF) réglementé. Ce choix structure l'ensemble du produit (cf. section 8).

**Double objectif du projet** : générer un revenu réel via abonnement, et constituer une vitrine de compétences (produit, architecture, quant) pour une reconversion vers la gestion de projets innovation.

---

## 2. Parcours utilisateur

### 2.1 Onboarding (à l'installation)
1. Objectif principal recherché (épargner pour un projet, préparer la retraite, se désendetter, construire un matelas de sécurité, optimiser sans objectif précis)
2. Situation familiale (célibataire, couple, enfants à charge — nombre et âge)
3. Âge de l'utilisateur (et du conjoint le cas échéant)
4. Revenus fixes (salaire net, autres revenus récurrents)
5. Revenus variables (primes, freelance, etc.) — moyenne mensuelle estimée
6. Charges fixes (loyer/crédit, assurances, abonnements, crédits en cours)
7. Tolérance au risque perçue (échelle simple, ex. 1 à 5) — utile pour la partie épargne/placement
8. Horizon de temps pour l'objectif principal

À l'issue de l'onboarding : un premier profil budgétaire est généré, avec une répartition suggérée des dépenses variables et une estimation du potentiel d'épargne mensuel.

### 2.2 Usage courant (gratuit)
- Saisie manuelle des dépenses par catégorie (variable) — formulaire rapide, catégories prédéfinies + personnalisables
- Tableau de bord : réalisé vs. recommandé par catégorie
- Alerte simple en cas de dépassement
- Estimation du potentiel d'épargne mensuel actualisée
- Contenu pédagogique générique sur les grandes classes d'actifs (Livret A/LDDS, PEA, assurance-vie, PER...) associées à des profils types (horizon + tolérance au risque), **sans recommandation nominative**

### 2.3 Usage avancé (payant)
- Moteur d'optimisation d'allocation d'épargne (réutilisation du framework quant existant — Black-Litterman, HRP, Risk Parity — adapté en simulateur par classes d'actifs génériques, pas par tickers)
- Simulations de scénarios ("si j'épargne X€/mois pendant Y ans avec un profil Z, projection de trajectoire")
- Comparaison de plusieurs stratégies d'allocation dans le temps
- **Bilan périodique avancé** : analyse de tendances multi-mois/trimestres, décomposition des écarts par catégorie, comparaison à la moyenne des mois précédents, projections de trajectoire d'épargne, export PDF du bilan

---

## 3. Fonctionnalités détaillées par palier

| Fonctionnalité | Gratuit | Payant |
|---|---|---|
| Onboarding profil | ✅ | ✅ |
| Saisie manuelle des dépenses | ✅ | ✅ |
| Répartition budgétaire recommandée | ✅ (règle pondérée par profil) | ✅ |
| Potentiel d'épargne | ✅ (calcul simple) | ✅ (avec projections) |
| Recommandation de virement automatique (pay yourself first) | ✅ | ✅ |
| Ajustement forcé de l'épargne (priorisation des catégories) | ✅ | ✅ |
| Contenu pédagogique placements | ✅ (générique) | ✅ |
| Simulateur d'allocation avancé (moteur quant) | ❌ | ✅ |
| Bilan mensuel simple | ✅ | ✅ |
| Bilan trimestriel avancé + tendances + export | ❌ | ✅ |
| Objectifs multiples suivis en parallèle | ❌ (1 seul) | ✅ (illimité) |

---

## 4. Architecture technique

### 4.1 Vue d'ensemble

```
┌─────────────────────┐         ┌──────────────────────┐
│   App Flutter        │◄───────►│   Backend API          │
│   (iOS/Android)       │  HTTPS  │   FastAPI (Python)     │
│                       │  REST   │                        │
└─────────────────────┘         └──────────┬───────────┘
                                            │
                        ┌───────────────────┼───────────────────┐
                        │                   │                   │
                ┌───────▼──────┐   ┌────────▼────────┐  ┌───────▼───────┐
                │ PostgreSQL    │   │ Moteur quant     │  │ Stripe /      │
                │ (données      │   │ (module Python,  │  │ RevenueCat    │
                │ utilisateur)  │   │ réutilise         │  │ (abonnements) │
                │               │   │ QuantFolio v2)    │  │               │
                └───────────────┘   └──────────────────┘  └───────────────┘
```

### 4.2 Frontend — Flutter
- Architecture propre (ex. Clean Architecture ou MVVM avec Riverpod/Bloc pour la gestion d'état — à trancher selon ta préférence, tu as déjà de l'expérience avec Flutter)
- Stockage local léger pour le cache (dernier état du dashboard, mode hors-ligne partiel)
- Pas de logique métier lourde côté client : la répartition budgétaire et l'optimisation sont calculées côté serveur, l'app affiche et collecte

### 4.3 Backend — FastAPI (Python)
- Endpoints REST versionnés (`/v1/...`)
- Authentification JWT (email/mot de passe au MVP ; option OAuth Google/Apple ensuite)
- Séparation claire des modules :
  - `budgeting/` — logique de répartition des dépenses variables
  - `savings/` — calcul du potentiel d'épargne
  - `optimizer/` — wrapper autour de QuantFolio v2, adapté en entrée profil (pas tickers)
  - `reports/` — génération des bilans périodiques
  - `billing/` — intégration Stripe/RevenueCat, gestion des accès par palier
- Le moteur d'optimisation reste **propriétaire côté serveur** — jamais exposé en clair au client, ce qui protège ton travail quant et sécurise la monétisation

### 4.4 Base de données — PostgreSQL
Choix justifié par la structure relationnelle claire des données (utilisateur → revenus/charges → catégories → historique de saisies → bilans) et la fiabilité pour des données financières sensibles.

### 4.5 Paiement
- RevenueCat recommandé pour simplifier la gestion cross-plateforme des abonnements in-app (iOS/Android), avec Stripe en backend si besoin d'une offre web complémentaire plus tard

### 4.6 Sécurité & conformité RGPD
- Chiffrement des données sensibles au repos (colonnes revenus/charges) et en transit (TLS)
- Minimisation des données : pas de connexion bancaire en V1 = surface de risque réduite
- Politique de confidentialité claire, consentement explicite au traitement, droit à l'export/suppression des données
- Hébergement UE (obligatoire vu la nature des données)

---

## 5. Modèle de données (schéma logique)

| Entité | Champs clés | Relations |
|---|---|---|
| `User` | id, email, password_hash, created_at, subscription_tier | 1—1 `Profile`, 1—N `SavingsGoal` |
| `Profile` | user_id, age, situation_familiale, nb_enfants, tolerance_risque, horizon | appartient à `User` |
| `Income` | id, user_id, type (fixe/variable), libellé, montant, fréquence | appartient à `User` |
| `FixedExpense` | id, user_id, libellé, montant, catégorie | appartient à `User` |
| `VariableExpenseCategory` | id, user_id, libellé, montant_recommandé, montant_réalisé (par mois) | appartient à `User` |
| `ExpenseEntry` | id, category_id, montant, date | appartient à `VariableExpenseCategory` |
| `SavingsGoal` | id, user_id, libellé, montant_cible, horizon, profil_risque | appartient à `User` |
| `AllocationSimulation` | id, user_id, goal_id, stratégie (BL/HRP/RiskParity), résultat_json, date | appartient à `SavingsGoal` (payant uniquement) |
| `PeriodicReport` | id, user_id, période (mois/trimestre), contenu_json, généré_le | appartient à `User` |
| `Subscription` | user_id, tier, statut, date_début, date_fin, provider_ref | 1—1 `User` |

---

## 6. Endpoints API principaux (aperçu)

```
POST   /v1/auth/register
POST   /v1/auth/login

POST   /v1/onboarding          # crée profil + revenus + charges initiales
GET    /v1/dashboard           # vue d'ensemble budget courant

POST   /v1/expenses            # ajoute une dépense
GET    /v1/expenses/categories # répartition recommandée vs réalisée

GET    /v1/savings/potential   # calcul potentiel d'épargne

POST   /v1/savings/goals       # créer un objectif
GET    /v1/savings/goals/{id}/simulation   # [payant] lance le moteur d'optimisation

GET    /v1/reports/monthly
GET    /v1/reports/quarterly   # [payant] version avancée

GET    /v1/billing/status
POST   /v1/billing/webhook     # callback RevenueCat/Stripe
```

---

## 7. Roadmap proposée

**Phase 1 — MVP gratuit**
Onboarding, saisie manuelle, répartition budgétaire de base, potentiel d'épargne simple, contenu pédagogique statique.

**Phase 2 — Bilans**
Bilan mensuel automatisé, historique, visualisations.

**Phase 3 — Palier payant**
Intégration du moteur d'optimisation (adaptation de QuantFolio v2 en simulateur par classes d'actifs), bilan trimestriel avancé, abonnement.

**Phase 4 — Itération**
Objectifs multiples, affinement des règles de répartition (apprentissage des habitudes de l'utilisateur), éventuellement connexion bancaire si le produit valide sa traction.

---

## 8. Cadre réglementaire — points de vigilance

- Le simulateur d'allocation doit rester **par classes d'actifs génériques** (ex. "actions monde / obligations / fonds euro / or"), jamais par instrument nominatif (pas de ticker, pas de nom de produit précis conseillé à l'utilisateur).
- Disclaimer visible sur toutes les vues de simulation : outil à but pédagogique et de simulation, ne constitue pas un conseil en investissement financier au sens de l'AMF.
- Aucune vente ou mise en relation avec un produit financier précis dans la V1 (pas d'affiliation courtier/assureur) pour éviter toute ambiguïté avec le statut de CIF ou de courtier (COBSP/IOBSP).
- À réévaluer si le produit évolue vers de la recommandation nominative : nécessiterait un statut ORIAS et probablement un partenariat avec un acteur déjà agréé.

---

## 9. Points ouverts à trancher avant le développement

1. Gestion d'état Flutter : Riverpod ou Bloc ?
2. Authentification : email/mot de passe seul au MVP, ou OAuth dès le départ ?
3. Catégories de dépenses variables : liste prédéfinie fixe ou personnalisable dès la V1 ?
4. Modèle de règle de répartition budgétaire par défaut (avant tout apprentissage) : quelle formule de départ ?

---

## 10. Décisions arrêtées

### 10.1 Gestion d'état Flutter
**Riverpod**, retenu pour la légèreté du boilerplate et l'adéquation avec un projet solo dont la logique métier est majoritairement déportée côté backend.

### 10.2 Authentification
Email/mot de passe au MVP. OAuth (Google/Apple) envisageable en itération ultérieure, non bloquant pour le lancement.

### 10.3 Catégories de dépenses variables
Liste fixe et prédéfinie en V1 (pas de création libre de catégories par l'utilisateur). Les **montants recommandés par catégorie restent personnalisables** : l'utilisateur peut forcer une catégorie à 0 (ex. transport pris en charge par l'employeur), auquel cas le montant correspondant est redistribué proportionnellement sur les autres catégories plutôt que simplement retiré de l'enveloppe.

### 10.4 Règle de répartition budgétaire par défaut (modèle bottom-up, par tranche de revenu/habitant)

Le modèle initial calculait d'abord un taux d'épargne cible, puis répartissait les catégories sur ce qu'il restait — ce qui couple artificiellement le budget "besoins" au taux d'épargne choisi. Or le produit promet de calculer un **potentiel d'épargne**, pas d'imposer un objectif a priori. L'épargne doit donc être un **résultat** (ce qui reste une fois les besoins couverts), pas une contrainte de départ qui détermine l'enveloppe variable. Le modèle est refondu en conséquence, en gardant la logique par tranche + plafonds absolus pour éviter la dérive proportionnelle en haut de distribution (loi d'Engel).

**Étage 1 — Calcul du disponible par habitant**

```
Disponible = Revenus totaux − Charges fixes
Disponible_par_hab = Disponible / Nb_personnes_du_foyer
```

*Note d'évolution : raffinement possible en unités de consommation (échelle INSEE) en Phase 4.*

**Étage 2 — Calcul des catégories de dépenses variables directement sur le Disponible**

Poids de base et plafonds absolus par habitant, appliqués directement sur le Disponible (pas sur un reliquat post-épargne) :

| Catégorie | Poids de base | Plafond absolu | Élastique ? |
|---|---|---|---|
| Alimentation | 35% | 450€/hab/mois | Non (plafonnée) |
| Transport (hors charges fixes) | 15% | 250€/hab/mois | Non (plafonnée) |
| Vêtements | 8% | 120€/hab/mois | Non (plafonnée) |
| Santé (hors mutuelle) | 5% | 100€/hab/mois | Non (plafonnée) |
| Enfants / activités | 12% (0% si pas d'enfants) | 200€/enfant/mois | Non (plafonnée) |
| Loisirs / sorties | 15% jusqu'à 3000€/hab, puis 7% au-delà | — | Oui (dégressive) |
| Imprévus / divers | 10% jusqu'à 3000€/hab, puis 4% au-delà | — | Oui (dégressive) |

```
montant_catégorie = min(poids_base × Disponible, plafond × nb_personnes_concernées)   [catégories plafonnées]

# catégories élastiques (Loisirs, Imprévus), par tranche de Disponible_par_hab :
montant_catégorie = poids_plein × min(Disponible_par_hab, 3000) × nb_personnes
                   + poids_réduit × max(Disponible_par_hab − 3000, 0) × nb_personnes
```

Cette dégressivité évite qu'à très haut revenu (50 000€/mois par exemple), Loisirs et Imprévus ne croissent de façon strictement linéaire et infinie — le taux marginal diminue au-delà d'un certain niveau de vie déjà confortable, un peu comme un barème progressif.

**Étage 3 — L'épargne comme résidu, comparée à une cible de référence**

```
Épargne_potentielle = Disponible − Σ(montant_catégorie)
```

Cette épargne potentielle est ensuite comparée à un **taux cible de référence**, déterminé par tranche de revenu/habitant et modulé par l'objectif déclaré — non plus pour contraindre le calcul, mais pour générer une recommandation :

| Tranche (Disponible/hab/mois) | Taux d'épargne de référence |
|---|---|
| < 500€ | 5% |
| 500 – 1000€ | 12% |
| 1000 – 3000€ | 20% |
| 3000 – 5000€ | 35% |
| > 5000€ | 50% |

Modulation selon l'objectif (points ajoutés à la référence, bornés entre 5% et 70%) :

| Objectif | Modificateur |
|---|---|
| Désendettement prioritaire | −5 pts |
| Matelas de sécurité (tant que < 3 mois de charges fixes accumulées) | +10 pts |
| Retraite / projet long terme (horizon > 7 ans) | +5 pts |
| Projet à moyen terme (horizon 2–7 ans) | +0 pt |
| Pas d'objectif précis | +0 pt |

**Logique de recommandation** :
- Si `Épargne_potentielle < Épargne_référence` : l'app peut suggérer de comprimer les catégories élastiques (Loisirs, Imprévus) pour se rapprocher de la cible, avec un message explicite plutôt qu'une contrainte imposée.
- Si `Épargne_potentielle ≥ Épargne_référence` : message positif ; l'app peut suggérer d'augmenter l'objectif d'épargne ou d'orienter le surplus vers le simulateur d'allocation (fonctionnalité payante).

Exemple : célibataire, Disponible = 10 000€/mois, logement payé → catégories plafonnées ≈ 920€ (alimentation 450 + transport 250 + vêtements 120 + santé 100), Loisirs = 15%×3000 + 7%×7000 = 940€, Imprévus = 10%×3000 + 4%×7000 = 580€ → Épargne_potentielle ≈ 7 560€ (75,6%), largement au-dessus de la référence de 50-55% pour cette tranche. Cohérent avec l'intuition de départ, et la dégressivité renforce encore le résultat sans intervention manuelle.

**Étage 4 — Ajustement forcé de l'épargne (priorisation des catégories)**

Lorsque l'utilisateur (ou l'objectif choisi à l'onboarding) fixe une cible d'épargne supérieure à l'Épargne_potentielle calculée, l'algorithme réduit les catégories dans l'ordre de priorité suivant, jamais les catégories essentielles :

| Niveau | Catégories | Réductible ? |
|---|---|---|
| 1 — Essentiel | Alimentation, Santé, Enfants/activités | Non, jamais réduit automatiquement |
| 2 — Semi-essentiel | Transport, Vêtements | Réductible jusqu'à −30% du montant calculé |
| 3 — Discrétionnaire | Loisirs, Imprévus | Réductible jusqu'à 0 |

```
Écart = Épargne_cible_forcée − Épargne_potentielle
# 1. Réduire proportionnellement le niveau 3 jusqu'à combler l'écart ou atteindre 0
# 2. Si écart résiduel : réduire proportionnellement le niveau 2, jusqu'à −30% max
# 3. Si écart encore résiduel : ne pas toucher au niveau 1 — informer l'utilisateur
#    que la cible n'est pas atteignable sans réduire les besoins essentiels
```

**Recommandation de virement automatique ("pay yourself first")**

Une fois l'épargne calculée (potentielle ou forcée), l'application recommande explicitement à l'utilisateur de mettre en place un **virement permanent** du montant d'épargne vers un compte dédié, programmé en tout début de mois — avant les dépenses variables plutôt qu'après. Ce principe de finance comportementale limite le risque que l'épargne devienne la variable d'ajustement résiduelle en fin de mois (souvent proche de zéro en pratique). En V1 (pas de connexion bancaire), cette recommandation reste **déclarative et pédagogique** : l'app affiche le montant conseillé et la date recommandée, avec un rappel/notification, mais n'exécute aucun virement — la mise en place reste manuelle par l'utilisateur dans son app bancaire.

**Ajustements complémentaires** :
- Un override utilisateur à 0 sur une catégorie plafonnée (ex. transport pris en charge par l'employeur) redistribue son montant proportionnellement sur les catégories élastiques (pas sur les autres catégories plafonnées, qui reflètent des besoins réels indépendants).
- Évolution possible en Phase 4 : plafonds ou dégressivité sur les catégories élastiques elles-mêmes pour éviter une croissance strictement linéaire aux revenus très élevés ; pondération apprise à partir de l'historique réel de l'utilisateur ; raffinement du "par habitant" en unités de consommation.
