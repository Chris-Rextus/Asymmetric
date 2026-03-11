# backend/config.py

from pathlib import Path
from dotenv import load_dotenv
import os

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

ENV_FILE = BASE_DIR / ".env"
CLIENT_SECRET_FILE = BASE_DIR / "client_secret.json"
TOKEN_FILE = DATA_DIR / "token.json"
FOLLOWING_FILE = DATA_DIR / "following.js"

# ── Load .env ─────────────────────────────────────────────────────────────────

load_dotenv(ENV_FILE)

# ── YouTube ───────────────────────────────────────────────────────────────────

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]
YOUTUBE_MAX_SUBSCRIPTIONS = int(os.getenv("YOUTUBE_MAX_SUBSCRIPTIONS", "50"))
YOUTUBE_MAX_VIDEOS_PER_CHANNEL = int(os.getenv("YOUTUBE_MAX_VIDEOS_PER_CHANNEL", "5"))
CACHE_TTL_MINUTES = int(os.getenv("CACHE_TTL_MINUTES", "30"))

# ── Nitter ────────────────────────────────────────────────────────────────────

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
]
NITTER_TIMEOUT = int(os.getenv("NITTER_TIMEOUT", "8"))
NITTER_MAX_TWEETS_PER_HANDLE = int(os.getenv("NITTER_MAX_TWEETS_PER_HANDLE", "10"))

# ── Server ────────────────────────────────────────────────────────────────────

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))