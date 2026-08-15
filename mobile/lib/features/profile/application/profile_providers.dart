import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/network/providers.dart';
import '../../onboarding/data/onboarding_models.dart';
import '../data/profile_models.dart';
import '../data/profile_repository.dart';

final profileRepositoryProvider = Provider<ProfileRepository>((ref) {
  return ProfileRepository(ref.watch(apiClientProvider));
});

/// Charge le profil courant (pour préremplir le formulaire d'édition).
final profileProvider = FutureProvider.autoDispose<ProfileDetail>((ref) {
  return ref.watch(profileRepositoryProvider).getProfile();
});

final profileUpdateControllerProvider =
    StateNotifierProvider.autoDispose<ProfileUpdateController, ProfileUpdateState>((ref) {
  return ProfileUpdateController(ref.watch(profileRepositoryProvider));
});

class ProfileUpdateState {
  const ProfileUpdateState({this.isSubmitting = false, this.errorMessage});

  final bool isSubmitting;
  final String? errorMessage;

  ProfileUpdateState copyWith({
    bool? isSubmitting,
    String? errorMessage,
    bool clearError = false,
  }) {
    return ProfileUpdateState(
      isSubmitting: isSubmitting ?? this.isSubmitting,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }
}

class ProfileUpdateController extends StateNotifier<ProfileUpdateState> {
  ProfileUpdateController(this._repository) : super(const ProfileUpdateState());

  final ProfileRepository _repository;

  Future<bool> submit(OnboardingRequest request) async {
    state = state.copyWith(isSubmitting: true, clearError: true);
    try {
      await _repository.updateProfile(request);
      state = state.copyWith(isSubmitting: false);
      return true;
    } on ApiException catch (error) {
      state = state.copyWith(isSubmitting: false, errorMessage: error.message);
      return false;
    }
  }
}
