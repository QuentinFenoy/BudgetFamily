"""Endpoints liés à la gestion des objectifs d'épargne."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser
from app.db.session import get_db
from app.savings.engine import repartir_epargne
from app.savings.models import ObjectifEpargne
from app.savings.planning_service import construire_plan_epargne
from app.savings.persistence_service import (
    create_goal,
    delete_goal,
    get_goal,
    list_goals,
    repartir_epargne_automatique,
    update_goal,
)
from app.savings.schemas import (
    AllocationObjectifResponse,
    PlanEpargneResponse,
    RepartitionAutoRequest,
    RepartitionEpargneRequest,
    ResultatRepartitionResponse,
    SavingsGoalCreate,
    SavingsGoalResponse,
    SavingsGoalUpdate,
)

router = APIRouter(prefix="/savings", tags=["savings"])


@router.post("/repartition", response_model=ResultatRepartitionResponse)
def calculate_repartition(payload: RepartitionEpargneRequest) -> ResultatRepartitionResponse:
    """Répartit un montant d'épargne disponible entre plusieurs objectifs fournis dans
    la requête (stateless, ne touche pas aux objectifs persistés)."""
    objectifs = [
        ObjectifEpargne(
            id=o.id,
            nom=o.nom,
            montant_cible=o.montant_cible,
            montant_actuel=o.montant_actuel,
            priorite=o.priorite,
        )
        for o in payload.objectifs
    ]
    resultat = repartir_epargne(objectifs, payload.epargne_disponible, methode=payload.methode)
    return ResultatRepartitionResponse(
        epargne_disponible=resultat.epargne_disponible,
        allocations=[AllocationObjectifResponse(**a.__dict__) for a in resultat.allocations],
        epargne_non_allouee=resultat.epargne_non_allouee,
    )


# ── Objectifs d'épargne persistés (CRUD) ─────────────────────────────────────────


@router.post("/goals", response_model=SavingsGoalResponse, status_code=status.HTTP_201_CREATED)
def create_savings_goal(
    payload: SavingsGoalCreate, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> SavingsGoalResponse:
    return create_goal(db, current_user, payload)


@router.get("/goals", response_model=list[SavingsGoalResponse])
def list_savings_goals(
    current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> list[SavingsGoalResponse]:
    return list_goals(db, current_user)


@router.get("/goals/{goal_id}", response_model=SavingsGoalResponse)
def get_savings_goal(
    goal_id: int, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> SavingsGoalResponse:
    return get_goal(db, current_user, goal_id)


@router.patch("/goals/{goal_id}", response_model=SavingsGoalResponse)
def update_savings_goal(
    goal_id: int,
    payload: SavingsGoalUpdate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> SavingsGoalResponse:
    return update_goal(db, current_user, goal_id, payload)


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_savings_goal(
    goal_id: int, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> None:
    delete_goal(db, current_user, goal_id)


@router.post("/repartition-auto", response_model=ResultatRepartitionResponse)
def repartition_automatique(
    payload: RepartitionAutoRequest,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> ResultatRepartitionResponse:
    """Comme /repartition, mais charge directement les objectifs persistés de
    l'utilisateur — pas besoin de les renvoyer intégralement à chaque appel."""
    return repartir_epargne_automatique(db, current_user, payload)


@router.get("/plan", response_model=PlanEpargneResponse)
def plan_epargne(
    current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> PlanEpargneResponse:
    """Plan d'épargne de l'utilisateur : la capacité d'épargne mensuelle (calculée par
    le budget) est répartie entre les objectifs selon leur priorité. Pour les comptes
    premium, chaque objectif reçoit en plus le rendement brut annuel requis pour tenir
    l'échéance, le risque associé (note /5 + volatilité), un verdict de faisabilité et
    les rendements nets indicatifs par enveloppe fiscale."""
    return construire_plan_epargne(db, current_user)
