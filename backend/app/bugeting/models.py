"""Modèles de données pour le module de répartition budgétaire."""

from dataclasses import dataclass, field
from enum import Enum


class Objectif(str, Enum):
    DESENDETTEMENT = "desendettement"
    MATELAS_SECURITE = "matelas_securite"
    RETRAITE_LONG_TERME = "retraite_long_terme"
    MOYEN_TERME = "moyen_terme"
    AUCUN = "aucun"


class Priorite(str, Enum):
    ESSENTIEL = "essentiel"          # jamais réduit automatiquement
    SEMI_ESSENTIEL = "semi_essentiel"  # réductible jusqu'à -30%
    DISCRETIONNAIRE = "discretionnaire"  # réductible jusqu'à 0


@dataclass
class ProfilFoyer:
    """Situation déclarée à l'onboarding, nécessaire au calcul."""
    revenus_total: float          # revenus fixes + variables moyens, mensuels
    charges_fixes_total: float    # loyer/crédit, assurances, abonnements, etc.
    nb_personnes: int             # nombre total d'habitants du foyer (adultes + enfants)
    nb_enfants: int = 0
    objectif: Objectif = Objectif.AUCUN
    matelas_securite_atteint: bool = False  # True si >= 3 mois de charges fixes déjà épargnés

    def __post_init__(self):
        if self.nb_personnes < 1:
            raise ValueError("nb_personnes doit être >= 1")
        if self.nb_enfants < 0 or self.nb_enfants > self.nb_personnes:
            raise ValueError("nb_enfants incohérent avec nb_personnes")


@dataclass
class ResultatBudget:
    """Sortie du calcul de répartition."""
    disponible: float
    disponible_par_hab: float
    montants_categories: dict = field(default_factory=dict)
    epargne_potentielle: float = 0.0
    epargne_reference_taux: float = 0.0
    epargne_reference_montant: float = 0.0
    ajustement_applique: bool = False
    ecart_non_couvert: float = 0.0  # > 0 si la cible forcée n'est pas atteignable
