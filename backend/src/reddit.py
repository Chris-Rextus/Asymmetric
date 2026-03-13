# backend/src/reddit.py

import json
import asyncio
import httpx

from datetime import datetime, timezone, timedelta

from config import (
    DATA_DIR,
    REDDIT_SUBREDDITS,
    REDDIT_CACHE_TTL_MINUTES,
    REDDIT_MAX_POSTS_PER_SUBREDDIT,
)

CACHE_FILE = DATA_DIR / "reddit_cache.json"

HEADERS = {
    "User-Agent": "infosec-feed/1.0 (personal aggregator)",
}

# ── Icons ──────────────────────────────────────────────────────────────────────

async def _fetch_subreddit_icon(subreddit: str, client: httpx.AsyncClient) -> str:
    try:
        r = await client.get(
            f"https://www.reddit.com/r/{subreddit}/about.json",
            headers=HEADERS, timeout=10, follow_redirects=True,
        )
        if r.status_code != 200:
            return ""
        data = r.json()["data"]
        icon = data.get("icon_img") or data.get("community_icon") or ""

        print(f"[reddit] r/{subreddit} icon_img={data.get('icon_img')!r} community_icon={data.get('community_icon')!r}")

        return icon.replace("&amp;", "&")
    except Exception:
        return ""

# ── Cache ─────────────────────────────────────────────────────────────────────

def _load_cache() -> list | None:

    if not CACHE_FILE.exists():
        return None
    
    raw       = json.loads(CACHE_FILE.read_text())
    cached_at = datetime.fromisoformat(raw["cached_at"])
    age       = datetime.now(timezone.utc) - cached_at

    if age > timedelta(minutes=REDDIT_CACHE_TTL_MINUTES):
        return None
    
    return raw["items"]


def _save_cache(items: list) -> None:

    CACHE_FILE.write_text(json.dumps({
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "items":     items,
    }, indent=2))

# ── Fetch one subreddit ───────────────────────────────────────────────────────

async def _fetch_subreddit(subreddit: str, client: httpx.AsyncClient) -> list[dict]:

    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={REDDIT_MAX_POSTS_PER_SUBREDDIT}"

    try:
        r = await client.get(url, headers=HEADERS, timeout=10, follow_redirects=True)

        if r.status_code != 200:
            print(f"[reddit] r/{subreddit} returned {r.status_code}")
            return []

        data  = r.json()
        posts = data["data"]["children"]
        items = []

        for post in posts:
            p = post["data"]

            # skip stickied mod posts
            if p.get("stickied"):
                continue

            published = datetime.fromtimestamp(
                p["created_utc"], tz=timezone.utc
            ).isoformat()

            # best thumbnail: prefer preview image, fallback to thumbnail
            thumbnail = ""
            try:
                thumbnail = p["preview"]["images"][0]["source"]["url"].replace("&amp;", "&")
            except Exception:
                t = p.get("thumbnail", "")
                if t and t not in ("self", "default", "nsfw", "spoiler", ""):
                    thumbnail = t

            post_url = f"https://reddit.com{p['permalink']}"

            items.append({
                "platform":    "reddit",
                "id":          post_url,
                "title":       p.get("title", "")[:200],
                "author":      f"r/{subreddit}",
                "avatar":      "",
                "thumbnail":   thumbnail,
                "url":         post_url,
                "published":   published,
                "description": p.get("selftext", "")[:500] or p.get("title", ""),
                "subreddit":   subreddit,
                "score":       p.get("score", 0),
                "num_comments": p.get("num_comments", 0),
                "post_hint":   p.get("post_hint", ""),
                "domain":      p.get("domain", ""),
            })

        return items

    except Exception as e:
        print(f"[reddit] error fetching r/{subreddit}: {e}")
        return []
    
# ── Fetch all subreddits ──────────────────────────────────────────────────────

async def _fetch_all(subreddits: list[str]) -> list[dict]:

    async with httpx.AsyncClient() as client:
        post_tasks = [_fetch_subreddit(s, client) for s in subreddits]
        icon_tasks = [_fetch_subreddit_icon(s, client) for s in subreddits]
        post_results, icon_results = await asyncio.gather(
            asyncio.gather(*post_tasks),
            asyncio.gather(*icon_tasks),
        )

    icon_map = {s: icon for s, icon in zip(subreddits, icon_results)}

    items = []
    for sublist in post_results:
        for item in sublist:
            item["avatar"] = icon_map.get(item["subreddit"], "")
            items.append(item)

    items.sort(key=lambda x: x["published"], reverse=True)
    return items

# ── Subreddits summary ────────────────────────────────────────────────────────

def get_subreddits_summary(items: list[dict]) -> list[dict]:

    seen: dict[str, dict] = {}

    for item in items:
        sub = item["subreddit"]
        if sub not in seen:
            seen[sub] = {
                "subreddit":        sub,
                "post_count":       0,
                "latest_published": item["published"],
                "latest_title":     item["title"],
            }
        seen[sub]["post_count"] += 1
        if item["published"] > seen[sub]["latest_published"]:
            seen[sub]["latest_published"] = item["published"]
            seen[sub]["latest_title"]     = item["title"]

    result = list(seen.values())
    result.sort(key=lambda x: x["latest_published"], reverse=True)
    return result

# ── Public fetch ──────────────────────────────────────────────────────────────

async def fetch_feed() -> dict:

    if not REDDIT_SUBREDDITS:
        return {"error": "no_subreddits", "items": []}

    cached = _load_cache()
    if cached is not None:
        return {"error": None, "items": cached, "from_cache": True}

    try:
        items = await _fetch_all(REDDIT_SUBREDDITS)
        _save_cache(items)
        return {"error": None, "items": items, "from_cache": False}

    except Exception as e:
        return {"error": str(e), "items": []}