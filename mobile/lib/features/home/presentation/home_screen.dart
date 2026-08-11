import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../auth/application/auth_controller.dart';

/// Écran temporaire : confirme que l'authentification fonctionne de bout en
/// bout contre le backend réel. Sera remplacé par l'écran d'onboarding puis
/// le dashboard dans un prochain incrément.
class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authControllerProvider).user;

    return Scaffold(
      appBar: AppBar(
        title: const Text('BudgetFamily'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Se déconnecter',
            onPressed: () => ref.read(authControllerProvider.notifier).logout(),
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.check_circle, size: 48, color: Colors.green),
            const SizedBox(height: 16),
            Text('Connecté en tant que ${user?.email ?? "?"}'),
            const SizedBox(height: 8),
            Text('Palier : ${user?.subscriptionTier ?? "?"}'),
          ],
        ),
      ),
    );
  }
}
