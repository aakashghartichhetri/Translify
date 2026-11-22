import 'dart:async';
import 'package:http/http.dart' as http;
import 'api_failure.dart';
import 'endpoints.dart';
import 'get_token.dart';
import 'log_out_service.dart';

Future<bool> getUserStatus({http.Client? client}) async {
  final accessToken = await getToken();
  if (accessToken.isEmpty) return false;
  final ownClient = client == null;
  final active = client ?? http.Client();
  try {
    final response = await active.get(
      Endpoints.me,
      headers: {'Authorization': 'Bearer $accessToken'},
    ).timeout(const Duration(seconds: 15));
    if (response.statusCode == 200) return true;
    if (response.statusCode == 401 || response.statusCode == 403) {
      await logOutService();
      return false;
    }
    throw apiFailureForStatus(response.statusCode);
  } on TimeoutException {
    throw const ApiFailure('Unable to verify your session. Check your connection.');
  } finally {
    if (ownClient) active.close();
  }
}
