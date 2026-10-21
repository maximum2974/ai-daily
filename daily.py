"""Archive a truthful daily RSS/Atom check. Python standard library only."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import html
import gzip
import io
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode, quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

SHANGHAI = ZoneInfo("Asia/Shanghai")
ATOM = "{http://www.w3.org/2005/Atom}"
ROOT = Path(__file__).resolve().parent
AI_PATTERN = re.compile(
    r"(?<![a-z0-9_])(?:AI|AIGC|LLMs?|GPT[a-z0-9.-]*|AGI|RAG|MCP|agents?|agentic|Claude|Anthropic|"
    r"OpenAI|DeepSeek|Qwen|Gemini|Copilot|ChatGPT|Llama|Mistral|Kimi|MiniMax|"
    r"diffusion|transformers?|robotics|CUDA|vLLM)(?![a-z0-9_])|"
    r"artificial intelligence|machine learning|deep learning|neural network|"
    r"人工智能|大模型|语言模型|智能体|机器学习|深度学习|生成式|多模态|"
    r"具身智能|机器人|算力|智谱|通义|千问|豆包|文心|混元|可灵|生图|生视频",
    re.I,
)


def canonical_url(url):
    """Remove tracking and fragments, keeping parameters that identify articles."""
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
             if not key.lower().startswith('utm_') and key.lower() not in
             {'fbclid', 'gclid', 'mc_cid', 'mc_eid'}]
    host = parts.netloc.lower()
    if host.startswith('www.'):
        host = host[4:]
    return urlunsplit((parts.scheme.lower(), host, parts.path.rstrip('/') or '/',
                       urlencode(sorted(query)), ''))


def matches_source(item, source):
    text = item['title'] + ' ' + item.get('tags', '')
    return not source.get('ai_only') or bool(AI_PATTERN.search(text))


def read_response(response, limit):
    raw = response.read(limit + 1)
    if len(raw) > limit:
        raise ValueError(f'Response exceeds {limit} byte limit')
    if raw.startswith(b'\x1f\x8b'):
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as compressed:
            raw = compressed.read(limit + 1)
        if len(raw) > limit:
            raise ValueError(f'Decompressed response exceeds {limit} byte limit')
    return raw


def parse_date(value):
    try:
        date = parsedate_to_datetime(value)
    except (ValueError, TypeError):
        date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if date.tzinfo is None:
        raise ValueError("Feed timestamp has no timezone")
    return date.astimezone(timezone.utc)


def clean_title(value):
    return " ".join(html.unescape(re.sub(r"<[^>]*>", "", value)).split())[:300]


def markdown(value):
    return re.sub(r"([\\`*_{}\[\]<>|])", r"\\\1", value)


def parse_feed(data):
    root = ET.fromstring(data)
    if root.tag == "rss":
        nodes = root.findall("./channel/item")
    elif root.tag == ATOM + "feed":
        nodes = root.findall(ATOM + "entry")
    else:
        raise ValueError("Expected RSS or Atom feed")
    items, skipped = [], 0
    for node in nodes:
        if root.tag == "rss":
            title = node.findtext("title", "")
            url = node.findtext("link", "").strip()
            stamp = node.findtext("pubDate") or node.findtext("{http://purl.org/dc/elements/1.1/}date", "")
            summary = node.findtext("description", "")
            tags = ' '.join(tag.text or '' for tag in node.findall('category'))
            publisher = node.findtext('source', '')
        else:
            title = node.findtext(ATOM + "title", "")
            url = next((link.get("href", "") for link in node.findall(ATOM + "link")
                        if link.get("rel", "alternate") == "alternate"), "").strip()
            stamp = node.findtext(ATOM + "published") or node.findtext(ATOM + "updated", "")
            summary = node.findtext(ATOM + 'summary', '')
            tags = ' '.join(tag.get('term', '') for tag in node.findall(ATOM + 'category'))
            publisher = ''
        try:
            date = parse_date(stamp)
            if urlsplit(url).scheme not in ("https", "http") or not urlsplit(url).netloc:
                raise ValueError("Invalid article URL")
            title = clean_title(title)
            if not title:
                raise ValueError("Missing title")
        except (ValueError, TypeError, OverflowError):
            skipped += 1
            continue
        item = {"title": title, "url": url, "date": date, "summary": clean_title(summary)[:180],
                "tags": clean_title(tags)}
        if publisher:
            item['source'] = clean_title(publisher)
        items.append(item)
    if nodes and not items:
        raise ValueError("No valid dated entries in feed")
    return items, skipped


def fetch_source(source):
    if source.get("kind") == "radar":
        return fetch_radar(source)
    for attempt in range(3):
        try:
            request = Request(source["url"], headers={
                "User-Agent": "Mozilla/5.0 (compatible; ai-daily/1.0)",
                "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml",
            })
            with urlopen(request, timeout=25) as response:
                data = read_response(response, 8_000_000)
            items, skipped = parse_feed(data)
            return {**source, "items": items, "skipped": skipped, "error": None}
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            if attempt < 2:
                time.sleep(2 ** attempt)
    return {**source, "items": [], "skipped": 0, "error": error}


def read_json(url):
    with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; ai-daily/1.0)"}), timeout=25) as response:
        raw = read_response(response, 8_000_000)
    return json.loads(raw)


def parse_radar(data, mode, now, max_items=20, max_references=3):
    generated = parse_date(data["generated_at"])
    limit = 48 if mode == "brief" else 36
    age = (now - generated).total_seconds() / 3600
    if age > limit or age < -1:
        raise ValueError(f"数据时间 {generated.isoformat()}，已超过 {limit} 小时新鲜度限制或时间异常")
    records = data["items"] if mode == "brief" else data["items_ai"]
    if not isinstance(records, list):
        raise ValueError("Invalid Radar items")
    if mode == "brief":
        normalized = []
        for story in records:
            primary = story.get("primary_item") or {}
            original = next((s for s in story.get("sources", []) if s.get("url") == story.get("url")), {})
            item = {**primary, **original, **story}
            item["source"] = original.get("source") or primary.get("source") or story.get("source")
            item["published_at"] = original.get("published_at") or story.get("published_at") or story.get("latest_at")
            item["title_zh"] = original.get("title_zh") or primary.get("title_zh")
            if "source_tier_rank" not in item:
                item["source_tier_rank"] = 0 if story.get("category") == "official" else 5 if story.get("category") == "multi_source" else 3
                item["source_tier_label"] = "官方一手源" if item["source_tier_rank"] == 0 else "热议参考" if item["source_tier_rank"] == 5 else "聚合资讯（未提供细分层级）"
            normalized.append(item)
        records = normalized
    def rank(item):
        return (int(item.get("source_tier_rank", 3)), -float(item.get("ai_score", 0)))
    records = sorted(records, key=rank)
    labels = {"model_release": "模型发布", "ai_product_update": "产品与工具",
              "developer_tool": "产品与工具", "agent_workflow": "产品与工具",
              "research_paper": "论文与技术", "infra_compute": "论文与技术",
              "robotics": "论文与技术", "ai_tech": "论文与技术"}
    items, skipped, references = [], 0, 0
    for record in records:
        try:
            url = record["url"]
            if urlsplit(url).scheme not in ("http", "https") or not urlsplit(url).netloc:
                raise ValueError("Invalid Radar link")
            stamp = record.get("published_at") or record.get("first_seen_at")
            if not stamp:
                raise ValueError("Missing item timestamp")
            date = parse_date(stamp)
            if not now - timedelta(hours=48) <= date <= now:
                continue
            tier = int(record.get("source_tier_rank", 3))
            if tier >= 5:
                if references >= max_references:
                    continue
                references += 1
            title = clean_title(record.get("title_zh") or record.get("title_bilingual") or record["title"])
            category = "值得注意（热议参考）" if tier >= 5 else labels.get(record.get("ai_label"), "官方资讯" if tier == 0 else "行业与综合")
            items.append({"title": title, "url": url, "date": date, "category": category,
                          "source": record.get("source") or record.get("source_name") or "AI News Radar",
                          "tier": record.get("source_tier_label", "未分层"),
                          "tier_rank": tier,
                          "review": clean_title(record.get("persona_review") or ""),
                          "intro": clean_title(record.get("recommend_reason_zh") or "")[:180]})
        except (KeyError, TypeError, ValueError):
            skipped += 1
        if max_items is not None and len(items) >= max_items:
            break
    return items, skipped, generated


def fetch_radar(source):
    base = source["url"].rstrip("/")
    endpoints = [(base + "/daily-brief.json", "brief"),
                 (base + "/latest-24h.json", "latest"),
                 ("https://raw.githubusercontent.com/LearnPrompt/ai-news-radar/master/data/latest-24h.json", "latest")]
    errors, collected, generated_times, used_urls = [], {}, [], []
    skipped_total = 0
    for url, mode in endpoints:
        try:
            items, skipped, generated = parse_radar(
                read_json(url), mode, datetime.now(timezone.utc),
                max_items=source.get('max_items', 20), max_references=source.get('max_references', 3))
            for item in items:
                # Preserve the brief's Chinese introductions when the full feed repeats a URL.
                collected.setdefault(canonical_url(item['url']), item)
            skipped_total += skipped
            generated_times.append(generated)
            used_urls.append(url)
            if mode == 'latest':
                break
        except Exception as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
    if used_urls:
        note = f"数据时间 {max(generated_times).astimezone(SHANGHAI):%Y-%m-%d %H:%M}（北京时间）"
        if len(used_urls) > 1:
            note += '；已合并精选与完整时间线'
        if errors:
            fallback = '已使用备用数据' if used_urls[-1] == endpoints[-1][0] else '已保留可用数据'
            note += f'；部分入口不可用或过期，{fallback}；覆盖可能不完整'
        return {**source, 'items': list(collected.values()), 'skipped': skipped_total,
                'error': None, 'note': note, 'data_url': ' 、 '.join(used_urls)}
    return {**source, "items": [], "skipped": 0, "error": "; ".join(errors),
            "note": "雷达数据不可用或过期，本次仅收录可用 RSS 来源"}


def is_prerelease(title):
    return bool(re.search(r"(?:^|[-.\s])(alpha|beta|rc|preview|nightly|canary)(?:[-.\d\s]|$)", title, re.I))


def generate(root=ROOT, now=None, fetcher=fetch_source):
    now = (now or datetime.now(SHANGHAI)).astimezone(SHANGHAI)
    day = now.strftime("%Y-%m-%d")
    target = root / "daily" / now.strftime("%Y/%m") / f"{day}.md"
    if target.exists():
        print(f"Already archived {day}; skip duplicate run.")
        return False
    sources = json.loads((root / "sources.json").read_text())
    if not sources:
        raise RuntimeError("No sources configured")
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetcher, sources))
    if all(result["error"] for result in results):
        raise RuntimeError("All sources failed; keep repository unchanged for retry. " +
                           "; ".join(r["name"] + ": " + r["error"] for r in results))

    state_file = root / "data" / "seen.json"
    seen = json.loads(state_file.read_text()) if state_file.exists() else {}
    seen = {canonical_url(url): stamp for url, stamp in seen.items()}
    # A 48-hour lookback tolerates delayed publication; history removes duplicates.
    cutoff = now - timedelta(hours=48)
    entries = []
    for result in results:
        result['added'] = 0
        result['filtered'] = 0
        for item in result["items"]:
            if not matches_source(item, result):
                result['filtered'] += 1
                continue
            if result.get("exclude_prerelease") and is_prerelease(item["title"]):
                continue
            key = canonical_url(item['url'])
            if cutoff <= item["date"] <= now and key not in seen:
                entries.append({**item, "source": item.get("source", result["name"]),
                                "category": item.get("category", result["category"]),
                                "tier": item.get('tier', result.get('tier', '')),
                                "tier_rank": item.get('tier_rank', result.get('tier_rank', 3))})
                seen[key] = item["date"].isoformat()
                result['added'] += 1
    entries.sort(key=lambda item: (item.get("tier_rank", 0), -item["date"].timestamp(), item["url"]))
    papers = [item for item in entries if item['category'] == '论文预印本']
    paper_target = target.with_name(f'{day}.papers.md')
    success = sum(result["error"] is None for result in results)
    lines = [f"# AI 每日观察 · {day}", "",
             "> 本文由 GitHub Actions 自动采集；雷达中文标题与导读来自 AI News Radar，事实与细节请以原始来源为准。", "",
             f"- 检查时间：{now:%Y-%m-%d %H:%M}（北京时间）",
             "- 收录范围：最近 48 小时发布或更新、且未在历史日报收录的条目。",
             f"- 信息源：{success}/{len(results)} 可用；本次新增：{len(entries)} 条。", ""]
    for result in results:
        if result.get("kind") == "radar" and result.get("note"):
            lines += ["> 雷达状态：" + result["note"] + "。", ""]
    categories = ["模型发布", "官方资讯", "产品与工具", "国内动态", "行业与综合", "政策与安全",
                  "融资与算力", "工具更新", "论文与技术", "深度阅读", "论文预印本", "值得注意（热议参考）"]
    categories += [item["category"] for item in entries if item["category"] not in categories]
    lines += ['## 栏目导航', '']
    for category in dict.fromkeys(categories):
        count = sum(item['category'] == category for item in entries)
        if count:
            anchor = re.sub(r'[^\w\s-]', '', category).replace(' ', '-').lower()
            lines.append(f'- [{category}](#{anchor})：{count} 条')
    lines.append('')
    for category in dict.fromkeys(categories):
        if not any(item["category"] == category for item in entries):
            continue
        lines += [f"## {category}", ""]
        selected = [item for item in entries if item["category"] == category]
        if category == '论文预印本':
            lines += ['> 预印本未经同行评审；跨学科重复链接仅收录一次。', '',
                      f'本次共 {len(papers)} 篇，见 [完整论文清单](__PAPERS_REPORT__)。', '',
                      '<details>', f'<summary>展开前 {min(25, len(papers))} 篇论文预览</summary>', '']
            selected = selected[:25]
        for item in selected:
            safe_url = quote(item["url"], safe=":/?&=#%+@~!$;,-._")
            lines += [f"- **[{markdown(item['title'])}]({safe_url})**",
                      f"  - 来源：{markdown(item['source'])} · 来源时间：{item['date'].astimezone(SHANGHAI):%m-%d %H:%M}（北京时间）"]
            if item.get("tier"):
                lines.append(f"  - 信源分层：{markdown(item['tier'])}")
            if item.get("intro"):
                lines.append(f"  - 雷达导读（上游提供）：{markdown(item['intro'])}")
            elif item.get('summary') and category != '论文预印本':
                lines.append(f"  - 来源摘要（截取）：{markdown(item['summary'])}")
            if item.get("review"):
                lines.append(f"  - 雷达点评（上游提供）：{markdown(item['review'])}")
        lines.append("")
        if category == '论文预印本':
            lines += ['</details>', '']
    if not entries:
        lines += ["本次从可用信息源中未检索到符合收录条件的新条目。", ""]
    lines += ["## 来源检查", "", "| 来源 | 状态 | 获取条目 | 本次新增 |", "| --- | --- | ---: | ---: |"]
    for result in results:
        status = "获取成功" if result["error"] is None else "获取失败（不代表没有更新）"
        if result["skipped"]:
            status += f"；跳过 {result['skipped']} 条缺失日期或格式异常的条目"
        if result.get("note"):
            status += "；" + markdown(result["note"])
        if result['filtered']:
            status += f"；过滤 {result['filtered']} 条非 AI 内容"
        lines.append(f"| [{markdown(result['name'])}]({result['url']}) | {status} | {len(result['items'])} | {result['added']} |")
        if result["error"]:
            print(f"Source failed: {result['name']}: {result['error']}")
    for result in results:
        if result.get("data_url"):
            lines += ["", f"雷达数据文件：{result['data_url']}", "", result["note"] + "。"]
    lines += ["", "## 我的阅读笔记", "", "<!-- 可以在这里补充自己的学习笔记；当天补跑不会覆盖本文件。 -->", ""]
    target.parent.mkdir(parents=True, exist_ok=True)
    report = '\n'.join(lines)
    target.write_text(report.replace('__PAPERS_REPORT__', paper_target.name), encoding='utf-8')
    if papers:
        paper_lines = [f'# AI 论文清单 · {day}', '',
                       f'[返回当日日报]({target.name}) · 本次 {len(papers)} 篇', '',
                       '> arXiv 预印本未经同行评审。跨分类重复链接仅保留一次，以下为完整收录清单。', '']
        for item in papers:
            safe_url = quote(item['url'], safe=":/?&=#%+@~!$;,-._")
            paper_lines.append(f"- [{markdown(item['title'])}]({safe_url}) · {markdown(item['source'])} · "
                               f"{item['date'].astimezone(SHANGHAI):%m-%d %H:%M}（北京时间）")
        paper_target.write_text('\n'.join(paper_lines) + '\n', encoding='utf-8')
    state_file.parent.mkdir(parents=True, exist_ok=True)
    # Retain ample history without unbounded growth.
    seen = {url: stamp for url, stamp in seen.items() if parse_date(stamp) >= now - timedelta(days=30)}
    state_file.write_text(json.dumps(seen, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    (root / "LATEST.md").write_text(report.replace('__PAPERS_REPORT__', paper_target.relative_to(root).as_posix()), encoding='utf-8')
    archives = sorted((path for path in (root / "daily").glob("*/*/*.md")
                       if re.fullmatch(r'\d{4}-\d{2}-\d{2}', path.stem)), reverse=True)
    (root / "ARCHIVE.md").write_text("# 日报归档\n\n" + "\n".join(
        f"- [{path.stem}]({path.relative_to(root).as_posix()})" for path in archives) + "\n")
    print(f"Wrote {target.relative_to(root)}: {len(entries)} new entries; {success}/{len(results)} sources OK.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT)
    parser.add_argument('--check-sources', action='store_true', help='Check feeds without writing archives')
    args = parser.parse_args()
    if args.check_sources:
        sources = json.loads((args.output_root / 'sources.json').read_text())
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(fetch_source, sources))
        for result in results:
            print(json.dumps({'name': result['name'], 'error': result['error'],
                              'items': len(result['items']),
                              'ai_items': sum(matches_source(i, result) for i in result['items']),
                              'latest': max((i['date'].isoformat() for i in result['items']), default=None)},
                             ensure_ascii=False))
        raise SystemExit(1 if any(result['error'] for result in results) else 0)
    generate(args.output_root)
