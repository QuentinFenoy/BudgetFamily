import '../../../core/network/api_client.dart';
import 'savings_models.dart';

class SavingsRepository {
  SavingsRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<List<SavingsGoal>> listGoals() async {
    final response = await _apiClient.get<List<dynamic>>('/savings/goals');
    return (response.data ?? [])
        .map((e) => SavingsGoal.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> createGoal({
    required String libelle,
    required double montantCible,
    required double montantActuel,
    required int priorite,
  }) async {
    await _apiClient.post<Map<String, dynamic>>('/savings/goals', data: {
      'libelle': libelle,
      'montant_cible': montantCible,
      'montant_actuel': montantActuel,
      'priorite': priorite,
    });
  }

  Future<void> updateGoal(
    int id, {
    required String libelle,
    required double montantCible,
    required double montantActuel,
    required int priorite,
  }) async {
    await _apiClient.patch<Map<String, dynamic>>('/savings/goals/$id', data: {
      'libelle': libelle,
      'montant_cible': montantCible,
      'montant_actuel': montantActuel,
      'priorite': priorite,
    });
  }

  Future<void> deleteGoal(int id) async {
    await _apiClient.delete<void>('/savings/goals/$id');
  }

  Future<RepartitionResult> repartitionAuto({
    required double epargneDisponible,
    required String methode,
  }) async {
    final response = await _apiClient.post<Map<String, dynamic>>(
      '/savings/repartition-auto',
      data: {'epargne_disponible': epargneDisponible, 'methode': methode},
    );
    return RepartitionResult.fromJson(response.data!);
  }
}
