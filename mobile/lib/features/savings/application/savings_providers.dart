import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/providers.dart';
import '../data/savings_models.dart';
import '../data/savings_repository.dart';

final savingsRepositoryProvider = Provider<SavingsRepository>((ref) {
  return SavingsRepository(ref.watch(apiClientProvider));
});

/// Liste des objectifs d'épargne de l'utilisateur. autoDispose + invalidable après
/// chaque création / modification / suppression.
final goalsProvider = FutureProvider.autoDispose<List<SavingsGoal>>((ref) {
  return ref.watch(savingsRepositoryProvider).listGoals();
});

/// Plan d'épargne : capacité répartie par priorité + projection premium par objectif.
/// À invalider en même temps que goalsProvider après toute mutation d'objectif.
final planProvider = FutureProvider.autoDispose<PlanEpargne>((ref) {
  return ref.watch(savingsRepositoryProvider).getPlan();
});
