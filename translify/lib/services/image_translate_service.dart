import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_failure.dart';
import 'endpoints.dart';
import 'get_token.dart';
import 'package:translify/models/image_translation_response_model.dart';
import 'get_history_setting.dart';

Future<List<ImageTranslationResponseModel>> imageTranslationService(
  String filepath,
  String originalLang,
  String targetLang, {
  http.Client? client,
}) async {
  final token = await getToken();
  if (token.isEmpty) {
    throw const ApiFailure('Please log in to translate images.');
  }
  final history = await getHistorySetting();
  final ownClient = client == null;
  final active = client ?? http.Client();
  try {
    final request = http.MultipartRequest('POST', Endpoints.imageTranslate)
      ..headers['Authorization'] = 'Bearer $token'
      ..fields['source_language'] = originalLang
      ..fields['target_language'] = targetLang
      ..fields['store_history'] = history;
    request.files.add(await http.MultipartFile.fromPath('image', filepath));
    final response = await active
        .send(request)
        .timeout(const Duration(seconds: 65));
    final body = await response.stream.bytesToString();
    if (response.statusCode != 200) {
      throw apiFailureForStatus(response.statusCode);
    }
    final dynamic data = jsonDecode(body);
    if (data is! Map<String, dynamic> || data['blocks'] is! List) {
      throw const ApiFailure('The image result could not be read.');
    }
    return (data['blocks'] as List)
        .map((item) => ImageTranslationResponseModel.fromJson(item))
        .toList();
  } on TimeoutException {
    throw const ApiFailure('Image translation timed out. Please try again.');
  } on FormatException {
    throw const ApiFailure('The image result could not be read.');
  } finally {
    if (ownClient) active.close();
  }
}
