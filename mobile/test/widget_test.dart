// Smoke test : l'application démarre et construit son shell de navigation.
//
// On surcharge tokenStorageProvider par une implémentation de test pour éviter
// tout accès au canal natif flutter_secure_storage (indisponible sous
// `flutter test`). Sans token stocké, le bootstrap d'authentification résout
// simplement vers l'état "non authentifié", sans appel réseau.

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:budgetfamily/core/network/providers.dart';
import 'package:budgetfamily/core/network/token_storage.dart';
import 'package:budgetfamily/main.dart';

class _FakeTokenStorage extends TokenStorage {
  @override
  Future<String?> readToken() async => null;

  @override
  Future<void> saveToken(String token, {bool persist = true}) async {}

  @override
  Future<void> clearToken() async {}
}

void main() {
  testWidgets("l'application démarre et rend un MaterialApp", (tester) async {
    await tester.pumpWidget(
      ProviderScope(
        overrides: [tokenStorageProvider.overrideWithValue(_FakeTokenStorage())],
        child: const BudgetFamilyApp(),
      ),
    );

    // Laisse le bootstrap asynchrone (lecture du token) se résoudre.
    await tester.pump();

    // Le shell de navigation MaterialApp.router est présent dès le démarrage,
    // quel que soit l'écran affiché (splash puis login sans token).
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}