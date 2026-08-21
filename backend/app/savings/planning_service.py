"""Construit le plan d'épargne : répartit la capacité d'épargne mensuelle (déjà
calculée par le budget) entre les objectifs selon leur priorité, et — pour les
comptes premium — projette pour chaque objectif le rendement brut requis, le risque
associé, la faisabilité et les rendements nets par enveloppe.

S'appuie sur les briques existantes plutôt que de dupliquer : la capacité vient de
app.dashboard.service (épargne potentielle du mois), la répartition de
app.savings.engine, la frontière rendement/risque de app.portfolio.allocator.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dashboard.service import situation_mois
from app.db.models import SavingsGoal, SubscriptionTier, User
from app.portfolio.allocator import construire_allocation
from app.portfolio.data_provider import load_asset_class_stats
from app.savings.engine import repartir_epargne
from app.savings.models import ObjectifEpargne
from app.savings.projection import (
    NOTE_RENDEMENT_BRUT,
    bruts_par_enveloppe,
    message_faisabilite,
    rendement_net_annuel_requis,
    risque_pour_rendement,
)
from app.savings.schemas import (
    PlanEpargneResponse,
    PlanObjectif,
    RendementBrutEnveloppeResponse,
)


def _frontiere_rendement_risque(stats) -> list[tuple[int, float, float]]:
    """Points (note 1..5, rendement espéré, volatilité) SANS plafond d'âge/horizon/objectif
    — la seule tolérance au risque pilote, pour situer un rendement requis sur l'échelle."""
    points = []
    for tolerance in range(1, 6):
        allocation = construire_allocation(stats, tolerance, None, None, "aucun")
        points.append(
            (tolerance, allocation.rendement_annuel_espere, allocation.volatilite_annuelle_estimee)
        )
    return points


def construire_plan_epargne(db: Session, user: User) -> PlanEpargneResponse:
    # Capacité d'épargne mensuelle = épargne potentielle du budget courant.
    resultat, _, _ = situation_mois(db, user)  # lève 404 si aucun profil
    capacite = round(max(resultat.epargne_potentielle, 0.0), 2)

    goals = db.scalars(
        select(SavingsGoal).where(SavingsGoal.user_id == user.id).order_by(SavingsGoal.priorite)
    ).all()

    # Répartition de la capacité entre objectifs, par priorité (cascade).
    mensualites: dict[str, float] = {}
    mois_restants: dict[str, float | None] = {}
    if goals:
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
        repartition = repartir_epargne(objectifs, capacite, methode="cascade")
        mensualites = {a.objectif_id: a.montant_alloue_ce_mois for a in repartition.allocations}
        mois_restants = {a.objectif_id: a.mois_restants_estimes for a in repartition.allocations}

    is_premium = user.subscription_tier == SubscriptionTier.PREMIUM.value
    frontiere = _frontiere_rendement_risque(load_asset_class_stats()) if is_premium else None

    objectifs_plan: list[PlanObjectif] = []
    for g in goals:
        gid = str(g.id)
        mensualite = mensualites.get(gid, 0.0)
        montant_restant = max(round(g.montant_cible - g.montant_actuel, 2), 0.0)

        champs: dict = {
            "objectif_id": gid,
            "libelle": g.libelle,
            "montant_cible": g.montant_cible,
            "montant_actuel": g.montant_actuel,
            "montant_restant": montant_restant,
            "priorite": g.priorite,
            "horizon_mois": g.horizon_mois,
            "mensualite_attribuee": mensualite,
            "mois_restants_au_rythme_actuel": mois_restants.get(gid),
        }

        if is_premium and g.horizon_mois:
            rendement = rendement_net_annuel_requis(
                g.montant_cible, g.montant_actuel, mensualite, g.horizon_mois
            )
            champs["rendement_net_annuel_requis"] = rendement
            champs["realisable"] = message_faisabilite(rendement)

            if rendement is not None and rendement > 0.0:
                risque = risque_pour_rendement(frontiere, rendement)
                champs["risque_note"] = risque.note_sur_5
                champs["volatilite_estimee"] = risque.volatilite_annuelle
                champs["au_dela_frontiere"] = risque.au_dela_frontiere
                champs["bruts_par_enveloppe"] = [
                    RendementBrutEnveloppeResponse(
                        enveloppe=b.enveloppe,
                        taux_imposition=b.taux_imposition,
                        rendement_brut_indicatif=b.rendement_brut_indicatif,
                    )
                    for b in bruts_par_enveloppe(rendement)
                ]
            elif rendement == 0.0:
                champs["risque_note"] = 0
                champs["volatilite_estimee"] = 0.0

        objectifs_plan.append(PlanObjectif(**champs))

    return PlanEpargneResponse(
        capacite_epargne_mensuelle=capacite,
        methode="cascade",
        premium=is_premium,
        note_rendement_brut=NOTE_RENDEMENT_BRUT if is_premium else "",
        objectifs=objectifs_plan,
    )
