import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_failure.dart';
import 'endpoints.dart';
import 'get_history_setting.dart';
import 'get_token.dart';

Future<String> textTranslateService(String text, String source, String target,
    {http.Client? client}) async {
  final token = await getToken();
  if (token.isEmpty) throw const ApiFailure('Please log in to translate text.');
  final store = await getHistorySetting();
  final ownClient = client == null;
  final active = client ?? http.Client();
  try {
    final response = await active.post(
      Endpoints.textTranslate,
      headers: {'Authorization': 'Bearer $token', 'Content-Type': 'application/json'},
      body: jsonEncode({
        'text': text, 'source_language': source, 'target_language': target,
        'store_history': store == 'true',
      }),
    ).timeout(const Duration(seconds: 35));
    if (response.statusCode != 200) throw apiFailureForStatus(response.statusCode);
    final dynamic body = jsonDecode(response.body);
    if (body is! Map<String, dynamic> || body['translated_text'] is! String) {
      throw const ApiFailure('The translation service returned an invalid response.');
    }
    return body['translated_text'] as String;
  } on TimeoutException {
    throw const ApiFailure('Translation timed out. Please try again.');
  } on FormatException {
    throw const ApiFailure('The translation service returned an invalid response.');
  } finally {
    if (ownClient) active.close();
  }
}
