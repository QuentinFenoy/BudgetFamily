"""Modèles de données pour la gestion des objectifs d'épargne."""

from dataclasses import dataclass, field


@dataclass
class ObjectifEpargne:
    """Un objectif d'épargne déclaré par l'utilisateur (ex: fonds d'urgence, apport immobilier)."""
    id: str
    nom: str
    montant_cible: float
    montant_actuel: float = 0.0
    priorite: int = 1  # 1 = le plus prioritaire, utilisé par la méthode "cascade"

    def __post_init__(self):
        if self.montant_cible <= 0:
            raise ValueError("montant_cible doit être > 0")
        if self.montant_actuel < 0:
            raise ValueError("montant_actuel doit être >= 0")
        if self.priorite < 1:
            raise ValueError("priorite doit être >= 1")

    @property
    def montant_restant(self) -> float:
        return max(round(self.montant_cible - self.montant_actuel, 2), 0.0)

    @property
    def est_atteint(self) -> bool:
        return self.montant_actuel >= self.montant_cible


@dataclass
class AllocationObjectif:
    """Résultat de la répartition pour un objectif donné, pour le mois courant."""
    objectif_id: str
    montant_alloue_ce_mois: float
    mois_restants_estimes: float | None  # None si l'objectif ne recevra jamais assez pour être atteint


@dataclass
class ResultatRepartitionEpargne:
    epargne_disponible: float
    allocations: list[AllocationObjectif] = field(default_factory=list)
    epargne_non_allouee: float = 0.0  # reliquat si tous les objectifs actifs sont déjà couverts
