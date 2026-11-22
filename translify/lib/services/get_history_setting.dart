import 'package:flutter_secure_storage/flutter_secure_storage.dart';

Future<String> getHistorySetting() async {
  const storage = FlutterSecureStorage();
  final setting = await storage.read(key: 'save');
  // This is opt-in, including after a fresh install or a failed read.
  return setting?.toLowerCase() == 'true' ? 'true' : 'false';
}
