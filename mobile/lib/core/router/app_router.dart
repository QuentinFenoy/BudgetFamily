import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../features/auth/application/auth_controller.dart';
import '../../features/auth/application/auth_state.dart';
import '../../features/auth/presentation/forgot_password_screen.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/register_screen.dart';
import '../../features/auth/presentation/reset_password_screen.dart';
import '../../features/home/presentation/home_screen.dart';
import '../../features/onboarding/presentation/onboarding_screen.dart';
import '../../features/portfolio/presentation/allocation_screen.dart';
import '../../features/portfolio/presentation/history_screen.dart';
import '../../features/profile/presentation/edit_profile_screen.dart';
import '../../features/reports/presentation/reports_screen.dart';
import '../../features/savings/presentation/plan_screen.dart';
import '../../features/savings/presentation/savings_screen.dart';
import '../widgets/splash_screen.dart';

/// Transforme les changements de authControllerProvider en notifications que
/// GoRouter peut écouter (refreshListenable attend un Listenable, pas un
/// Riverpod provider directement).
class _RouterRefreshNotifier extends ChangeNotifier {
  _RouterRefreshNotifier(Ref ref) {
    ref.listen(authControllerProvider, (previous, next) {
      if (previous?.status != next.status) notifyListeners();
    });
  }
}

final routerProvider = Provider<GoRouter>((ref) {
  final refreshNotifier = _RouterRefreshNotifier(ref);

  return GoRouter(
    initialLocation: '/splash',
    refreshListenable: refreshNotifier,
    redirect: (context, state) {
      final authState = ref.read(authControllerProvider);
      final location = state.matchedLocation;
      final isAuthRoute = location == '/login' ||
          location == '/register' ||
          location == '/forgot-password' ||
          location == '/reset-password';

      if (authState.status == AuthStatus.unknown) {
        return location == '/splash' ? null : '/splash';
      }

      final loggedIn = authState.status == AuthStatus.authenticated;
      if (!loggedIn) {
        return isAuthRoute ? null : '/login';
      }
      // Connecté : on ne doit jamais rester sur splash/login/register.
      return (location == '/splash' || isAuthRoute) ? '/home' : null;
    },
    routes: [
      GoRoute(path: '/splash', builder: (context, state) => const SplashScreen()),
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      GoRoute(path: '/register', builder: (context, state) => const RegisterScreen()),
      GoRoute(path: '/forgot-password', builder: (context, state) => const ForgotPasswordScreen()),
      GoRoute(
        path: '/reset-password',
        builder: (context, state) => ResetPasswordScreen(initialToken: state.extra as String?),
      ),
      GoRoute(path: '/home', builder: (context, state) => const HomeScreen()),
      GoRoute(path: '/onboarding', builder: (context, state) => const OnboardingScreen()),
      GoRoute(path: '/profile/edit', builder: (context, state) => const EditProfileScreen()),
      GoRoute(path: '/portfolio', builder: (context, state) => const AllocationScreen()),
      GoRoute(path: '/portfolio/history', builder: (context, state) => const HistoryScreen()),
      GoRoute(path: '/savings', builder: (context, state) => const SavingsScreen()),
      GoRoute(path: '/savings/plan', builder: (context, state) => const PlanScreen()),
      GoRoute(path: '/reports', builder: (context, state) => const ReportsScreen()),
    ],
  );
});
