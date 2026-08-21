import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Enveloppe autour de flutter_secure_storage pour le token d'accès.
///
/// Deux modes selon « Rester connecté » :
/// - persistant (défaut) : le token est écrit dans le stockage sécurisé (Keychain sur
///   iOS, EncryptedSharedPreferences sur Android) et survit à la fermeture de l'app ;
/// - session seule : le token n'est gardé qu'en mémoire ; l'app se déconnecte au
///   prochain démarrage.
class TokenStorage {
  TokenStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const _accessTokenKey = 'access_token';

  final FlutterSecureStorage _storage;
  String? _memoryToken;

  /// Renvoie le token de la session en mémoire s'il existe, sinon celui persisté.
  Future<String?> readToken() async {
    if (_memoryToken != null) return _memoryToken;
    _memoryToken = await _storage.read(key: _accessTokenKey);
    return _memoryToken;
  }

  /// [persist] true : conservé après fermeture de l'app (« rester connecté »).
  /// false : gardé en mémoire pour la session courante uniquement, et le stockage
  /// persistant est purgé pour ne pas laisser traîner le token d'une session passée.
  Future<void> saveToken(String token, {bool persist = true}) async {
    _memoryToken = token;
    if (persist) {
      await _storage.write(key: _accessTokenKey, value: token);
    } else {
      await _storage.delete(key: _accessTokenKey);
    }
  }

  Future<void> clearToken() async {
    _memoryToken = null;
    await _storage.delete(key: _accessTokenKey);
  }
}
