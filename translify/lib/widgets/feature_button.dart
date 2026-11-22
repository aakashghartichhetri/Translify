import 'package:flutter/material.dart';

class FeatureButton extends StatelessWidget {
  const FeatureButton({super.key, required this.action, required this.icon,
    required this.text, required this.accentColor, required this.backgroundColor});

  final VoidCallback action;
  final IconData icon;
  final String text;
  final Color accentColor;
  final Color backgroundColor;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      button: true,
      label: text,
      child: ElevatedButton.icon(
        onPressed: action,
        icon: Icon(icon, color: accentColor, size: 36),
        label: Text(text, style: TextStyle(color: accentColor, fontSize: 19)),
        style: ElevatedButton.styleFrom(
          backgroundColor: backgroundColor,
          minimumSize: const Size.fromHeight(88),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        ),
      ),
    );
  }
}
