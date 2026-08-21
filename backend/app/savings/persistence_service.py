"""Persistance des objectifs d'épargne (SavingsGoal) et pont vers le moteur pur.

Séparé de app.savings.engine à dessein : l'engine reste un module de calcul pur
(dataclasses en mémoire, aucune dépendance DB), testé indépendamment. Ce service
fait la conversion entre les lignes SavingsGoal persistées et les ObjectifEpargne
que le moteur attend, dans les deux sens.
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import SavingsGoal, User
from app.savings.engine import repartir_epargne
from app.savings.models import ObjectifEpargne
from app.savings.schemas import (
    AllocationObjectifResponse,
    RepartitionAutoRequest,
    ResultatRepartitionResponse,
    SavingsGoalCreate,
    SavingsGoalResponse,
    SavingsGoalUpdate,
)


def _to_response(goal: SavingsGoal) -> SavingsGoalResponse:
    montant_restant = max(round(goal.montant_cible - goal.montant_actuel, 2), 0.0)
    return SavingsGoalResponse(
        id=goal.id,
        libelle=goal.libelle,
        montant_cible=goal.montant_cible,
        montant_actuel=goal.montant_actuel,
        priorite=goal.priorite,
        horizon_mois=goal.horizon_mois,
        montant_restant=montant_restant,
        est_atteint=goal.montant_actuel >= goal.montant_cible,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )


def _get_owned_goal(db: Session, user: User, goal_id: int) -> SavingsGoal:
    goal = db.scalar(select(SavingsGoal).where(SavingsGoal.id == goal_id, SavingsGoal.user_id == user.id))
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Objectif d'épargne introuvable.")
    return goal


def create_goal(db: Session, user: User, payload: SavingsGoalCreate) -> SavingsGoalResponse:
    goal = SavingsGoal(
        user_id=user.id,
        libelle=payload.libelle,
        montant_cible=payload.montant_cible,
        montant_actuel=payload.montant_actuel,
        priorite=payload.priorite,
        horizon_mois=payload.horizon_mois,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return _to_response(goal)


def list_goals(db: Session, user: User) -> list[SavingsGoalResponse]:
    goals = db.scalars(
        select(SavingsGoal).where(SavingsGoal.user_id == user.id).order_by(SavingsGoal.priorite)
    ).all()
    return [_to_response(g) for g in goals]


def get_goal(db: Session, user: User, goal_id: int) -> SavingsGoalResponse:
    return _to_response(_get_owned_goal(db, user, goal_id))


def update_goal(db: Session, user: User, goal_id: int, payload: SavingsGoalUpdate) -> SavingsGoalResponse:
    goal = _get_owned_goal(db, user, goal_id)

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(goal, field, value)

    if goal.montant_actuel > goal.montant_cible:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="montant_actuel ne peut pas dépasser montant_cible.",
        )

    db.commit()
    db.refresh(goal)
    return _to_response(goal)


def delete_goal(db: Session, user: User, goal_id: int) -> None:
    goal = _get_owned_goal(db, user, goal_id)
    db.delete(goal)
    db.commit()


def repartir_epargne_automatique(
    db: Session, user: User, payload: RepartitionAutoRequest
) -> ResultatRepartitionResponse:
    """Charge les objectifs persistés de l'utilisateur et calcule la répartition
    dessus, sans que le client ait à les renvoyer intégralement à chaque appel
    (contrairement à POST /v1/savings/repartition, resté stateless)."""
    goals = db.scalars(select(SavingsGoal).where(SavingsGoal.user_id == user.id)).all()
    if not goals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun objectif d'épargne enregistré — créez-en un via POST /v1/savings/goals.",
        )

    objectifs = [
        ObjectifEpargne(
            id=str(g.id),
            nom=g.libelle,
            montant_cible=g.montant_cible,
            montant_actuel=g.montant_actuel,
            priorite=g.priorite,
        )
        for g in goals
    ]
    resultat = repartir_epargne(objectifs, payload.epargne_disponible, methode=payload.methode)

    return ResultatRepartitionResponse(
        epargne_disponible=resultat.epargne_disponible,
        allocations=[AllocationObjectifResponse(**a.__dict__) for a in resultat.allocations],
        epargne_non_allouee=resultat.epargne_non_allouee,
    )
