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
  });

  final int id;
  final String libelle;
  final double montantCible;
  final double montantActuel;
  final double montantRestant;
  final int priorite;
  final bool estAtteint;

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
