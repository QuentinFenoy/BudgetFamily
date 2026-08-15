import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/format.dart';
import '../../../core/network/api_exception.dart';
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

/// Feuille de répartition automatique d'un montant d'épargne entre les objectifs
/// existants de l'utilisateur (via /savings/repartition-auto).
class RepartitionSheet extends ConsumerStatefulWidget {
  const RepartitionSheet({required this.goals, super.key});

  final List<SavingsGoal> goals;

  @override
  ConsumerState<RepartitionSheet> createState() => _RepartitionSheetState();
}

class _RepartitionSheetState extends ConsumerState<RepartitionSheet> {
  final _montant = TextEditingController();
  String _methode = 'cascade';
  bool _loading = false;
  String? _error;
  RepartitionResult? _result;

  @override
  void dispose() {
    _montant.dispose();
    super.dispose();
  }

  Future<void> _repartir() async {
    final montant = _parseMontant(_montant.text);
    if (montant == null || montant < 0) {
      setState(() => _error = 'Montant attendu.');
      return;
    }
    FocusScope.of(context).unfocus();
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await ref.read(savingsRepositoryProvider).repartitionAuto(
            epargneDisponible: montant,
            methode: _methode,
          );
      if (!mounted) return;
      setState(() {
        _loading = false;
        _result = result;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = e.message;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final libelles = {for (final g in widget.goals) g.id.toString(): g.libelle};

    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Répartir mon épargne', style: theme.textTheme.titleLarge),
            const SizedBox(height: 4),
            Text(
              'Répartit un montant entre vos objectifs, selon leur priorité.',
              style: theme.textTheme.bodySmall,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _montant,
              decoration: const InputDecoration(labelText: 'Montant à répartir (€)'),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
            ),
            const SizedBox(height: 12),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'cascade', label: Text('Par priorité')),
                ButtonSegment(value: 'proportionnelle', label: Text('Proportionnelle')),
              ],
              selected: {_methode},
              onSelectionChanged: (s) => setState(() => _methode = s.first),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: _loading ? null : _repartir,
              icon: _loading
                  ? const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.calculate_outlined),
              label: const Text('Répartir'),
            ),
            if (_error != null) ...[
              const SizedBox(height: 12),
              Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
            ],
            if (_result != null) ...[
              const SizedBox(height: 20),
              ..._result!.allocations.map((a) {
                final libelle = libelles[a.objectifId] ?? 'Objectif ${a.objectifId}';
                final mois = a.moisRestantsEstimes;
                return Padding(
                  padding: const EdgeInsets.symmetric(vertical: 6),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(child: Text(libelle, style: theme.textTheme.bodyLarge)),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.end,
                        children: [
                          Text(
                            formatEuros(a.montantAlloueCeMois),
                            style: theme.textTheme.titleSmall,
                          ),
                          if (mois != null && mois.isFinite)
                            Text(
                              '~${mois.ceil()} mois restants',
                              style: theme.textTheme.bodySmall,
                            ),
                        ],
                      ),
                    ],
                  ),
                );
              }),
              const Divider(height: 24),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text('Non alloué', style: theme.textTheme.bodyMedium),
                  Text(formatEuros(_result!.epargneNonAllouee), style: theme.textTheme.titleSmall),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}
