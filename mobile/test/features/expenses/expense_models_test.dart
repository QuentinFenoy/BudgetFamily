import 'package:flutter_test/flutter_test.dart';

import 'package:budgetfamily/features/expenses/data/expense_models.dart';

void main() {
  group('ExpenseEntryRequest.toJson', () {
    test('sérialise la date au format ISO YYYY-MM-DD', () {
      final req = ExpenseEntryRequest(
        categorie: 'alimentation',
        montant: 42.5,
        dateOperation: DateTime(2026, 8, 9),
      );

      final json = req.toJson();

      expect(json['categorie'], 'alimentation');
      expect(json['montant'], 42.5);
      expect(json['date_operation'], '2026-08-09');
    });

    test('omet la date quand elle est absente', () {
      final req = ExpenseEntryRequest(categorie: 'loisirs', montant: 10);

      final json = req.toJson();

      expect(json.containsKey('date_operation'), isFalse);
      expect(json['categorie'], 'loisirs');
    });
  });
}
