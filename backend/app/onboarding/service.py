"""Logique d'onboarding : persiste la situation du foyer puis calcule le premier budget.

Volontairement séparé du router (qui reste fin) : cette fonction est le point de jonction
entre le socle de persistance (app.db) et le moteur de calcul existant (app.budgeting).
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.budgeting.engine import calculer_budget
from app.budgeting.models import ProfilFoyer
from app.budgeting.schemas import ResultatBudgetResponse
from app.db.models import (
    FixedExpense,
    Income,
    Profile,
    User,
    VariableExpenseCategory,
)
from app.onboarding.schemas import OnboardingRequest, OnboardingResponse, ProfileSummary


def run_onboarding(db: Session, user: User, payload: OnboardingRequest) -> OnboardingResponse:
    # L'onboarding est un flux unique : un profil existant bloque l'opération.
    existing = db.scalar(select(Profile).where(Profile.user_id == user.id))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un profil existe déjà pour cet utilisateur",
        )

    revenus_total = sum(r.montant for r in payload.revenus)
    charges_total = sum(c.montant for c in payload.charges_fixes)

    # Construction du profil de calcul ; les incohérences déclenchent un 422 propre
    # plutôt qu'une 500 (double filet avec la validation Pydantic).
    try:
        profil = ProfilFoyer(
            revenus_total=revenus_total,
            charges_fixes_total=charges_total,
            nb_personnes=payload.nb_personnes,
            nb_enfants=payload.nb_enfants,
            objectif=payload.objectif,
            matelas_securite_atteint=payload.matelas_securite_atteint,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    resultat = calculer_budget(profil)

    profile_row = Profile(
        user_id=user.id,
        age=payload.age,
        situation_familiale=payload.situation_familiale,
        nb_personnes=payload.nb_personnes,
        nb_enfants=payload.nb_enfants,
        objectif=payload.objectif.value,
        tolerance_risque=payload.tolerance_risque,
        horizon_annees=payload.horizon_annees,
        matelas_securite_atteint=payload.matelas_securite_atteint,
    )
    db.add(profile_row)

    for r in payload.revenus:
        db.add(
            Income(
                user_id=user.id,
                type=r.type,
                libelle=r.libelle,
                montant=r.montant,
                frequence=r.frequence,
            )
        )
    for c in payload.charges_fixes:
        db.add(
            FixedExpense(
                user_id=user.id, libelle=c.libelle, montant=c.montant, categorie=c.categorie
            )
        )
    # On matérialise les montants recommandés par catégorie : ils serviront de référence
    # au dashboard (réalisé vs recommandé) dans l'incrément suivant.
    for nom, montant in resultat.montants_categories.items():
        db.add(VariableExpenseCategory(user_id=user.id, libelle=nom, montant_recommande=montant))

    db.commit()
    db.refresh(profile_row)

    return OnboardingResponse(
        profile=ProfileSummary.model_validate(profile_row),
        budget=ResultatBudgetResponse(**resultat.__dict__),
    )
