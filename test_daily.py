from datetime import datetime, timedelta
import json
from pathlib import Path
import tempfile
import unittest
from daily import generate, parse_feed, SHANGHAI, is_prerelease, parse_radar, fetch_radar
from unittest.mock import patch


class DailyTests(unittest.TestCase):
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
