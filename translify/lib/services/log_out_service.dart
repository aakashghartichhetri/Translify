import 'package:flutter_secure_storage/flutter_secure_storage.dart';

Future<void> logOutService() async {
  const storage = FlutterSecureStorage();
  await storage.delete(key: 'access_token');
  // The next account must explicitly opt into its own translation history.
  await storage.delete(key: 'save');
}
