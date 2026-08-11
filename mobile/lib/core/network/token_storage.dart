import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Enveloppe autour de flutter_secure_storage, dédiée au token d'accès.
///
/// Sur Android, s'appuie sur EncryptedSharedPreferences ; sur iOS, sur le
/// Keychain. Le token n'est donc jamais stocké en clair sur le disque.
class TokenStorage {
  TokenStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const _accessTokenKey = 'access_token';

  final FlutterSecureStorage _storage;

  Future<String?> readToken() => _storage.read(key: _accessTokenKey);

  Future<void> saveToken(String token) =>
      _storage.write(key: _accessTokenKey, value: token);

  Future<void> clearToken() => _storage.delete(key: _accessTokenKey);
}
