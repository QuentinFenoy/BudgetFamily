import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/network/providers.dart';
import '../data/allocation_models.dart';
import '../data/asset_class_info.dart';
import '../data/allocation_repository.dart';

final allocationRepositoryProvider = Provider<AllocationRepository>((ref) {
  return AllocationRepository(ref.watch(apiClientProvider));
});

/// État de l'allocation : `AsyncData(null)` = rien de encore calculé ;
/// `AsyncLoading` pendant le calcul ; `AsyncData(alloc)` ou `AsyncError` ensuite.
final allocationControllerProvider =
    StateNotifierProvider.autoDispose<AllocationController, AsyncValue<PortfolioAllocation?>>(
        (ref) {
  return AllocationController(ref.watch(allocationRepositoryProvider));
});

/// Fiches pédagogiques des classes d'actifs, indexées par nom (= champ `classe`
/// des lignes d'allocation) pour un accès direct depuis l'écran.
final assetClassesProvider = FutureProvider.autoDispose<Map<String, AssetClassInfo>>((ref) async {
  final liste = await ref.watch(allocationRepositoryProvider).listAssetClasses();
  return {for (final info in liste) info.nom: info};
});

/// Historique des simulations enregistrées, plus récentes d'abord.
final simulationsProvider = FutureProvider.autoDispose<List<SimulationSummary>>((ref) {
  return ref.watch(allocationRepositoryProvider).listSimulations();
});

class AllocationController extends StateNotifier<AsyncValue<PortfolioAllocation?>> {
  AllocationController(this._repository) : super(const AsyncData(null));

  final AllocationRepository _repository;

  Future<void> load({required String methode, double? montant}) async {
    state = const AsyncLoading();
    try {
      final result = await _repository.getAllocation(methode: methode, montant: montant);
      if (mounted) state = AsyncData(result);
    } on ApiException catch (error, stack) {
      if (mounted) state = AsyncError(error, stack);
    }
  }

  /// Recalcule et ENREGISTRE la simulation courante dans l'historique, sans
  /// modifier l'état affiché. Renvoie true en cas de succès.
  Future<bool> saveCurrent({required String methode, double? montant}) async {
    try {
      await _repository.getAllocation(methode: methode, montant: montant, save: true);
      return true;
    } on ApiException {
      return false;
    }
  }
}
