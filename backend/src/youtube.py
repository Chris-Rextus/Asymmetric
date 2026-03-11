# backend/src/youtube.py

import json

from datetime import datetime, timezone, timedelta
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from config import (
    CLIENT_SECRET_FILE,
    TOKEN_FILE,
    DATA_DIR,
    YOUTUBE_SCOPES,
    YOUTUBE_MAX_SUBSCRIPTIONS,
    YOUTUBE_MAX_VIDEOS_PER_CHANNEL,
)

CACHE_FILE = DATA_DIR / "yt_cache.json"
CACHE_TTL_MINUTES = 30

# ── Auth ──────────────────────────────────────────────────────────────────────

def get_credentials() -> Credentials | None:

    if not TOKEN_FILE.exists():
        return None
    
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, YOUTUBE_SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json())

    return creds if creds and creds.valid else None


def build_auth_flow(redirect_url: str) -> Flow:

    return Flow.from_client_secrets_file(
        CLIENT_SECRET_FILE,
        scopes=YOUTUBE_SCOPES,
        redirect_url=redirect_url,
    )


def save_token_from_code(code: str, redirect_uri: str) -> None:

    flow = build_auth_flow(redirect_uri)
    flow.fetch_token(code=code)
    TOKEN_FILE.write_text(flow.credentials.to_json())


def is_authenticated() -> bool:

    return get_credentials() is not None


# ── Cache ─────────────────────────────────────────────────────────────────────

def _load_cache() -> dict | None:

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


# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_feed() -> dict:

    creds = get_credentials()
    if not creds:
        return {"error": "not_authenticated", "items": []}
    
    cached = _load_cache()
    if cached is not None:
        return {"error": None, "items": cached, "from_cache": True}
    
    try:
        items = _fetch_from_api(creds)
        _save_cache(items)
        return {"error": None, "items": items, "from_cache": False}
    
    except Exception as e:
        return {"error": str(e), "items": []}
    

def _fetch_from_api(creds: Credentials) -> list:

    youtube = build("youtube", "v3", credentials=creds)

    # 1. Get subscriptions
    subs = youtube.subscriptions().list(
        part="snippet",
        mine=True,
        maxResults=YOUTUBE_MAX_SUBSCRIPTIONS,
    ).execute()

    channel_ids = [
        item["snippet"]["resourceId"]["channelId"]
        for item in subs.get("items", [])
    ]

    if not channel_ids:
        return []

    # 2. Get channel details (name, avatar, uploads playlist)
    channels = youtube.channels().list(
        part="contentDetails,snippet",
        id=",".join(channel_ids),
    ).execute()

    items = []

    for ch in channels.get("items", []):
        playlist_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]
        channel_name = ch["snippet"]["title"]
        avatar = (
            ch["snippet"]
            .get("thumbnails", {})
            .get("default", {})
            .get("url", "")
        )

        try:
            playlist = youtube.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=YOUTUBE_MAX_VIDEOS_PER_CHANNEL,
            ).execute()
        except Exception:
            continue

        for vid in playlist.get("items", []):
            s = vid["snippet"]
            vid_id = s.get("resourceId", {}).get("videoId", "")
            if not vid_id:
                continue

            items.append({
                "platform": "youtube",
                "id": vid_id,
                "title": s.get("title", ""),
                "author": channel_name,
                "avatar": avatar,
                "thumbnail": (
                    s.get("thumbnails", {})
                    .get("medium", {})
                    .get("url", "")
                ),
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "published": s.get("publishedAt", ""),
                "description": s.get("description", "")[:200],
            })

    items.sort(key=lambda x: x["published"], reverse=True)
    return items
