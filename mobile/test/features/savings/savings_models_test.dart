import 'package:flutter_test/flutter_test.dart';

import 'package:budgetfamily/features/savings/data/savings_models.dart';

void main() {
  group('SavingsGoal.fromJson', () {
    test('parse les champs et calcule la progression', () {
      final json = {
        'id': 1,
        'libelle': "Fonds d'urgence",
        'montant_cible': 6000.0,
        'montant_actuel': 1500.0,
        'montant_restant': 4500.0,
        'priorite': 1,
        'est_atteint': false,
        'created_at': '2026-01-01T00:00:00',
        'updated_at': '2026-01-01T00:00:00',
      };

      final g = SavingsGoal.fromJson(json);

      expect(g.libelle, "Fonds d'urgence");
      expect(g.montantRestant, 4500.0);
      expect(g.priorite, 1);
      expect(g.estAtteint, isFalse);
      expect(g.progression, closeTo(0.25, 1e-9));
    });

    test('progression bornée à 1 quand l\'objectif est dépassé', () {
      final g = SavingsGoal.fromJson({
        'id': 2,
        'libelle': 'Voyage',
        'montant_cible': 100.0,
        'montant_actuel': 150.0,
        'montant_restant': 0.0,
        'priorite': 2,
        'est_atteint': true,
        'created_at': '2026-01-01T00:00:00',
        'updated_at': '2026-01-01T00:00:00',
      });

      expect(g.estAtteint, isTrue);
      expect(g.progression, 1.0);
    });
  });

  test('RepartitionResult.fromJson parse allocations et mois restants', () {
    final json = {
      'epargne_disponible': 500.0,
      'allocations': [
        {'objectif_id': '1', 'montant_alloue_ce_mois': 300.0, 'mois_restants_estimes': 15.0},
        {'objectif_id': '2', 'montant_alloue_ce_mois': 200.0, 'mois_restants_estimes': null},
      ],
      'epargne_non_allouee': 0.0,
    };

    final r = RepartitionResult.fromJson(json);

    expect(r.epargneDisponible, 500.0);
    expect(r.allocations, hasLength(2));
    expect(r.allocations.first.objectifId, '1');
    expect(r.allocations.first.montantAlloueCeMois, 300.0);
    expect(r.allocations.first.moisRestantsEstimes, 15.0);
    expect(r.allocations[1].moisRestantsEstimes, isNull);
  });
}
