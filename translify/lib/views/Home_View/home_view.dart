import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:translify/router/routes.dart';
import 'package:translify/colors/colors.dart';
import 'package:translify/widgets/feature_button.dart';

class HomeView extends StatelessWidget {
  const HomeView({super.key});

  Future<void> _camera(BuildContext context) async {
    final permission = await Permission.camera.status;
    if (!context.mounted) return;
    context.push(permission.isGranted ? AppRoutes.initialCamera : AppRoutes.cameraPermission);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: TranslifyColors.backgroundColor,
      appBar: AppBar(
        title: const Text('Translify'),
        actions: [IconButton(tooltip: 'Settings and history',
          onPressed: () => context.push(AppRoutes.settings),
          icon: const Icon(Icons.settings))],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 500),
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              FeatureButton(action: () => context.push(AppRoutes.textTranslation),
                icon: Icons.translate, text: 'Text translation',
                accentColor: TranslifyColors.cameraTranslationAccentColor,
                backgroundColor: TranslifyColors.nonAdminButtonColor),
              const SizedBox(height: 16),
              FeatureButton(action: () => _camera(context),
                icon: Icons.photo_camera_outlined, text: 'Camera translation',
                accentColor: TranslifyColors.cameraTranslationAccentColor,
                backgroundColor: TranslifyColors.nonAdminButtonColor),
              const SizedBox(height: 16),
              FeatureButton(action: () => context.push(AppRoutes.conversation),
                icon: Icons.mic_none_rounded, text: 'Conversation translation',
                accentColor: TranslifyColors.convesationTranslationAccentColor,
                backgroundColor: TranslifyColors.nonAdminButtonColor),
            ],
          ),
        ),
      ),
    );
  }
}
