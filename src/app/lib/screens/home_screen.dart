import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../models/quote.dart';
import '../services/api_service.dart';
import '../services/offline_store.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _controller = TextEditingController();
  final _api = ApiService();
  final _store = OfflineStore();

  List<Quote> _results = [];
  List<HistoryEntry> _history = [];
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _loadHistory() async {
    final history = await _store.load();
    if (mounted) setState(() => _history = history);
  }

  Future<void> _search() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final results = await _api.search(text);
      final entry = HistoryEntry(
        query: text,
        results: results,
        createdAt: DateTime.now(),
      );
      final history = await _store.add(entry);
      if (!mounted) return;
      setState(() {
        _results = results;
        _history = history;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = 'Could not reach the server. '
          'Showing offline history instead.');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _openSource(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Best Quote Responses'),
        actions: [
          IconButton(
            tooltip: 'Clear history',
            icon: const Icon(Icons.delete_outline),
            onPressed: () async {
              await _store.clear();
              setState(() => _history = []);
            },
          ),
        ],
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 720),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextField(
                  controller: _controller,
                  decoration: InputDecoration(
                    hintText: 'Type a thought, feeling or situation...',
                    border: const OutlineInputBorder(),
                    suffixIcon: IconButton(
                      icon: const Icon(Icons.search),
                      onPressed: _loading ? null : _search,
                    ),
                  ),
                  onSubmitted: (_) => _search(),
                ),
                const SizedBox(height: 12),
                if (_loading) const LinearProgressIndicator(),
                if (_error != null)
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 8),
                    child: Text(_error!,
                        style: TextStyle(color: Theme.of(context).colorScheme.error)),
                  ),
                Expanded(child: _buildBody()),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildBody() {
    if (_results.isNotEmpty) {
      return ListView(
        children: [
          const _SectionLabel('Best matches'),
          ..._results.map(_quoteCard),
        ],
      );
    }
    if (_history.isNotEmpty) {
      return ListView(
        children: [
          const _SectionLabel('Recent (saved offline)'),
          ..._history.expand((h) => [
                Padding(
                  padding: const EdgeInsets.only(top: 8, bottom: 4),
                  child: Text('"${h.query}"',
                      style: const TextStyle(fontStyle: FontStyle.italic)),
                ),
                if (h.results.isNotEmpty) _quoteCard(h.results.first),
              ]),
        ],
      );
    }
    return const Center(
      child: Text('Ask anything to find a fitting quote.'),
    );
  }

  Widget _quoteCard(Quote q) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 6),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('"${q.text}"',
                style: const TextStyle(fontSize: 16, height: 1.4)),
            const SizedBox(height: 8),
            Row(
              children: [
                if (q.author != null)
                  Expanded(
                    child: Text('— ${q.author}',
                        style:
                            const TextStyle(fontWeight: FontWeight.w600)),
                  ),
                Text('${(q.similarity * 100).round()}% match',
                    style: TextStyle(color: Colors.grey[600], fontSize: 12)),
              ],
            ),
            if (q.sourceUrl != null) ...[
              const SizedBox(height: 6),
              TextButton.icon(
                style: TextButton.styleFrom(
                    padding: EdgeInsets.zero,
                    alignment: Alignment.centerLeft),
                icon: const Icon(Icons.open_in_new, size: 16),
                label: Text(q.sourceName ?? 'Source'),
                onPressed: () => _openSource(q.sourceUrl!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Text(text.toUpperCase(),
          style: TextStyle(
              fontSize: 12,
              letterSpacing: 1,
              color: Colors.grey[600],
              fontWeight: FontWeight.w600)),
    );
  }
}
