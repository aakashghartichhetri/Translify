import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:translify/services/api_failure.dart';
import 'package:translify/services/login_service.dart';
import 'package:translify/services/sign_up_service.dart';

void main() {
  test('signup accepts HTTP 201', () async {
    final client = MockClient((_) async => http.Response('{}', 201));
    expect(await signUpService('test@example.com', 'test-password', client: client), 'Good');
    client.close();
  });

  test('signup reports duplicate accounts without server internals', () async {
    final client = MockClient((_) async => http.Response('internal error', 409));
    expect(() => signUpService('test@example.com', 'test-password', client: client),
      throwsA(isA<ApiFailure>()));
    client.close();
  });

  test('login validates token and persists it through an injectable store', () async {
    String? saved;
    final client = MockClient((_) async => http.Response(jsonEncode({'access_token': 'example.token'}), 200));
    final ok = await loginService('test@example.com', 'test-password', client: client,
      persistToken: (token) async { saved = token; });
    expect(ok, true);
    expect(saved, 'example.token');
    client.close();
  });

  test('login rejects malformed success payload', () async {
    final client = MockClient((_) async => http.Response(jsonEncode({'unexpected': true}), 200));
    expect(() => loginService('test@example.com', 'test-password', client: client),
      throwsA(isA<ApiFailure>()));
    client.close();
  });
}
