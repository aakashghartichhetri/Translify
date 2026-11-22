import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_failure.dart';
import 'endpoints.dart';
import 'get_history_setting.dart';
import 'get_token.dart';

Future<(String, String)> speechTranslateService(
  String filepath,
  String originalLang,
  String targetLang, {
  http.Client? client,
}) async {
  final token = await getToken();
  if (token.isEmpty) {
    throw const ApiFailure('Please log in to translate speech.');
  }
  final history = await getHistorySetting();
  final ownClient = client == null;
  final active = client ?? http.Client();
  try {
    final request = http.MultipartRequest('POST', Endpoints.speechTranslate)
      ..headers['Authorization'] = 'Bearer $token'
      ..fields['source_language'] = originalLang
      ..fields['target_language'] = targetLang
      ..fields['store_history'] = history;
    request.files.add(await http.MultipartFile.fromPath('recording', filepath));
    final response = await active
        .send(request)
        .timeout(const Duration(seconds: 110));
    final body = await response.stream.bytesToString();
    if (response.statusCode != 200) {
      throw apiFailureForStatus(response.statusCode);
    }
    final dynamic data = jsonDecode(body);
    if (data is! Map<String, dynamic> ||
        data['original_text'] is! String ||
        data['translated_text'] is! String) {
      throw const ApiFailure('The speech result could not be read.');
    }
    return (data['original_text'] as String, data['translated_text'] as String);
  } on TimeoutException {
    throw const ApiFailure('Speech translation timed out. Please try again.');
  } on FormatException {
    throw const ApiFailure('The speech result could not be read.');
  } finally {
    if (ownClient) active.close();
  }
}
