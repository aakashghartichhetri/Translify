import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:translify/widgets/forms/login_form.dart';
import 'package:translify/colors/colors.dart';
import 'package:translify/router/routes.dart';
import 'package:translify/services/api_failure.dart';
import 'package:translify/services/login_service.dart';

class LoginView extends StatefulWidget {
  const LoginView({super.key});

  @override
  State<LoginView> createState() => _LoginViewState();
}

class _LoginViewState extends State<LoginView> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _loading = false;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate() || _loading) return;
    setState(() => _loading = true);
    try {
      await loginService(_email.text, _password.text);
      if (mounted) context.go(AppRoutes.afterNewUser);
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(readableFailure(error))),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: TranslifyColors.backgroundColor,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 480),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text('Translify', style: TextStyle(
                    color: TranslifyColors.headerTextColor, fontSize: 46,
                  )),
                  const SizedBox(height: 36),
                  LoginForm(email: _email, password: _password, formKey: _formKey),
                  const SizedBox(height: 24),
                  if (_loading) const CircularProgressIndicator()
                  else ...[
                    ElevatedButton(onPressed: _login, child: const Text('Log in')),
                    TextButton(onPressed: () => context.push(AppRoutes.signUp),
                      child: const Text('Create an account')),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
