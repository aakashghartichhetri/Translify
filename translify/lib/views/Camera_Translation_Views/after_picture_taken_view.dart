import 'dart:io';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:translify/languages/languages.dart';
import 'package:translify/colors/colors.dart';
import 'package:translify/widgets/language_selector.dart';
import 'package:translify/router/routes.dart';
import 'package:translify/services/api_failure.dart';
import 'package:translify/services/image_translate_service.dart';

class AfterPictureTakenView extends StatefulWidget {
  const AfterPictureTakenView({
    super.key,
    required this.imagePath,
    required this.initialSourceLanguage,
    required this.initialTargetLanguage,
  });
  final String imagePath;
  final String initialSourceLanguage;
  final String initialTargetLanguage;

  @override
  State<AfterPictureTakenView> createState() => _AfterPictureTakenViewState();
}

class _AfterPictureTakenViewState extends State<AfterPictureTakenView> {
  late String _source;
  late String _target;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _source = widget.initialSourceLanguage;
    _target = widget.initialTargetLanguage;
  }

  String _languageName(String code) =>
      Languages.values.firstWhere((language) => language.code == code).name;

  Future<void> _translate() async {
    if (_loading) return;
    setState(() => _loading = true);
    try {
      final blocks = await imageTranslationService(
        widget.imagePath,
        _source,
        _target,
      );
      if (!mounted) return;
      context.push(
        AppRoutes.cameraTranslationResult,
        extra: {'path': widget.imagePath, 'results': blocks},
      );
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(readableFailure(error))));
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, result) {
        if (!didPop) context.pushReplacement(AppRoutes.initialCamera);
      },
      child: Scaffold(
        appBar: AppBar(title: const Text('Translate your photo')),
        backgroundColor: TranslifyColors.backgroundColor,
        body: Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 650),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                SizedBox(
                  height: MediaQuery.of(context).size.height * .45,
                  child: Image.file(
                    File(widget.imagePath),
                    fit: BoxFit.contain,
                    errorBuilder: (context, error, stack) => const Center(
                      child: Text(
                        'Photo could not be displayed. Please take another.',
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                LanguageSelector(
                  updateLanguageChoice: (language) => setState(() {
                    if (_target == language.code) _target = _source;
                    _source = language.code;
                  }),
                  buttonText: 'Source language: ${_languageName(_source)}',
                  buttonBackgroundColor:
                      TranslifyColors.cameraTranslationAccentColor,
                  buttonTextColor: TranslifyColors.darkButtonText,
                  menuItemBackgroundColor: TranslifyColors.nonAdminButtonColor,
                  menuItemTextColor:
                      TranslifyColors.cameraTranslationAccentColor,
                  currentLanguage: _source,
                  disabledColor: TranslifyColors.disabledOptionColor,
                ),
                const SizedBox(height: 12),
                LanguageSelector(
                  updateLanguageChoice: (language) => setState(() {
                    if (_source == language.code) _source = _target;
                    _target = language.code;
                  }),
                  buttonText: 'Target language: ${_languageName(_target)}',
                  buttonBackgroundColor:
                      TranslifyColors.cameraTranslationAccentColor,
                  buttonTextColor: TranslifyColors.darkButtonText,
                  menuItemBackgroundColor: TranslifyColors.nonAdminButtonColor,
                  menuItemTextColor:
                      TranslifyColors.cameraTranslationAccentColor,
                  currentLanguage: _target,
                  disabledColor: TranslifyColors.disabledOptionColor,
                ),
                const SizedBox(height: 22),
                if (_loading)
                  const Center(child: CircularProgressIndicator())
                else
                  ElevatedButton(
                    onPressed: _translate,
                    child: const Text('Translate photo'),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
