import 'package:flutter/material.dart';

/// Direction artistique de BudgetFamily.
///
/// Teal profond (confiance, sérieux financier) réchauffé par un accent ambre
/// (l'épargne qui fructifie) et une terracotta douce pour les visuels. Material 3,
/// surfaces claires, coins arrondis et typographie plus affirmée.
class AppTheme {
  static const Color _teal = Color(0xFF0F5257);
  static const Color _amber = Color(0xFFE39A2E);
  static const Color _terracotta = Color(0xFFCE7B4E);

  static const Color _background = Color(0xFFF4F6F5);
  static const Color _surface = Color(0xFFFFFFFF);
  static const Color _fieldFill = Color(0xFFEDF1F0);
  static const Color _border = Color(0xFFDCE4E2);
  static const Color _fabIcon = Color(0xFF12484C);

  static ThemeData get light {
    final scheme = ColorScheme.fromSeed(
      seedColor: _teal,
      brightness: Brightness.light,
    ).copyWith(
      primary: _teal,
      tertiary: _terracotta,
      surface: _surface,
    );

    final base = ThemeData(useMaterial3: true, colorScheme: scheme);

    final textTheme = base.textTheme.copyWith(
      headlineMedium: base.textTheme.headlineMedium?.copyWith(
        fontWeight: FontWeight.w700,
        letterSpacing: -0.5,
      ),
      headlineSmall: base.textTheme.headlineSmall?.copyWith(
        fontWeight: FontWeight.w700,
        letterSpacing: -0.3,
      ),
      titleLarge: base.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w700),
      titleMedium: base.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600),
      titleSmall: base.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600),
      labelLarge: base.textTheme.labelLarge?.copyWith(
        fontWeight: FontWeight.w600,
        letterSpacing: 0.2,
      ),
    );

    OutlineInputBorder inputBorder(Color color, double width) => OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: color, width: width),
        );

    return base.copyWith(
      scaffoldBackgroundColor: _background,
      textTheme: textTheme,
      appBarTheme: AppBarTheme(
        backgroundColor: _background,
        foregroundColor: scheme.onSurface,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: textTheme.titleLarge,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: _fieldFill,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        border: inputBorder(Colors.transparent, 0),
        enabledBorder: inputBorder(Colors.transparent, 0),
        focusedBorder: inputBorder(scheme.primary, 1.6),
        errorBorder: inputBorder(scheme.error, 1.2),
        focusedErrorBorder: inputBorder(scheme.error, 1.6),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: scheme.primary,
          foregroundColor: scheme.onPrimary,
          disabledBackgroundColor: _border,
          disabledForegroundColor: Colors.white,
          elevation: 0,
          minimumSize: const Size.fromHeight(52),
          textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(52),
          textStyle: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: scheme.primary,
          minimumSize: const Size.fromHeight(50),
          side: const BorderSide(color: _border),
          textStyle: const TextStyle(fontWeight: FontWeight.w600),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
      ),
      textButtonTheme: TextButtonThemeData(
        style: TextButton.styleFrom(
          foregroundColor: scheme.primary,
          textStyle: const TextStyle(fontWeight: FontWeight.w600),
        ),
      ),
      floatingActionButtonTheme: FloatingActionButtonThemeData(
        backgroundColor: _amber,
        foregroundColor: _fabIcon,
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: _fieldFill,
        side: BorderSide.none,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        labelStyle: textTheme.labelLarge?.copyWith(color: scheme.onSurface),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      ),
      progressIndicatorTheme: const ProgressIndicatorThemeData(
        color: _teal,
        linearTrackColor: _fieldFill,
        linearMinHeight: 8,
      ),
      bottomSheetTheme: const BottomSheetThemeData(
        backgroundColor: _surface,
        surfaceTintColor: Colors.transparent,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
        ),
      ),
      dividerTheme: const DividerThemeData(color: _border, thickness: 1),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: const Color(0xFF22302F),
        contentTextStyle: const TextStyle(color: Colors.white),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}
