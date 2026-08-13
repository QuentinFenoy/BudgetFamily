import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../application/expense_controller.dart';
import '../data/expense_models.dart';

double? _parseMontant(String raw) {
  final cleaned = raw
      .trim()
      .replaceAll(' ', '')
      .replaceAll('\u202F', '')
      .replaceAll('\u00A0', '')
      .replaceAll(',', '.');
  if (cleaned.isEmpty) return null;
  return double.tryParse(cleaned);
}

String _capitalise(String s) => s.isEmpty ? s : '${s[0].toUpperCase()}${s.substring(1)}';

String _formatDate(DateTime d) =>
    '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';

/// Feuille modale d'ajout d'une dépense sur une catégorie existante. Renvoie
/// `true` via Navigator.pop quand la dépense a bien été enregistrée, pour que le
/// parent rafraîchisse le dashboard.
class AddExpenseSheet extends ConsumerStatefulWidget {
  const AddExpenseSheet({required this.categories, super.key});

  final List<String> categories;

  @override
  ConsumerState<AddExpenseSheet> createState() => _AddExpenseSheetState();
}

class _AddExpenseSheetState extends ConsumerState<AddExpenseSheet> {
  final _formKey = GlobalKey<FormState>();
  final _montant = TextEditingController();
  late String _categorie = widget.categories.first;
  DateTime _date = DateTime.now();

  @override
  void dispose() {
    _montant.dispose();
    super.dispose();
  }

  Future<void> _choisirDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime(now.year - 2),
      lastDate: now,
    );
    if (picked != null) setState(() => _date = picked);
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final messenger = ScaffoldMessenger.of(context);
    final navigator = Navigator.of(context);

    final ok = await ref.read(expenseControllerProvider.notifier).submit(
          ExpenseEntryRequest(
            categorie: _categorie,
            montant: _parseMontant(_montant.text)!,
            dateOperation: _date,
          ),
        );
    if (!mounted) return;

    if (ok) {
      navigator.pop(true);
    } else {
      final msg = ref.read(expenseControllerProvider).errorMessage ?? 'Une erreur est survenue.';
      messenger.showSnackBar(SnackBar(content: Text(msg)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final submitState = ref.watch(expenseControllerProvider);
    final theme = Theme.of(context);

    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Ajouter une dépense', style: theme.textTheme.titleLarge),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _categorie,
              decoration: const InputDecoration(labelText: 'Catégorie'),
              items: widget.categories
                  .map((c) => DropdownMenuItem(value: c, child: Text(_capitalise(c))))
                  .toList(),
              onChanged: (v) => setState(() => _categorie = v ?? _categorie),
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _montant,
              decoration: const InputDecoration(labelText: 'Montant €'),
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              autofocus: true,
              validator: (v) {
                final m = _parseMontant(v ?? '');
                if (m == null) return 'Montant attendu';
                if (m <= 0) return 'Doit être supérieur à 0';
                return null;
              },
            ),
            const SizedBox(height: 12),
            InputDecorator(
              decoration: const InputDecoration(labelText: 'Date'),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(_formatDate(_date)),
                  TextButton.icon(
                    icon: const Icon(Icons.calendar_today, size: 18),
                    label: const Text('Modifier'),
                    onPressed: _choisirDate,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            ElevatedButton(
              onPressed: submitState.isSubmitting ? null : _submit,
              child: submitState.isSubmitting
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Enregistrer'),
            ),
          ],
        ),
      ),
    );
  }
}
