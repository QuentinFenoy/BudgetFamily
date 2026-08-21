import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/network/providers.dart';
import '../../../core/network/token_storage.dart';
import '../data/auth_repository.dart';
import 'auth_state.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(ref.watch(apiClientProvider));
});

final authControllerProvider = StateNotifierProvider<AuthController, AuthState>((ref) {
  return AuthController(
    repository: ref.watch(authRepositoryProvider),
    tokenStorage: ref.watch(tokenStorageProvider),
  )..bootstrap();
});

/// Gère le cycle de vie de l'authentification : démarrage (token déjà
/// présent ?), connexion, inscription, déconnexion. Les écrans ne parlent
/// jamais directement au repository — uniquement à ce contrôleur.
class AuthController extends StateNotifier<AuthState> {
  AuthController({required this.repository, required this.tokenStorage})
      : super(const AuthState());

  final AuthRepository repository;
  final TokenStorage tokenStorage;

  /// Appelé une seule fois au démarrage de l'app : si un token est déjà
  /// stocké, on vérifie qu'il est toujours valide en rechargeant l'utilisateur
  /// plutôt que de supposer aveuglément qu'il l'est encore.
  Future<void> bootstrap() async {
    final token = await tokenStorage.readToken();
    if (token == null) {
      state = state.copyWith(status: AuthStatus.unauthenticated);
      return;
    }
    try {
      final user = await repository.fetchCurrentUser();
      state = state.copyWith(status: AuthStatus.authenticated, user: user);
    } on ApiException {
      await tokenStorage.clearToken();
      state = state.copyWith(status: AuthStatus.unauthenticated);
    }
  }

  Future<void> register({required String email, required String password}) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final token = await repository.register(email: email, password: password);
      await tokenStorage.saveToken(token.accessToken);
      final user = await repository.fetchCurrentUser();
      state = state.copyWith(status: AuthStatus.authenticated, user: user, isLoading: false);
    } on ApiException catch (error) {
      state = state.copyWith(isLoading: false, errorMessage: error.message);
    }
  }

  Future<void> login({
    required String email,
    required String password,
    bool rememberMe = true,
  }) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final token = await repository.login(email: email, password: password);
      await tokenStorage.saveToken(token.accessToken, persist: rememberMe);
      final user = await repository.fetchCurrentUser();
      state = state.copyWith(status: AuthStatus.authenticated, user: user, isLoading: false);
    } on ApiException catch (error) {
      state = state.copyWith(isLoading: false, errorMessage: error.message);
    }
  }

  Future<void> logout() async {
    await tokenStorage.clearToken();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }

  /// Supprime définitivement le compte côté serveur, puis efface le token local et
  /// bascule en non-connecté (le router redirige alors vers /login).
  Future<void> deleteAccount() async {
    await repository.deleteAccount();
    await tokenStorage.clearToken();
    state = const AuthState(status: AuthStatus.unauthenticated);
  }
}
