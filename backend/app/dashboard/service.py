"""Construit le dashboard : budget recalculé à chaud, croisé avec les dépenses réelles.

Recalculer via le moteur (plutôt que relire le snapshot figé à l'onboarding) garantit
que le dashboard reste cohérent si les règles de calcul évoluent, sans migration de
données nécessaire.
"""

import calendar
from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.budgeting.engine import calculer_budget
from app.budgeting.models import Objectif, ProfilFoyer, ResultatBudget
from app.dashboard.schemas import CategorieBudgetStatus, DashboardResponse
from app.db.models import ExpenseEntry, FixedExpense, Income, Profile, User, VariableExpenseCategory


def _bornes_mois(mois: str | None) -> tuple[date, date, str]:
    """Renvoie (début inclus, fin exclue, libellé 'YYYY-MM') pour le mois demandé,
    ou le mois courant si non précisé."""
    if mois is None:
        today = date.today()
        annee, mois_num = today.year, today.month
    else:
        try:
            annee_str, mois_str = mois.split("-")
            annee, mois_num = int(annee_str), int(mois_str)
            if not (1 <= mois_num <= 12):
                raise ValueError
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Le paramètre 'mois' doit être au format YYYY-MM (ex: 2026-08)",
            )

    debut = date(annee, mois_num, 1)
    dernier_jour = calendar.monthrange(annee, mois_num)[1]
    fin_exclue = date(annee, mois_num, dernier_jour) + timedelta(days=1)
    return debut, fin_exclue, f"{annee:04d}-{mois_num:02d}"


def situation_mois(
    db: Session, user: User, mois: str | None = None
) -> tuple[ResultatBudget, list[CategorieBudgetStatus], str]:
    """Calcule la situation budgétaire (recommandé/réalisé par catégorie) pour un mois donné.

    Fonction réutilisable : le dashboard l'utilise directement, et le module reports
    s'appuie dessus pour bâtir les bilans mensuels/trimestriels — évite de dupliquer
    cette logique entre les deux modules.
    """
    profile = db.scalar(select(Profile).where(Profile.user_id == user.id))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun profil trouvé — complétez d'abord l'onboarding (POST /v1/onboarding).",
        )

    debut, fin_exclue, periode_label = _bornes_mois(mois)

    incomes = db.scalars(select(Income).where(Income.user_id == user.id)).all()
    charges = db.scalars(select(FixedExpense).where(FixedExpense.user_id == user.id)).all()

    profil_foyer = ProfilFoyer(
        revenus_total=sum(r.montant for r in incomes),
        charges_fixes_total=sum(c.montant for c in charges),
        nb_personnes=profile.nb_personnes,
        nb_enfants=profile.nb_enfants,
        objectif=Objectif(profile.objectif),
        matelas_securite_atteint=profile.matelas_securite_atteint,
    )
    resultat = calculer_budget(profil_foyer)

    categories_db = db.scalars(
        select(VariableExpenseCategory).where(VariableExpenseCategory.user_id == user.id)
    ).all()
    id_par_libelle = {c.libelle: c.id for c in categories_db}

    categories_status = []
    for libelle, montant_recommande in resultat.montants_categories.items():
        category_id = id_par_libelle.get(libelle)
        montant_realise = 0.0
        if category_id is not None:
            montant_realise = db.scalar(
                select(func.coalesce(func.sum(ExpenseEntry.montant), 0.0)).where(
                    ExpenseEntry.category_id == category_id,
                    ExpenseEntry.date_operation >= debut,
                    ExpenseEntry.date_operation < fin_exclue,
                )
            )
        categories_status.append(
            CategorieBudgetStatus(
                libelle=libelle,
                montant_recommande=montant_recommande,
                montant_realise=montant_realise,
                ecart=round(montant_recommande - montant_realise, 2),
            )
        )

    return resultat, categories_status, periode_label


def get_dashboard(db: Session, user: User, mois: str | None = None) -> DashboardResponse:
    resultat, categories_status, periode_label = situation_mois(db, user, mois)

    return DashboardResponse(
        periode=periode_label,
        disponible=resultat.disponible,
        categories=categories_status,
        epargne_potentielle=resultat.epargne_potentielle,
        epargne_reference_taux=resultat.epargne_reference_taux,
        epargne_reference_montant=resultat.epargne_reference_montant,
    )
