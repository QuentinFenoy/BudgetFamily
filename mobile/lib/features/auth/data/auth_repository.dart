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
}
