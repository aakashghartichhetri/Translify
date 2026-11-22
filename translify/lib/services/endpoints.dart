class Endpoints {
  // Override at build time for an emulator, staging environment, or production.
  // Example: flutter run --dart-define=TRANSLIFY_API_BASE=http://10.0.2.2:8000
  static const String base = String.fromEnvironment(
    'TRANSLIFY_API_BASE',
    defaultValue: 'https://server-core-273257216805.us-central1.run.app',
  );
  static Uri me = Uri.parse('$base/me');
  static Uri signUp = Uri.parse('$base/signup');
  static Uri login = Uri.parse('$base/login');
  static Uri textTranslate = Uri.parse('$base/translate');
  static Uri speechTranslate = Uri.parse('$base/translate/speech-to-text');
  static Uri imageTranslate = Uri.parse('$base/translate/image-to-text');
  static Uri userHistory = Uri.parse('$base/history');
}
