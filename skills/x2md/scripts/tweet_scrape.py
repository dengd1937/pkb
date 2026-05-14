#!/usr/bin/env python3
"""
tweet_scrape.py — Scrape a single tweet, X Article, or thread into Markdown.

Usage:
  tweet_scrape.py <url> [--output FILE] [--thread] [--images skip|local|r2]
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path

TWEET_URL_RE = re.compile(
    r"https?://(?:x|twitter|fxtwitter|nitter)\.com/(?P<user>[A-Za-z0-9_]+)/status/(?P<id>\d+)"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


# ── URL / text helpers ─────────────────────────────────────────────────────────


def parse_tweet_url(url: str) -> tuple[str, str]:
    m = TWEET_URL_RE.search(url)
    if not m:
        raise ValueError(f"unrecognized tweet URL: {url}")
    return m.group("user"), m.group("id")


def clean_text(html_fragment: str) -> str:
    t = re.sub(r"<[^>]+>", " ", html_fragment).strip()
    t = re.sub(r"\s+", " ", t)
    entities = {
        "&gt;": ">",
        "&lt;": "<",
        "&amp;": "&",
        "&#x27;": "'",
        "&quot;": '"',
        "&#39;": "'",
        "&nbsp;": " ",
    }
    for old, new in entities.items():
        t = t.replace(old, new)
    return t


# ── Twitter media helpers ─────────────────────────────────────────────────────


def collect_twimg_media(html: str) -> list[str]:
    """Extract pbs.twimg.com media IDs (any URL form) and return canonical large URLs."""
    images: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(
        r"pbs\.twimg\.com/media/([A-Za-z0-9_-]{10,})", html
    ):
        media_id = m.group(1)
        if media_id in seen:
            continue
        seen.add(media_id)
        images.append(
            f"https://pbs.twimg.com/media/{media_id}?format=jpg&name=large"
        )
    return images


def download_twimg(url: str, dst: Path) -> None:
    """Download a pbs.twimg.com asset with a browser-like UA (default UA gets 403)."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Referer": "https://x.com/"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        dst.write_bytes(resp.read())


# ── Browser fetch ──────────────────────────────────────────────────────────────


async def fetch_page(url: str, wait_selector: str | None = None, timeout: int = 35000) -> str:
    from patchright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 4000},
            user_agent=USER_AGENT,
        )
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=timeout)

        if wait_selector:
            try:
                await page.wait_for_selector(wait_selector, timeout=15000)
            except Exception:
                pass

        await asyncio.sleep(2)

        try:
            show_more = await page.query_selector('[data-testid="tweet-text-show-more-link"]')
            if show_more:
                await show_more.click()
                await asyncio.sleep(1)
        except Exception:
            pass

        html = await page.content()
        await browser.close()
        return html


# ── Content extraction ────────────────────────────────────────────────────────


def extract_tweet(html: str, username: str, status_id: str) -> dict | None:
    text_blocks = re.findall(
        r'data-testid="tweetText"[^>]*>(.*?)</div>', html, re.DOTALL
    )
    texts = [clean_text(tb) for tb in text_blocks if clean_text(tb)]

    time_matches = re.findall(r'<time[^>]*datetime="([^"]+)"', html)

    if not texts or not time_matches:
        return None

    images = collect_twimg_media(html)

    is_reply = bool(re.search(r"Replying to", html[:5000]))

    return {
        "id": status_id,
        "username": username,
        "url": f"https://x.com/{username}/status/{status_id}",
        "date": time_matches[0],
        "text": texts[0],
        "quoted_text": texts[1] if len(texts) > 1 else None,
        "images": images,
        "is_reply": is_reply,
    }


def extract_article(html: str, username: str, status_id: str) -> dict | None:
    """Detect and extract an X Article. Returns a self-contained dict or None."""
    if not re.search(
        r'data-testid="(?:twitterArticleReadView|twitterArticleRichTextView)"', html
    ):
        return None

    title = ""
    m = re.search(
        r'data-testid="twitter-article-title"[^>]*>(.{0,2000})', html, re.DOTALL
    )
    if m:
        snippet = m.group(1)
        cutoff = re.search(r"</(h[1-6]|div|article|button)\b", snippet)
        if cutoff:
            snippet = snippet[: cutoff.start()]
        title = clean_text(snippet)

    body_match = re.search(
        r'data-testid="twitterArticleRichTextView"[^>]*>(.*?)</article>',
        html,
        re.DOTALL,
    )
    if not body_match:
        return None
    body_html = body_match.group(1)

    parts: list[str] = []
    for m in re.finditer(r"<(h[1-6]|p|li)[^>]*>(.*?)</\1>", body_html, re.DOTALL):
        tag, content = m.group(1), m.group(2)
        text = clean_text(content)
        if not text:
            continue
        if tag.startswith("h"):
            level = int(tag[1])
            parts.append(f"{'#' * level} {text}")
        elif tag == "li":
            parts.append(f"- {text}")
        else:
            parts.append(text)

    if not parts:
        return None

    time_matches = re.findall(r'<time[^>]*datetime="([^"]+)"', html)
    date = time_matches[0] if time_matches else ""

    images = collect_twimg_media(html)

    return {
        "title": title or f"Article by @{username}",
        "body": "\n\n".join(parts),
        "username": username,
        "status_id": status_id,
        "url": f"https://x.com/{username}/status/{status_id}",
        "date": date,
        "images": images,
    }


async def fetch_thread(username: str, lead_id: str) -> list[dict]:
    url = f"https://x.com/{username}/status/{lead_id}"
    html = await fetch_page(url, wait_selector="article")

    articles = re.findall(r"<article[^>]*>(.*?)</article>", html, re.DOTALL)
    tweets: list[dict] = []
    seen: set[str] = set()

    for art in articles:
        link_match = re.search(
            rf'href="/{re.escape(username)}/status/(\d+)"', art, re.IGNORECASE
        )
        if not link_match:
            continue
        tid = link_match.group(1)
        if tid in seen:
            continue
        seen.add(tid)

        text_blocks = re.findall(
            r'data-testid="tweetText"[^>]*>(.*?)</div>', art, re.DOTALL
        )
        texts = [clean_text(tb) for tb in text_blocks if clean_text(tb)]
        time_matches = re.findall(r'<time[^>]*datetime="([^"]+)"', art)

        if not texts or not time_matches:
            continue

        tweets.append(
            {
                "id": tid,
                "username": username,
                "url": f"https://x.com/{username}/status/{tid}",
                "date": time_matches[0],
                "text": texts[0],
            }
        )

    tweets.sort(key=lambda t: t["date"])
    return tweets


# ── Image handling ─────────────────────────────────────────────────────────────


def load_r2_config() -> dict | None:
    required = ["R2_BUCKET", "R2_ACCESS_KEY", "R2_SECRET_KEY", "R2_ENDPOINT", "R2_PUBLIC_URL"]
    values = {k: os.environ.get(k) for k in required}
    if not all(values.values()):
        return None
    return {
        "bucket": values["R2_BUCKET"],
        "access_key": values["R2_ACCESS_KEY"],
        "secret_key": values["R2_SECRET_KEY"],
        "endpoint": values["R2_ENDPOINT"],
        "public_url": values["R2_PUBLIC_URL"].rstrip("/"),
        "prefix": os.environ.get("R2_PREFIX", "tweets").strip("/"),
    }


def handle_images(
    images: list[str],
    mode: str,
    output_path: Path | None,
    status_id: str,
) -> list[str]:
    if not images or mode == "skip":
        return []

    if mode == "local":
        if output_path is None:
            print("[WARN] --images local requires --output", file=sys.stderr)
            return []
        assets_dir = output_path.parent / "assets" / status_id
        assets_dir.mkdir(parents=True, exist_ok=True)
        refs: list[str] = []
        for i, url in enumerate(images, start=1):
            dst = assets_dir / f"{status_id}_{i}.jpg"
            try:
                download_twimg(url, dst)
                refs.append(str(dst.relative_to(output_path.parent)))
                print(f"  [img] saved {dst}", file=sys.stderr)
            except Exception as e:
                print(f"  [WARN] failed to download {url}: {e}", file=sys.stderr)
        return refs

    if mode == "r2":
        r2 = load_r2_config()
        if not r2:
            print(
                "[ERROR] --images r2 requires R2_BUCKET / R2_ACCESS_KEY / R2_SECRET_KEY "
                "/ R2_ENDPOINT / R2_PUBLIC_URL env vars",
                file=sys.stderr,
            )
            return []
        try:
            import boto3
        except ImportError:
            print("[ERROR] boto3 not installed in venv", file=sys.stderr)
            return []

        s3 = boto3.client(
            "s3",
            endpoint_url=r2["endpoint"],
            aws_access_key_id=r2["access_key"],
            aws_secret_access_key=r2["secret_key"],
            region_name="auto",
        )
        refs = []
        for i, url in enumerate(images, start=1):
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                download_twimg(url, Path(tmp_path))
                key = f"{r2['prefix']}/{status_id}_{i}.jpg"
                s3.upload_file(
                    tmp_path,
                    r2["bucket"],
                    key,
                    ExtraArgs={"ContentType": "image/jpeg"},
                )
                public = f"{r2['public_url']}/{key}"
                refs.append(public)
                print(f"  [img] uploaded {public}", file=sys.stderr)
            finally:
                Path(tmp_path).unlink(missing_ok=True)
        return refs

    return []


# ── Slug & path helpers ───────────────────────────────────────────────────────


def kebab_slug(text: str, max_len: int = 60) -> str:
    """Make a filename-safe slug. Keeps ASCII alphanumerics and CJK characters."""
    text = (text or "").strip().lower()
    text = re.sub(r"[^\w\s一-鿿-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len] or "untitled"


def published_date(iso_datetime: str) -> str:
    return iso_datetime[:10] if iso_datetime else datetime.now().strftime("%Y-%m-%d")


def build_pkb_path(
    raw_dir: Path,
    topic: str,
    *,
    kind: str,
    username: str,
    status_id: str,
    iso_date: str,
    title: str | None = None,
) -> Path:
    """Return the canonical pkb raw/<topic>/<date>-<slug>.md path."""
    date_str = published_date(iso_date)
    if kind == "article" and title:
        slug = f"{kebab_slug(title)}-{status_id}"
    elif kind == "thread":
        slug = f"{username}-thread-{status_id}"
    else:
        slug = f"{username}-{status_id}"
    return raw_dir / topic / f"{date_str}-{slug}.md"


# ── Markdown formatting ────────────────────────────────────────────────────────


def pkb_header(title: str, source_url: str, published_iso: str | None) -> list[str]:
    """Emit the raw-template header expected by pkb's llm-wiki."""
    pub = published_date(published_iso) if published_iso else "Unknown"
    today = datetime.now().strftime("%Y-%m-%d")
    return [
        f"# {title}",
        "",
        f"> Source: {source_url}",
        f"> Collected: {today}",
        f"> Published: {pub}",
        "",
    ]


def format_tweet_markdown(tweet: dict, image_refs: list[str]) -> str:
    title = f'Tweet by @{tweet["username"]} — {tweet["date"][:10]}'
    lines = pkb_header(title, tweet["url"], tweet["date"])
    lines.append(tweet["text"])
    if tweet.get("quoted_text"):
        lines += ["", "> 📎 Quoted:", f'> {tweet["quoted_text"]}']
    if image_refs:
        lines += ["", "---", ""]
        for ref in image_refs:
            lines.append(f"![image]({ref})")
    return "\n".join(lines) + "\n"


def format_article_markdown(article: dict, image_refs: list[str]) -> str:
    lines = pkb_header(article["title"], article["url"], article["date"])
    lines.append(f'作者：@{article["username"]}')
    lines += ["", "---", "", article["body"]]
    if image_refs:
        lines += ["", "---", ""]
        for ref in image_refs:
            lines.append(f"![image]({ref})")
    return "\n".join(lines) + "\n"


def format_thread_markdown(tweets: list[dict], image_refs: list[str]) -> str:
    if not tweets:
        return ""
    lead = tweets[0]
    title = f'Thread by @{lead["username"]} — {lead["date"][:10]} ({len(tweets)} tweets)'
    lines = pkb_header(title, lead["url"], lead["date"])
    for i, tw in enumerate(tweets, start=1):
        lines.append(f'## {i}/{len(tweets)} — {tw["date"]}')
        lines.append("")
        lines.append(tw["text"])
        lines.append("")
        lines.append(f'🔗 {tw["url"]}')
        lines.append("")
    if image_refs:
        lines += ["---", ""]
        for ref in image_refs:
            lines.append(f"![image]({ref})")
    return "\n".join(lines) + "\n"


def format_fallback_markdown(url: str, username: str, og_desc: str) -> str:
    title = f"Tweet by @{username}"
    lines = pkb_header(title, url, None)
    lines += [
        "> ⚠️ 未能解析推文 DOM，以下是 og:description 兜底内容（可能截断）",
        "",
        og_desc,
    ]
    return "\n".join(lines) + "\n"


# ── Main ──────────────────────────────────────────────────────────────────────


async def run(args: argparse.Namespace) -> int:
    try:
        username, status_id = parse_tweet_url(args.url)
    except ValueError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2

    print(f"[fetch] {args.url}", file=sys.stderr)
    html = await fetch_page(args.url, wait_selector="article")

    article = extract_article(html, username, status_id)
    tweet = None if article else extract_tweet(html, username, status_id)

    if article:
        kind = "article"
    elif tweet and args.thread:
        kind = "thread"
    elif tweet:
        kind = "tweet"
    else:
        kind = "fallback"

    iso_date = (article or tweet or {}).get("date") or ""
    title_for_slug = article["title"] if article else None

    if args.stdout:
        output_path: Path | None = None
    elif args.output:
        output_path = Path(args.output).resolve()
    else:
        raw_dir = Path(args.raw_dir).resolve()
        output_path = build_pkb_path(
            raw_dir,
            args.topic,
            kind=kind,
            username=username,
            status_id=status_id,
            iso_date=iso_date,
            title=title_for_slug,
        )

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    md: str

    if kind == "article":
        print("[detect] X Article (long-form)", file=sys.stderr)
        image_refs = handle_images(article["images"], args.images, output_path, status_id)
        md = format_article_markdown(article, image_refs)

    elif kind == "thread":
        print("[detect] thread mode", file=sys.stderr)
        thread_tweets = await fetch_thread(username, status_id)
        image_refs = handle_images(tweet["images"], args.images, output_path, status_id)
        md = format_thread_markdown(thread_tweets, image_refs)

    elif kind == "tweet":
        print("[detect] single tweet", file=sys.stderr)
        image_refs = handle_images(tweet["images"], args.images, output_path, status_id)
        md = format_tweet_markdown(tweet, image_refs)

    else:
        og_desc = re.search(
            r'<meta[^>]*property="og:description"[^>]*content="([^"]+)"', html
        )
        if og_desc:
            print("[detect] fallback to og:description", file=sys.stderr)
            md = format_fallback_markdown(args.url, username, og_desc.group(1))
        else:
            print("[ERROR] could not extract any content from the page", file=sys.stderr)
            return 1

    if output_path:
        output_path.write_text(md, encoding="utf-8")
        print(f"[saved] {output_path} ({len(md)} chars)", file=sys.stderr)
    else:
        sys.stdout.write(md)

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scrape a single tweet / X Article / thread into Markdown, "
        "defaulting to ./raw/<topic>/<date>-<slug>.md (pkb raw layout)."
    )
    parser.add_argument("url", help="Tweet/article URL (x.com, twitter.com, fxtwitter.com)")
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Override output path. If omitted, writes to <raw-dir>/<topic>/<date>-<slug>.md",
    )
    parser.add_argument(
        "--raw-dir",
        default="./raw",
        help="Base raw/ directory for pkb mode (default: ./raw)",
    )
    parser.add_argument(
        "--topic",
        default="tweets",
        help="Topic subdirectory under raw/ (default: tweets)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print Markdown to stdout instead of writing a file",
    )
    parser.add_argument(
        "--thread",
        action="store_true",
        help="Also collect the thread this tweet belongs to (single-tweet mode only)",
    )
    parser.add_argument(
        "--images",
        choices=["skip", "local", "r2"],
        default="skip",
        help="Image handling strategy (default: skip)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return asyncio.run(run(args))


if __name__ == "__main__":
    sys.exit(main())
