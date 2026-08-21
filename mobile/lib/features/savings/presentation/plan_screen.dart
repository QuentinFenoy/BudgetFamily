import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/format.dart';
import '../../../core/network/api_exception.dart';
import '../application/savings_providers.dart';
import '../data/savings_models.dart';

String _pct(double v) => '${(v * 100).toStringAsFixed(1)} %';

Color _couleurFaisabilite(ThemeData theme, double? rendementNet) {
  if (rendementNet == null) return theme.colorScheme.error;
  if (rendementNet <= 0.04) return theme.colorScheme.primary;
  if (rendementNet <= 0.08) return theme.colorScheme.tertiary;
  return theme.colorScheme.error;
}

void _montrerBruts(BuildContext context, PlanObjectif objectif, String note) {
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
            Text('Rendement brut à viser', style: theme.textTheme.titleLarge),
            const SizedBox(height: 4),
            Text(
              'Pour obtenir le rendement net requis une fois la fiscalité déduite :',
              style: theme.textTheme.bodyMedium,
            ),
            const SizedBox(height: 16),
            ...objectif.brutsParEnveloppe.map(
              (b) => Padding(
                padding: const EdgeInsets.symmetric(vertical: 6),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(child: Text(b.enveloppe, style: theme.textTheme.bodyLarge)),
                    Text(
                      _pct(b.rendementBrutIndicatif),
                      style: theme.textTheme.titleSmall,
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(note, style: theme.textTheme.bodySmall),
          ],
        ),
      );
    },
  );
}

class PlanScreen extends ConsumerWidget {
  const PlanScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final plan = ref.watch(planProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Plan d\'épargne')),
      body: plan.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) {
          final estProfil = error is ApiException && error.isNotFound;
          return _Message(
            icon: estProfil ? Icons.person_outline : Icons.cloud_off,
            message: estProfil
                ? 'Complétez d\'abord votre profil pour estimer votre capacité d\'épargne.'
                : (error is ApiException ? error.message : 'Impossible de charger le plan.'),
            onRetry: () => ref.invalidate(planProvider),
          );
        },
        data: (p) => RefreshIndicator(
          onRefresh: () async => ref.invalidate(planProvider),
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            children: [
              _CapaciteCard(capacite: p.capaciteEpargneMensuelle),
              const SizedBox(height: 16),
              if (p.objectifs.isEmpty)
                const _Empty()
              else ...[
                ...p.objectifs.map((o) => Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: _PlanGoalCard(objectif: o, premium: p.premium, note: p.noteRendementBrut),
                    )),
                if (!p.premium) const _PremiumHint(),
              ],
            ],
          ),
        ),
      ),
    );
  }
}

class _CapaciteCard extends StatelessWidget {
  const _CapaciteCard({required this.capacite});

  final double capacite;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      elevation: 0,
      color: theme.colorScheme.primaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Capacité d\'épargne mensuelle', style: theme.textTheme.bodyMedium),
            Text(
              '${formatEuros(capacite)} / mois',
              style: theme.textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.onPrimaryContainer,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              'Répartie entre vos objectifs par ordre de priorité.',
              style: theme.textTheme.bodySmall,
            ),
          ],
        ),
      ),
    );
  }
}

class _PlanGoalCard extends StatelessWidget {
  const _PlanGoalCard({required this.objectif, required this.premium, required this.note});

  final PlanObjectif objectif;
  final bool premium;
  final String note;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final o = objectif;

    final horizonTexte =
        o.horizonMois != null ? 'en ${o.horizonMois} mois' : 'durée non renseignée';
    final rythmeTexte = o.mensualiteAttribuee <= 0
        ? 'Aucune part ce mois-ci (priorité plus basse)'
        : (o.moisRestantsAuRythmeActuel != null
            ? 'À ce rythme : ~${o.moisRestantsAuRythmeActuel!.ceil()} mois'
            : 'À ce rythme : objectif non atteint');

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
              children: [
                Expanded(child: Text(o.libelle, style: theme.textTheme.titleMedium)),
                Chip(label: Text('P${o.priorite}'), visualDensity: VisualDensity.compact),
              ],
            ),
            const SizedBox(height: 4),
            Text('Cible : ${formatEuros(o.montantCible)} · $horizonTexte',
                style: theme.textTheme.bodyMedium),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Attribué', style: theme.textTheme.bodySmall),
                Text('${formatEuros(o.mensualiteAttribuee)} / mois',
                    style: theme.textTheme.titleSmall),
              ],
            ),
            Text(rythmeTexte, style: theme.textTheme.bodySmall),
            if (premium) _blocPremium(context, theme),
          ],
        ),
      ),
    );
  }

  Widget _blocPremium(BuildContext context, ThemeData theme) {
    final o = objectif;
    if (o.horizonMois == null || o.realisable == null) {
      return Padding(
        padding: const EdgeInsets.only(top: 8),
        child: Text(
          'Renseignez une durée pour obtenir le rendement requis et la faisabilité.',
          style: theme.textTheme.bodySmall?.copyWith(color: theme.hintColor),
        ),
      );
    }

    final couleur = _couleurFaisabilite(theme, o.rendementNetAnnuelRequis);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Divider(height: 20),
        if (o.rendementNetAnnuelRequis != null && o.rendementNetAnnuelRequis! > 0) ...[
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text('Rendement net requis', style: theme.textTheme.bodyMedium),
              Row(
                children: [
                  Text('${_pct(o.rendementNetAnnuelRequis!)}/an',
                      style: theme.textTheme.titleSmall?.copyWith(color: couleur)),
                  IconButton(
                    icon: const Icon(Icons.info_outline, size: 18),
                    tooltip: 'Rendement brut par enveloppe',
                    visualDensity: VisualDensity.compact,
                    onPressed: () => _montrerBruts(context, o, note),
                  ),
                ],
              ),
            ],
          ),
          if (o.risqueNote != null && o.risqueNote! > 0)
            Text(
              'Risque : ${o.risqueNote}/5'
              '${o.volatiliteEstimee != null ? ' · volatilité ~${_pct(o.volatiliteEstimee!)}' : ''}'
              '${o.auDelaFrontiere ? ' (au-delà d\'un portefeuille diversifié)' : ''}',
              style: theme.textTheme.bodySmall,
            ),
          const SizedBox(height: 6),
        ],
        Text(
          o.realisable!,
          style: theme.textTheme.bodyMedium?.copyWith(color: couleur, fontWeight: FontWeight.w600),
        ),
      ],
    );
  }
}

class _PremiumHint extends StatelessWidget {
  const _PremiumHint();

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
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(Icons.workspace_premium_outlined, color: theme.colorScheme.primary),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                'Passez à l\'offre payante pour connaître, par objectif, le rendement net '
                'requis, le risque associé et la faisabilité du projet.',
                style: theme.textTheme.bodySmall,
              ),
            ),
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
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 32),
      child: Column(
        children: [
          Icon(Icons.savings_outlined, size: 48, color: theme.colorScheme.primary),
          const SizedBox(height: 12),
          Text(
            'Aucun objectif pour l\'instant. Créez-en un pour voir votre plan.',
            textAlign: TextAlign.center,
            style: theme.textTheme.bodyMedium,
          ),
        ],
      ),
    );
  }
}

class _Message extends StatelessWidget {
  const _Message({required this.icon, required this.message, required this.onRetry});

  final IconData icon;
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
            Icon(icon, size: 48, color: theme.colorScheme.primary),
            const SizedBox(height: 12),
            Text(message, textAlign: TextAlign.center, style: theme.textTheme.bodyLarge),
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
