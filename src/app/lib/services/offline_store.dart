import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../models/quote.dart';

/// Persists past requests locally so they can be viewed offline.
///
/// Works on web (localStorage), iOS and Android via shared_preferences.
class OfflineStore {
  static const _key = 'request_history';
  static const _maxEntries = 100;

  Future<List<HistoryEntry>> load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null || raw.isEmpty) return [];
    final list = jsonDecode(raw) as List<dynamic>;
    return list
        .map((e) => HistoryEntry.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<HistoryEntry>> add(HistoryEntry entry) async {
    final prefs = await SharedPreferences.getInstance();
    final history = await load();
    history.insert(0, entry);
    if (history.length > _maxEntries) {
      history.removeRange(_maxEntries, history.length);
    }
    await prefs.setString(
      _key,
      jsonEncode(history.map((e) => e.toJson()).toList()),
    );
    return history;
  }

  Future<void> clear() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_key);
  }
}
