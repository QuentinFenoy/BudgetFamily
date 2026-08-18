import 'package:flutter_test/flutter_test.dart';

import 'package:budgetfamily/features/reports/data/report_models.dart';

void main() {
  test('MonthlyReport.fromJson parse agrégats et catégories', () {
    final json = {
      'periode': '2026-08',
      'disponible': 2700.0,
      'categories': [
        {
          'libelle': 'alimentation',
          'montant_recommande': 660.0,
          'montant_realise': 500.0,
          'ecart': 160.0,
        },
      ],
      'total_recommande': 1983.0,
      'total_realise': 1400.0,
      'epargne_potentielle': 717.0,
      'epargne_realisee_estimee': 1300.0,
      'epargne_reference_taux': 0.2,
      'epargne_reference_montant': 540.0,
      'ecart_epargne_vs_reference': 760.0,
    };

    final r = MonthlyReport.fromJson(json);

    expect(r.periode, '2026-08');
    expect(r.categories, hasLength(1));
    expect(r.categories.first.libelle, 'alimentation');
    expect(r.epargneRealiseeEstimee, 1300.0);
    expect(r.ecartEpargneVsReference, 760.0);
  });

  test('QuarterlyReport.fromJson parse la tendance sur 3 mois', () {
    final json = {
      'mois': ['2026-06', '2026-07', '2026-08'],
      'bilans': <dynamic>[],
      'tendances': [
        {'periode': '2026-06', 'total_realise': 1400.0, 'epargne_realisee_estimee': 1300.0},
        {'periode': '2026-07', 'total_realise': 1500.0, 'epargne_realisee_estimee': 1200.0},
        {'periode': '2026-08', 'total_realise': 1600.0, 'epargne_realisee_estimee': 1100.0},
      ],
      'moyenne_totale_realisee': 1500.0,
      'epargne_totale_trimestre': 3600.0,
      'ecart_mois_courant_vs_moyenne': 100.0,
    };

    final r = QuarterlyReport.fromJson(json);

    expect(r.mois, hasLength(3));
    expect(r.tendances, hasLength(3));
    expect(r.tendances.last.periode, '2026-08');
    expect(r.epargneTotaleTrimestre, 3600.0);
  });
}
