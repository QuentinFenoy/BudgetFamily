/// Modèle de POST /v1/expenses. `date_operation` est optionnelle (défaut backend :
/// aujourd'hui) et sérialisée au format ISO `YYYY-MM-DD` attendu par FastAPI.

String _isoDate(DateTime d) =>
    '${d.year.toString().padLeft(4, '0')}-'
    '${d.month.toString().padLeft(2, '0')}-'
    '${d.day.toString().padLeft(2, '0')}';

class ExpenseEntryRequest {
  ExpenseEntryRequest({
    required this.categorie,
    required this.montant,
    this.dateOperation,
  });

  final String categorie;
  final double montant;
  final DateTime? dateOperation;

  Map<String, dynamic> toJson() => {
        'categorie': categorie,
        'montant': montant,
        if (dateOperation != null) 'date_operation': _isoDate(dateOperation!),
      };
}
