import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../application/savings_providers.dart';
import '../data/savings_models.dart';

double? _parseMontant(String raw) {
  final cleaned = raw
      .trim()
      .replaceAll(' ', '')
      .replaceAll('\u202F', '')
      .replaceAll('\u00A0', '')
      .replaceAll(',', '.');
  if (cleaned.isEmpty) return null;
  return double.tryParse(cleaned);
}

String _montantToText(double v) => v == v.roundToDouble() ? v.toInt().toString() : v.toString();

/// Feuille de création / édition d'un objectif d'épargne. Renvoie `true` via
/// Navigator.pop quand l'opération a réussi (le parent rafraîchit la liste).
class GoalFormSheet extends ConsumerStatefulWidget {
  const GoalFormSheet({this.goal, super.key});

  final SavingsGoal? goal;

  @override
  ConsumerState<GoalFormSheet> createState() => _GoalFormSheetState();
}

class _GoalFormSheetState extends ConsumerState<GoalFormSheet> {
  final _formKey = GlobalKey<FormState>();
  final _libelle = TextEditingController();
  final _cible = TextEditingController();
  final _actuel = TextEditingController(text: '0');
  int _priorite = 1;
  bool _submitting = false;

  bool get _isEdit => widget.goal != null;

  @override
  void initState() {
    super.initState();
    final g = widget.goal;
    if (g != null) {
      _libelle.text = g.libelle;
      _cible.text = _montantToText(g.montantCible);
      _actuel.text = _montantToText(g.montantActuel);
      _priorite = g.priorite;
    }
  }

  @override
  void dispose() {
    _libelle.dispose();
    _cible.dispose();
    _actuel.dispose();
    super.dispose();
  }

  String? _validateMontant(String? value, {bool strictPositif = false}) {
    final m = _parseMontant(value ?? '');
    if (m == null) return 'Montant attendu';
    if (strictPositif && m <= 0) return 'Doit être supérieur à 0';
    if (m < 0) return 'Doit être positif';
    return null;
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);
    final repo = ref.read(savingsRepositoryProvider);

    setState(() => _submitting = true);
    try {
      final libelle = _libelle.text.trim();
      final cible = _parseMontant(_cible.text)!;
      final actuel = _parseMontant(_actuel.text)!;
      if (_isEdit) {
        await repo.updateGoal(
          widget.goal!.id,
          libelle: libelle,
          montantCible: cible,
          montantActuel: actuel,
          priorite: _priorite,
        );
      } else {
        await repo.createGoal(
          libelle: libelle,
          montantCible: cible,
          montantActuel: actuel,
          priorite: _priorite,
        );
      }
      ref.invalidate(goalsProvider);
      if (!mounted) return;
      navigator.pop(true);
    } catch (error) {
      if (!mounted) return;
      setState(() => _submitting = false);
      messenger.showSnackBar(SnackBar(content: Text(error.toString())));
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              _isEdit ? 'Modifier l\'objectif' : 'Nouvel objectif',
              style: theme.textTheme.titleLarge,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _libelle,
              decoration: const InputDecoration(
                labelText: 'Nom',
                hintText: 'ex. Fonds d\'urgence, apport immobilier',
              ),
              validator: (v) => (v == null || v.trim().isEmpty) ? 'Requis' : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _cible,
              decoration: const InputDecoration(labelText: 'Montant cible (€)'),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              validator: (v) => _validateMontant(v, strictPositif: true),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _actuel,
              decoration: const InputDecoration(labelText: 'Déjà épargné (€)'),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              validator: (v) => _validateMontant(v),
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<int>(
              value: _priorite,
              decoration: const InputDecoration(labelText: 'Priorité (1 = prioritaire)'),
              items: const [
                DropdownMenuItem(value: 1, child: Text('1 — Prioritaire')),
                DropdownMenuItem(value: 2, child: Text('2')),
                DropdownMenuItem(value: 3, child: Text('3')),
                DropdownMenuItem(value: 4, child: Text('4')),
                DropdownMenuItem(value: 5, child: Text('5 — Secondaire')),
              ],
              onChanged: (v) => setState(() => _priorite = v ?? 1),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: _submitting ? null : _submit,
              child: _submitting
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : Text(_isEdit ? 'Enregistrer' : 'Créer l\'objectif'),
            ),
          ],
        ),
      ),
    );
  }
}
