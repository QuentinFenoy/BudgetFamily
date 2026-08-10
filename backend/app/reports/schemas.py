"""Schémas Pydantic des bilans périodiques (GET /v1/reports/monthly, /quarterly)."""

from pydantic import BaseModel

from app.dashboard.schemas import CategorieBudgetStatus


class BilanMensuel(BaseModel):
    """Bilan d'un mois donné : reprend la structure du dashboard, enrichie d'agrégats
    globaux (totaux, épargne réellement dégagée) utiles à un bilan plutôt qu'à un
    suivi au jour le jour."""

    periode: str  # "YYYY-MM"
    disponible: float
    categories: list[CategorieBudgetStatus]
    total_recommande: float
    total_realise: float
    epargne_potentielle: float  # théorique, calculée par le moteur (si le budget est bien suivi)
    epargne_realisee_estimee: float  # Disponible - total réellement dépensé ce mois
    epargne_reference_taux: float
    epargne_reference_montant: float
    ecart_epargne_vs_reference: float  # epargne_realisee_estimee - epargne_reference_montant


class TendanceMensuelle(BaseModel):
    """Point d'une série temporelle, pour la vue trimestrielle."""

    periode: str
    total_realise: float
    epargne_realisee_estimee: float


class BilanTrimestriel(BaseModel):
    """Bilan trimestriel avancé [payant] : 3 bilans mensuels + analyse de tendance."""

    mois: list[str]  # les 3 périodes couvertes, ordre chronologique croissant
    bilans: list[BilanMensuel]
    tendances: list[TendanceMensuelle]
    moyenne_totale_realisee: float  # moyenne des dépenses totales réalisées sur les 3 mois
    epargne_totale_trimestre: float  # somme des épargnes réalisées estimées sur les 3 mois
    ecart_mois_courant_vs_moyenne: float  # total_realise du dernier mois - moyenne_totale_realisee
