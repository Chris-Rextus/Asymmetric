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

X_HANDLES = [
    h.strip().lstrip('@')
    for h in os.getenv("X_HANDLES", "").split(",")
    if h.strip()
]

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
]
NITTER_TIMEOUT = int(os.getenv("NITTER_TIMEOUT", "8"))
NITTER_MAX_TWEETS_PER_HANDLE = int(os.getenv("NITTER_MAX_TWEETS_PER_HANDLE", "10"))

# ── Telegram ──────────────────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_IDS = [
    ch.strip()
    for ch in os.getenv("TELEGRAM_CHANNEL_IDS", "").split(",")
    if ch.strip()
]
TELEGRAM_MAX_MESSAGES_PER_CHANNEL = int(os.getenv("TELEGRAM_MAX_MESSAGES_PER_CHANNEL", "20"))
TELEGRAM_CACHE_TTL_MINUTES = int(os.getenv("TELEGRAM_CACHE_TTL_MINUTES", "15"))

# ── Reddit ────────────────────────────────────────────────────────────────────
REDDIT_SUBREDDITS = [
    s.strip()
    for s in os.getenv("REDDIT_SUBREDDITS", "").split(",")
    if s.strip()
]
REDDIT_CACHE_TTL_MINUTES = int(os.getenv("REDDIT_CACHE_TTL_MINUTES", "30"))
REDDIT_MAX_POSTS_PER_SUBREDDIT = int(os.getenv("REDDIT_MAX_POSTS_PER_SUBREDDIT", "25"))

# ── Mainstream News ────────────────────────────────────────────────────────────

NEWS_CACHE_TTL_MINUTES      = int(os.getenv("NEWS_CACHE_TTL_MINUTES", "20"))
NEWS_MAX_ITEMS_PER_SOURCE   = int(os.getenv("NEWS_MAX_ITEMS_PER_SOURCE", "40"))

NEWS_SOURCES = [

    # ── Infosec ───────────────────────────────────────────────────────────────
    {"id": "krebs",          "name": "Krebs on Security",    "category": "infosec",     "url": "https://krebsonsecurity.com/feed/"},
    {"id": "bleepingcomputer","name": "Bleeping Computer",   "category": "infosec",     "url": "https://www.bleepingcomputer.com/feed/"},
    {"id": "thehackernews",  "name": "The Hacker News",      "category": "infosec",     "url": "https://feeds.feedburner.com/TheHackersNews"},
    {"id": "darkreading",    "name": "Dark Reading",         "category": "infosec",     "url": "https://www.darkreading.com/rss.xml"},
    {"id": "schneier",       "name": "Schneier on Security", "category": "infosec",     "url": "https://www.schneier.com/feed/atom"},
    {"id": "recordedfuture", "name": "Recorded Future",      "category": "infosec",     "url": "https://www.recordedfuture.com/feed"},
    {"id": "threatpost",     "name": "Threatpost",           "category": "infosec",     "url": "https://threatpost.com/feed/"},

    # ── Tech ─────────────────────────────────────────────────────────────────
    {"id": "wired",          "name": "Wired",                "category": "tech",        "url": "https://www.wired.com/feed/rss"},
    {"id": "arstechnica",    "name": "Ars Technica",         "category": "tech",        "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"id": "theregister",    "name": "The Register",         "category": "tech",        "url": "https://www.theregister.com/headlines.atom"},
    {"id": "zdnet",          "name": "ZDNet",                "category": "tech",        "url": "https://www.zdnet.com/news/rss.xml"},

    # ── Mainstream ────────────────────────────────────────────────────────────
    {"id": "reuters",        "name": "Reuters Tech",         "category": "mainstream",  "url": "https://feeds.reuters.com/reuters/technology"},
    {"id": "bbc",            "name": "BBC Technology",       "category": "mainstream",  "url": "https://feeds.bbci.co.uk/news/technology/rss.xml"},
    {"id": "guardian",       "name": "The Guardian Tech",    "category": "mainstream",  "url": "https://www.theguardian.com/technology/rss"},
    {"id": "ap",             "name": "AP Technology",        "category": "mainstream",  "url": "https://rsshub.app/apnews/topics/technology"},

    # ── Government ───────────────────────────────────────────────────────────
    {"id": "cisa",           "name": "CISA Advisories",      "category": "government",  "url": "https://www.cisa.gov/cybersecurity-advisories/all.xml"},
    {"id": "ncsc",           "name": "NCSC UK",              "category": "government",  "url": "https://www.ncsc.gov.uk/api/1/services/v1/all-rss-feed.xml"},
    {"id": "msrc",           "name": "Microsoft MSRC",       "category": "government",  "url": "https://api.msrc.microsoft.com/update-guide/rss"},
    {"id": "enisa",          "name": "ENISA",                "category": "government",  "url": "https://www.enisa.europa.eu/news/enisa-news/RSS"},

    # ── Infosec (extra) ───────────────────────────────────────────────────────
    {"id": "securityweek",   "name": "SecurityWeek",        "category": "infosec",     "url": "https://feeds.feedburner.com/securityweek"},
    {"id": "Graham Cluley",  "name": "Graham Cluley",       "category": "infosec",     "url": "https://grahamcluley.com/feed/"},
    {"id": "troyhunt",       "name": "Troy Hunt",           "category": "infosec",     "url": "https://www.troyhunt.com/rss/"},
    {"id": "malwarebytes",   "name": "Malwarebytes Labs",   "category": "infosec",     "url": "https://www.malwarebytes.com/blog/feed/"},
    {"id": "crowdstrike",    "name": "CrowdStrike Blog",    "category": "infosec",     "url": "https://www.crowdstrike.com/blog/feed/"},
    {"id": "sentinelone",    "name": "SentinelOne",         "category": "infosec",     "url": "https://www.sentinelone.com/blog/feed/"},
    {"id": "checkpointres",  "name": "Check Point Research","category": "infosec",     "url": "https://research.checkpoint.com/feed/"},
    {"id": "unit42",         "name": "Palo Alto Unit 42",   "category": "infosec",     "url": "https://unit42.paloaltonetworks.com/feed/"},
    {"id": "googleprojectzero","name": "Google Project Zero","category": "infosec",    "url": "https://googleprojectzero.blogspot.com/feeds/posts/default"},
    {"id": "mandiant",       "name": "Mandiant Blog",       "category": "infosec",     "url": "https://www.mandiant.com/resources/blog/rss.xml"},
    {"id": "exploitdb",      "name": "Exploit-DB",          "category": "infosec",     "url": "https://www.exploit-db.com/rss.xml"},
    {"id": "packetstorm",    "name": "Packet Storm",        "category": "infosec",     "url": "https://packetstormsecurity.com/rss.xml"},

    # ── Tech (extra) ──────────────────────────────────────────────────────────
    {"id": "techcrunch",     "name": "TechCrunch",          "category": "tech",        "url": "https://techcrunch.com/feed/"},
    {"id": "hackernews_yc",  "name": "Hacker News (YC)",    "category": "tech",        "url": "https://news.ycombinator.com/rss"},
    {"id": "technologyreview","name": "MIT Tech Review",    "category": "tech",        "url": "https://www.technologyreview.com/feed/"},
    {"id": "verge",          "name": "The Verge",           "category": "tech",        "url": "https://www.theverge.com/rss/index.xml"},

    # ── Mainstream (extra) ────────────────────────────────────────────────────
    {"id": "nyttech",        "name": "NYT Technology",      "category": "mainstream",  "url": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"},
    {"id": "wapotech",       "name": "Washington Post Tech","category": "mainstream",  "url": "https://feeds.washingtonpost.com/rss/business/technology"},
    {"id": "ft",             "name": "Financial Times Tech","category": "mainstream",  "url": "https://www.ft.com/technology?format=rss"},

    # ── Government (extra) ───────────────────────────────────────────────────
    {"id": "nist_nvd",       "name": "NIST NVD",            "category": "government",  "url": "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml"},
    {"id": "cisa_ics",       "name": "CISA ICS Advisories", "category": "government",  "url": "https://www.cisa.gov/cybersecurity-advisories/ics-advisories.xml"},
]

# ── Server ────────────────────────────────────────────────────────────────────

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))