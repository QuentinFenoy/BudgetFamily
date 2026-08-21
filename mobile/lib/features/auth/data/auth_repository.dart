import '../../../core/network/api_client.dart';
import 'auth_models.dart';

class AuthRepository {
  AuthRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<AuthTokenResponse> register({required String email, required String password}) async {
    final response = await _apiClient.post<Map<String, dynamic>>(
      '/auth/register',
      data: {'email': email, 'password': password},
    );
    return AuthTokenResponse.fromJson(response.data!);
  }

  Future<AuthTokenResponse> login({required String email, required String password}) async {
    final response = await _apiClient.post<Map<String, dynamic>>(
      '/auth/login',
      data: {'email': email, 'password': password},
    );
    return AuthTokenResponse.fromJson(response.data!);
  }

  Future<CurrentUser> fetchCurrentUser() async {
    final response = await _apiClient.get<Map<String, dynamic>>('/auth/me');
    return CurrentUser.fromJson(response.data!);
  }

  /// Demande un lien de réinitialisation. Renvoie le jeton en développement (le
  /// backend le fournit alors dans la réponse), null en production (envoyé par e-mail).
  Future<String?> forgotPassword(String email) async {
    final response = await _apiClient.post<Map<String, dynamic>>(
      '/auth/forgot-password',
      data: {'email': email},
    );
    return response.data?['reset_token'] as String?;
  }

  Future<void> resetPassword({required String token, required String newPassword}) async {
    await _apiClient.post<void>(
      '/auth/reset-password',
      data: {'token': token, 'new_password': newPassword},
    );
  }

  Future<void> deleteAccount() async {
    await _apiClient.delete<void>('/auth/me');
  }
}
