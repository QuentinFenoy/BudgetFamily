/// Réponse de POST /v1/auth/register et /v1/auth/login.
class AuthTokenResponse {
  const AuthTokenResponse({required this.accessToken, required this.tokenType});

  factory AuthTokenResponse.fromJson(Map<String, dynamic> json) {
    return AuthTokenResponse(
      accessToken: json['access_token'] as String,
      tokenType: json['token_type'] as String? ?? 'bearer',
    );
  }

  final String accessToken;
  final String tokenType;
}

/// Réponse de GET /v1/auth/me.
class CurrentUser {
  const CurrentUser({
    required this.id,
    required this.email,
    required this.subscriptionTier,
  });

  factory CurrentUser.fromJson(Map<String, dynamic> json) {
    return CurrentUser(
      id: json['id'] as int,
      email: json['email'] as String,
      subscriptionTier: json['subscription_tier'] as String? ?? 'free',
    );
  }

  final int id;
  final String email;
  final String subscriptionTier;

  bool get isPremium => subscriptionTier == 'premium';
}
