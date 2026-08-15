import '../../onboarding/data/onboarding_models.dart';

/// Détail du profil renvoyé par GET /v1/profile. Réutilise les modèles d'entrée
/// de l'onboarding (IncomeInput / FixedExpenseInput / enums) pour préremplir
/// directement le même formulaire en mode édition.
class ProfileDetail {
  ProfileDetail({
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

  factory ProfileDetail.fromJson(Map<String, dynamic> json) {
    return ProfileDetail(
      nbPersonnes: json['nb_personnes'] as int,
      nbEnfants: json['nb_enfants'] as int,
      situationFamiliale: json['situation_familiale'] as String?,
      age: json['age'] as int?,
      objectif: Objectif.fromApi(json['objectif'] as String),
      toleranceRisque: json['tolerance_risque'] as int?,
      horizonAnnees: json['horizon_annees'] as int?,
      matelasSecuriteAtteint: json['matelas_securite_atteint'] as bool,
      revenus: (json['revenus'] as List<dynamic>)
          .map((e) => IncomeInput(
                type: IncomeType.fromApi(e['type'] as String),
                libelle: e['libelle'] as String,
                montant: (e['montant'] as num).toDouble(),
                frequence: e['frequence'] as String? ?? 'mensuel',
              ))
          .toList(),
      chargesFixes: (json['charges_fixes'] as List<dynamic>)
          .map((e) => FixedExpenseInput(
                libelle: e['libelle'] as String,
                montant: (e['montant'] as num).toDouble(),
                categorie: e['categorie'] as String?,
              ))
          .toList(),
    );
  }
}
