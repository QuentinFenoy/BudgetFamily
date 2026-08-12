import 'package:flutter_test/flutter_test.dart';

import 'package:budgetfamily/features/onboarding/data/onboarding_models.dart';

void main() {
  group('OnboardingRequest.toJson', () {
    test('sérialise en snake_case, avec valeurs d\'enum et sans clés nulles', () {
      final request = OnboardingRequest(
        nbPersonnes: 3,
        nbEnfants: 1,
        objectif: Objectif.matelasSecurite,
        matelasSecuriteAtteint: false,
        revenus: [IncomeInput(type: IncomeType.fixe, libelle: 'Salaire', montant: 2500)],
        chargesFixes: [
          FixedExpenseInput(libelle: 'Loyer', montant: 900, categorie: 'logement'),
        ],
      );

      final json = request.toJson();

      expect(json['nb_personnes'], 3);
      expect(json['nb_enfants'], 1);
      expect(json['objectif'], 'matelas_securite');
      expect(json['matelas_securite_atteint'], false);
      // Facultatifs non fournis -> absents (le backend applique ses défauts).
      expect(json.containsKey('age'), isFalse);
      expect(json.containsKey('situation_familiale'), isFalse);
      expect(json.containsKey('tolerance_risque'), isFalse);

      final revenus = json['revenus'] as List;
      expect(revenus.first['type'], 'fixe');
      expect(revenus.first['frequence'], 'mensuel');

      final charges = json['charges_fixes'] as List;
      expect(charges.first['categorie'], 'logement');
    });

    test('inclut les champs facultatifs quand ils sont renseignés', () {
      final request = OnboardingRequest(
        nbPersonnes: 1,
        nbEnfants: 0,
        situationFamiliale: 'celibataire',
        age: 30,
        objectif: Objectif.aucun,
        toleranceRisque: 4,
        horizonAnnees: 10,
        matelasSecuriteAtteint: true,
        revenus: [IncomeInput(type: IncomeType.variable, libelle: 'Freelance', montant: 1800)],
        chargesFixes: const [],
      );

      final json = request.toJson();

      expect(json['situation_familiale'], 'celibataire');
      expect(json['age'], 30);
      expect(json['tolerance_risque'], 4);
      expect(json['horizon_annees'], 10);
      expect(json['objectif'], 'aucun');
      expect(json['revenus'] as List, hasLength(1));
      expect(json['charges_fixes'] as List, isEmpty);
    });
  });
}
