import 'package:flutter_test/flutter_test.dart';

import 'package:budgetfamily/features/portfolio/data/asset_class_info.dart';

void main() {
  test('AssetClassInfo.fromJson parse définition et exemples', () {
    final json = {
      'cle': 'monetaire_liquidites',
      'nom': 'Monétaire et liquidités',
      'categorie': 'Défensif',
      'definition': 'Votre argent « au chaud » : disponible et sans risque sur le capital.',
      'exemples': ['Un Livret A ou un LDDS', 'Un fonds monétaire'],
    };

    final info = AssetClassInfo.fromJson(json);

    expect(info.cle, 'monetaire_liquidites');
    expect(info.nom, 'Monétaire et liquidités');
    expect(info.categorie, 'Défensif');
    expect(info.definition.isNotEmpty, isTrue);
    expect(info.exemples, hasLength(2));
    expect(info.exemples.first, 'Un Livret A ou un LDDS');
  });
}
