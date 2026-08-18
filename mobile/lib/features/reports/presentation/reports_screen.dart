import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/format.dart';
import '../../../core/network/api_exception.dart';
import '../../dashboard/data/dashboard_models.dart';
import '../application/report_providers.dart';
import '../data/report_models.dart';

String _shiftMonth(String ym, int delta) {
  final parts = ym.split('-');
  var y = int.parse(parts[0]);
  var m = int.parse(parts[1]) + delta;
  while (m < 1) {
    m += 12;
    y -= 1;
  }
  while (m > 12) {
    m -= 12;
    y += 1;
  }
  return '${y.toString().padLeft(4, '0')}-${m.toString().padLeft(2, '0')}';
}

String _currentMonth() {
  final n = DateTime.now();
  return '${n.year.toString().padLeft(4, '0')}-${n.month.toString().padLeft(2, '0')}';
}

class ReportsScreen extends ConsumerStatefulWidget {
  const ReportsScreen({super.key});

  @override
  ConsumerState<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends ConsumerState<ReportsScreen> {
  String _mode = 'mensuel';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Bilans')),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: 'mensuel', label: Text('Mensuel')),
                  ButtonSegment(value: 'trimestriel', label: Text('Trimestriel')),
                ],
                selected: {_mode},
                onSelectionChanged: (s) => setState(() => _mode = s.first),
              ),
            ),
            Expanded(
              child: _mode == 'mensuel' ? const _MonthlyView() : const _QuarterlyView(),
            ),
          ],
        ),
      ),
    );
  }
}

class _MonthlyView extends ConsumerWidget {
  const _MonthlyView();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final mois = ref.watch(selectedMonthProvider);
    final report = ref.watch(monthlyReportProvider);
    final peutAvancer = mois.compareTo(_currentMonth()) < 0;

    return Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            IconButton(
              icon: const Icon(Icons.chevron_left),
              onPressed: () =>
                  ref.read(selectedMonthProvider.notifier).state = _shiftMonth(mois, -1),
            ),
            Text(formatPeriode(mois), style: theme.textTheme.titleMedium),
            IconButton(
              icon: const Icon(Icons.chevron_right),
              onPressed: peutAvancer
                  ? () => ref.read(selectedMonthProvider.notifier).state = _shiftMonth(mois, 1)
                  : null,
            ),
          ],
        ),
        Expanded(
          child: report.when(
            loading: () => const Center(child: CircularProgressIndicator()),
            error: (error, _) => _ErrorState(
              message: error is ApiException ? error.message : 'Impossible de charger le bilan.',
              onRetry: () => ref.invalidate(monthlyReportProvider),
            ),
            data: (r) => _MonthlyContent(report: r),
          ),
        ),
      ],
    );
  }
}

class _MonthlyContent extends StatelessWidget {
  const _MonthlyContent({required this.report});

  final MonthlyReport report;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final ecart = report.ecartEpargneVsReference;
    final positif = ecart >= 0;
    final couleurEcart = positif ? theme.colorScheme.tertiary : theme.colorScheme.error;

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
      children: [
        Card(
          elevation: 0,
          color: theme.colorScheme.primaryContainer,
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Épargne réalisée ce mois', style: theme.textTheme.bodyMedium),
                Text(
                  formatEuros(report.epargneRealiseeEstimee),
                  style: theme.textTheme.headlineMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.onPrimaryContainer,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  positif
                      ? '${formatEuros(ecart)} au-dessus de la référence (${formatEuros(report.epargneReferenceMontant)})'
                      : '${formatEuros(ecart.abs())} en dessous de la référence (${formatEuros(report.epargneReferenceMontant)})',
                  style: theme.textTheme.bodySmall?.copyWith(color: couleurEcart, fontWeight: FontWeight.w600),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(child: _Stat(label: 'Dépensé', value: formatEuros(report.totalRealise))),
            Expanded(child: _Stat(label: 'Recommandé', value: formatEuros(report.totalRecommande))),
          ],
        ),
        const SizedBox(height: 20),
        Text('Par catégorie', style: theme.textTheme.titleMedium),
        const SizedBox(height: 8),
        ...report.categories.map((c) => _CategoryRow(status: c)),
      ],
    );
  }
}

class _CategoryRow extends StatelessWidget {
  const _CategoryRow({required this.status});

  final CategoryBudgetStatus status;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final couleur = status.depasse ? theme.colorScheme.error : theme.colorScheme.primary;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(status.libelle, style: theme.textTheme.titleSmall),
              Text(
                '${formatEuros(status.montantRealise)} / ${formatEuros(status.montantRecommande)}',
                style: theme.textTheme.bodySmall,
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(value: status.progression, color: couleur),
          ),
        ],
      ),
    );
  }
}

class _QuarterlyView extends ConsumerWidget {
  const _QuarterlyView();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final report = ref.watch(quarterlyReportProvider);

    return report.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, _) {
        if (error is ApiException && error.isForbidden) {
          return const _Message(
            icon: Icons.workspace_premium_outlined,
            message: 'Le bilan trimestriel est réservé à l\'offre payante.',
          );
        }
        return _ErrorState(
          message: error is ApiException ? error.message : 'Impossible de charger le bilan.',
          onRetry: () => ref.invalidate(quarterlyReportProvider),
        );
      },
      data: (r) => _QuarterlyContent(report: r),
    );
  }
}

class _QuarterlyContent extends StatelessWidget {
  const _QuarterlyContent({required this.report});

  final QuarterlyReport report;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final maxEpargne = report.tendances
        .map((t) => t.epargneRealiseeEstimee)
        .fold<double>(1, (a, b) => b > a ? b : a);

    return ListView(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
      children: [
        Text('Épargne réalisée sur 3 mois', style: theme.textTheme.titleMedium),
        const SizedBox(height: 12),
        ...report.tendances.map((t) {
          final fraction = (t.epargneRealiseeEstimee.clamp(0, maxEpargne) / maxEpargne).toDouble();
          final negatif = t.epargneRealiseeEstimee < 0;
          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(formatPeriode(t.periode), style: theme.textTheme.titleSmall),
                    Text(
                      formatEuros(t.epargneRealiseeEstimee),
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: negatif ? theme.colorScheme.error : theme.colorScheme.onSurface,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: negatif ? 0 : fraction,
                    minHeight: 10,
                    color: theme.colorScheme.tertiary,
                  ),
                ),
              ],
            ),
          );
        }),
        const SizedBox(height: 20),
        Card(
          elevation: 0,
          color: theme.colorScheme.surface,
          shape: RoundedRectangleBorder(
            side: BorderSide(color: theme.colorScheme.outline),
            borderRadius: BorderRadius.circular(12),
          ),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                _Ligne(label: 'Épargne totale du trimestre', value: formatEuros(report.epargneTotaleTrimestre)),
                const Divider(height: 20),
                _Ligne(label: 'Dépense moyenne / mois', value: formatEuros(report.moyenneTotaleRealisee)),
                const Divider(height: 20),
                _Ligne(
                  label: 'Mois courant vs moyenne',
                  value: (report.ecartMoisCourantVsMoyenne >= 0 ? '+' : '') +
                      formatEuros(report.ecartMoisCourantVsMoyenne),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: theme.textTheme.bodySmall),
        const SizedBox(height: 2),
        Text(value, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
      ],
    );
  }
}

class _Ligne extends StatelessWidget {
  const _Ligne({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Flexible(child: Text(label, style: theme.textTheme.bodyMedium)),
        Text(value, style: theme.textTheme.titleSmall),
      ],
    );
  }
}

class _Message extends StatelessWidget {
  const _Message({required this.icon, required this.message});

  final IconData icon;
  final String message;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 48, color: theme.colorScheme.primary),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center, style: theme.textTheme.bodyLarge),
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
