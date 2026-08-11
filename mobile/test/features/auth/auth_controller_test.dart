import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:budgetfamily/core/network/api_exception.dart';
import 'package:budgetfamily/core/network/token_storage.dart';
import 'package:budgetfamily/features/auth/application/auth_controller.dart';
import 'package:budgetfamily/features/auth/application/auth_state.dart';
import 'package:budgetfamily/features/auth/data/auth_models.dart';
import 'package:budgetfamily/features/auth/data/auth_repository.dart';

class _MockAuthRepository extends Mock implements AuthRepository {}

class _MockTokenStorage extends Mock implements TokenStorage {}

void main() {
  late _MockAuthRepository repository;
  late _MockTokenStorage tokenStorage;

  const user = CurrentUser(id: 1, email: 'test@example.com', subscriptionTier: 'free');
  const token = AuthTokenResponse(accessToken: 'fake-token', tokenType: 'bearer');

  setUp(() {
    repository = _MockAuthRepository();
    tokenStorage = _MockTokenStorage();
  });

  group('bootstrap', () {
    test('sans token stocké -> unauthenticated', () async {
      when(() => tokenStorage.readToken()).thenAnswer((_) async => null);

      final controller = AuthController(repository: repository, tokenStorage: tokenStorage);
      await controller.bootstrap();

      expect(controller.state.status, AuthStatus.unauthenticated);
      expect(controller.state.user, isNull);
    });

    test('avec token valide -> authenticated et utilisateur chargé', () async {
      when(() => tokenStorage.readToken()).thenAnswer((_) async => 'stored-token');
      when(() => repository.fetchCurrentUser()).thenAnswer((_) async => user);

      final controller = AuthController(repository: repository, tokenStorage: tokenStorage);
      await controller.bootstrap();

      expect(controller.state.status, AuthStatus.authenticated);
      expect(controller.state.user?.email, 'test@example.com');
    });

    test('avec token expiré/invalide -> nettoie le token et repasse unauthenticated', () async {
      when(() => tokenStorage.readToken()).thenAnswer((_) async => 'expired-token');
      when(() => repository.fetchCurrentUser())
          .thenThrow(const ApiException('Session expirée', statusCode: 401));
      when(() => tokenStorage.clearToken()).thenAnswer((_) async {});

      final controller = AuthController(repository: repository, tokenStorage: tokenStorage);
      await controller.bootstrap();

      expect(controller.state.status, AuthStatus.unauthenticated);
      verify(() => tokenStorage.clearToken()).called(1);
    });
  });

  group('login', () {
    test('succès -> sauvegarde le token et passe authenticated', () async {
      when(() => tokenStorage.readToken()).thenAnswer((_) async => null);
      when(() => repository.login(email: any(named: 'email'), password: any(named: 'password')))
          .thenAnswer((_) async => token);
      when(() => tokenStorage.saveToken(any())).thenAnswer((_) async {});
      when(() => repository.fetchCurrentUser()).thenAnswer((_) async => user);

      final controller = AuthController(repository: repository, tokenStorage: tokenStorage);
      await controller.login(email: 'test@example.com', password: 'motdepasse123');

      expect(controller.state.status, AuthStatus.authenticated);
      expect(controller.state.isLoading, isFalse);
      verify(() => tokenStorage.saveToken('fake-token')).called(1);
    });

    test('échec -> expose errorMessage sans planter', () async {
      when(() => tokenStorage.readToken()).thenAnswer((_) async => null);
      when(() => repository.login(email: any(named: 'email'), password: any(named: 'password')))
          .thenThrow(const ApiException('Email ou mot de passe incorrect', statusCode: 401));

      final controller = AuthController(repository: repository, tokenStorage: tokenStorage);
      await controller.login(email: 'test@example.com', password: 'mauvais');

      expect(controller.state.status, AuthStatus.unknown);
      expect(controller.state.isLoading, isFalse);
      expect(controller.state.errorMessage, 'Email ou mot de passe incorrect');
    });
  });

  group('logout', () {
    test('nettoie le token et repasse unauthenticated', () async {
      when(() => tokenStorage.readToken()).thenAnswer((_) async => null);
      when(() => tokenStorage.clearToken()).thenAnswer((_) async {});

      final controller = AuthController(repository: repository, tokenStorage: tokenStorage);
      await controller.logout();

      expect(controller.state.status, AuthStatus.unauthenticated);
      expect(controller.state.user, isNull);
      verify(() => tokenStorage.clearToken()).called(1);
    });
  });
}
