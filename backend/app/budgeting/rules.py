"""Constantes du modèle de répartition budgétaire (cf. document d'architecture, section 10.4).

Coefficients recalibrés sur des ordres de grandeur français réalistes. L'alimentation
était surévaluée (450 €/personne et 35 % du disponible), ce qui comprimait mécaniquement
l'épargne, réduite à un simple résidu. Elle passe à 330 €/personne / 30 %, et les postes
discrétionnaires (loisirs, imprévus) sont légèrement resserrés. Ces valeurs restent des
heuristiques par défaut, ajustables — pas un conseil budgétaire personnalisé.
"""

from .models import Objectif, Priorite

# --- Catégories plafonnées (besoins de base) ---
# poids: part du Disponible ; plafond: montant max par habitant (ou par enfant)
CATEGORIES_PLAFONNEES = {
    "alimentation": {"poids": 0.30, "plafond_par_hab": 330.0, "priorite": Priorite.ESSENTIEL},
    "transport": {"poids": 0.15, "plafond_par_hab": 250.0, "priorite": Priorite.SEMI_ESSENTIEL},
    "vetements": {"poids": 0.07, "plafond_par_hab": 110.0, "priorite": Priorite.SEMI_ESSENTIEL},
    "sante": {"poids": 0.05, "plafond_par_hab": 100.0, "priorite": Priorite.ESSENTIEL},
    "enfants": {"poids": 0.12, "plafond_par_enfant": 220.0, "priorite": Priorite.ESSENTIEL},
}

# --- Catégories élastiques (dégressives par palier, jamais plafonnées) ---
# poids_plein s'applique jusqu'au seuil (en €/hab), poids_reduit au-delà
SEUIL_DEGRESSIVITE_PAR_HAB = 3000.0

CATEGORIES_ELASTIQUES = {
    "loisirs": {"poids_plein": 0.13, "poids_reduit": 0.06, "priorite": Priorite.DISCRETIONNAIRE},
    "imprevus": {"poids_plein": 0.09, "poids_reduit": 0.04, "priorite": Priorite.DISCRETIONNAIRE},
}

# --- Taux d'épargne de référence par tranche de Disponible/hab ---
TRANCHES_EPARGNE_REFERENCE = [
    (0, 500, 0.05),
    (500, 1000, 0.12),
    (1000, 3000, 0.20),
    (3000, 5000, 0.35),
    (5000, float("inf"), 0.50),
]

MODIFICATEURS_OBJECTIF = {
    Objectif.DESENDETTEMENT: -0.05,
    Objectif.MATELAS_SECURITE: 0.10,
    Objectif.RETRAITE_LONG_TERME: 0.05,
    Objectif.MOYEN_TERME: 0.0,
    Objectif.AUCUN: 0.0,
}

TAUX_EPARGNE_MIN = 0.05
TAUX_EPARGNE_MAX = 0.70

REDUCTION_MAX_SEMI_ESSENTIEL = 0.30  # -30% max sur transport/vêtements
