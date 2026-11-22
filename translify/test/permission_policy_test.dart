import 'package:flutter_test/flutter_test.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:translify/services/permission_policy.dart';

void main() {
  test('only granted microphone permissions allow recording', () {
    expect(microphoneIsGranted(PermissionStatus.granted), isTrue);
    expect(microphoneIsGranted(PermissionStatus.denied), isFalse);
    expect(microphoneIsGranted(PermissionStatus.permanentlyDenied), isFalse);
  });

  test('permanent denials are directed to settings', () {
    expect(microphoneNeedsSettings(PermissionStatus.permanentlyDenied), isTrue);
    expect(microphoneNeedsSettings(PermissionStatus.denied), isFalse);
  });
}
