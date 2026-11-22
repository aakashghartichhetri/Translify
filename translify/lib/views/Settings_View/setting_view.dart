import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:translify/router/routes.dart';
import 'package:translify/services/api_failure.dart';
import 'package:translify/services/delete_history_service.dart';
import 'package:translify/services/get_user_history_service.dart';
import 'package:translify/services/log_out_service.dart';

class SettingView extends StatefulWidget {
  const SettingView({super.key});
  @override
  State<SettingView> createState() => _SettingViewState();
}

class _SettingViewState extends State<SettingView> {
  bool _loading = true;
  String? _error;
  List<dynamic> _history = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final history = await getUserHistoryService();
      if (mounted) setState(() => _history = history);
    } catch (error) {
      if (mounted) setState(() => _error = readableFailure(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _delete() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete translation history?'),
        content: const Text(
          'This permanently deletes translations saved to your account.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    try {
      await deleteHistoryService();
      if (mounted) await _load();
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(readableFailure(error))));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Settings and history')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 700),
          child: Column(
            children: [
              Wrap(
                spacing: 8,
                alignment: WrapAlignment.center,
                children: [
                  TextButton.icon(
                    onPressed: () => context.push(AppRoutes.afterNewUser),
                    icon: const Icon(Icons.privacy_tip),
                    label: const Text('History preference'),
                  ),
                  TextButton.icon(
                    onPressed: _history.isEmpty ? null : _delete,
                    icon: const Icon(Icons.delete_outline),
                    label: const Text('Delete saved history'),
                  ),
                  TextButton.icon(
                    onPressed: _load,
                    icon: const Icon(Icons.refresh),
                    label: const Text('Refresh'),
                  ),
                  TextButton.icon(
                    onPressed: () async {
                      await logOutService();
                      if (context.mounted) context.go(AppRoutes.login);
                    },
                    icon: const Icon(Icons.logout),
                    label: const Text('Log out'),
                  ),
                ],
              ),
              if (_loading)
                const Expanded(
                  child: Center(child: CircularProgressIndicator()),
                )
              else if (_error != null)
                Expanded(child: Center(child: Text(_error!)))
              else if (_history.isEmpty)
                const Expanded(
                  child: Center(child: Text('No translations saved yet.')),
                )
              else
                Expanded(
                  child: ListView.builder(
                    itemCount: _history.length,
                    itemBuilder: (context, index) {
                      final item = _history[index] as Map<String, dynamic>;
                      return ListTile(
                        title: Text(item['translated_text'] as String? ?? ''),
                        subtitle: Text(item['original_text'] as String? ?? ''),
                        isThreeLine: true,
                      );
                    },
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
