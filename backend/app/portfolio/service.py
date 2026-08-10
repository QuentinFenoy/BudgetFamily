"""Service d'allocation : contrôle d'accès, lecture du profil stocké, construction
de la réponse à partir du cœur d'allocation (app.portfolio.allocator).

Le profil est relu depuis la base (même approche que le dashboard), l'allocation est
calculée à chaud. Chaque simulation réussie est persistée dans AllocationSimulation
(historique consultable via list_simulations/get_simulation), sauf si l'appelant
passe explicitement save=False (ex. un aperçu que l'utilisateur ne veut pas garder).
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AllocationSimulation, Profile, SubscriptionTier, User
from app.portfolio.allocator import METHODES, construire_allocation
from app.portfolio.data_provider import load_asset_class_stats
from app.portfolio.schemas import (
    AllocationSimulationDetail,
    AllocationSimulationSummary,
    LigneAllocationResponse,
    PortfolioAllocationResponse,
)

_CATEGORIE_LABEL = {"croissance": "Croissance", "defensif": "Défensif"}

_AVERTISSEMENT = (
    "Information éducative fournie à titre indicatif, sur la base de classes d'actifs "
    "génériques. Ne constitue pas un conseil en investissement personnalisé ni une "
    "recommandation d'achat d'instruments financiers. Les rendements affichés sont des "
    "hypothèses de long terme, pas une garantie : les performances passées ne préjugent "
    "pas des performances futures et le capital investi peut être perdu. Consultez un "
    "conseiller financier agréé avant toute décision."
)


def get_allocation(
    db: Session,
    user: User,
    methode: str = "hrp",
    montant: float | None = None,
    save: bool = True,
) -> PortfolioAllocationResponse:
    # Fonctionnalité de conseil réservée à l'offre payante (cf. doc, sections 3 et 8).
    _verifier_acces_premium(user)

    if methode not in METHODES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Méthode inconnue : {methode!r} (attendu : {', '.join(METHODES)})",
        )

    profile = db.scalar(select(Profile).where(Profile.user_id == user.id))
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun profil trouvé — complétez d'abord l'onboarding (POST /v1/onboarding).",
        )

    stats = load_asset_class_stats()
    allocation = construire_allocation(
        stats=stats,
        tolerance_risque=profile.tolerance_risque,
        age=profile.age,
        horizon_annees=profile.horizon_annees,
        objectif=profile.objectif,
        methode=methode,
    )

    lignes = [
        LigneAllocationResponse(
            classe=ligne.nom,
            categorie=_CATEGORIE_LABEL.get(ligne.sleeve, ligne.sleeve),
            part=ligne.part,
            montant=round(ligne.part * montant, 2) if montant is not None else None,
        )
        for ligne in allocation.lignes
    ]

    hypotheses = (
        f"Rendements et volatilités estimés par classe d'actifs générique "
        f"({allocation.rendement_annuel_espere * 100:.1f}% de rendement annuel espéré, "
        f"{allocation.volatilite_annuelle_estimee * 100:.1f}% de volatilité). L'allocation "
        f"intra-classe suit la méthode {methode.upper()} (parité de risque), et la "
        f"répartition croissance/défensif découle de votre profil (risque, âge, horizon, objectif)."
    )

    resultat = PortfolioAllocationResponse(
        profil_risque=profile.tolerance_risque,
        age=profile.age,
        horizon_annees=profile.horizon_annees,
        objectif=profile.objectif,
        methode=methode,
        part_croissance=allocation.part_croissance,
        part_defensive=allocation.part_defensive,
        allocation=lignes,
        rendement_annuel_espere=allocation.rendement_annuel_espere,
        volatilite_annuelle_estimee=allocation.volatilite_annuelle_estimee,
        ratio_sharpe_estime=allocation.ratio_sharpe_estime,
        source_donnees=stats.source,
        hypotheses=hypotheses,
        avertissement=_AVERTISSEMENT,
    )

    if save:
        save_simulation(db, user, resultat, montant)

    return resultat


def _verifier_acces_premium(user: User) -> None:
    if user.subscription_tier != SubscriptionTier.PREMIUM.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cette fonctionnalité est réservée à l'offre payante.",
        )


def save_simulation(
    db: Session, user: User, resultat: PortfolioAllocationResponse, montant: float | None
) -> AllocationSimulation:
    """Enregistre un instantané de la simulation déjà calculée.

    Ne stocke que ce qui a déjà été renvoyé à l'utilisateur (classes génériques,
    jamais de ticker) — cf. AllocationSimulation dans app.db.models pour le détail
    de cet invariant.
    """
    simulation = AllocationSimulation(
        user_id=user.id,
        methode=resultat.methode,
        montant=montant,
        part_croissance=resultat.part_croissance,
        part_defensive=resultat.part_defensive,
        rendement_annuel_espere=resultat.rendement_annuel_espere,
        volatilite_annuelle_estimee=resultat.volatilite_annuelle_estimee,
        ratio_sharpe_estime=resultat.ratio_sharpe_estime,
        source_donnees=resultat.source_donnees,
        allocation_json=[ligne.model_dump() for ligne in resultat.allocation],
    )
    db.add(simulation)
    db.commit()
    db.refresh(simulation)
    return simulation


def list_simulations(db: Session, user: User, limit: int = 20) -> list[AllocationSimulationSummary]:
    _verifier_acces_premium(user)
    lignes = db.scalars(
        select(AllocationSimulation)
        .where(AllocationSimulation.user_id == user.id)
        .order_by(AllocationSimulation.created_at.desc(), AllocationSimulation.id.desc())
        .limit(limit)
    ).all()
    return [AllocationSimulationSummary.model_validate(s) for s in lignes]


def get_simulation(db: Session, user: User, simulation_id: int) -> AllocationSimulationDetail:
    _verifier_acces_premium(user)
    simulation = db.scalar(
        select(AllocationSimulation).where(
            AllocationSimulation.id == simulation_id, AllocationSimulation.user_id == user.id
        )
    )
    if simulation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Simulation introuvable.")

    return AllocationSimulationDetail(
        id=simulation.id,
        methode=simulation.methode,
        montant=simulation.montant,
        part_croissance=simulation.part_croissance,
        part_defensive=simulation.part_defensive,
        rendement_annuel_espere=simulation.rendement_annuel_espere,
        volatilite_annuelle_estimee=simulation.volatilite_annuelle_estimee,
        ratio_sharpe_estime=simulation.ratio_sharpe_estime,
        source_donnees=simulation.source_donnees,
        created_at=simulation.created_at,
        allocation=[LigneAllocationResponse(**ligne) for ligne in simulation.allocation_json],
    )
