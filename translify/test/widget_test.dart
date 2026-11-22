import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:translify/services/api_failure.dart';
import 'package:translify/views/Text_Translation_Views/text_translation_view.dart';

void main() {
  testWidgets('text translation displays a result', (tester) async {
    await tester.pumpWidget(MaterialApp(home: TextTranslationView(
      translate: (text, source, target) async => '$text translated',
    )));
    await tester.enterText(find.byKey(const Key('translation-input')), 'Hello');
    await tester.tap(find.text('Translate'));
    await tester.pumpAndSettle();
    expect(find.text('Hello translated'), findsOneWidget);
  });

  testWidgets('empty text requests are rejected without a network call', (tester) async {
    var calls = 0;
    await tester.pumpWidget(MaterialApp(home: TextTranslationView(
      translate: (text, source, target) async { calls++; return 'hi'; },
    )));
    await tester.tap(find.text('Translate'));
    await tester.pump();
    expect(find.text('Enter text to translate.'), findsOneWidget);
    expect(calls, 0);
  });

  testWidgets('network failures show a useful message', (tester) async {
    await tester.pumpWidget(MaterialApp(home: TextTranslationView(
      translate: (text, source, target) async => throw const ApiFailure('Network is unavailable.'),
    )));
    await tester.enterText(find.byKey(const Key('translation-input')), 'Hello');
    await tester.tap(find.text('Translate'));
    await tester.pumpAndSettle();
    expect(find.text('Network is unavailable.'), findsOneWidget);
  });
}
