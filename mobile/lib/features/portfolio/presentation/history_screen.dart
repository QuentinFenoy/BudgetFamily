import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/format.dart';
import '../../../core/network/api_exception.dart';
import '../application/allocation_providers.dart';
import '../data/allocation_models.dart';

String _formatDateTime(DateTime d) {
  final local = d.toLocal();
  String two(int n) => n.toString().padLeft(2, '0');
  return '${two(local.day)}/${two(local.month)}/${local.year} à ${two(local.hour)}:${two(local.minute)}';
}

String _methodeLabel(String m) => m == 'erc' ? 'Risk Parity' : 'HRP';

class HistoryScreen extends ConsumerWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final simulations = ref.watch(simulationsProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Historique des simulations')),
      body: simulations.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) => _ErrorState(
          message: error is ApiException ? error.message : "Impossible de charger l'historique.",
          onRetry: () => ref.invalidate(simulationsProvider),
        ),
        data: (liste) => liste.isEmpty
            ? const _Empty()
            : RefreshIndicator(
                onRefresh: () async => ref.invalidate(simulationsProvider),
                child: ListView.separated(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.all(16),
                  itemCount: liste.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 12),
                  itemBuilder: (_, i) => _SimulationTile(simulation: liste[i]),
                ),
              ),
      ),
    );
  }
}

class _SimulationTile extends StatelessWidget {
  const _SimulationTile({required this.simulation});

  final SimulationSummary simulation;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final s = simulation;

    return Card(
      elevation: 0,
      color: theme.colorScheme.surface,
      shape: RoundedRectangleBorder(
        side: BorderSide(color: theme.colorScheme.outline),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(_formatDateTime(s.createdAt), style: theme.textTheme.titleSmall),
                Chip(
                  label: Text(_methodeLabel(s.methode)),
                  visualDensity: VisualDensity.compact,
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Croissance ${(s.partCroissance * 100).toStringAsFixed(0)} %  ·  '
              'Défensif ${(s.partDefensive * 100).toStringAsFixed(0)} %',
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 4),
            Text(
              'Rendement ${(s.rendementAnnuelEspere * 100).toStringAsFixed(1)} %/an  ·  '
              'Volatilité ${(s.volatiliteAnnuelleEstimee * 100).toStringAsFixed(1)} %  ·  '
              'Sharpe ${s.ratioSharpeEstime.toStringAsFixed(2)}',
              style: theme.textTheme.bodySmall,
            ),
            if (s.montant != null) ...[
              const SizedBox(height: 4),
              Text(
                'Capital réparti : ${formatEuros(s.montant!)}',
                style: theme.textTheme.bodySmall?.copyWith(fontWeight: FontWeight.w600),
              ),
            ],
          ],
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
            Icon(Icons.inbox_outlined, size: 48, color: theme.colorScheme.primary),
            const SizedBox(height: 12),
            Text(
              'Aucune simulation enregistrée. Calculez une allocation puis '
              'enregistrez-la pour la retrouver ici.',
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
