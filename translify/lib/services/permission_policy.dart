import 'package:permission_handler/permission_handler.dart';

bool microphoneIsGranted(PermissionStatus status) => status.isGranted;
bool microphoneNeedsSettings(PermissionStatus status) =>
    status.isPermanentlyDenied || status.isRestricted;
