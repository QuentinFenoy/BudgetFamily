import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../../core/format.dart';
import '../../../core/network/api_exception.dart';
import '../../auth/application/auth_controller.dart';
import '../../dashboard/application/dashboard_providers.dart';
import '../../dashboard/data/dashboard_models.dart';
import '../../expenses/presentation/add_expense_sheet.dart';

/// Écran principal : affiche le tableau de bord budgétaire du mois courant,
/// premier appel API authentifié réel (GET /v1/dashboard).
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;
    final dashboard = ref.watch(dashboardProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Tableau de bord'),
        actions: [
          if (user?.isPremium ?? false)
            const Padding(
              padding: EdgeInsets.only(right: 4),
              child: Chip(
                avatar: Icon(Icons.star, size: 16),
                label: Text('Premium'),
                visualDensity: VisualDensity.compact,
              ),
            ),
          if (dashboard.hasValue)
            PopupMenuButton<String>(
              icon: const Icon(Icons.more_vert),
              onSelected: (route) => context.push('/$route'),
              itemBuilder: (_) => const [
                PopupMenuItem(
                  value: 'portfolio',
                  child: Row(children: [
                    Icon(Icons.pie_chart_outline),
                    SizedBox(width: 12),
                    Text('Allocation'),
                  ]),
                ),
                PopupMenuItem(
                  value: 'savings',
                  child: Row(children: [
                    Icon(Icons.savings_outlined),
                    SizedBox(width: 12),
                    Text('Objectifs d\'épargne'),
                  ]),
                ),
                PopupMenuItem(
                  value: 'profile/edit',
                  child: Row(children: [
                    Icon(Icons.edit_outlined),
                    SizedBox(width: 12),
                    Text('Modifier le profil'),
                  ]),
                ),
              ],
            ),
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Se déconnecter',
            onPressed: () => ref.read(authControllerProvider.notifier).logout(),
          ),
        ],
      ),
      floatingActionButton: dashboard.maybeWhen(
        data: (summary) => summary.categories.isEmpty
            ? null
            : FloatingActionButton.extended(
                onPressed: () => _ajouterDepense(
                  context,
                  ref,
                  summary.categories.map((c) => c.libelle).toList(),
                ),
                icon: const Icon(Icons.add),
                label: const Text('Dépense'),
              ),
        orElse: () => null,
      ),
      body: dashboard.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, _) {
          if (error is ApiException && error.isNotFound) {
            return _ProfilAComplete(email: user?.email);
          }
          return _ErrorState(
            message: error is ApiException ? error.message : 'Une erreur est survenue.',
            onRetry: () => ref.invalidate(dashboardProvider),
          );
        },
        data: (summary) => RefreshIndicator(
          onRefresh: () async {
            try {
              await ref.refresh(dashboardProvider.future);
            } catch (_) {
              // L'erreur est déjà rendue par le `when` au prochain build.
            }
          },
          child: _DashboardBody(summary: summary),
        ),
      ),
    );
  }
}

class _DashboardBody extends StatelessWidget {
  const _DashboardBody({required this.summary});

  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.all(16),
      children: [
        _HeroCard(summary: summary),
        const SizedBox(height: 24),
        Text('Dépenses par catégorie', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        if (summary.categories.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 24),
            child: Text('Aucune catégorie de dépense pour le moment.'),
          )
        else
          ...summary.categories.map((c) => _CategoryTile(status: c)),
      ],
    );
  }
}

class _HeroCard extends StatelessWidget {
  const _HeroCard({required this.summary});

  final DashboardSummary summary;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final tauxPct = (summary.epargneReferenceTaux * 100).round();

    return Card(
      elevation: 0,
      color: theme.colorScheme.primaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              formatPeriode(summary.periode),
              style: theme.textTheme.labelLarge?.copyWith(
                color: theme.colorScheme.onPrimaryContainer,
              ),
            ),
            const SizedBox(height: 4),
            Text('Disponible ce mois', style: theme.textTheme.bodyMedium),
            Text(
              formatEuros(summary.disponible),
              style: theme.textTheme.headlineMedium?.copyWith(
                fontWeight: FontWeight.bold,
                color: theme.colorScheme.onPrimaryContainer,
              ),
            ),
            const Divider(height: 28),
            Row(
              children: [
                Expanded(
                  child: _MiniStat(
                    label: 'Épargne potentielle',
                    value: formatEuros(summary.epargnePotentielle),
                  ),
                ),
                Expanded(
                  child: _MiniStat(
                    label: 'Référence ($tauxPct %)',
                    value: formatEuros(summary.epargneReferenceMontant),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _MiniStat extends StatelessWidget {
  const _MiniStat({required this.label, required this.value});

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

class _CategoryTile extends StatelessWidget {
  const _CategoryTile({required this.status});

  final CategoryBudgetStatus status;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final couleur = status.depasse ? theme.colorScheme.error : theme.colorScheme.primary;
    final sousTitre = status.ecart >= 0
        ? 'Il reste ${formatEuros(status.ecart)}'
        : 'Dépassé de ${formatEuros(status.ecart.abs())}';

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
            child: LinearProgressIndicator(
              value: status.progression,
              minHeight: 8,
              color: couleur,
            ),
          ),
          const SizedBox(height: 4),
          Text(sousTitre, style: theme.textTheme.bodySmall?.copyWith(color: couleur)),
        ],
      ),
    );
  }
}

class _ProfilAComplete extends StatelessWidget {
  const _ProfilAComplete({this.email});

  final String? email;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.person_add_alt, size: 56, color: theme.colorScheme.primary),
            const SizedBox(height: 16),
            Text(
              email == null ? 'Bienvenue !' : 'Bienvenue, $email !',
              style: theme.textTheme.titleMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Text(
              'Complétez votre profil (revenus, charges, objectif) pour découvrir '
              'votre budget recommandé.',
              style: theme.textTheme.bodyMedium,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              icon: const Icon(Icons.arrow_forward),
              label: const Text('Compléter mon profil'),
              onPressed: () => context.push('/onboarding'),
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
            Icon(Icons.cloud_off, size: 56, color: theme.colorScheme.error),
            const SizedBox(height: 16),
            Text(message, style: theme.textTheme.bodyLarge, textAlign: TextAlign.center),
            const SizedBox(height: 24),
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

/// Ouvre la feuille de saisie d'une dépense ; en cas de succès, rafraîchit le
/// dashboard pour que le « réalisé » des catégories se mette à jour.
Future<void> _ajouterDepense(BuildContext context, WidgetRef ref, List<String> categories) async {
  final added = await showModalBottomSheet<bool>(
    context: context,
    isScrollControlled: true,
    showDragHandle: true,
    builder: (_) => AddExpenseSheet(categories: categories),
  );
  if (added == true) {
    ref.invalidate(dashboardProvider);
    if (context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Dépense ajoutée.')),
      );
    }
  }
}
