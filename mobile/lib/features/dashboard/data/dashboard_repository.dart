import '../../../core/network/api_client.dart';
import 'dashboard_models.dart';

class DashboardRepository {
  DashboardRepository(this._apiClient);

  final ApiClient _apiClient;

  /// Récupère le tableau de bord du mois demandé (ou du mois courant si `mois`
  /// est nul). `mois` doit être au format `YYYY-MM`.
  Future<DashboardSummary> fetchDashboard({String? mois}) async {
    final response = await _apiClient.get<Map<String, dynamic>>(
      '/dashboard',
      queryParameters: mois == null ? null : {'mois': mois},
    );
    return DashboardSummary.fromJson(response.data!);
  }
}
