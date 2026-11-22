import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:translify/widgets/forms/sign_up_form.dart';
import 'package:translify/colors/colors.dart';
import 'package:translify/services/api_failure.dart';
import 'package:translify/services/sign_up_service.dart';

class SignUpView extends StatefulWidget {
  const SignUpView({super.key});

  @override
  State<SignUpView> createState() => _SignUpViewState();
}

class _SignUpViewState extends State<SignUpView> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _confirmPassword = TextEditingController();
  final _formKey = GlobalKey<FormState>();
  bool _loading = false;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    _confirmPassword.dispose();
    super.dispose();
  }

  Future<void> _signUp() async {
    if (!_formKey.currentState!.validate() || _loading) return;
    setState(() => _loading = true);
    try {
      await signUpService(_email.text, _password.text);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Account created. You can now log in.')),
      );
      context.pop(); // Calling pop matters: the old code only referenced the function.
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
                  Text('Create account', style: TextStyle(
                    color: TranslifyColors.headerTextColor, fontSize: 34,
                  )),
                  const SizedBox(height: 32),
                  SignUpForm(email: _email, password: _password,
                    confirmPassword: _confirmPassword, formKey: _formKey),
                  const SizedBox(height: 24),
                  if (_loading) const CircularProgressIndicator()
                  else ElevatedButton(onPressed: _signUp, child: const Text('Sign up')),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
