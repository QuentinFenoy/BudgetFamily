import 'package:flutter_test/flutter_test.dart';

import 'package:budgetfamily/features/savings/data/savings_models.dart';

void main() {
  test('PlanEpargne.fromJson parse capacité et objectifs premium', () {
    final json = {
      'capacite_epargne_mensuelle': 624.0,
      'methode': 'cascade',
      'premium': true,
      'note_rendement_brut': 'Note fiscalité indicative.',
      'objectifs': [
        {
          'objectif_id': '1',
          'libelle': 'Retraite',
          'montant_cible': 50000.0,
          'montant_actuel': 0.0,
          'montant_restant': 50000.0,
          'priorite': 1,
          'horizon_mois': 60,
          'mensualite_attribuee': 624.0,
          'mois_restants_au_rythme_actuel': 81.0,
          'rendement_net_annuel_requis': 0.119,
          'realisable': 'Difficile.',
          'risque_note': 5,
          'volatilite_estimee': 0.127,
          'au_dela_frontiere': true,
          'bruts_par_enveloppe': [
            {'enveloppe': 'Livret A / LDDS', 'taux_imposition': 0.0, 'rendement_brut_indicatif': 0.119},
            {'enveloppe': 'Compte-titres (flat tax)', 'taux_imposition': 0.30, 'rendement_brut_indicatif': 0.17},
          ],
        },
      ],
    };

    final plan = PlanEpargne.fromJson(json);

    expect(plan.capaciteEpargneMensuelle, 624.0);
    expect(plan.premium, isTrue);
    final o = plan.objectifs.single;
    expect(o.libelle, 'Retraite');
    expect(o.horizonMois, 60);
    expect(o.rendementNetAnnuelRequis, 0.119);
    expect(o.risqueNote, 5);
    expect(o.auDelaFrontiere, isTrue);
    expect(o.brutsParEnveloppe, hasLength(2));
    expect(o.brutsParEnveloppe.last.rendementBrutIndicatif, 0.17);
  });

  test('PlanEpargne.fromJson gère un objectif gratuit sans champs premium', () {
    final json = {
      'capacite_epargne_mensuelle': 300.0,
      'methode': 'cascade',
      'premium': false,
      'note_rendement_brut': '',
      'objectifs': [
        {
          'objectif_id': '2',
          'libelle': 'Voyage',
          'montant_cible': 3000.0,
          'montant_actuel': 500.0,
          'montant_restant': 2500.0,
          'priorite': 2,
          'horizon_mois': null,
          'mensualite_attribuee': 300.0,
          'mois_restants_au_rythme_actuel': 9.0,
        },
      ],
    };

    final plan = PlanEpargne.fromJson(json);
    final o = plan.objectifs.single;

    expect(plan.premium, isFalse);
    expect(o.horizonMois, isNull);
    expect(o.rendementNetAnnuelRequis, isNull);
    expect(o.brutsParEnveloppe, isEmpty);
    expect(o.moisRestantsAuRythmeActuel, 9.0);
  });
}
