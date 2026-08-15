"""Catalogue des classes d'actifs génériques et leurs proxys internes.

Contrainte réglementaire (doc d'architecture, section 8) : l'utilisateur ne voit
JAMAIS d'instrument nominatif — uniquement des classes d'actifs génériques. Les
tickers ci-dessous (`proxys`) ne servent qu'en interne, pour estimer les statistiques
de chaque classe à partir de données de marché réelles (script de rafraîchissement
hors-ligne, cf. scripts/refresh_asset_class_stats.py). Chaque classe est adossée à un
PANIER de plusieurs proxys dont on moyenne les rendements, pour un estimateur plus
robuste qu'un instrument unique.

Proxys retenus : supports larges, liquides, accessibles depuis la zone euro (perspective
d'un investisseur particulier français). Ce ne sont pas des recommandations d'achat.
ATTENTION : ce sont des ETF UCITS SAUF pour l'or, où les proxys sont des ETC (titres de
dette adossés à de l'or physique) — la réglementation UCITS interdit un fonds
mono-matière première. Cette nuance n'a pas d'incidence sur les statistiques calculées,
mais compte si un support est un jour présenté à l'utilisateur.

Les hypothèses de marché long terme (`DEFAULT_CMA` : rendement annuel espéré,
volatilité, corrélations) fournissent une covariance par défaut quand aucun snapshot
de marché n'a encore été calculé. Elles sont volontairement prudentes et génériques,
et destinées à être remplacées par des statistiques dérivées des proxys réels.
"""

from dataclasses import dataclass

# Rôle d'une classe dans la glide-path profil -> allocation.
SLEEVE_CROISSANCE = "croissance"
SLEEVE_DEFENSIF = "defensif"


@dataclass(frozen=True)
class AssetClass:
    cle: str          # identifiant technique stable
    nom: str          # libellé générique montré à l'utilisateur
    description: str
    sleeve: str       # SLEEVE_CROISSANCE | SLEEVE_DEFENSIF
    proxys: tuple[str, ...]  # USAGE INTERNE UNIQUEMENT — jamais exposé par l'API
    definition: str = ""          # explication accessible, montrée à l'utilisateur
    exemples: tuple[str, ...] = ()  # exemples concrets, génériques (pédagogie)


# Ordre canonique des classes (sert d'index aux vecteurs/matrices).
ASSET_CLASSES: tuple[AssetClass, ...] = (
    AssetClass(
        cle="actions_monde_developpe",
        nom="Actions monde développé",
        description="Grandes et moyennes capitalisations des marchés développés, diversifiées mondialement.",
        sleeve=SLEEVE_CROISSANCE,
        proxys=("IWDA.AS", "XDWD.DE"),
        definition="Des parts d'entreprises cotées dans les grands pays développés. Vous devenez copropriétaire de milliers de sociétés et profitez de leur croissance sur le long terme, en acceptant des variations parfois fortes à court terme.",
        exemples=("De grandes entreprises comme Apple, LVMH ou Nestlé", "Un fonds indiciel « actions monde » qui les regroupe"),
    ),
    AssetClass(
        cle="actions_marches_emergents",
        nom="Actions marchés émergents",
        description="Actions des économies émergentes — potentiel de croissance supérieur, volatilité plus élevée.",
        sleeve=SLEEVE_CROISSANCE,
        proxys=("EIMI.L", "XMME.DE"),
        definition="Des parts d'entreprises des économies en développement (Chine, Inde, Brésil…). Un potentiel de croissance plus élevé, mais des variations et des risques (politiques, monétaires) plus importants.",
        exemples=("De grands groupes comme Samsung, TSMC ou Tencent", "Un fonds « marchés émergents »"),
    ),
    AssetClass(
        cle="immobilier_cote",
        nom="Immobilier coté",
        description="Sociétés foncières cotées (immobilier international) — source de revenus et de diversification.",
        sleeve=SLEEVE_CROISSANCE,
        proxys=("IWDP.AS",),
        definition="Investir dans l'immobilier via la Bourse, sans acheter de bien en direct. Des sociétés cotées détiennent bureaux, commerces et logements, et vous en reversent les loyers.",
        exemples=("Une foncière cotée comme Unibail-Rodamco ou Klépierre", "Un fonds « immobilier » (pierre-papier cotée)"),
    ),
    AssetClass(
        cle="obligations_souveraines_euro",
        nom="Obligations d'État zone euro",
        description="Dette souveraine de la zone euro — socle défensif, faible volatilité.",
        sleeve=SLEEVE_DEFENSIF,
        proxys=("IEGA.AS",),
        definition="Prêter de l'argent à un État de la zone euro, qui vous verse des intérêts puis vous rembourse. Peu risqué, pour un rendement modéré.",
        exemples=("Les obligations de la France (OAT) ou de l'Allemagne (Bund)", "Un fonds d'obligations d'État"),
    ),
    AssetClass(
        cle="obligations_entreprises_euro",
        nom="Obligations d'entreprises zone euro",
        description="Dette d'entreprises de qualité (investment grade) en euro — rendement supérieur aux souveraines.",
        sleeve=SLEEVE_DEFENSIF,
        proxys=("IEAC.AS",),
        definition="Prêter à de grandes entreprises solides plutôt qu'à des États. Un peu plus risqué que la dette d'État, donc un peu mieux rémunéré.",
        exemples=("La dette émise par des groupes comme Sanofi ou TotalEnergies", "Un fonds d'obligations d'entreprises"),
    ),
    AssetClass(
        cle="or_metaux_precieux",
        nom="Or et métaux précieux",
        description="Or physique — actif de diversification, décorrélé des actions en période de stress.",
        sleeve=SLEEVE_DEFENSIF,
        proxys=("IGLN.L", "SGLD.L"),
        definition="L'or, valeur refuge : il ne verse aucun revenu mais tend à protéger en cas de crise ou d'inflation, quand les actions baissent. Sert surtout à diversifier.",
        exemples=("De l'or physique (lingots, pièces)", "Un fonds adossé à de l'or"),
    ),
    AssetClass(
        cle="monetaire_liquidites",
        nom="Monétaire et liquidités",
        description="Placements monétaires euro à très court terme — capital stable, forte liquidité.",
        sleeve=SLEEVE_DEFENSIF,
        proxys=("XEON.DE",),
        definition="Votre argent « au chaud » : disponible à tout moment et sans risque sur le capital, mais faiblement rémunéré. C'est le matelas de sécurité du portefeuille.",
        exemples=("Un Livret A ou un LDDS", "Un fonds monétaire"),
    ),
)

CLES = tuple(ac.cle for ac in ASSET_CLASSES)
PAR_CLE = {ac.cle: ac for ac in ASSET_CLASSES}


# ── Hypothèses de marché long terme (par défaut, hors-ligne) ────────────────────
# Rendement annuel espéré et volatilité annuelle par classe.
DEFAULT_MU_VOL: dict[str, tuple[float, float]] = {
    "actions_monde_developpe": (0.112, 0.156),
    "actions_marches_emergents": (0.050, 0.192),
    "immobilier_cote": (0.025, 0.164),
    "obligations_souveraines_euro": (0.001, 0.055),
    "obligations_entreprises_euro": (0.01, 0.045),
    "or_metaux_precieux": (0.10, 0.162),
    "monetaire_liquidites": (0.009, 0.004),
}

# Corrélations (symétriques ; diagonale = 1 implicite). Clé = paire ordonnée par CLES.
DEFAULT_CORRELATIONS: dict[tuple[str, str], float] = {
    ("actions_monde_developpe", "actions_marches_emergents"): 0.75,
    ("actions_monde_developpe", "immobilier_cote"): 0.65,
    ("actions_monde_developpe", "obligations_souveraines_euro"): 0.09,
    ("actions_monde_developpe", "obligations_entreprises_euro"): 0.39,
    ("actions_monde_developpe", "or_metaux_precieux"): 0.10,
    ("actions_monde_developpe", "monetaire_liquidites"): 0.00,
    ("actions_marches_emergents", "immobilier_cote"): 0.55,
    ("actions_marches_emergents", "obligations_souveraines_euro"): +0.07,
    ("actions_marches_emergents", "obligations_entreprises_euro"): 0.25,
    ("actions_marches_emergents", "or_metaux_precieux"): 0.15,
    ("actions_marches_emergents", "monetaire_liquidites"): 0.00,
    ("immobilier_cote", "obligations_souveraines_euro"): 0.20,
    ("immobilier_cote", "obligations_entreprises_euro"): 0.35,
    ("immobilier_cote", "or_metaux_precieux"): 0.10,
    ("immobilier_cote", "monetaire_liquidites"): 0.00,
    ("obligations_souveraines_euro", "obligations_entreprises_euro"): 0.70,
    ("obligations_souveraines_euro", "or_metaux_precieux"): 0.20,
    ("obligations_souveraines_euro", "monetaire_liquidites"): -0.03,
    ("obligations_entreprises_euro", "or_metaux_precieux"): 0.15,
    ("obligations_entreprises_euro", "monetaire_liquidites"): -0.03,
    ("or_metaux_precieux", "monetaire_liquidites"): 0.00,
}


# --- Hypothèses de rendement LONG TERME (prospectives) ------------------------------
# Distinctes de DEFAULT_MU_VOL, dont les rendements viennent des ~10 dernières années
# (obligations ~0 %, or à 10 % : une décennie atypique, mauvais estimateur du futur).
# Utilisées UNIQUEMENT pour le rendement/Sharpe affichés. La covariance — c.-à-d. le
# risque, qui pilote les poids — reste, elle, estimée sur données de marché.
LONG_RUN_MU: dict[str, float] = {
    "actions_monde_developpe": 0.065,
    "actions_marches_emergents": 0.075,
    "immobilier_cote": 0.055,
    "obligations_souveraines_euro": 0.028,
    "obligations_entreprises_euro": 0.038,
    "or_metaux_precieux": 0.030,
    "monetaire_liquidites": 0.022,
}
