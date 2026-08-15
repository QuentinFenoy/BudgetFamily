import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/format.dart';
import '../../../core/network/api_exception.dart';
import '../application/savings_providers.dart';
import '../data/savings_models.dart';
import 'goal_form_sheet.dart';
import 'repartition_sheet.dart';

Future<void> _ouvrirFormulaire(BuildContext context, {SavingsGoal? goal}) async {
  final ok = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (_) => GoalFormSheet(goal: goal),
  );
  if (ok == true && context.mounted) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Objectif enregistré.')),
    );
  }
}

Future<void> _confirmerSuppression(BuildContext context, WidgetRef ref, SavingsGoal goal) async {
  final confirme = await showDialog<bool>(
    context: context,
    builder: (_) => AlertDialog(
      title: const Text('Supprimer cet objectif ?'),
      content: Text('« ${goal.libelle} » sera définitivement supprimé.'),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Annuler')),
        FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Supprimer')),
      ],
    ),
  );
  if (confirme != true) return;

  final messenger = ScaffoldMessenger.of(context);
  try {
    await ref.read(savingsRepositoryProvider).deleteGoal(goal.id);
    ref.invalidate(goalsProvider);
    messenger.showSnackBar(const SnackBar(content: Text('Objectif supprimé.')));
  } on ApiException catch (e) {
    messenger.showSnackBar(SnackBar(content: Text(e.message)));
  }
}

class SavingsScreen extends ConsumerWidget {
  const SavingsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final goals = ref.watch(goalsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Objectifs d\'épargne'),
        actions: [
          if (goals.valueOrNull?.isNotEmpty ?? false)
            IconButton(
              icon: const Icon(Icons.calculate_outlined),
              tooltip: 'Répartir mon épargne',
              onPressed: () => showModalBottomSheet<void>(
                context: context,
                isScrollControlled: true,
                showDragHandle: true,
                builder: (_) => RepartitionSheet(goals: goals.value ?? const []),
              ),
            ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _ouvrirFormulaire(context),
        icon: const Icon(Icons.add),
        label: const Text('Objectif'),
      ),
      body: goals.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => _ErrorState(
          message: error is ApiException ? error.message : 'Impossible de charger vos objectifs.',
          onRetry: () => ref.invalidate(goalsProvider),
        ),
        data: (liste) => liste.isEmpty
            ? const _Empty()
            : RefreshIndicator(
                onRefresh: () async => ref.invalidate(goalsProvider),
                child: ListView.separated(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(16, 16, 16, 88),
                  itemCount: liste.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemBuilder: (_, i) => _GoalCard(goal: liste[i]),
                ),
              ),
      ),
    );
  }
}

class _GoalCard extends ConsumerWidget {
  const _GoalCard({required this.goal});

  final SavingsGoal goal;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);

    return Card(
      elevation: 0,
      color: theme.colorScheme.surface,
      shape: RoundedRectangleBorder(
        side: BorderSide(color: theme.colorScheme.outline),
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        onTap: () => _ouvrirFormulaire(context, goal: goal),
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(goal.libelle, style: theme.textTheme.titleMedium),
                  ),
                  Chip(
                    label: Text('P${goal.priorite}'),
                    visualDensity: VisualDensity.compact,
                  ),
                  IconButton(
                    icon: const Icon(Icons.delete_outline),
                    tooltip: 'Supprimer',
                    onPressed: () => _confirmerSuppression(context, ref, goal),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: goal.progression,
                  minHeight: 8,
                  color: goal.estAtteint ? theme.colorScheme.tertiary : theme.colorScheme.primary,
                ),
              ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '${formatEuros(goal.montantActuel)} / ${formatEuros(goal.montantCible)}',
                    style: theme.textTheme.bodyMedium,
                  ),
                  Text(
                    goal.estAtteint ? 'Atteint ✓' : 'Il reste ${formatEuros(goal.montantRestant)}',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: goal.estAtteint ? theme.colorScheme.tertiary : theme.colorScheme.onSurface,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  const _Empty();

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.savings_outlined, size: 56, color: theme.colorScheme.primary),
            const SizedBox(height: 16),
            Text(
              'Aucun objectif pour le moment. Créez-en un (fonds d\'urgence, apport, '
              'voyage…) pour épargner vers un but précis.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium,
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.cloud_off, size: 48, color: theme.colorScheme.error),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 16),
            OutlinedButton.icon(
              icon: const Icon(Icons.refresh),
              label: const Text('Réessayer'),
              onPressed: onRetry,
            ),
          ],
        ),
      ),
    );
  }
}
