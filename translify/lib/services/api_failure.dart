import 'dart:async';
import 'dart:io';
import 'package:http/http.dart' as http;

class ApiFailure implements Exception {
  final String message;
  const ApiFailure(this.message);

  @override
  String toString() => message;
}

String readableFailure(Object error) {
  if (error is ApiFailure) return error.message;
  if (error is TimeoutException || error is SocketException || error is http.ClientException) {
    return 'The server could not be reached. Check your connection and try again.';
  }
  return 'Something went wrong. Please try again.';
}

ApiFailure apiFailureForStatus(int status) {
  if (status == 401 || status == 403) {
    return const ApiFailure('Your session has expired. Please log in again.');
  }
  if (status == 413) return const ApiFailure('This file is too large to upload.');
  if (status == 422 || status == 400) {
    return const ApiFailure('Please check your input and try again.');
  }
  if (status == 502 || status == 503 || status == 504) {
    return const ApiFailure('The translation service is temporarily unavailable.');
  }
  return const ApiFailure('The request could not be completed. Please try again.');
}
