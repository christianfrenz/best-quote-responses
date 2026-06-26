import 'package:flutter/material.dart';

import 'screens/home_screen.dart';

void main() {
  runApp(const BestQuoteApp());
}

class BestQuoteApp extends StatelessWidget {
  const BestQuoteApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Best Quote Responses',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: Colors.indigo,
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}
