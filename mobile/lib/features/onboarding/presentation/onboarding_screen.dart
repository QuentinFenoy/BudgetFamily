import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../dashboard/application/dashboard_providers.dart';
import '../application/onboarding_controller.dart';
import '../data/onboarding_models.dart';

/// Convertit une saisie utilisateur ("1 200", "1200,50") en montant. Renvoie
/// null si non parsable — utilisé aussi bien par la validation que la soumission.
double? parseMontant(String raw) {
  final cleaned = raw
      .trim()
      .replaceAll(' ', '')
      .replaceAll('\u202F', '')
      .replaceAll('\u00A0', '')
      .replaceAll(',', '.');
  if (cleaned.isEmpty) return null;
  return double.tryParse(cleaned);
}

class _RevenuRow {
  IncomeType type = IncomeType.fixe;
  final TextEditingController libelle = TextEditingController();
  final TextEditingController montant = TextEditingController();

  void dispose() {
    libelle.dispose();
    montant.dispose();
  }
}

class _ChargeRow {
  final TextEditingController libelle = TextEditingController();
  final TextEditingController montant = TextEditingController();
  final TextEditingController categorie = TextEditingController();

  void dispose() {
    libelle.dispose();
    montant.dispose();
    categorie.dispose();
  }
}

class OnboardingScreen extends ConsumerStatefulWidget {
  const OnboardingScreen({super.key});

  @override
  ConsumerState<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends ConsumerState<OnboardingScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nbPersonnes = TextEditingController(text: '1');
  final _nbEnfants = TextEditingController(text: '0');
  final _age = TextEditingController();
  final _horizon = TextEditingController();

  String? _situation;
  Objectif _objectif = Objectif.aucun;
  int? _tolerance;
  bool _matelas = false;

  final List<_RevenuRow> _revenus = [_RevenuRow()];
  final List<_ChargeRow> _charges = [];

  @override
  void dispose() {
    _nbPersonnes.dispose();
    _nbEnfants.dispose();
    _age.dispose();
    _horizon.dispose();
    for (final r in _revenus) {
      r.dispose();
    }
    for (final c in _charges) {
      c.dispose();
    }
    super.dispose();
  }

  String? _validateEntier(String? value, {required int min, int? max, bool obligatoire = true}) {
    final trimmed = value?.trim() ?? '';
    if (trimmed.isEmpty) {
      return obligatoire ? 'Requis' : null;
    }
    final n = int.tryParse(trimmed);
    if (n == null) return 'Nombre entier attendu';
    if (n < min) return 'Minimum $min';
    if (max != null && n > max) return 'Maximum $max';
    return null;
  }

  String? _validateMontant(String? value) {
    final montant = parseMontant(value ?? '');
    if (montant == null) return 'Montant attendu';
    if (montant < 0) return 'Doit être positif';
    return null;
  }

  int? _entierOuNull(TextEditingController c) {
    final t = c.text.trim();
    return t.isEmpty ? null : int.parse(t);
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;

    final nbPers = int.parse(_nbPersonnes.text.trim());
    final nbEnf = int.parse(_nbEnfants.text.trim());
    final messenger = ScaffoldMessenger.of(context);

    if (nbEnf > nbPers) {
      messenger.showSnackBar(
        const SnackBar(content: Text("Le nombre d'enfants ne peut pas dépasser le foyer.")),
      );
      return;
    }
    if (_revenus.isEmpty) {
      messenger.showSnackBar(const SnackBar(content: Text('Ajoutez au moins un revenu.')));
      return;
    }

    final request = OnboardingRequest(
      nbPersonnes: nbPers,
      nbEnfants: nbEnf,
      situationFamiliale: _situation,
      age: _entierOuNull(_age),
      objectif: _objectif,
      toleranceRisque: _tolerance,
      horizonAnnees: _entierOuNull(_horizon),
      matelasSecuriteAtteint: _matelas,
      revenus: _revenus
          .map((r) => IncomeInput(
                type: r.type,
                libelle: r.libelle.text.trim(),
                montant: parseMontant(r.montant.text)!,
              ))
          .toList(),
      chargesFixes: _charges
          .map((c) => FixedExpenseInput(
                libelle: c.libelle.text.trim(),
                montant: parseMontant(c.montant.text)!,
                categorie: c.categorie.text.trim().isEmpty ? null : c.categorie.text.trim(),
              ))
          .toList(),
    );

    final ok = await ref.read(onboardingControllerProvider.notifier).submit(request);
    if (!mounted) return;

    if (ok) {
      // Le profil existe désormais : on force le rechargement du dashboard puis
      // on revient dessus (il affichera le budget au lieu du 404).
      ref.invalidate(dashboardProvider);
      context.pop();
    } else {
      final msg = ref.read(onboardingControllerProvider).errorMessage ?? 'Une erreur est survenue.';
      messenger.showSnackBar(SnackBar(content: Text(msg)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final submitState = ref.watch(onboardingControllerProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Votre profil')),
      body: SafeArea(
        child: Form(
          key: _formKey,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              Text(
                'Ces informations servent à calculer votre budget recommandé. '
                'Tous les montants sont mensuels.',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 16),

              _SectionTitle('Foyer'),
              Row(
                children: [
                  Expanded(
                    child: TextFormField(
                      controller: _nbPersonnes,
                      decoration: const InputDecoration(labelText: 'Personnes'),
                      keyboardType: TextInputType.number,
                      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                      validator: (v) => _validateEntier(v, min: 1),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: TextFormField(
                      controller: _nbEnfants,
                      decoration: const InputDecoration(labelText: 'Enfants'),
                      keyboardType: TextInputType.number,
                      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                      validator: (v) => _validateEntier(v, min: 0),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String?>(
                value: _situation,
                decoration: const InputDecoration(labelText: 'Situation familiale (facultatif)'),
                items: const [
                  DropdownMenuItem(value: null, child: Text('Non renseignée')),
                  DropdownMenuItem(value: 'celibataire', child: Text('Célibataire')),
                  DropdownMenuItem(value: 'couple', child: Text('En couple')),
                  DropdownMenuItem(value: 'famille_monoparentale', child: Text('Famille monoparentale')),
                  DropdownMenuItem(value: 'autre', child: Text('Autre')),
                ],
                onChanged: (v) => setState(() => _situation = v),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _age,
                decoration: const InputDecoration(labelText: 'Âge (facultatif)'),
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                validator: (v) => _validateEntier(v, min: 0, max: 120, obligatoire: false),
              ),

              const SizedBox(height: 24),
              _SectionTitle('Objectif et épargne'),
              DropdownButtonFormField<Objectif>(
                value: _objectif,
                decoration: const InputDecoration(labelText: 'Objectif principal'),
                items: Objectif.values
                    .map((o) => DropdownMenuItem(value: o, child: Text(o.label)))
                    .toList(),
                onChanged: (v) => setState(() => _objectif = v ?? Objectif.aucun),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<int?>(
                value: _tolerance,
                decoration: const InputDecoration(labelText: 'Tolérance au risque (facultatif)'),
                items: const [
                  DropdownMenuItem(value: null, child: Text('Non renseignée')),
                  DropdownMenuItem(value: 1, child: Text('1 — Très prudent')),
                  DropdownMenuItem(value: 2, child: Text('2 — Prudent')),
                  DropdownMenuItem(value: 3, child: Text('3 — Équilibré')),
                  DropdownMenuItem(value: 4, child: Text('4 — Dynamique')),
                  DropdownMenuItem(value: 5, child: Text('5 — Offensif')),
                ],
                onChanged: (v) => setState(() => _tolerance = v),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _horizon,
                decoration: const InputDecoration(
                  labelText: 'Horizon de placement en années (facultatif)',
                ),
                keyboardType: TextInputType.number,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                validator: (v) => _validateEntier(v, min: 0, obligatoire: false),
              ),
              const SizedBox(height: 4),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: const Text('Épargne de précaution déjà constituée'),
                subtitle: const Text('Au moins 3 mois de charges fixes de côté'),
                value: _matelas,
                onChanged: (v) => setState(() => _matelas = v),
              ),

              const SizedBox(height: 16),
              _SectionTitle('Revenus'),
              ..._revenus.asMap().entries.map((e) => _revenuCard(e.key, e.value)),
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton.icon(
                  icon: const Icon(Icons.add),
                  label: const Text('Ajouter un revenu'),
                  onPressed: () => setState(() => _revenus.add(_RevenuRow())),
                ),
              ),

              const SizedBox(height: 8),
              _SectionTitle('Charges fixes (facultatif)'),
              ..._charges.asMap().entries.map((e) => _chargeCard(e.key, e.value)),
              Align(
                alignment: Alignment.centerLeft,
                child: TextButton.icon(
                  icon: const Icon(Icons.add),
                  label: const Text('Ajouter une charge'),
                  onPressed: () => setState(() => _charges.add(_ChargeRow())),
                ),
              ),

              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: submitState.isSubmitting ? null : _submit,
                child: submitState.isSubmitting
                    ? const SizedBox(
                        height: 20,
                        width: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Text('Valider mon profil'),
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _revenuCard(int index, _RevenuRow row) {
    return Card(
      elevation: 1,
      margin: const EdgeInsets.symmetric(vertical: 6),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 12, 4, 12),
        child: Row(
          children: [
            Expanded(
              child: Column(
                children: [
                  Row(
                    children: [
                      Expanded(
                        flex: 3,
                        child: TextFormField(
                          controller: row.libelle,
                          decoration: const InputDecoration(labelText: 'Libellé'),
                          validator: (v) =>
                              (v == null || v.trim().isEmpty) ? 'Requis' : null,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        flex: 2,
                        child: TextFormField(
                          controller: row.montant,
                          decoration: const InputDecoration(labelText: 'Montant €'),
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          validator: _validateMontant,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<IncomeType>(
                    value: row.type,
                    decoration: const InputDecoration(labelText: 'Type'),
                    items: IncomeType.values
                        .map((t) => DropdownMenuItem(value: t, child: Text(t.label)))
                        .toList(),
                    onChanged: (v) => setState(() => row.type = v ?? IncomeType.fixe),
                  ),
                ],
              ),
            ),
            IconButton(
              icon: const Icon(Icons.delete_outline),
              tooltip: 'Supprimer',
              onPressed: _revenus.length == 1
                  ? null
                  : () => setState(() {
                        _revenus.removeAt(index).dispose();
                      }),
            ),
          ],
        ),
      ),
    );
  }

  Widget _chargeCard(int index, _ChargeRow row) {
    return Card(
      elevation: 1,
      margin: const EdgeInsets.symmetric(vertical: 6),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 12, 4, 12),
        child: Row(
          children: [
            Expanded(
              child: Row(
                children: [
                  Expanded(
                    flex: 3,
                    child: TextFormField(
                      controller: row.libelle,
                      decoration: const InputDecoration(labelText: 'Libellé'),
                      validator: (v) => (v == null || v.trim().isEmpty) ? 'Requis' : null,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    flex: 2,
                    child: TextFormField(
                      controller: row.montant,
                      decoration: const InputDecoration(labelText: 'Montant €'),
                      keyboardType: const TextInputType.numberWithOptions(decimal: true),
                      validator: _validateMontant,
                    ),
                  ),
                ],
              ),
            ),
            IconButton(
              icon: const Icon(Icons.delete_outline),
              tooltip: 'Supprimer',
              onPressed: () => setState(() {
                _charges.removeAt(index).dispose();
              }),
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(text, style: Theme.of(context).textTheme.titleMedium),
    );
  }
}
