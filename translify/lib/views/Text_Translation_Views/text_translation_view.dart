import 'package:flutter/material.dart';
import 'package:translify/services/api_failure.dart';
import 'package:translify/services/text_translate_service.dart';

typedef TranslateText = Future<String> Function(String text, String source, String target);

class TextTranslationView extends StatefulWidget {
  const TextTranslationView({super.key, this.translate = textTranslateService});
  final TranslateText translate;

  @override
  State<TextTranslationView> createState() => _TextTranslationViewState();
}

class _TextTranslationViewState extends State<TextTranslationView> {
  final _input = TextEditingController();
  String _source = 'en';
  String _target = 'es';
  String? _result;
  String? _error;
  bool _loading = false;
  static const languages = {'en': 'English', 'es': 'Spanish', 'fr': 'French'};

  @override
  void dispose() {
    _input.dispose();
    super.dispose();
  }

  Future<void> _translate() async {
    if (_loading) return;
    if (_input.text.trim().isEmpty) {
      setState(() => _error = 'Enter text to translate.');
      return;
    }
    setState(() { _loading = true; _error = null; _result = null; });
    try {
      final result = await widget.translate(_input.text, _source, _target);
      if (mounted) setState(() => _result = result);
    } catch (error) {
      if (mounted) setState(() => _error = readableFailure(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Text translation')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 640),
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              const Text('Choose languages and enter a phrase.'),
              const SizedBox(height: 16),
              DropdownButtonFormField<String>(
                key: const Key('source-language'), initialValue: _source,
                decoration: const InputDecoration(labelText: 'From'),
                items: languages.entries.map((entry) => DropdownMenuItem(
                  value: entry.key, child: Text(entry.value))).toList(),
                onChanged: _loading ? null : (value) { if (value != null) setState(() => _source = value); },
              ),
              DropdownButtonFormField<String>(
                key: const Key('target-language'), initialValue: _target,
                decoration: const InputDecoration(labelText: 'To'),
                items: languages.entries.map((entry) => DropdownMenuItem(
                  value: entry.key, child: Text(entry.value))).toList(),
                onChanged: _loading ? null : (value) { if (value != null) setState(() => _target = value); },
              ),
              const SizedBox(height: 16),
              TextField(
                key: const Key('translation-input'), controller: _input,
                maxLines: 5, maxLength: 5000,
                decoration: const InputDecoration(labelText: 'Text to translate',
                  border: OutlineInputBorder()),
              ),
              const SizedBox(height: 16),
              ElevatedButton(onPressed: _loading ? null : _translate,
                child: const Text('Translate')),
              if (_loading) const Center(child: CircularProgressIndicator()),
              if (_error != null) Padding(
                padding: const EdgeInsets.only(top: 16),
                child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
              ),
              if (_result != null) Padding(
                padding: const EdgeInsets.only(top: 16),
                child: SelectableText(_result!, key: const Key('translation-result')),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
