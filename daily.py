"""Archive a truthful daily RSS/Atom check. Python standard library only."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
import html
import json
from pathlib import Path
import re
import time
from urllib.parse import urlsplit, quote
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

SHANGHAI = ZoneInfo("Asia/Shanghai")
ATOM = "{http://www.w3.org/2005/Atom}"
ROOT = Path(__file__).resolve().parent


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
            stamp = node.findtext("pubDate", "")
        else:
            title = node.findtext(ATOM + "title", "")
            url = next((link.get("href", "") for link in node.findall(ATOM + "link")
                        if link.get("rel", "alternate") == "alternate"), "").strip()
            stamp = node.findtext(ATOM + "published") or node.findtext(ATOM + "updated", "")
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
        items.append({"title": title, "url": url, "date": date})
    if nodes and not items:
        raise ValueError("No valid dated entries in feed")
    return items, skipped


def fetch_source(source):
    for attempt in range(3):
        try:
            request = Request(source["url"], headers={
                "User-Agent": "Mozilla/5.0 (compatible; ai-daily/1.0)",
                "Accept": "application/atom+xml, application/rss+xml, application/xml, text/xml",
            })
            with urlopen(request, timeout=25) as response:
                data = response.read(5_000_001)
            if len(data) > 5_000_000:
                raise ValueError("Feed exceeds 5 MB limit")
            items, skipped = parse_feed(data)
            return {**source, "items": items, "skipped": skipped, "error": None}
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            if attempt < 2:
                time.sleep(2 ** attempt)
    return {**source, "items": [], "skipped": 0, "error": error}


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
    with ThreadPoolExecutor(max_workers=6) as executor:
        results = list(executor.map(fetcher, sources))
    if all(result["error"] for result in results):
        raise RuntimeError("All sources failed; keep repository unchanged for retry. " +
                           "; ".join(r["name"] + ": " + r["error"] for r in results))

    state_file = root / "data" / "seen.json"
    seen = json.loads(state_file.read_text()) if state_file.exists() else {}
    # A 48-hour lookback tolerates delayed publication; history removes duplicates.
    cutoff = now - timedelta(hours=48)
    entries = []
    for result in results:
        for item in result["items"]:
            if result.get("exclude_prerelease") and is_prerelease(item["title"]):
                continue
            if cutoff <= item["date"] <= now and item["url"] not in seen:
                entries.append({**item, "source": result["name"], "category": result["category"]})
                seen[item["url"]] = item["date"].isoformat()
    entries.sort(key=lambda item: (item["date"], item["url"]), reverse=True)
    success = sum(result["error"] is None for result in results)
    lines = [f"# AI 每日观察 · {day}", "",
             "> 本文由 GitHub Actions 自动采集；标题保留原文，事实与细节请以来源为准。", "",
             f"- 检查时间：{now:%Y-%m-%d %H:%M}（北京时间）",
             "- 收录范围：最近 48 小时发布或更新、且未在历史日报收录的条目。",
             f"- 信息源：{success}/{len(results)} 可用；本次新增：{len(entries)} 条。", ""]
    for category in dict.fromkeys(source["category"] for source in sources):
        lines += [f"## {category}", ""]
        selected = [item for item in entries if item["category"] == category]
        if not selected:
            lines += ["本次从可用信息源中未检索到符合收录条件的新条目。", ""]
        for item in selected:
            safe_url = quote(item["url"], safe=":/?&=#%+@~!$;,-._")
            lines += [f"- **[{markdown(item['title'])}]({safe_url})**",
                      f"  - 来源：{markdown(item['source'])} · 来源时间：{item['date'].astimezone(SHANGHAI):%m-%d %H:%M}（北京时间）"]
        lines.append("")
    lines += ["## 来源检查", "", "| 来源 | 状态 |", "| --- | --- |"]
    for result in results:
        status = "获取成功" if result["error"] is None else "获取失败（不代表没有更新）"
        if result["skipped"]:
            status += f"；跳过 {result['skipped']} 条缺失日期或格式异常的条目"
        lines.append(f"| [{markdown(result['name'])}]({result['url']}) | {status} |")
        if result["error"]:
            print(f"Source failed: {result['name']}: {result['error']}")
    lines += ["", "## 我的阅读笔记", "", "<!-- 可以在这里补充自己的学习笔记；当天补跑不会覆盖本文件。 -->", ""]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    state_file.parent.mkdir(parents=True, exist_ok=True)
    # Retain ample history without unbounded growth.
    seen = {url: stamp for url, stamp in seen.items() if parse_date(stamp) >= now - timedelta(days=30)}
    state_file.write_text(json.dumps(seen, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    (root / "LATEST.md").write_text("\n".join(lines), encoding="utf-8")
    archives = sorted((root / "daily").glob("*/*/*.md"), reverse=True)
    (root / "ARCHIVE.md").write_text("# 日报归档\n\n" + "\n".join(
        f"- [{path.stem}]({path.relative_to(root).as_posix()})" for path in archives) + "\n")
    print(f"Wrote {target.relative_to(root)}: {len(entries)} new entries; {success}/{len(results)} sources OK.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT)
    generate(parser.parse_args().output_root)
