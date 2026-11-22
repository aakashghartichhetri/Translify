import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:translify/router/routes.dart';
import 'package:translify/services/set_translation_history.dart';
import 'package:translify/services/get_history_setting.dart';

class AfterNewUserView extends StatefulWidget {
  const AfterNewUserView({super.key});
  @override
  State<AfterNewUserView> createState() => _AfterNewUserViewState();
}

class _AfterNewUserViewState extends State<AfterNewUserView> {
  bool _save = false;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final setting = await getHistorySetting();
      if (mounted) setState(() { _save = setting == 'true'; _loading = false; });
    } catch (_) {
      if (mounted) setState(() { _error = 'Could not load your preference.'; _loading = false; });
    }
  }

  Future<void> _update(bool value) async {
    try {
      await setTranslationHistory(value ? 'true' : 'false');
      if (mounted) setState(() { _save = value; _error = null; });
    } catch (_) {
      if (mounted) setState(() => _error = 'Could not save your preference. Please retry.');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Translation history')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 540),
          child: ListView(padding: const EdgeInsets.all(24), children: [
            const Icon(Icons.privacy_tip_outlined, size: 64),
            const SizedBox(height: 20),
            Text('Your history, your choice', style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: 12),
            const Text('Turn this on to save future translations to your account so you can view them later. '
              'It is off by default. Turning it off will not delete previously saved translations.'),
            const SizedBox(height: 24),
            if (_loading) const Center(child: CircularProgressIndicator())
            else SwitchListTile(
              title: const Text('Save future translations'),
              subtitle: Text(_save ? 'On' : 'Off'),
              value: _save, onChanged: _update,
            ),
            if (_error != null) Padding(
              padding: const EdgeInsets.all(12),
              child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
            ),
            const SizedBox(height: 20),
            ElevatedButton(onPressed: _loading ? null : () => context.go(AppRoutes.home),
              child: const Text('Continue')),
          ]),
        ),
      ),
    );
  }
}
