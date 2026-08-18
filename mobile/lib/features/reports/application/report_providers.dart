import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/providers.dart';
import '../data/report_models.dart';
import '../data/report_repository.dart';

final reportRepositoryProvider = Provider<ReportRepository>((ref) {
  return ReportRepository(ref.watch(apiClientProvider));
});

String _moisCourant() {
  final now = DateTime.now();
  return '${now.year.toString().padLeft(4, '0')}-${now.month.toString().padLeft(2, '0')}';
}

/// Mois affiché pour le bilan mensuel (format YYYY-MM). L'utilisateur navigue
/// dans le passé ; par défaut, le mois courant.
final selectedMonthProvider = StateProvider.autoDispose<String>((ref) => _moisCourant());

final monthlyReportProvider = FutureProvider.autoDispose<MonthlyReport>((ref) {
  final mois = ref.watch(selectedMonthProvider);
  return ref.watch(reportRepositoryProvider).getMonthly(mois: mois);
});

final quarterlyReportProvider = FutureProvider.autoDispose<QuarterlyReport>((ref) {
  return ref.watch(reportRepositoryProvider).getQuarterly();
});
