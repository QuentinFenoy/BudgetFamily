import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/providers.dart';
import '../data/dashboard_models.dart';
import '../data/dashboard_repository.dart';

final dashboardRepositoryProvider = Provider<DashboardRepository>((ref) {
  return DashboardRepository(ref.watch(apiClientProvider));
});

/// Charge le dashboard du mois courant. `autoDispose` : rechargé à chaque entrée
/// sur l'écran (pas de donnée figée entre deux sessions), et invalidable pour un
/// rafraîchissement manuel (pull-to-refresh).
final dashboardProvider = FutureProvider.autoDispose<DashboardSummary>((ref) {
  return ref.watch(dashboardRepositoryProvider).fetchDashboard();
});
