import 'dart:io';
import 'package:flutter/material.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:record/record.dart';
import 'package:translify/services/api_failure.dart';
import 'package:translify/services/permission_policy.dart';
import 'package:translify/services/speech_translate_service.dart';

class ConversationTranslationView extends StatefulWidget {
  const ConversationTranslationView({super.key});
  @override
  State<ConversationTranslationView> createState() => _ConversationTranslationViewState();
}

class _ConversationTranslationViewState extends State<ConversationTranslationView> {
  late final AudioRecorder _recorder;
  String _first = 'en';
  String _second = 'es';
  String _firstText = 'Tap the microphone to speak.';
  String _secondText = 'The translated text will appear here.';
  bool _recording = false;
  bool _loading = false;
  int? _speaker;
  String? _recordingPath;
  static const _languages = {'en': 'English', 'es': 'Spanish', 'fr': 'French'};

  @override
  void initState() {
    super.initState();
    _recorder = AudioRecorder();
  }

  @override
  void dispose() {
    _recorder.dispose();
    super.dispose();
  }

  void _message(String content) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(content)));
  }

  Future<bool> _requestMicrophone() async {
    var status = await Permission.microphone.status;
    if (microphoneIsGranted(status)) return true;
    if (microphoneNeedsSettings(status)) {
      _message('Microphone access is disabled. Enable it in your device settings.');
      return false;
    }
    status = await Permission.microphone.request();
    if (microphoneIsGranted(status)) return true;
    if (microphoneNeedsSettings(status)) {
      _message('Enable microphone permission in your device settings.');
    } else {
      _message('Microphone permission is needed to translate speech.');
    }
    return false;
  }

  Future<void> _start(int speaker) async {
    if (_loading || _recording) return;
    try {
      if (!await _requestMicrophone() || !mounted) return;
      final directory = await getTemporaryDirectory();
      final path = '${directory.path}/translify_${DateTime.now().microsecondsSinceEpoch}.wav';
      await _recorder.start(const RecordConfig(encoder: AudioEncoder.wav), path: path);
      if (mounted) setState(() { _speaker = speaker; _recording = true; _recordingPath = path; });
    } catch (error) {
      _message(readableFailure(error));
    }
  }

  Future<void> _finish({required bool cancelled}) async {
    if (!_recording || _loading) return;
    final speaker = _speaker;
    final source = speaker == 1 ? _first : _second;
    final target = speaker == 1 ? _second : _first;
    String? path = _recordingPath;
    if (mounted) setState(() { _recording = false; _loading = !cancelled; });
    try {
      if (cancelled) {
        await _recorder.cancel();
      } else {
        path = await _recorder.stop();
        if (path == null) throw const ApiFailure('No audio was recorded. Please try again.');
        final result = await speechTranslateService(path, source, target);
        if (!mounted) return;
        setState(() {
          if (speaker == 1) {
            _firstText = result.$1;
            _secondText = result.$2;
          } else {
            _firstText = result.$2;
            _secondText = result.$1;
          }
        });
      }
    } catch (error) {
      _message(readableFailure(error));
    } finally {
      if (path != null) {
        try { await File(path).delete(); } on FileSystemException { /* already removed */ }
      }
      if (mounted) setState(() { _recording = false; _loading = false; _speaker = null; _recordingPath = null; });
    }
  }

  Widget _language(String title, String value, void Function(String?) change) {
    return DropdownButtonFormField<String>(
      key: ValueKey('$title:$value'),
      initialValue: value,
      decoration: InputDecoration(labelText: title),
      items: _languages.entries.map((entry) => DropdownMenuItem(
        value: entry.key, child: Text(entry.value))).toList(),
      onChanged: _loading || _recording ? null : change,
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Conversation translation')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 700),
          child: ListView(padding: const EdgeInsets.all(20), children: [
            _language('Speaker 1 language', _first, (value) {
              if (value == null) return;
              setState(() { if (value == _second) _second = _first; _first = value; });
            }),
            const SizedBox(height: 12),
            _language('Speaker 2 language', _second, (value) {
              if (value == null) return;
              setState(() { if (value == _first) _first = _second; _second = value; });
            }),
            const SizedBox(height: 20),
            Card(child: Padding(padding: const EdgeInsets.all(18), child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [Text('Speaker 1', style: Theme.of(context).textTheme.titleLarge),
                SelectableText(_firstText)],
            ))),
            Card(child: Padding(padding: const EdgeInsets.all(18), child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [Text('Speaker 2', style: Theme.of(context).textTheme.titleLarge),
                SelectableText(_secondText)],
            ))),
            const SizedBox(height: 12),
            if (_loading) const Center(child: CircularProgressIndicator())
            else if (_recording) ...[
              const Center(child: Text('Recording…')),
              Row(mainAxisAlignment: MainAxisAlignment.spaceEvenly, children: [
                TextButton(onPressed: () => _finish(cancelled: true), child: const Text('Cancel')),
                ElevatedButton(onPressed: () => _finish(cancelled: false), child: const Text('Finish recording')),
              ]),
            ] else ...[
              ElevatedButton.icon(onPressed: () => _start(1),
                icon: const Icon(Icons.mic), label: const Text('Record speaker 1')),
              const SizedBox(height: 8),
              ElevatedButton.icon(onPressed: () => _start(2),
                icon: const Icon(Icons.mic), label: const Text('Record speaker 2')),
            ],
          ]),
        ),
      ),
    );
  }
}
