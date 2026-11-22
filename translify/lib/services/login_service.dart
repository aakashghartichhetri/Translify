import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_failure.dart';
import 'save_token.dart';
import 'set_translation_history.dart';
import 'endpoints.dart';

Future<bool> loginService(
  String email,
  String password, {
  http.Client? client,
  Future<void> Function(String)? persistToken,
}) async {
  final ownClient = client == null;
  final active = client ?? http.Client();
  try {
    final response = await active.post(
      Endpoints.login,
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {'username': email.trim(), 'password': password},
    ).timeout(const Duration(seconds: 20));
    if (response.statusCode == 401) {
      throw const ApiFailure('Incorrect email or password.');
    }
    if (response.statusCode != 200) throw apiFailureForStatus(response.statusCode);
    final dynamic data = jsonDecode(response.body);
    if (data is! Map<String, dynamic> || data['access_token'] is! String ||
        (data['access_token'] as String).isEmpty) {
      throw const ApiFailure('The server returned an invalid login response.');
    }
    // Consent is tied to this sign-in, not reused from any previous account.
    if (persistToken == null) {
      await setTranslationHistory('false');
    }
    await (persistToken ?? saveToken)(data['access_token'] as String);
    return true;
  } on TimeoutException {
    throw const ApiFailure('Login timed out. Check your connection and try again.');
  } on FormatException {
    throw const ApiFailure('The server returned an invalid login response.');
  } finally {
    if (ownClient) active.close();
  }
}
