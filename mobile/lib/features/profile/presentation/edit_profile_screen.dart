import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../onboarding/presentation/onboarding_screen.dart';
import '../application/profile_providers.dart';

/// Charge le profil courant puis réutilise le formulaire d'onboarding en mode
/// édition (prérempli). La soumission passe alors par PUT /v1/profile.
class EditProfileScreen extends ConsumerWidget {
  const EditProfileScreen({super.key});

  Widget _shell(Widget body) => Scaffold(
        appBar: AppBar(title: const Text('Modifier le profil')),
        body: body,
      );

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final profile = ref.watch(profileProvider);

    return profile.when(
      data: (detail) => OnboardingScreen(initial: detail),
      loading: () => _shell(const Center(child: CircularProgressIndicator())),
      error: (error, _) => _shell(
        Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  error is ApiException ? error.message : 'Impossible de charger le profil.',
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 16),
                OutlinedButton.icon(
                  icon: const Icon(Icons.refresh),
                  label: const Text('Réessayer'),
                  onPressed: () => ref.invalidate(profileProvider),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
