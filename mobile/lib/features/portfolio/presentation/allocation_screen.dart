import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/format.dart';
import '../../../core/network/api_exception.dart';
import '../application/allocation_providers.dart';
import '../data/allocation_models.dart';
import '../data/asset_class_info.dart';

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

class AllocationScreen extends ConsumerStatefulWidget {
  const AllocationScreen({super.key});

  @override
  ConsumerState<AllocationScreen> createState() => _AllocationScreenState();
}

class _AllocationScreenState extends ConsumerState<AllocationScreen> {
  final _montant = TextEditingController();
  String _methode = 'hrp';
  bool _saving = false;

  @override
  void dispose() {
    _montant.dispose();
    super.dispose();
  }

  void _calculer() {
    FocusScope.of(context).unfocus();
    ref.read(allocationControllerProvider.notifier).load(
          methode: _methode,
          montant: _parseMontant(_montant.text),
        );
  }

  Future<void> _enregistrer() async {
    setState(() => _saving = true);
    final ok = await ref.read(allocationControllerProvider.notifier).saveCurrent(
          methode: _methode,
          montant: _parseMontant(_montant.text),
        );
    if (!mounted) return;
    setState(() => _saving = false);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(ok ? 'Simulation enregistrée.' : "Échec de l'enregistrement.")),
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(allocationControllerProvider);
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Allocation d\'investissement'),
        actions: [
          IconButton(
            icon: const Icon(Icons.history),
            tooltip: 'Historique',
            onPressed: () => context.push('/portfolio/history'),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              'Répartition indicative par classe d\'actifs générique, adaptée à votre '
              'profil (risque, âge, horizon, objectif). Renseignez le capital total '
              'déjà placé pour obtenir des montants.',
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _montant,
              decoration: const InputDecoration(
                labelText: 'Capital total placé (€, facultatif)',
                hintText: 'ex. 15000',
              ),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
            ),
            const SizedBox(height: 16),
            Text('Méthode de répartition', style: theme.textTheme.labelLarge),
            const SizedBox(height: 6),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'hrp', label: Text('HRP')),
                ButtonSegment(value: 'erc', label: Text('Risk Parity')),
              ],
              selected: {_methode},
              onSelectionChanged: (s) => setState(() => _methode = s.first),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: state.isLoading ? null : _calculer,
              icon: state.isLoading
                  ? const SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.calculate_outlined),
              label: const Text('Calculer mon allocation'),
            ),
            const SizedBox(height: 24),
            state.when(
              loading: () => const SizedBox.shrink(),
              data: (allocation) => allocation == null
                  ? _Hint(theme: theme)
                  : _AllocationResult(allocation: allocation),
              error: (error, _) => _ErrorArea(error: error, onRetry: _calculer),
            ),
            if (state.valueOrNull != null) ...[
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: _saving ? null : _enregistrer,
                icon: _saving
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.bookmark_add_outlined),
                label: const Text('Enregistrer dans l\'historique'),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _Hint extends StatelessWidget {
  const _Hint({required this.theme});

  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    return Text(
      'Lancez le calcul pour voir votre répartition recommandée.',
      style: theme.textTheme.bodyMedium?.copyWith(color: theme.hintColor),
    );
  }
}

class _AllocationResult extends ConsumerWidget {
  const _AllocationResult({required this.allocation});

  final PortfolioAllocation allocation;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final theme = Theme.of(context);
    final infos = ref.watch(assetClassesProvider).valueOrNull;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        _SplitBar(
          croissance: allocation.partCroissance,
          defensive: allocation.partDefensive,
        ),
        const SizedBox(height: 20),
        Text('Répartition par classe d\'actifs', style: theme.textTheme.titleMedium),
        const SizedBox(height: 8),
        ...allocation.lignes.map((l) => _ClassTile(ligne: l, info: infos?[l.classe])),
        const SizedBox(height: 20),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: [
            _StatChip(
              label: 'Rendement espéré',
              value: '${(allocation.rendementAnnuelEspere * 100).toStringAsFixed(1)} %/an',
            ),
            _StatChip(
              label: 'Volatilité',
              value: '${(allocation.volatiliteAnnuelleEstimee * 100).toStringAsFixed(1)} %',
            ),
            _StatChip(
              label: 'Ratio de Sharpe',
              value: allocation.ratioSharpeEstime.toStringAsFixed(2),
            ),
          ],
        ),
        const SizedBox(height: 16),
        Text(allocation.hypotheses, style: theme.textTheme.bodySmall),
        const SizedBox(height: 16),
        _Disclaimer(texte: allocation.avertissement),
      ],
    );
  }
}

class _SplitBar extends StatelessWidget {
  const _SplitBar({required this.croissance, required this.defensive});

  final double croissance;
  final double defensive;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final flexCroissance = (croissance * 1000).round().clamp(1, 1000);
    final flexDefensive = (defensive * 1000).round().clamp(1, 1000);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: Row(
            children: [
              Expanded(
                flex: flexCroissance,
                child: Container(height: 24, color: theme.colorScheme.primary),
              ),
              Expanded(
                flex: flexDefensive,
                child: Container(height: 24, color: theme.colorScheme.tertiary),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            _Legend(
              color: theme.colorScheme.primary,
              label: 'Croissance ${(croissance * 100).toStringAsFixed(0)} %',
            ),
            _Legend(
              color: theme.colorScheme.tertiary,
              label: 'Défensif ${(defensive * 100).toStringAsFixed(0)} %',
            ),
          ],
        ),
      ],
    );
  }
}

class _Legend extends StatelessWidget {
  const _Legend({required this.color, required this.label});

  final Color color;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(width: 12, height: 12, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
        const SizedBox(width: 6),
        Text(label, style: Theme.of(context).textTheme.bodySmall),
      ],
    );
  }
}

class _ClassTile extends StatelessWidget {
  const _ClassTile({required this.ligne, this.info});

  final AllocationLine ligne;
  final AssetClassInfo? info;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final estCroissance = ligne.categorie.toLowerCase().startsWith('croissance');
    final couleur = estCroissance ? theme.colorScheme.primary : theme.colorScheme.tertiary;
    final tappable = info != null;

    return InkWell(
      onTap: tappable ? () => _showClassInfo(context, info!) : null,
      borderRadius: BorderRadius.circular(8),
      child: Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Row(
                  children: [
                    Flexible(child: Text(ligne.classe, style: theme.textTheme.titleSmall)),
                    if (tappable) ...[
                      const SizedBox(width: 4),
                      Icon(Icons.info_outline, size: 15, color: theme.colorScheme.outline),
                    ],
                  ],
                ),
              ),
              Text(
                ligne.montant != null
                    ? '${(ligne.part * 100).toStringAsFixed(1)} %  ·  ${formatEuros(ligne.montant!)}'
                    : '${(ligne.part * 100).toStringAsFixed(1)} %',
                style: theme.textTheme.bodyMedium,
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: ligne.part.clamp(0, 1).toDouble(),
              minHeight: 6,
              color: couleur,
            ),
          ),
        ],
      ),
      ),
    );
  }
}

void _showClassInfo(BuildContext context, AssetClassInfo info) {
  showModalBottomSheet<void>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (context) {
      final theme = Theme.of(context);
      return Padding(
        padding: EdgeInsets.only(
          left: 20,
          right: 20,
          bottom: 24 + MediaQuery.of(context).viewInsets.bottom,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(info.nom, style: theme.textTheme.titleLarge),
            const SizedBox(height: 4),
            Text(
              info.categorie,
              style: theme.textTheme.labelMedium?.copyWith(color: theme.colorScheme.primary),
            ),
            const SizedBox(height: 16),
            Text(info.definition, style: theme.textTheme.bodyMedium),
            const SizedBox(height: 20),
            Text('Exemples', style: theme.textTheme.titleSmall),
            const SizedBox(height: 8),
            ...info.exemples.map(
              (ex) => Padding(
                padding: const EdgeInsets.only(bottom: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Icon(Icons.circle, size: 6, color: theme.colorScheme.outline),
                    ),
                    const SizedBox(width: 8),
                    Expanded(child: Text(ex, style: theme.textTheme.bodyMedium)),
                  ],
                ),
              ),
            ),
          ],
        ),
      );
    },
  );
}

class _StatChip extends StatelessWidget {
  const _StatChip({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: theme.colorScheme.primaryContainer,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label, style: theme.textTheme.bodySmall),
          const SizedBox(height: 2),
          Text(value, style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}

class _Disclaimer extends StatelessWidget {
  const _Disclaimer({required this.texte});

  final String texte;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      color: theme.colorScheme.surface,
      shape: RoundedRectangleBorder(
        side: BorderSide(color: theme.colorScheme.outline),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(Icons.info_outline, size: 18, color: theme.colorScheme.onSurfaceVariant),
            const SizedBox(width: 8),
            Expanded(
              child: Text(texte, style: theme.textTheme.bodySmall),
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorArea extends StatelessWidget {
  const _ErrorArea({required this.error, required this.onRetry});

  final Object error;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    if (error is ApiException && (error as ApiException).isForbidden) {
      return _Message(
        icon: Icons.workspace_premium_outlined,
        message: 'L\'allocation d\'investissement est réservée à l\'offre payante.',
      );
    }
    if (error is ApiException && (error as ApiException).isNotFound) {
      return _Message(
        icon: Icons.person_outline,
        message: 'Complétez d\'abord votre profil pour obtenir une allocation.',
      );
    }

    return Column(
      children: [
        Icon(Icons.cloud_off, size: 48, color: theme.colorScheme.error),
        const SizedBox(height: 12),
        Text(
          error is ApiException ? (error as ApiException).message : 'Une erreur est survenue.',
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          icon: const Icon(Icons.refresh),
          label: const Text('Réessayer'),
          onPressed: onRetry,
        ),
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
        padding: const EdgeInsets.symmetric(vertical: 24),
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
