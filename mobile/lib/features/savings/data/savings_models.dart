/// Modèles du module épargne (GET/POST/PATCH /v1/savings/goals et /repartition-auto).

class SavingsGoal {
  SavingsGoal({
    required this.id,
    required this.libelle,
    required this.montantCible,
    required this.montantActuel,
    required this.montantRestant,
    required this.priorite,
    required this.estAtteint,
    this.horizonMois,
  });

  final int id;
  final String libelle;
  final double montantCible;
  final double montantActuel;
  final double montantRestant;
  final int priorite;
  final bool estAtteint;
  final int? horizonMois;

  /// Fraction atteinte, bornée à [0, 1] pour la barre de progression.
  double get progression {
    if (montantCible <= 0) return montantActuel > 0 ? 1 : 0;
    return (montantActuel / montantCible).clamp(0, 1).toDouble();
  }

  factory SavingsGoal.fromJson(Map<String, dynamic> json) {
    return SavingsGoal(
      id: json['id'] as int,
      libelle: json['libelle'] as String,
      montantCible: (json['montant_cible'] as num).toDouble(),
      montantActuel: (json['montant_actuel'] as num).toDouble(),
      montantRestant: (json['montant_restant'] as num).toDouble(),
      priorite: json['priorite'] as int,
      estAtteint: json['est_atteint'] as bool,
      horizonMois: json['horizon_mois'] as int?,
    );
  }
}

class RepartitionAllocation {
  RepartitionAllocation({
    required this.objectifId,
    required this.montantAlloueCeMois,
    this.moisRestantsEstimes,
  });

  final String objectifId;
  final double montantAlloueCeMois;
  final double? moisRestantsEstimes;

  factory RepartitionAllocation.fromJson(Map<String, dynamic> json) {
    return RepartitionAllocation(
      objectifId: json['objectif_id'].toString(),
      montantAlloueCeMois: (json['montant_alloue_ce_mois'] as num).toDouble(),
      moisRestantsEstimes: json['mois_restants_estimes'] == null
          ? null
          : (json['mois_restants_estimes'] as num).toDouble(),
    );
  }
}

class RepartitionResult {
  RepartitionResult({
    required this.epargneDisponible,
    required this.allocations,
    required this.epargneNonAllouee,
  });

  final double epargneDisponible;
  final List<RepartitionAllocation> allocations;
  final double epargneNonAllouee;

  factory RepartitionResult.fromJson(Map<String, dynamic> json) {
    return RepartitionResult(
      epargneDisponible: (json['epargne_disponible'] as num).toDouble(),
      allocations: (json['allocations'] as List<dynamic>)
          .map((e) => RepartitionAllocation.fromJson(e as Map<String, dynamic>))
          .toList(),
      epargneNonAllouee: (json['epargne_non_allouee'] as num).toDouble(),
    );
  }
}


// ── Plan d'épargne (GET /v1/savings/plan) ────────────────────────────────────────

/// Rendement BRUT à viser dans une enveloppe pour obtenir le net requis.
class BrutEnveloppe {
  BrutEnveloppe({
    required this.enveloppe,
    required this.tauxImposition,
    required this.rendementBrutIndicatif,
  });

  final String enveloppe;
  final double tauxImposition;
  final double rendementBrutIndicatif;

  factory BrutEnveloppe.fromJson(Map<String, dynamic> json) {
    return BrutEnveloppe(
      enveloppe: json['enveloppe'] as String,
      tauxImposition: (json['taux_imposition'] as num).toDouble(),
      rendementBrutIndicatif: (json['rendement_brut_indicatif'] as num).toDouble(),
    );
  }
}

class PlanObjectif {
  PlanObjectif({
    required this.objectifId,
    required this.libelle,
    required this.montantCible,
    required this.montantActuel,
    required this.montantRestant,
    required this.priorite,
    required this.mensualiteAttribuee,
    this.horizonMois,
    this.moisRestantsAuRythmeActuel,
    this.rendementNetAnnuelRequis,
    this.realisable,
    this.risqueNote,
    this.volatiliteEstimee,
    this.auDelaFrontiere = false,
    this.brutsParEnveloppe = const [],
  });

  final String objectifId;
  final String libelle;
  final double montantCible;
  final double montantActuel;
  final double montantRestant;
  final int priorite;
  final int? horizonMois;
  final double mensualiteAttribuee;
  final double? moisRestantsAuRythmeActuel;

  // Premium uniquement (null / [] pour les comptes gratuits).
  final double? rendementNetAnnuelRequis;
  final String? realisable;
  final int? risqueNote;
  final double? volatiliteEstimee;
  final bool auDelaFrontiere;
  final List<BrutEnveloppe> brutsParEnveloppe;

  factory PlanObjectif.fromJson(Map<String, dynamic> json) {
    return PlanObjectif(
      objectifId: json['objectif_id'].toString(),
      libelle: json['libelle'] as String,
      montantCible: (json['montant_cible'] as num).toDouble(),
      montantActuel: (json['montant_actuel'] as num).toDouble(),
      montantRestant: (json['montant_restant'] as num).toDouble(),
      priorite: json['priorite'] as int,
      horizonMois: json['horizon_mois'] as int?,
      mensualiteAttribuee: (json['mensualite_attribuee'] as num).toDouble(),
      moisRestantsAuRythmeActuel: json['mois_restants_au_rythme_actuel'] == null
          ? null
          : (json['mois_restants_au_rythme_actuel'] as num).toDouble(),
      rendementNetAnnuelRequis: json['rendement_net_annuel_requis'] == null
          ? null
          : (json['rendement_net_annuel_requis'] as num).toDouble(),
      realisable: json['realisable'] as String?,
      risqueNote: json['risque_note'] as int?,
      volatiliteEstimee: json['volatilite_estimee'] == null
          ? null
          : (json['volatilite_estimee'] as num).toDouble(),
      auDelaFrontiere: (json['au_dela_frontiere'] as bool?) ?? false,
      brutsParEnveloppe: ((json['bruts_par_enveloppe'] as List<dynamic>?) ?? [])
          .map((e) => BrutEnveloppe.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class PlanEpargne {
  PlanEpargne({
    required this.capaciteEpargneMensuelle,
    required this.methode,
    required this.premium,
    required this.noteRendementBrut,
    required this.objectifs,
  });

  final double capaciteEpargneMensuelle;
  final String methode;
  final bool premium;
  final String noteRendementBrut;
  final List<PlanObjectif> objectifs;

  factory PlanEpargne.fromJson(Map<String, dynamic> json) {
    return PlanEpargne(
      capaciteEpargneMensuelle: (json['capacite_epargne_mensuelle'] as num).toDouble(),
      methode: json['methode'] as String,
      premium: json['premium'] as bool,
      noteRendementBrut: json['note_rendement_brut'] as String,
      objectifs: (json['objectifs'] as List<dynamic>)
          .map((e) => PlanObjectif.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}
