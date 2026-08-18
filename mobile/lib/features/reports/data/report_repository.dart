import '../../../core/network/api_client.dart';
import 'report_models.dart';

class ReportRepository {
  ReportRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<MonthlyReport> getMonthly({String? mois}) async {
    final response = await _apiClient.get<Map<String, dynamic>>(
      '/reports/monthly',
      queryParameters: mois == null ? null : {'mois': mois},
    );
    return MonthlyReport.fromJson(response.data!);
  }

  Future<QuarterlyReport> getQuarterly({String? mois}) async {
    final response = await _apiClient.get<Map<String, dynamic>>(
      '/reports/quarterly',
      queryParameters: mois == null ? null : {'mois': mois},
    );
    return QuarterlyReport.fromJson(response.data!);
  }
}
