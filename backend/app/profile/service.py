"""Lecture et mise à jour du profil.

Point délicat de la mise à jour : les catégories de dépense (VariableExpenseCategory)
portent les dépenses saisies (ExpenseEntry) via une relation en cascade. On met donc à
jour les montants recommandés EN PLACE (par libellé) au lieu de supprimer/recréer les
catégories, pour ne pas effacer les dépenses de l'utilisateur. Le moteur produisant
toujours le même jeu de catégories, un simple upsert par libellé suffit.

Recalculer ici réapplique aussi la formule courante au profil existant.
"""

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.budgeting.engine import calculer_budget
from app.budgeting.models import ProfilFoyer
from app.budgeting.schemas import ResultatBudgetResponse
from app.db.models import FixedExpense, Income, Profile, User, VariableExpenseCategory
from app.onboarding.schemas import OnboardingRequest, OnboardingResponse, ProfileSummary
from app.profile.schemas import FixedExpenseItemOut, IncomeItemOut, ProfileDetailResponse


def _profil_ou_404(db: Session, user: User) -> Profile:
    profile = db.scalar(select(Profile).where(Profile.user_id == user.id))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun profil — complétez d'abord l'onboarding (POST /v1/onboarding).",
        )
    return profile


def get_profile_detail(db: Session, user: User) -> ProfileDetailResponse:
    profile = _profil_ou_404(db, user)
    revenus = db.scalars(select(Income).where(Income.user_id == user.id)).all()
    charges = db.scalars(select(FixedExpense).where(FixedExpense.user_id == user.id)).all()

    return ProfileDetailResponse(
        id=profile.id,
        nb_personnes=profile.nb_personnes,
        nb_enfants=profile.nb_enfants,
        situation_familiale=profile.situation_familiale,
        age=profile.age,
        objectif=profile.objectif,
        tolerance_risque=profile.tolerance_risque,
        horizon_annees=profile.horizon_annees,
        matelas_securite_atteint=profile.matelas_securite_atteint,
        revenus=[
            IncomeItemOut(type=r.type, libelle=r.libelle, montant=r.montant, frequence=r.frequence)
            for r in revenus
        ],
        charges_fixes=[
            FixedExpenseItemOut(libelle=c.libelle, montant=c.montant, categorie=c.categorie)
            for c in charges
        ],
    )


def update_profile(db: Session, user: User, payload: OnboardingRequest) -> OnboardingResponse:
    profile = _profil_ou_404(db, user)

    revenus_total = sum(r.montant for r in payload.revenus)
    charges_total = sum(c.montant for c in payload.charges_fixes)

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

    # Profil : mise à jour en place.
    profile.age = payload.age
    profile.situation_familiale = payload.situation_familiale
    profile.nb_personnes = payload.nb_personnes
    profile.nb_enfants = payload.nb_enfants
    profile.objectif = payload.objectif.value
    profile.tolerance_risque = payload.tolerance_risque
    profile.horizon_annees = payload.horizon_annees
    profile.matelas_securite_atteint = payload.matelas_securite_atteint

    # Revenus et charges : aucune dépendance -> remplacement franc.
    db.execute(delete(Income).where(Income.user_id == user.id))
    db.execute(delete(FixedExpense).where(FixedExpense.user_id == user.id))
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

    # Catégories : upsert par libellé pour PRÉSERVER les dépenses déjà saisies.
    existantes = {
        c.libelle: c
        for c in db.scalars(
            select(VariableExpenseCategory).where(VariableExpenseCategory.user_id == user.id)
        )
    }
    for nom, montant in resultat.montants_categories.items():
        if nom in existantes:
            existantes[nom].montant_recommande = montant
        else:
            db.add(VariableExpenseCategory(user_id=user.id, libelle=nom, montant_recommande=montant))

    db.commit()
    db.refresh(profile)

    return OnboardingResponse(
        profile=ProfileSummary.model_validate(profile),
        budget=ResultatBudgetResponse(**resultat.__dict__),
    )
