import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/quote.dart';

/// Talks to the backend search API.
///
/// Override the base URL at build/run time:
///   flutter run --dart-define=API_BASE_URL=http://localhost:8000
class ApiService {
  ApiService({String? baseUrl})
      : baseUrl = baseUrl ??
            const String.fromEnvironment(
              'API_BASE_URL',
              defaultValue: 'http://localhost:8000',
            );

  final String baseUrl;

  Future<List<Quote>> search(String text, {int limit = 5}) async {
    final uri = Uri.parse('$baseUrl/api/search');
    final response = await http
        .post(
          uri,
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'text': text, 'limit': limit}),
        )
        .timeout(const Duration(seconds: 30));

    if (response.statusCode != 200) {
      throw Exception('Search failed (${response.statusCode})');
    }

    final data = jsonDecode(response.body) as Map<String, dynamic>;
    return (data['results'] as List<dynamic>)
        .map((e) => Quote.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
