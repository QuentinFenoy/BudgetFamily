import '../../../core/network/api_client.dart';
import 'onboarding_models.dart';

class OnboardingRepository {
  OnboardingRepository(this._apiClient);

  final ApiClient _apiClient;

  /// Envoie le profil du foyer au backend. En cas de succès le backend crée le
  /// profil et calcule le premier budget ; on n'a pas besoin d'exploiter la
  /// réponse ici, le dashboard sera rechargé juste après.
  Future<void> submit(OnboardingRequest request) async {
    await _apiClient.post<Map<String, dynamic>>('/onboarding', data: request.toJson());
  }
}
