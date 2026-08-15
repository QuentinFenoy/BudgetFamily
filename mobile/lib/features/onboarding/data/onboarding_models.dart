/// Modèles de POST /v1/onboarding. Les clés JSON (snake_case) et les valeurs
/// d'objectif viennent directement des schémas backend (app/onboarding/schemas.py
/// et app/budgeting/models.py).

enum IncomeType {
  fixe('fixe', 'Fixe'),
  variable('variable', 'Variable');

  const IncomeType(this.apiValue, this.label);

  final String apiValue;
  final String label;

  static IncomeType fromApi(String value) =>
      IncomeType.values.firstWhere((t) => t.apiValue == value, orElse: () => IncomeType.fixe);
}

enum Objectif {
  desendettement('desendettement', 'Rembourser mes dettes'),
  matelasSecurite('matelas_securite', 'Constituer une épargne de précaution'),
  retraiteLongTerme('retraite_long_terme', 'Préparer le long terme / la retraite'),
  moyenTerme('moyen_terme', 'Financer un projet à moyen terme'),
  aucun('aucun', "Pas d'objectif particulier");

  const Objectif(this.apiValue, this.label);

  final String apiValue;
  final String label;

  static Objectif fromApi(String value) =>
      Objectif.values.firstWhere((o) => o.apiValue == value, orElse: () => Objectif.aucun);
}

class IncomeInput {
  IncomeInput({
    required this.type,
    required this.libelle,
    required this.montant,
    this.frequence = 'mensuel',
  });

  final IncomeType type;
  final String libelle;
  final double montant;
  final String frequence;

  Map<String, dynamic> toJson() => {
        'type': type.apiValue,
        'libelle': libelle,
        'montant': montant,
        'frequence': frequence,
      };
}

class FixedExpenseInput {
  FixedExpenseInput({required this.libelle, required this.montant, this.categorie});

  final String libelle;
  final double montant;
  final String? categorie;

  Map<String, dynamic> toJson() => {
        'libelle': libelle,
        'montant': montant,
        if (categorie != null && categorie!.isNotEmpty) 'categorie': categorie,
      };
}

class OnboardingRequest {
  OnboardingRequest({
    required this.nbPersonnes,
    required this.nbEnfants,
    this.situationFamiliale,
    this.age,
    required this.objectif,
    this.toleranceRisque,
    this.horizonAnnees,
    required this.matelasSecuriteAtteint,
    required this.revenus,
    required this.chargesFixes,
  });

  final int nbPersonnes;
  final int nbEnfants;
  final String? situationFamiliale;
  final int? age;
  final Objectif objectif;
  final int? toleranceRisque;
  final int? horizonAnnees;
  final bool matelasSecuriteAtteint;
  final List<IncomeInput> revenus;
  final List<FixedExpenseInput> chargesFixes;

  Map<String, dynamic> toJson() => {
        'nb_personnes': nbPersonnes,
        'nb_enfants': nbEnfants,
        if (situationFamiliale != null) 'situation_familiale': situationFamiliale,
        if (age != null) 'age': age,
        'objectif': objectif.apiValue,
        if (toleranceRisque != null) 'tolerance_risque': toleranceRisque,
        if (horizonAnnees != null) 'horizon_annees': horizonAnnees,
        'matelas_securite_atteint': matelasSecuriteAtteint,
        'revenus': revenus.map((r) => r.toJson()).toList(),
        'charges_fixes': chargesFixes.map((c) => c.toJson()).toList(),
      };
}
