import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/network/providers.dart';
import '../data/onboarding_models.dart';
import '../data/onboarding_repository.dart';

final onboardingRepositoryProvider = Provider<OnboardingRepository>((ref) {
  return OnboardingRepository(ref.watch(apiClientProvider));
});

final onboardingControllerProvider =
    StateNotifierProvider.autoDispose<OnboardingController, OnboardingSubmitState>((ref) {
  return OnboardingController(ref.watch(onboardingRepositoryProvider));
});

class OnboardingSubmitState {
  const OnboardingSubmitState({this.isSubmitting = false, this.errorMessage});

  final bool isSubmitting;
  final String? errorMessage;

  OnboardingSubmitState copyWith({
    bool? isSubmitting,
    String? errorMessage,
    bool clearError = false,
  }) {
    return OnboardingSubmitState(
      isSubmitting: isSubmitting ?? this.isSubmitting,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }
}

class OnboardingController extends StateNotifier<OnboardingSubmitState> {
  OnboardingController(this._repository) : super(const OnboardingSubmitState());

  final OnboardingRepository _repository;

  /// Renvoie `true` si le profil a bien été créé. En cas d'échec, `errorMessage`
  /// porte le message renvoyé par le backend (ex. validation 422).
  Future<bool> submit(OnboardingRequest request) async {
    state = state.copyWith(isSubmitting: true, clearError: true);
    try {
      await _repository.submit(request);
      state = state.copyWith(isSubmitting: false);
      return true;
    } on ApiException catch (error) {
      state = state.copyWith(isSubmitting: false, errorMessage: error.message);
      return false;
    }
  }
}
