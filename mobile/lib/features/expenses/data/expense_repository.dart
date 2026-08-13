import '../../../core/network/api_client.dart';
import 'expense_models.dart';

class ExpenseRepository {
  ExpenseRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<void> addExpense(ExpenseEntryRequest request) async {
    await _apiClient.post<Map<String, dynamic>>('/expenses', data: request.toJson());
  }
}
