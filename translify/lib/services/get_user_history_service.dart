import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_failure.dart';
import 'endpoints.dart';
import 'get_token.dart';

Future<List<dynamic>> getUserHistoryService({http.Client? client}) async {
  final token = await getToken();
  if (token.isEmpty) throw const ApiFailure('Please log in to view your history.');
  final ownClient = client == null;
  final active = client ?? http.Client();
  try {
    final response = await active.get(
      Endpoints.userHistory,
      headers: {'Authorization': 'Bearer $token'},
    ).timeout(const Duration(seconds: 20));
    if (response.statusCode != 200) throw apiFailureForStatus(response.statusCode);
    final dynamic body = jsonDecode(response.body);
    if (body is! Map<String, dynamic> || body['items'] is! List) {
      throw const ApiFailure('Could not read your translation history.');
    }
    return body['items'] as List<dynamic>;
  } on TimeoutException {
    throw const ApiFailure('History took too long to load. Please try again.');
  } on FormatException {
    throw const ApiFailure('Could not read your translation history.');
  } finally {
    if (ownClient) active.close();
  }
}
