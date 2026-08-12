/// Formatage d'affichage, volontairement sans dépendance aux données de locale
/// d'intl (pas d'initialisation à prévoir) : déterministe et testable.

const _moisFr = <String>[
  'janvier', 'février', 'mars', 'avril', 'mai', 'juin',
  'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre',
];

/// Formate un montant en euros, à la française : espace fine insécable comme
/// séparateur de milliers, virgule décimale. Ex. `formatEuros(1234.5, decimals: 2)`
/// -> `1 234,50 €`.
String formatEuros(double value, {int decimals = 0}) {
  final negative = value < 0;
  final fixed = value.abs().toStringAsFixed(decimals);
  final parts = fixed.split('.');
  final intPart = parts[0];

  final buffer = StringBuffer();
  for (var i = 0; i < intPart.length; i++) {
    if (i > 0 && (intPart.length - i) % 3 == 0) {
      buffer.write('\u202F'); // espace fine insécable
    }
    buffer.write(intPart[i]);
  }

  var result = buffer.toString();
  if (decimals > 0) {
    result = '$result,${parts[1]}';
  }
  return '${negative ? '-' : ''}$result\u00A0€';
}

/// Transforme une période `YYYY-MM` en libellé lisible, ex. `2026-08` -> `Août 2026`.
/// Renvoie l'entrée inchangée si elle n'est pas au format attendu.
String formatPeriode(String periode) {
  final parts = periode.split('-');
  if (parts.length != 2) return periode;
  final annee = int.tryParse(parts[0]);
  final mois = int.tryParse(parts[1]);
  if (annee == null || mois == null || mois < 1 || mois > 12) return periode;
  final nom = _moisFr[mois - 1];
  return '${nom[0].toUpperCase()}${nom.substring(1)} $annee';
}
