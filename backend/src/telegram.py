# backend/src/telegram.py

import json
import asyncio
import re
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser

import httpx

from config import (
    DATA_DIR,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHANNEL_IDS,
    TELEGRAM_MAX_MESSAGES_PER_CHANNEL,
    TELEGRAM_CACHE_TTL_MINUTES,
)

CACHE_FILE = DATA_DIR / "telegram_cache.json"


# ── Cache ─────────────────────────────────────────────────────────────────────

def _load_cache() -> list | None:
    if not CACHE_FILE.exists():
        return None
    raw       = json.loads(CACHE_FILE.read_text())
    cached_at = datetime.fromisoformat(raw["cached_at"])
    age       = datetime.now(timezone.utc) - cached_at
    if age > timedelta(minutes=TELEGRAM_CACHE_TTL_MINUTES):
        return None
    return raw["items"]


def _save_cache(items: list) -> None:
    CACHE_FILE.write_text(json.dumps({
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "items":     items,
    }, indent=2))


# ── HTML stripper ─────────────────────────────────────────────────────────────

class _HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
    def handle_data(self, data):
        self.parts.append(data)
    def get_text(self):
        return ''.join(self.parts).strip()


def _strip_html(html: str) -> str:
    s = _HTMLStripper()
    s.feed(html)
    return s.get_text()


# ── Fetch one channel via t.me/s/ ────────────────────────────────────────────

async def _fetch_channel(channel_id: str, client: httpx.AsyncClient) -> list[dict]:

    clean    = channel_id.lstrip('@')
    url      = f"https://t.me/s/{clean}"

    try:
        r = await client.get(
            url,
            timeout=10,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )

        if r.status_code != 200:
            print(f"[telegram] {channel_id} returned {r.status_code}")
            return []

        return _parse_html(r.text, channel_id, clean)

    except Exception as e:
        print(f"[telegram] error fetching {channel_id}: {e}")
        return []


def _parse_html(html: str, channel_id: str, clean_id: str) -> list[dict]:

    items = []

    # channel title
    title_match = re.search(r'<div class="tgme_channel_info_header_title"[^>]*>(.*?)</div>', html, re.DOTALL)
    channel_name = _strip_html(title_match.group(1)) if title_match else clean_id

    # channel avatar
    avatar_match = re.search(r'<i class="tgme_page_photo_image[^"]*"[^>]*><img src="([^"]+)"', html)
    avatar = avatar_match.group(1) if avatar_match else ""

    # each message block
    messages = re.findall(
        r'<div class="tgme_widget_message_wrap[^"]*".*?</div>\s*</div>\s*</div>',
        html,
        re.DOTALL,
    )

    # simpler: find message text + date pairs
    text_blocks = re.findall(
        r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>',
        html,
        re.DOTALL,
    )
    date_blocks = re.findall(
        r'<time datetime="([^"]+)"',
        html,
    )
    msg_ids = re.findall(
        r'data-post="[^/]+/(\d+)"',
        html,
    )

    count = min(
        len(text_blocks),
        len(date_blocks),
        TELEGRAM_MAX_MESSAGES_PER_CHANNEL,
    )

    for i in range(count):
        raw_text  = text_blocks[i]
        # preserve links text
        text      = _strip_html(raw_text).strip()
        if not text:
            continue

        # extract URLs from the raw html block
        urls_in_msg = re.findall(r'href="(https?://[^"]+)"', raw_text)

        date_str  = date_blocks[i] if i < len(date_blocks) else ""
        msg_id    = msg_ids[i]     if i < len(msg_ids)     else str(i)

        try:
            published = datetime.fromisoformat(date_str.replace('Z', '+00:00')).isoformat()
        except Exception:
            published = datetime.now(timezone.utc).isoformat()

        post_url = f"https://t.me/{clean_id}/{msg_id}"

        # append URLs found in message to text if not already visible
        extra_urls = [u for u in urls_in_msg if u not in text]
        if extra_urls:
            text = text + "\n" + "\n".join(extra_urls)

        items.append({
            "platform":    "telegram",
            "id":          post_url,
            "title":       text[:80] + ("..." if len(text) > 80 else ""),
            "author":      channel_name,
            "avatar":      avatar,
            "thumbnail":   "",
            "url":         post_url,
            "published":   published,
            "description": text[:500],
            "channel_id":  channel_id,
        })

    # reverse so newest is last in list (we sort after gather)
    items.reverse()
    return items


# ── Fetch all channels ────────────────────────────────────────────────────────

async def _fetch_all(channel_ids: list[str]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        tasks   = [_fetch_channel(ch, client) for ch in channel_ids]
        results = await asyncio.gather(*tasks)

    items = [item for sublist in results for item in sublist]
    items.sort(key=lambda x: x["published"], reverse=True)
    return items


# ── Public fetch ──────────────────────────────────────────────────────────────

async def fetch_feed() -> dict:

    if not TELEGRAM_CHANNEL_IDS:
        return {"error": "no_channels", "items": []}

    cached = _load_cache()
    if cached is not None:
        return {"error": None, "items": cached, "from_cache": True}

    try:
        items = await _fetch_all(TELEGRAM_CHANNEL_IDS)
        _save_cache(items)
        return {"error": None, "items": items, "from_cache": False}

    except Exception as e:
        return {"error": str(e), "items": []}
    

# ── Channels summary ──────────────────────────────────────────────────────────

def get_channels_summary(items: list[dict]) -> list[dict]:

    """
    Given the flat list of feed items, return one summary entry per channel:
      { channel_id, name, avatar, message_count, latest_published, latest_preview }
    Sorted by latest_published descending.
    """

    seen: dict[str, dict] = {}

    for item in items:
        cid = item["channel_id"]
        if cid not in seen:
            seen[cid] = {
                "channel_id":       cid,
                "name":             item["author"],
                "avatar":           item["avatar"],
                "message_count":    0,
                "latest_published": item["published"],
                "latest_preview":   item["description"],
            }
        seen[cid]["message_count"] += 1
        if item["published"] > seen[cid]["latest_published"]:
            seen[cid]["latest_published"] = item["published"]
            seen[cid]["latest_preview"]   = item["description"]

    result = list(seen.values())
    result.sort(key=lambda x: x["latest_published"], reverse=True)
    return result