/// Configuration globale, surchargeable au lancement avec --dart-define.
///
/// Exemple : flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000/v1
/// (10.0.2.2 est l'adresse spéciale de l'émulateur Android pour joindre le
/// localhost de la machine hôte — "localhost" tout court ne fonctionne pas
/// depuis l'émulateur, contrairement à un simulateur iOS ou au web).
class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000/v1',
  );
}
