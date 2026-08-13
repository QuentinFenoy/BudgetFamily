import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_exception.dart';
import '../../../core/network/providers.dart';
import '../data/expense_models.dart';
import '../data/expense_repository.dart';

final expenseRepositoryProvider = Provider<ExpenseRepository>((ref) {
  return ExpenseRepository(ref.watch(apiClientProvider));
});

final expenseControllerProvider =
    StateNotifierProvider.autoDispose<ExpenseController, ExpenseSubmitState>((ref) {
  return ExpenseController(ref.watch(expenseRepositoryProvider));
});

class ExpenseSubmitState {
  const ExpenseSubmitState({this.isSubmitting = false, this.errorMessage});

  final bool isSubmitting;
  final String? errorMessage;

  ExpenseSubmitState copyWith({
    bool? isSubmitting,
    String? errorMessage,
    bool clearError = false,
  }) {
    return ExpenseSubmitState(
      isSubmitting: isSubmitting ?? this.isSubmitting,
      errorMessage: clearError ? null : (errorMessage ?? this.errorMessage),
    );
  }
}

class ExpenseController extends StateNotifier<ExpenseSubmitState> {
  ExpenseController(this._repository) : super(const ExpenseSubmitState());

  final ExpenseRepository _repository;

  Future<bool> submit(ExpenseEntryRequest request) async {
    state = state.copyWith(isSubmitting: true, clearError: true);
    try {
      await _repository.addExpense(request);
      state = state.copyWith(isSubmitting: false);
      return true;
    } on ApiException catch (error) {
      state = state.copyWith(isSubmitting: false, errorMessage: error.message);
      return false;
    }
  }
}
