import 'dart:async';
import 'package:http/http.dart' as http;
import 'api_failure.dart';
import 'endpoints.dart';
import 'get_token.dart';

Future<void> deleteHistoryService({http.Client? client}) async {
  final token = await getToken();
  if (token.isEmpty) throw const ApiFailure('Please log in again.');
  final ownClient = client == null;
  final active = client ?? http.Client();
  try {
    final response = await active.delete(Endpoints.userHistory,
      headers: {'Authorization': 'Bearer $token'}).timeout(const Duration(seconds: 20));
    if (response.statusCode != 200) throw apiFailureForStatus(response.statusCode);
  } on TimeoutException {
    throw const ApiFailure('Deleting your history timed out. Please try again.');
  } finally {
    if (ownClient) active.close();
  }
}
