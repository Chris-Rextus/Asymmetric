# backend/src/x_scraper.py

import json
import asyncio
import xml.etree.ElementTree as ET
import re

from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx

from config import (
    X_HANDLES,
    DATA_DIR,
    FOLLOWING_FILE,
    NITTER_INSTANCES,
    NITTER_TIMEOUT,
    NITTER_MAX_TWEETS_PER_HANDLE,
    CACHE_TTL_MINUTES,
)

CACHE_FILE = DATA_DIR / "x_cache.json"

# ── Following list ────────────────────────────────────────────────────────────

def load_handles() -> list[str]:
    
    # prefer .env handles, fall back to following.js
    if X_HANDLES:
        return X_HANDLES

    if not FOLLOWING_FILE.exists():
        return []

    raw = FOLLOWING_FILE.read_text(encoding="utf-8")
    raw = re.sub(r"^window\.\w+\.\w+\.\w+\s*=\s*", "", raw.strip())

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    handles = []
    for entry in data:
        link = entry.get("following", {}).get("userLink", "")
        if link:
            handle = link.rstrip("/").split("/")[-1]
            if handle:
                handles.append(handle)

    return list(dict.fromkeys(handles))


# ── Cache ─────────────────────────────────────────────────────────────────────

def _load_cache() -> list | None:

    if not CACHE_FILE.exists():
        return None
    
    raw = json.loads(CACHE_FILE.read_text())
    cached_at = datetime.fromisoformat(raw["cached_at"])
    age = datetime.now(timezone.utc) - cached_at

    if age > timedelta(minutes=CACHE_TTL_MINUTES):
        return None
    
    return raw["items"]


def _save_cache(items: list) -> None:

    CACHE_FILE.write_text(json.dumps({
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "items": items,
    }, indent=2))


# ── Nitter RSS ────────────────────────────────────────────────────────────────

SCRAPER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
}

async def _fetch_handle(handle: str, client: httpx.AsyncClient) -> list[dict]:

    """Try each Nitter instance in order, return on first success."""

    for instance in NITTER_INSTANCES:

        try:
            url = f"{instance}/{handle}/rss"
            r = await client.get(url, headers=SCRAPER_HEADERS, timeout=NITTER_TIMEOUT, follow_redirects=True)

            if r.status_code == 200:
                return _parse_rss(r.text, handle)
        
        except (httpx.TimeoutException, httpx.ConnectError):
            continue

        except Exception as e:
            print(f"_fetch_handle returned error: {e}")
            continue

    print("No NITTER instances found")
    return []


def _parse_rss(xml_text: str, handle: str) -> list[dict]:

    try:
        root = ET.fromstring(xml_text)

    except ET.ParseError:
        return []
    
    channel = root.find("channel")

    if channel is None:
        return []
    
    # avatar from <image><url>
    avatar = ""
    img = channel.find("image/url")
    if img is not None:
        avatar = img.text or ""

    items = []

    for item in channel.findall("item")[:NITTER_MAX_TWEETS_PER_HANDLE]:

        title = (item.findtext("title") or "").strip()
        link  = (item.findtext("link")  or "").strip()
        pub   = (item.findtext("pubDate") or "").strip()

        desc  = (item.findtext("description") or "").strip()

        # extract quoted/retweet image from HTML before stripping tags
        quote_img_match = re.search(r'<img src="([^"]+)"', desc)
        quote_img = quote_img_match.group(1).replace("&amp;", "&") if quote_img_match else ""

        # extract quoted author if present (bold tag before quoted text)
        quote_author_match = re.search(r'<b>([^<]+)</b>', desc)
        quote_author = quote_author_match.group(1) if quote_author_match else ""

        # strip HTML tags from description
        desc_clean = re.sub(r"<[^>]+>", "", desc).strip()[:500]

        # normalize date to ISO 8601
        try:
            published = parsedate_to_datetime(pub).isoformat()

        except Exception:
            published = pub

        # rewrite nitter links back to x.com
        canonical_url = re.sub(
            r"https?://[^/]+/",
            "https://x.com/",
            link,
        )

        items.append({
            "platform": "x",
            "id": canonical_url,
            "title": title,
            "author": handle,
            "avatar": avatar,
            "thumbnail": "",
            "url": canonical_url,
            "published": published,
            "description": desc_clean,
            "quote_img":   quote_img,
            "quote_author": quote_author,
        })

    return items


# ── Public fetch ──────────────────────────────────────────────────────────────


async def _fetch_all(handles: list[str]) -> list[dict]:

    async with httpx.AsyncClient() as client:
        tasks = [_fetch_handle(h, client) for h in handles]
        results = await asyncio.gather(*tasks)

    items = [item for sublist in results for item in sublist]
    items.sort(key=lambda x: x["published"], reverse=True)
    return items  


async def fetch_feed() -> dict:

    handles = load_handles()

    if not handles:
        return {"error": "no_handles", "items": []}
    
    cached = _load_cache()
    if cached is not None:
        return {"error": None, "items": cached, "from_cache": True}
    
    try:
        items = await _fetch_all(handles)
        _save_cache(items)

        return {"error": None, "items": items, "from_cache": False}
    
    except Exception as e:
        return {"error": str(e), "items": []}
    

