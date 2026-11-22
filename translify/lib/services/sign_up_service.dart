import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_failure.dart';
import 'endpoints.dart';

Future<String> signUpService(String email, String password, {http.Client? client}) async {
  final ownClient = client == null;
  final active = client ?? http.Client();
  try {
    final response = await active.post(
      Endpoints.signUp,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email.trim(), 'password': password}),
    ).timeout(const Duration(seconds: 20));
    if (response.statusCode == 200 || response.statusCode == 201) return 'Good';
    if (response.statusCode == 409) {
      throw const ApiFailure('This email address is already registered.');
    }
    throw apiFailureForStatus(response.statusCode);
  } on TimeoutException {
    throw const ApiFailure('Sign up timed out. Check your connection and try again.');
  } finally {
    if (ownClient) active.close();
  }
}
