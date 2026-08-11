/// Exception applicative uniforme : tout appel API échoué est traduit vers ce
/// type, avec un message déjà adapté à l'affichage utilisateur, pour éviter
/// que les écrans aient à connaître les détails de Dio/HTTP.
class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  bool get isUnauthorized => statusCode == 401;
  bool get isForbidden => statusCode == 403;
  bool get isNotFound => statusCode == 404;
  bool get isValidationError => statusCode == 422;

  @override
  String toString() => message;
}
