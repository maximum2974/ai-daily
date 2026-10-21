from datetime import datetime, timedelta
import json
import gzip
import io
from pathlib import Path
import tempfile
import unittest
from daily import generate, parse_feed, SHANGHAI, is_prerelease, parse_radar, fetch_radar
from unittest.mock import patch
from daily import canonical_url, matches_source, read_response


class DailyTests(unittest.TestCase):
    def test_compressed_feeds_and_decompression_limit(self):
        feed = b'<rss><channel><item><title>AI</title><link>https://example.com/a</link><pubDate>Mon, 28 Sep 2026 01:00:00 GMT</pubDate></item></channel></rss>'
        self.assertEqual(parse_feed(read_response(io.BytesIO(gzip.compress(feed)), 1000))[0][0]['title'], 'AI')
        self.assertEqual(read_response(io.BytesIO(feed), 1000), feed)
        with self.assertRaises(ValueError):
            read_response(io.BytesIO(gzip.compress(b'x' * 10000)), 1000)

    def test_general_media_filter_uses_titles_and_tags(self):
        source = {'ai_only': True}
        for title in ['OpenAI releases a model', '国产大模型与具身智能', 'AI chip funding', 'New agent workflow',
                      'DeepSeek开源框架', 'OpenAI发布新模型', '17岁Kimi前研究员', '中国AI公司融资']:
            self.assertTrue(matches_source({'title': title}, source), title)
        for title in ['Fair pricing for airlines', 'New phone camera', 'MCPaint color palette']:
            self.assertFalse(matches_source({'title': title}, source), title)
        self.assertTrue(matches_source({'title': 'New research', 'tags': 'Machine Learning'}, source))
        self.assertTrue(matches_source({'title': 'General news'}, {}))

    def test_tracking_dedup_keeps_article_identity_and_history(self):
        self.assertEqual(canonical_url('https://www.example.com/a/?utm_source=x&id=2#comments'),
                         'https://example.com/a?id=2')
        self.assertNotEqual(canonical_url('https://example.com/a?id=2'), canonical_url('https://example.com/a?id=3'))
        now = datetime(2026, 9, 28, 10, 0, tzinfo=SHANGHAI)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = {'name': 'Feed', 'url': 'https://example.com/rss', 'category': '官方资讯'}
            (root / 'sources.json').write_text(json.dumps([source]))
            (root / 'data').mkdir()
            (root / 'data/seen.json').write_text(json.dumps({'https://www.example.com/a?utm_source=old': now.isoformat()}))
            fetch = lambda s: {**s, 'items': [{'title': 'Duplicate', 'url': 'https://example.com/a#top', 'date': now}],
                               'skipped': 0, 'error': None}
            generate(root, now, fetch)
            self.assertIn('本次新增：0 条', (root / 'LATEST.md').read_text())

    def test_radar_merges_full_timeline_without_twenty_item_cap(self):
        now = datetime.now(SHANGHAI)
        records = [{'title': f'Article {n}', 'url': f'https://example.com/{n}',
                    'published_at': (now - timedelta(hours=2)).isoformat(), 'source_tier_rank': 0}
                   for n in range(45)]
        brief = {'generated_at': now.isoformat(), 'items': [dict(records[0], category='official', recommend_reason_zh='精选导读')]}
        latest = {'generated_at': now.isoformat(), 'items_ai': records}
        with patch('daily.read_json', side_effect=[brief, latest]) as reader:
            result = fetch_radar({'name': 'Radar', 'url': 'https://example.com/data', 'max_items': None})
        self.assertEqual(reader.call_count, 2)
        self.assertEqual(len(result['items']), 45)
        self.assertEqual(result['items'][0]['intro'], '精选导读')
        self.assertIn('合并精选与完整时间线', result['note'])
        with patch('daily.read_json', side_effect=[brief, OSError('offline'), OSError('offline')]):
            partial = fetch_radar({'name': 'Radar', 'url': 'https://example.com/data'})
        self.assertIsNone(partial['error'])
        self.assertEqual(len(partial['items']), 1)
        self.assertIn('覆盖可能不完整', partial['note'])

    def test_rss_namespace_date_and_publisher(self):
        rss = b'<rss xmlns:dc="http://purl.org/dc/elements/1.1/"><channel><item><title>AI report</title><link>https://example.com/a</link><dc:date>2026-09-28T02:00:00Z</dc:date><source>Original Publisher</source><description>Source abstract</description><category>AI</category></item></channel></rss>'
        items, _ = parse_feed(rss)
        self.assertEqual(items[0]['source'], 'Original Publisher')
        self.assertEqual(items[0]['summary'], 'Source abstract')
        self.assertEqual(items[0]['tags'], 'AI')

    def test_large_paper_section_is_complete_and_collapsed(self):
        now = datetime(2026, 9, 28, 10, 0, tzinfo=SHANGHAI)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = {'name': 'arXiv', 'url': 'https://example.com/rss', 'category': '论文预印本'}
            (root / 'sources.json').write_text(json.dumps([source]))
            fetch = lambda s: {**s, 'error': None, 'skipped': 0, 'items': [
                {'title': f'Paper {n}', 'url': f'https://example.com/paper/{n}', 'date': now} for n in range(65)]}
            generate(root, now, fetch)
            body = (root / 'LATEST.md').read_text()
            self.assertIn('本次新增：65 条', body)
            self.assertIn('<summary>展开前 25 篇论文预览</summary>', body)
            paper_path = root / 'daily/2026/09/2026-09-28.papers.md'
            self.assertIn('[Paper 64]', paper_path.read_text())
            self.assertIn('[完整论文清单](daily/2026/09/2026-09-28.papers.md)', body)
            self.assertIn('[完整论文清单](2026-09-28.papers.md)', (paper_path.parent / '2026-09-28.md').read_text())
            self.assertNotIn('papers', (root / 'ARCHIVE.md').read_text())
            self.assertIn('未经同行评审', body)

    def test_brief_nested_schema_uses_article_time_and_source(self):
        now = datetime.now(SHANGHAI)
        stamp = (now - timedelta(hours=4)).isoformat()
        primary = {'title_zh': '中文', 'source': 'Original Blog', 'published_at': stamp,
                   'url': 'https://example.com/brief', 'recommend_reason_zh': '上游导读'}
        story = {'title': 'Bilingual', 'url': primary['url'], 'source_name': 'Aggregator',
                 'category': 'official', 'latest_at': stamp, 'sources': [primary], 'primary_item': primary}
        items, _, _ = parse_radar({'generated_at': now.isoformat(), 'items': [story]}, 'brief', now)
        self.assertEqual(items[0]['date'].isoformat(), (now - timedelta(hours=4)).astimezone(items[0]['date'].tzinfo).isoformat())
        self.assertEqual(items[0]['source'], 'Original Blog')
        self.assertEqual(items[0]['title'], '中文')
        self.assertEqual(items[0]['category'], '官方资讯')
        self.assertEqual(items[0]['intro'], '上游导读')

    def test_radar_freshness_chinese_titles_and_fallback(self):
        now = datetime.now(SHANGHAI)
        record = {'title': 'English', 'title_zh': '中文标题', 'url': 'https://example.com/radar',
                  'published_at': (now - timedelta(hours=1)).isoformat(), 'source': 'Original Publisher',
                  'source_tier_rank': 5, 'ai_label': 'developer_tool'}
        data = {'generated_at': now.isoformat(), 'items_ai': [record]}
        items, skipped, stamp = parse_radar(data, 'latest', now)
        self.assertEqual(items[0]['title'], '中文标题')
        self.assertEqual(items[0]['source'], 'Original Publisher')
        self.assertEqual(items[0]['category'], '值得注意（热议参考）')
        with self.assertRaises(ValueError):
            parse_radar({**data, 'generated_at': (now-timedelta(hours=37)).isoformat()}, 'latest', now)
        with patch('daily.read_json', side_effect=[OSError('403'), OSError('403'), data]) as reader:
            result = fetch_radar({'name': 'Radar', 'kind': 'radar', 'url': 'https://news.learnprompt.pro/data'})
            self.assertIsNone(result['error'])
            self.assertEqual(reader.call_count, 3)
            self.assertIn('备用数据', result['note'])

    def test_prerelease_filter(self):
        for title in ["rust-v0.160.0-alpha.1", "v1.0.0-rc1", "v2.0-beta.2"]:
            self.assertTrue(is_prerelease(title))
        self.assertFalse(is_prerelease("0.158.0"))

    def test_rss_and_atom_dates_and_unsafe_links(self):
        rss = b'<rss><channel><item><title>Test &amp; news</title><link>https://example.com/a</link><pubDate>Mon, 28 Sep 2026 01:00:00 GMT</pubDate></item><item><title>Unsafe</title><link>javascript:alert(1)</link><pubDate>Mon, 28 Sep 2026 01:00:00 GMT</pubDate></item></channel></rss>'
        items, skipped = parse_feed(rss)
        self.assertEqual((len(items), skipped), (1, 1))
        self.assertEqual(items[0]['title'], 'Test & news')
        atom = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Release</title><link rel="self" href="https://example.com/api"/><link href="https://example.com/release"/><updated>2026-09-28T02:00:00Z</updated></entry></feed>'
        self.assertEqual(parse_feed(atom)[0][0]['url'], 'https://example.com/release')

    def test_archive_deduplication_failure_and_manual_notes(self):
        now = datetime(2026, 9, 28, 10, 0, tzinfo=SHANGHAI)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'sources.json').write_text(json.dumps([
                {'name': 'Working', 'category': '官方资讯', 'url': 'https://example.com/rss'},
                {'name': 'Broken', 'category': '开源工具', 'url': 'https://example.com/broken'}]))
            def fetch(source):
                return {**source, 'error': 'offline' if source['name'] == 'Broken' else None,
                        'skipped': 0, 'items': [] if source['name'] == 'Broken' else [
                            {'title': 'Recent', 'url': 'https://example.com/new', 'date': now - timedelta(hours=1)},
                            {'title': 'Old', 'url': 'https://example.com/old', 'date': now - timedelta(days=3)},
                            {'title': 'Future', 'url': 'https://example.com/future', 'date': now + timedelta(days=3)}]}
            self.assertTrue(generate(root, now, fetch))
            report = root / 'daily/2026/09/2026-09-28.md'
            body = report.read_text()
            self.assertIn('本次新增：1 条', body)
            self.assertIn('获取失败（不代表没有更新）', body)
            report.write_text(body + '\nMy notes\n')
            before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            self.assertFalse(generate(root, now, lambda _: self.fail('Fetched twice')))
            self.assertEqual(before, {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()})
            self.assertTrue(generate(root, now + timedelta(days=1), fetch))
            self.assertIn('本次新增：0 条', (root / 'LATEST.md').read_text())
            before = {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()}
            with self.assertRaises(RuntimeError):
                generate(root, now + timedelta(days=2), lambda s: {**s, 'error': 'offline', 'items': [], 'skipped': 0})
            self.assertEqual(before, {str(p): p.read_bytes() for p in root.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
