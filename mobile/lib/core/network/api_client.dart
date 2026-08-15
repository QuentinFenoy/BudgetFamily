import 'package:dio/dio.dart';

import '../app_config.dart';
import 'api_exception.dart';
import 'token_storage.dart';

/// Client HTTP unique de l'application, construit une seule fois et partagé
/// via Riverpod (cf. core/network/providers.dart).
class ApiClient {
  ApiClient({required TokenStorage tokenStorage, Dio? dio})
      : _tokenStorage = tokenStorage,
        _dio = dio ??
            Dio(BaseOptions(
              baseUrl: AppConfig.apiBaseUrl,
              connectTimeout: const Duration(seconds: 10),
              receiveTimeout: const Duration(seconds: 10),
            )) {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _tokenStorage.readToken();
          if (token != null) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
      ),
    );
  }

  final Dio _dio;
  final TokenStorage _tokenStorage;

  Future<Response<T>> get<T>(String path, {Map<String, dynamic>? queryParameters}) =>
      _guard(() => _dio.get<T>(path, queryParameters: queryParameters));

  Future<Response<T>> post<T>(String path, {Object? data}) =>
      _guard(() => _dio.post<T>(path, data: data));

  Future<Response<T>> put<T>(String path, {Object? data}) =>
      _guard(() => _dio.put<T>(path, data: data));

  Future<Response<T>> patch<T>(String path, {Object? data}) =>
      _guard(() => _dio.patch<T>(path, data: data));

  Future<Response<T>> delete<T>(String path) => _guard(() => _dio.delete<T>(path));

  Future<Response<T>> _guard<T>(Future<Response<T>> Function() request) async {
    try {
      return await request();
    } on DioException catch (error) {
      throw _translate(error);
    }
  }

  ApiException _translate(DioException error) {
    final statusCode = error.response?.statusCode;
    final data = error.response?.data;

    // FastAPI renvoie {"detail": "message"} pour la plupart des erreurs, ou
    // {"detail": [{"msg": "...", ...}, ...]} pour les erreurs de validation
    // Pydantic (422) — les deux formats sont gérés ici.
    String? detail;
    if (data is Map && data['detail'] != null) {
      final rawDetail = data['detail'];
      if (rawDetail is String) {
        detail = rawDetail;
      } else if (rawDetail is List) {
        detail = rawDetail
            .map((e) => e is Map ? e['msg']?.toString() : e.toString())
            .where((e) => e != null)
            .join(' ; ');
      }
    }

    if (detail != null && detail.isNotEmpty) {
      return ApiException(detail, statusCode: statusCode);
    }

    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return const ApiException(
          'La connexion au serveur a expiré. Vérifiez votre connexion internet.',
        );
      case DioExceptionType.connectionError:
        return const ApiException(
          'Impossible de joindre le serveur. Vérifiez votre connexion internet.',
        );
      default:
        return ApiException(
          'Une erreur est survenue (code $statusCode).',
          statusCode: statusCode,
        );
    }
  }
}
