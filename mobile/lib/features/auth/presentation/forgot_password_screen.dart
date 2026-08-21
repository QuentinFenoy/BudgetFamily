import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../application/auth_controller.dart';

class ForgotPasswordScreen extends ConsumerStatefulWidget {
  const ForgotPasswordScreen({super.key});

  @override
  ConsumerState<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends ConsumerState<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  bool _loading = false;
  bool _sent = false;
  String? _devToken; // renvoyé en développement uniquement
  String? _error;

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final token =
          await ref.read(authRepositoryProvider).forgotPassword(_emailController.text.trim());
      setState(() {
        _sent = true;
        _devToken = token;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Une erreur est survenue. Réessayez.';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(title: const Text('Mot de passe oublié')),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: _sent ? _confirmation(theme) : _formulaire(theme),
            ),
          ),
        ),
      ),
    );
  }

  Widget _formulaire(ThemeData theme) {
    return Form(
      key: _formKey,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            'Entrez votre adresse email : nous vous enverrons un lien pour réinitialiser '
            'votre mot de passe.',
            style: theme.textTheme.bodyMedium,
          ),
          const SizedBox(height: 24),
          TextFormField(
            controller: _emailController,
            decoration: const InputDecoration(labelText: 'Email'),
            keyboardType: TextInputType.emailAddress,
            validator: (v) => (v == null || !v.contains('@')) ? 'Adresse email invalide' : null,
          ),
          if (_error != null) ...[
            const SizedBox(height: 16),
            Text(_error!, style: TextStyle(color: theme.colorScheme.error)),
          ],
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _loading ? null : _submit,
            child: _loading
                ? const SizedBox(
                    height: 20,
                    width: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Text('Envoyer le lien'),
          ),
        ],
      ),
    );
  }

  Widget _confirmation(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(Icons.mark_email_read_outlined, size: 48, color: theme.colorScheme.primary),
        const SizedBox(height: 16),
        Text(
          'Si un compte existe pour cette adresse, un lien de réinitialisation vient d\'être '
          'envoyé. Suivez-le pour choisir un nouveau mot de passe.',
          style: theme.textTheme.bodyLarge,
          textAlign: TextAlign.center,
        ),
        const SizedBox(height: 24),
        ElevatedButton(
          onPressed: () => context.push('/reset-password', extra: _devToken),
          child: const Text('J\'ai un code de réinitialisation'),
        ),
        const SizedBox(height: 8),
        TextButton(
          onPressed: () => context.go('/login'),
          child: const Text('Retour à la connexion'),
        ),
      ],
    );
  }
}
