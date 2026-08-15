import '../../../core/network/api_client.dart';
import '../../onboarding/data/onboarding_models.dart';
import 'profile_models.dart';

class ProfileRepository {
  ProfileRepository(this._apiClient);

  final ApiClient _apiClient;

  Future<ProfileDetail> getProfile() async {
    final response = await _apiClient.get<Map<String, dynamic>>('/profile');
    return ProfileDetail.fromJson(response.data!);
  }

  Future<void> updateProfile(OnboardingRequest request) async {
    await _apiClient.put<Map<String, dynamic>>('/profile', data: request.toJson());
  }
}
