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

