/// Modèles de GET /v1/dashboard. Les noms de champs JSON (snake_case) viennent
/// directement des schémas Pydantic du backend (app/dashboard/schemas.py).

class CategoryBudgetStatus {
  const CategoryBudgetStatus({
    required this.libelle,
    required this.montantRecommande,
    required this.montantRealise,
    required this.ecart,
  });

  factory CategoryBudgetStatus.fromJson(Map<String, dynamic> json) {
    return CategoryBudgetStatus(
      libelle: json['libelle'] as String,
      montantRecommande: (json['montant_recommande'] as num).toDouble(),
      montantRealise: (json['montant_realise'] as num).toDouble(),
      ecart: (json['ecart'] as num).toDouble(),
    );
  }

  final String libelle;
  final double montantRecommande;
  final double montantRealise;

  /// montant_recommande - montant_realise (positif = marge restante).
  final double ecart;

  /// Fraction consommée, bornée à [0, 1] pour la barre de progression.
  double get progression {
    if (montantRecommande <= 0) return montantRealise > 0 ? 1 : 0;
    return (montantRealise / montantRecommande).clamp(0, 1).toDouble();
  }

  bool get depasse => montantRealise > montantRecommande;
}

class DashboardSummary {
  const DashboardSummary({
    required this.periode,
    required this.disponible,
    required this.categories,
    required this.epargnePotentielle,
    required this.epargneReferenceTaux,
    required this.epargneReferenceMontant,
  });

  factory DashboardSummary.fromJson(Map<String, dynamic> json) {
    return DashboardSummary(
      periode: json['periode'] as String,
      disponible: (json['disponible'] as num).toDouble(),
      categories: (json['categories'] as List<dynamic>)
          .map((e) => CategoryBudgetStatus.fromJson(e as Map<String, dynamic>))
          .toList(),
      epargnePotentielle: (json['epargne_potentielle'] as num).toDouble(),
      epargneReferenceTaux: (json['epargne_reference_taux'] as num).toDouble(),
      epargneReferenceMontant: (json['epargne_reference_montant'] as num).toDouble(),
    );
  }

  final String periode;
  final double disponible;
  final List<CategoryBudgetStatus> categories;
  final double epargnePotentielle;
  final double epargneReferenceTaux;
  final double epargneReferenceMontant;
}
