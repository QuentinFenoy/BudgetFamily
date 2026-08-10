"""Service d'allocation : contrôle d'accès, lecture du profil stocké, construction
de la réponse à partir du cœur d'allocation (app.portfolio.allocator).

Le profil est relu depuis la base (même approche que le dashboard), l'allocation est
calculée à chaud : rien n'est persisté à ce stade (la simulation stockée relève d'un
incrément ultérieur).
"""

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Profile, SubscriptionTier, User
from app.portfolio.allocator import METHODES, construire_allocation
from app.portfolio.data_provider import load_asset_class_stats
from app.portfolio.schemas import LigneAllocationResponse, PortfolioAllocationResponse

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
) -> PortfolioAllocationResponse:
    # Fonctionnalité de conseil réservée à l'offre payante (cf. doc, sections 3 et 8).
    if user.subscription_tier != SubscriptionTier.PREMIUM.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="L'allocation de portefeuille est réservée à l'offre payante.",
        )

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

    return PortfolioAllocationResponse(
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
