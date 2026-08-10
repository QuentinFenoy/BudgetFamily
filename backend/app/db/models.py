"""Modèles ORM (tables de persistance) du MVP — cf. doc d'architecture, section 5.

À ne pas confondre avec les dataclasses de domaine (app.budgeting.models,
app.savings.models) qui portent la logique de calcul : ici on décrit uniquement
le schéma de stockage.

Périmètre MVP (Phase 1) : User, Profile, Income, FixedExpense,
VariableExpenseCategory, ExpenseEntry. Les entités des paliers ultérieurs
(SavingsGoal, AllocationSimulation, PeriodicReport, Subscription) seront ajoutées
au fil des phases correspondantes.

Choix assumés pour le MVP :
- montants stockés en Float pour rester cohérent avec les moteurs de calcul existants
  (raffinement possible en entiers/centimes ou Numeric plus tard) ;
- `montant_realise` d'une catégorie n'est pas stocké : il se dérive de la somme des
  ExpenseEntry du mois, pour éviter une donnée dénormalisée à maintenir.
"""

from datetime import date, datetime, timezone
from enum import Enum

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SubscriptionTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class IncomeType(str, Enum):
    FIXE = "fixe"
    VARIABLE = "variable"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    subscription_tier: Mapped[str] = mapped_column(
        String(20), default=SubscriptionTier.FREE.value, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    profile: Mapped["Profile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    incomes: Mapped[list["Income"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    fixed_expenses: Mapped[list["FixedExpense"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    variable_categories: Mapped[list["VariableExpenseCategory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    allocation_simulations: Mapped[list["AllocationSimulation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Profile(Base):
    """Situation déclarée à l'onboarding (relation 1—1 avec User)."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    situation_familiale: Mapped[str | None] = mapped_column(String(30), nullable=True)
    nb_personnes: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    nb_enfants: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    objectif: Mapped[str] = mapped_column(String(30), default="aucun", nullable=False)
    tolerance_risque: Mapped[int | None] = mapped_column(Integer, nullable=True)  # échelle 1..5
    horizon_annees: Mapped[int | None] = mapped_column(Integer, nullable=True)
    matelas_securite_atteint: Mapped[bool] = mapped_column(default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="profile")


class Income(Base):
    __tablename__ = "incomes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # IncomeType
    libelle: Mapped[str] = mapped_column(String(120), nullable=False)
    montant: Mapped[float] = mapped_column(Float, nullable=False)
    frequence: Mapped[str] = mapped_column(String(20), default="mensuel", nullable=False)

    user: Mapped["User"] = relationship(back_populates="incomes")


class FixedExpense(Base):
    __tablename__ = "fixed_expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    libelle: Mapped[str] = mapped_column(String(120), nullable=False)
    montant: Mapped[float] = mapped_column(Float, nullable=False)
    categorie: Mapped[str | None] = mapped_column(String(60), nullable=True)

    user: Mapped["User"] = relationship(back_populates="fixed_expenses")


class VariableExpenseCategory(Base):
    """Catégorie de dépense variable, avec son montant recommandé par le moteur.

    Le montant réalisé n'est pas stocké ici : il se dérive de la somme des ExpenseEntry
    rattachées, sur la période considérée.
    """

    __tablename__ = "variable_expense_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    libelle: Mapped[str] = mapped_column(String(60), nullable=False)
    montant_recommande: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    user: Mapped["User"] = relationship(back_populates="variable_categories")
    entries: Mapped[list["ExpenseEntry"]] = relationship(
        back_populates="categorie", cascade="all, delete-orphan"
    )


class ExpenseEntry(Base):
    __tablename__ = "expense_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("variable_expense_categories.id", ondelete="CASCADE"), nullable=False
    )
    montant: Mapped[float] = mapped_column(Float, nullable=False)
    date_operation: Mapped[date] = mapped_column(Date, default=lambda: _utcnow().date(), nullable=False)

    categorie: Mapped["VariableExpenseCategory"] = relationship(back_populates="entries")


class Subscription(Base):
    """Historique des abonnements d'un utilisateur (une ligne par période d'abonnement).

    `User.subscription_tier` reste la source rapide d'accès pour les vérifications de
    palier ailleurs dans le code (ex. app.reports.service) ; cette table sert d'historique
    et de trace des événements reçus du fournisseur de paiement (webhook).
    """

    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tier: Mapped[str] = mapped_column(String(20), nullable=False)  # SubscriptionTier
    statut: Mapped[str] = mapped_column(String(20), nullable=False)  # SubscriptionStatus
    provider: Mapped[str] = mapped_column(String(30), nullable=False)  # "revenuecat" | "stripe" | "manual"
    provider_ref: Mapped[str | None] = mapped_column(String(120), nullable=True)
    date_debut: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    date_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="subscriptions")


class AllocationSimulation(Base):
    """Historique des simulations d'allocation de portefeuille (module app.portfolio).

    Chaque appel réussi à GET /v1/portfolio/allocation enregistre un instantané : la
    réponse est déjà entièrement calculée par app.portfolio.allocator au moment de la
    sauvegarde, donc `allocation_json` stocke directement les lignes telles que
    renvoyées à l'utilisateur (classes génériques uniquement — jamais de ticker, cf.
    doc d'architecture section 8, invariant déjà vérifié côté API).

    `goal_id` est volontairement absent pour l'instant : SavingsGoal (app.savings) est
    aujourd'hui un moteur de calcul pur, sans persistance en base. Le lien pourra être
    ajouté (FK nullable) le jour où les objectifs d'épargne seront eux-mêmes persistés,
    sans migration destructive puisqu'il s'agirait d'un ajout de colonne nullable.
    """

    __tablename__ = "allocation_simulations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    methode: Mapped[str] = mapped_column(String(10), nullable=False)  # "hrp" | "erc"
    montant: Mapped[float | None] = mapped_column(Float, nullable=True)

    part_croissance: Mapped[float] = mapped_column(Float, nullable=False)
    part_defensive: Mapped[float] = mapped_column(Float, nullable=False)
    rendement_annuel_espere: Mapped[float] = mapped_column(Float, nullable=False)
    volatilite_annuelle_estimee: Mapped[float] = mapped_column(Float, nullable=False)
    ratio_sharpe_estime: Mapped[float] = mapped_column(Float, nullable=False)
    source_donnees: Mapped[str] = mapped_column(String(60), nullable=False)

    # Liste des lignes d'allocation (classe, categorie, part, montant), telle que
    # renvoyée par l'API — cf. portfolio.schemas.LigneAllocationResponse.
    allocation_json: Mapped[list] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="allocation_simulations")
