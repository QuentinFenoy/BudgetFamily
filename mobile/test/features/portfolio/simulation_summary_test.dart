import 'package:flutter_test/flutter_test.dart';

import 'package:budgetfamily/features/portfolio/data/allocation_models.dart';

void main() {
  test('SimulationSummary.fromJson parse la date et les champs', () {
    final json = {
      'id': 7,
      'methode': 'erc',
      'goal_id': null,
      'montant': 15000.0,
      'part_croissance': 0.68,
      'part_defensive': 0.32,
      'rendement_annuel_espere': 0.06,
      'volatilite_annuelle_estimee': 0.12,
      'ratio_sharpe_estime': 0.33,
      'source_donnees': 'hypotheses_calibrees',
      'created_at': '2026-08-14T09:30:00',
    };

    final s = SimulationSummary.fromJson(json);

    expect(s.id, 7);
    expect(s.methode, 'erc');
    expect(s.goalId, isNull);
    expect(s.montant, 15000.0);
    expect(s.partCroissance, 0.68);
    expect(s.createdAt.year, 2026);
    expect(s.createdAt.month, 8);
    expect(s.createdAt.day, 14);
  });

  test('SimulationSummary.fromJson gère un montant absent', () {
    final json = {
      'id': 3,
      'methode': 'hrp',
      'goal_id': 5,
      'montant': null,
      'part_croissance': 0.5,
      'part_defensive': 0.5,
      'rendement_annuel_espere': 0.04,
      'volatilite_annuelle_estimee': 0.08,
      'ratio_sharpe_estime': 0.25,
      'source_donnees': 'hypotheses_calibrees',
      'created_at': '2026-07-01T12:00:00',
    };

    final s = SimulationSummary.fromJson(json);

    expect(s.montant, isNull);
    expect(s.goalId, 5);
  });
}
