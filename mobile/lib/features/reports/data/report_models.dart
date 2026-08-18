import '../../dashboard/data/dashboard_models.dart';

/// Modèles des bilans (GET /v1/reports/monthly et /quarterly). Les catégories
/// réutilisent CategoryBudgetStatus du dashboard (même structure côté backend).

class MonthlyReport {
  MonthlyReport({
    required this.periode,
    required this.disponible,
    required this.categories,
    required this.totalRecommande,
    required this.totalRealise,
    required this.epargnePotentielle,
    required this.epargneRealiseeEstimee,
    required this.epargneReferenceTaux,
    required this.epargneReferenceMontant,
    required this.ecartEpargneVsReference,
  });

  final String periode;
  final double disponible;
  final List<CategoryBudgetStatus> categories;
  final double totalRecommande;
  final double totalRealise;
  final double epargnePotentielle;
  final double epargneRealiseeEstimee;
  final double epargneReferenceTaux;
  final double epargneReferenceMontant;
  final double ecartEpargneVsReference;

  factory MonthlyReport.fromJson(Map<String, dynamic> json) {
    return MonthlyReport(
      periode: json['periode'] as String,
      disponible: (json['disponible'] as num).toDouble(),
      categories: (json['categories'] as List<dynamic>)
          .map((e) => CategoryBudgetStatus.fromJson(e as Map<String, dynamic>))
          .toList(),
      totalRecommande: (json['total_recommande'] as num).toDouble(),
      totalRealise: (json['total_realise'] as num).toDouble(),
      epargnePotentielle: (json['epargne_potentielle'] as num).toDouble(),
      epargneRealiseeEstimee: (json['epargne_realisee_estimee'] as num).toDouble(),
      epargneReferenceTaux: (json['epargne_reference_taux'] as num).toDouble(),
      epargneReferenceMontant: (json['epargne_reference_montant'] as num).toDouble(),
      ecartEpargneVsReference: (json['ecart_epargne_vs_reference'] as num).toDouble(),
    );
  }
}

class MonthlyTrend {
  MonthlyTrend({
    required this.periode,
    required this.totalRealise,
    required this.epargneRealiseeEstimee,
  });

  final String periode;
  final double totalRealise;
  final double epargneRealiseeEstimee;

  factory MonthlyTrend.fromJson(Map<String, dynamic> json) {
    return MonthlyTrend(
      periode: json['periode'] as String,
      totalRealise: (json['total_realise'] as num).toDouble(),
      epargneRealiseeEstimee: (json['epargne_realisee_estimee'] as num).toDouble(),
    );
  }
}

class QuarterlyReport {
  QuarterlyReport({
    required this.mois,
    required this.tendances,
    required this.moyenneTotaleRealisee,
    required this.epargneTotaleTrimestre,
    required this.ecartMoisCourantVsMoyenne,
  });

  final List<String> mois;
  final List<MonthlyTrend> tendances;
  final double moyenneTotaleRealisee;
  final double epargneTotaleTrimestre;
  final double ecartMoisCourantVsMoyenne;

  factory QuarterlyReport.fromJson(Map<String, dynamic> json) {
    return QuarterlyReport(
      mois: (json['mois'] as List<dynamic>).map((e) => e as String).toList(),
      tendances: (json['tendances'] as List<dynamic>)
          .map((e) => MonthlyTrend.fromJson(e as Map<String, dynamic>))
          .toList(),
      moyenneTotaleRealisee: (json['moyenne_totale_realisee'] as num).toDouble(),
      epargneTotaleTrimestre: (json['epargne_totale_trimestre'] as num).toDouble(),
      ecartMoisCourantVsMoyenne: (json['ecart_mois_courant_vs_moyenne'] as num).toDouble(),
    );
  }
}
