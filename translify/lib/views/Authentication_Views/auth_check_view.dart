import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:translify/colors/colors.dart';
import 'package:translify/services/api_failure.dart';
import 'package:translify/services/get_user_status.dart';
import 'package:translify/router/routes.dart';

class AuthCheckView extends StatefulWidget {
  const AuthCheckView({super.key});
  @override
  State<AuthCheckView> createState() => _AuthCheckViewState();
}

class _AuthCheckViewState extends State<AuthCheckView> {
  String? _error;

  Future<void> _check() async {
    setState(() => _error = null);
    try {
      final signedIn = await getUserStatus();
      if (!mounted) return;
      context.go(signedIn ? AppRoutes.home : AppRoutes.login);
    } catch (error) {
      if (mounted) setState(() => _error = readableFailure(error));
    }
  }

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _check();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: TranslifyColors.backgroundColor,
      body: Center(
        child: _error == null
            ? const CircularProgressIndicator()
            : Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(_error!, textAlign: TextAlign.center,
                    style: TextStyle(color: TranslifyColors.headerTextColor)),
                  const SizedBox(height: 12),
                  ElevatedButton(onPressed: _check, child: const Text('Retry')),
                ],
              ),
      ),
    );
  }
}
