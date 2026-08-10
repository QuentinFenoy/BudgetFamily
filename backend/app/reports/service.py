"""Construit les bilans périodiques, en s'appuyant sur app.dashboard.service.situation_mois
plutôt que de dupliquer la logique de calcul.
"""

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.dashboard.service import situation_mois
from app.db.models import SubscriptionTier, User
from app.reports.schemas import BilanMensuel, BilanTrimestriel, TendanceMensuelle


def _mois_precedents(mois_reference: str | None, n: int) -> list[str]:
    """Renvoie les n derniers mois se terminant à mois_reference (ou le mois courant
    si non précisé), en ordre chronologique croissant. Format 'YYYY-MM'.
    """
    if mois_reference is None:
        today = date.today()
        annee, mois_num = today.year, today.month
    else:
        try:
            annee_str, mois_str = mois_reference.split("-")
            annee, mois_num = int(annee_str), int(mois_str)
            if not (1 <= mois_num <= 12):
                raise ValueError
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Le paramètre 'mois' doit être au format YYYY-MM (ex: 2026-08)",
            )

    mois_liste = []
    a, m = annee, mois_num
    for _ in range(n):
        mois_liste.append(f"{a:04d}-{m:02d}")
        m -= 1
        if m == 0:
            m = 12
            a -= 1
    return list(reversed(mois_liste))


def build_bilan_mensuel(db: Session, user: User, mois: str | None = None) -> BilanMensuel:
    resultat, categories_status, periode_label = situation_mois(db, user, mois)

    total_recommande = round(sum(c.montant_recommande for c in categories_status), 2)
    total_realise = round(sum(c.montant_realise for c in categories_status), 2)
    epargne_realisee_estimee = round(resultat.disponible - total_realise, 2)

    return BilanMensuel(
        periode=periode_label,
        disponible=resultat.disponible,
        categories=categories_status,
        total_recommande=total_recommande,
        total_realise=total_realise,
        epargne_potentielle=resultat.epargne_potentielle,
        epargne_realisee_estimee=epargne_realisee_estimee,
        epargne_reference_taux=resultat.epargne_reference_taux,
        epargne_reference_montant=resultat.epargne_reference_montant,
        ecart_epargne_vs_reference=round(epargne_realisee_estimee - resultat.epargne_reference_montant, 2),
    )


def build_bilan_trimestriel(db: Session, user: User, mois: str | None = None) -> BilanTrimestriel:
    """Bilan trimestriel avancé — réservé à l'offre payante (cf. doc architecture, section 3)."""
    if user.subscription_tier != SubscriptionTier.PREMIUM.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Le bilan trimestriel est réservé à l'offre payante.",
        )

    mois_liste = _mois_precedents(mois, n=3)
    bilans = [build_bilan_mensuel(db, user, m) for m in mois_liste]

    tendances = [
        TendanceMensuelle(
            periode=b.periode,
            total_realise=b.total_realise,
            epargne_realisee_estimee=b.epargne_realisee_estimee,
        )
        for b in bilans
    ]

    moyenne_totale_realisee = round(sum(t.total_realise for t in tendances) / len(tendances), 2)
    epargne_totale_trimestre = round(sum(t.epargne_realisee_estimee for t in tendances), 2)
    ecart_mois_courant_vs_moyenne = round(tendances[-1].total_realise - moyenne_totale_realisee, 2)

    return BilanTrimestriel(
        mois=mois_liste,
        bilans=bilans,
        tendances=tendances,
        moyenne_totale_realisee=moyenne_totale_realisee,
        epargne_totale_trimestre=epargne_totale_trimestre,
        ecart_mois_courant_vs_moyenne=ecart_mois_courant_vs_moyenne,
    )
