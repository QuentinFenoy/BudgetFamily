import 'package:flutter_test/flutter_test.dart';

import 'package:budgetfamily/core/format.dart';
import 'package:budgetfamily/features/dashboard/data/dashboard_models.dart';

void main() {
  group('DashboardSummary.fromJson', () {
    test('parse le JSON renvoyé par le backend', () {
      final json = {
        'periode': '2026-08',
        'disponible': 2250.0,
        'categories': [
          {
            'libelle': 'alimentation',
            'montant_recommande': 600.0,
            'montant_realise': 450.0,
            'ecart': 150.0,
          },
          {
            'libelle': 'loisirs',
            'montant_recommande': 200.0,
            'montant_realise': 260.0,
            'ecart': -60.0,
          },
        ],
        'epargne_potentielle': 500.0,
        'epargne_reference_taux': 0.15,
        'epargne_reference_montant': 337.5,
      };

      final summary = DashboardSummary.fromJson(json);

      expect(summary.periode, '2026-08');
      expect(summary.disponible, 2250.0);
      expect(summary.categories, hasLength(2));
      expect(summary.categories.first.libelle, 'alimentation');
      expect(summary.epargneReferenceTaux, 0.15);
    });
  });

  group('CategoryBudgetStatus', () {
    test('progression bornée à 1 et dépassement détecté', () {
      const sousBudget = CategoryBudgetStatus(
        libelle: 'alimentation',
        montantRecommande: 600,
        montantRealise: 450,
        ecart: 150,
      );
      expect(sousBudget.depasse, isFalse);
      expect(sousBudget.progression, closeTo(0.75, 1e-9));

      const surBudget = CategoryBudgetStatus(
        libelle: 'loisirs',
        montantRecommande: 200,
        montantRealise: 260,
        ecart: -60,
      );
      expect(surBudget.depasse, isTrue);
      expect(surBudget.progression, 1.0); // 1.3 borné à 1
    });

    test('un recommandé nul ne divise pas par zéro', () {
      const c = CategoryBudgetStatus(
        libelle: 'x',
        montantRecommande: 0,
        montantRealise: 10,
        ecart: -10,
      );
      expect(c.progression, 1.0);
    });
  });

  group('format', () {
    test('formatEuros — séparateur de milliers et décimales à la française', () {
      expect(formatEuros(1234), '1\u202F234\u00A0€');
      expect(formatEuros(1234.5, decimals: 2), '1\u202F234,50\u00A0€');
      expect(formatEuros(-60), '-60\u00A0€');
    });

    test('formatPeriode — YYYY-MM lisible, sinon inchangé', () {
      expect(formatPeriode('2026-08'), 'Août 2026');
      expect(formatPeriode('2026-01'), 'Janvier 2026');
      expect(formatPeriode('pas-une-date'), 'pas-une-date');
    });
  });
}
