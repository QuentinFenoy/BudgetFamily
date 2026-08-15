import 'package:flutter_test/flutter_test.dart';

import 'package:budgetfamily/features/portfolio/data/allocation_models.dart';

void main() {
  group('PortfolioAllocation.fromJson', () {
    test('parse la réponse avec montants par classe', () {
      final json = {
        'profil_risque': 3,
        'age': 40,
        'horizon_annees': 20,
        'objectif': 'retraite_long_terme',
        'methode': 'hrp',
        'goal_id': null,
        'part_croissance': 0.6,
        'part_defensive': 0.4,
        'allocation': [
          {
            'classe': 'Actions monde développé',
            'categorie': 'Croissance',
            'part': 0.35,
            'montant': 3500.0,
          },
          {
            'classe': "Obligations d'État zone euro",
            'categorie': 'Défensif',
            'part': 0.25,
            'montant': 2500.0,
          },
        ],
        'rendement_annuel_espere': 0.055,
        'volatilite_annuelle_estimee': 0.11,
        'ratio_sharpe_estime': 0.32,
        'source_donnees': 'hypotheses_calibrees',
        'hypotheses': 'Hypothèses de marché long terme.',
        'avertissement': 'Ne constitue pas un conseil en investissement.',
      };

      final alloc = PortfolioAllocation.fromJson(json);

      expect(alloc.methode, 'hrp');
      expect(alloc.partCroissance, 0.6);
      expect(alloc.partDefensive, 0.4);
      expect(alloc.lignes, hasLength(2));
      expect(alloc.lignes.first.classe, 'Actions monde développé');
      expect(alloc.lignes.first.montant, 3500.0);
      expect(alloc.rendementAnnuelEspere, closeTo(0.055, 1e-9));
    });

    test('montant null quand aucun capital n\'est fourni', () {
      final json = {
        'profil_risque': null,
        'age': null,
        'horizon_annees': null,
        'objectif': 'aucun',
        'methode': 'erc',
        'goal_id': null,
        'part_croissance': 0.5,
        'part_defensive': 0.5,
        'allocation': [
          {
            'classe': 'Monétaire et liquidités',
            'categorie': 'Défensif',
            'part': 0.5,
            'montant': null,
          },
        ],
        'rendement_annuel_espere': 0.03,
        'volatilite_annuelle_estimee': 0.02,
        'ratio_sharpe_estime': 0.5,
        'source_donnees': 'hypotheses_calibrees',
        'hypotheses': 'x',
        'avertissement': 'y',
      };

      final alloc = PortfolioAllocation.fromJson(json);

      expect(alloc.methode, 'erc');
      expect(alloc.lignes.single.montant, isNull);
    });
  });
}
