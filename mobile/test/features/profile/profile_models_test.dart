import 'package:flutter_test/flutter_test.dart';

import 'package:budgetfamily/features/onboarding/data/onboarding_models.dart';
import 'package:budgetfamily/features/profile/data/profile_models.dart';

void main() {
  group('ProfileDetail.fromJson', () {
    test('reconstruit le profil et mappe les enums', () {
      final json = {
        'id': 1,
        'nb_personnes': 2,
        'nb_enfants': 1,
        'situation_familiale': 'couple',
        'age': 40,
        'objectif': 'retraite_long_terme',
        'tolerance_risque': 4,
        'horizon_annees': 20,
        'matelas_securite_atteint': true,
        'revenus': [
          {'type': 'fixe', 'libelle': 'Salaire', 'montant': 3000.0, 'frequence': 'mensuel'},
          {'type': 'variable', 'libelle': 'Primes', 'montant': 200.0, 'frequence': 'mensuel'},
        ],
        'charges_fixes': [
          {'libelle': 'Loyer', 'montant': 900.0, 'categorie': 'logement'},
        ],
      };

      final detail = ProfileDetail.fromJson(json);

      expect(detail.nbPersonnes, 2);
      expect(detail.objectif, Objectif.retraiteLongTerme);
      expect(detail.toleranceRisque, 4);
      expect(detail.matelasSecuriteAtteint, isTrue);
      expect(detail.revenus, hasLength(2));
      expect(detail.revenus.first.type, IncomeType.fixe);
      expect(detail.revenus[1].type, IncomeType.variable);
      expect(detail.chargesFixes.single.categorie, 'logement');
    });

    test('gère les champs nullables absents', () {
      final json = {
        'id': 2,
        'nb_personnes': 1,
        'nb_enfants': 0,
        'situation_familiale': null,
        'age': null,
        'objectif': 'aucun',
        'tolerance_risque': null,
        'horizon_annees': null,
        'matelas_securite_atteint': false,
        'revenus': [
          {'type': 'fixe', 'libelle': 'Salaire', 'montant': 1500.0, 'frequence': 'mensuel'},
        ],
        'charges_fixes': <dynamic>[],
      };

      final detail = ProfileDetail.fromJson(json);

      expect(detail.situationFamiliale, isNull);
      expect(detail.age, isNull);
      expect(detail.objectif, Objectif.aucun);
      expect(detail.horizonAnnees, isNull);
      expect(detail.chargesFixes, isEmpty);
    });
  });
}
