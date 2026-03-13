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

NEWS_SOURCES_TECH: list[dict] = [
    # ── Infosec ───────────────────────────────────────────────────────────────
    {"id": "krebs",          "name": "Krebs on Security",   "category": "infosec",  "url": "https://krebsonsecurity.com/feed/"},
    {"id": "bleepingcomputer","name": "BleepingComputer",   "category": "infosec",  "url": "https://www.bleepingcomputer.com/feed/"},
    {"id": "thehackernews",  "name": "The Hacker News",     "category": "infosec",  "url": "https://feeds.feedburner.com/TheHackersNews"},
    {"id": "darkreading",    "name": "Dark Reading",        "category": "infosec",  "url": "https://www.darkreading.com/rss.xml"},
    {"id": "schneier",       "name": "Schneier on Security","category": "infosec",  "url": "https://www.schneier.com/feed/atom"},
    {"id": "recordedfuture", "name": "Recorded Future",    "category": "infosec",  "url": "https://www.recordedfuture.com/feed"},
    {"id": "threatpost",     "name": "Threatpost",          "category": "infosec",  "url": "https://threatpost.com/feed/"},
    {"id": "securityweek",   "name": "SecurityWeek",        "category": "infosec",  "url": "https://feeds.feedburner.com/securityweek"},
    {"id": "troyhunt",       "name": "Troy Hunt",           "category": "infosec",  "url": "https://www.troyhunt.com/rss/"},
    {"id": "malwarebytes",   "name": "Malwarebytes Labs",   "category": "infosec",  "url": "https://www.malwarebytes.com/blog/feed/"},
    {"id": "sophos",         "name": "Sophos News",         "category": "infosec",  "url": "https://news.sophos.com/en-us/feed/"},
    {"id": "crowdstrike",    "name": "CrowdStrike Blog",    "category": "infosec",  "url": "https://www.crowdstrike.com/blog/feed/"},
    {"id": "sentinelone",    "name": "SentinelOne",         "category": "infosec",  "url": "https://www.sentinelone.com/blog/feed/"},
    {"id": "checkpointres",  "name": "Check Point Research","category": "infosec",  "url": "https://research.checkpoint.com/feed/"},
    {"id": "unit42",         "name": "Palo Alto Unit 42",   "category": "infosec",  "url": "https://unit42.paloaltonetworks.com/feed/"},
    {"id": "googleprojectzero","name":"Google Project Zero","category": "infosec",  "url": "https://googleprojectzero.blogspot.com/feeds/posts/default"},
    {"id": "mandiant",       "name": "Mandiant Blog",       "category": "infosec",  "url": "https://www.mandiant.com/resources/blog/rss.xml"},
    {"id": "exploitdb",      "name": "Exploit-DB",          "category": "infosec",  "url": "https://www.exploit-db.com/rss.xml"},
    {"id": "packetstorm",    "name": "Packet Storm",        "category": "infosec",  "url": "https://packetstormsecurity.com/rss.xml"},
    {"id": "Graham Cluley",  "name": "Graham Cluley",       "category": "infosec",  "url": "https://grahamcluley.com/feed/"},
    # ── Government / CERT ────────────────────────────────────────────────────
    {"id": "cisa",           "name": "CISA",                "category": "government","url": "https://www.cisa.gov/cybersecurity-advisories/all.xml"},
    {"id": "cisa_ics",       "name": "CISA ICS",            "category": "government","url": "https://www.cisa.gov/cybersecurity-advisories/ics-advisories.xml"},
    {"id": "nist_nvd",       "name": "NIST NVD",            "category": "government","url": "https://nvd.nist.gov/feeds/xml/cve/misc/nvd-rss.xml"},
    {"id": "msrc",           "name": "Microsoft MSRC",      "category": "government","url": "https://msrc.microsoft.com/blog/feed"},
    {"id": "ncsc",           "name": "NCSC UK",             "category": "government","url": "https://www.ncsc.gov.uk/api/1/services/v1/report-rss-feed.xml"},
    {"id": "enisa",          "name": "ENISA",               "category": "government","url": "https://www.enisa.europa.eu/news/enisa-news/RSS"},
    {"id": "austracyber",    "name": "ASD ACSC",            "category": "government","url": "https://www.cyber.gov.au/about-us/news/rss"},
    # ── Tech ─────────────────────────────────────────────────────────────────
    {"id": "wired",          "name": "Wired",               "category": "tech",     "url": "https://www.wired.com/feed/rss"},
    {"id": "arstechnica",    "name": "Ars Technica",        "category": "tech",     "url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"id": "theregister",    "name": "The Register",        "category": "tech",     "url": "https://www.theregister.com/headlines.atom"},
    {"id": "zdnet",          "name": "ZDNet",               "category": "tech",     "url": "https://www.zdnet.com/news/rss.xml"},
    {"id": "techcrunch",     "name": "TechCrunch",          "category": "tech",     "url": "https://techcrunch.com/feed/"},
    {"id": "hackernews_yc",  "name": "Hacker News (YC)",    "category": "tech",     "url": "https://news.ycombinator.com/rss"},
    {"id": "technologyreview","name":"MIT Tech Review",     "category": "tech",     "url": "https://www.technologyreview.com/feed/"},
    {"id": "verge",          "name": "The Verge",           "category": "tech",     "url": "https://www.theverge.com/rss/index.xml"},
]

NEWS_SOURCES_GENERAL: list[dict] = [
    # ── Finance / Economics ───────────────────────────────────────────────────
    {"id": "ft",             "name": "Financial Times",     "category": "finance",  "url": "https://www.ft.com/technology?format=rss"},
    {"id": "ft_markets",     "name": "FT Markets",          "category": "finance",  "url": "https://www.ft.com/markets?format=rss"},
    {"id": "ft_economy",     "name": "FT Economy",          "category": "finance",  "url": "https://www.ft.com/economics?format=rss"},
    {"id": "ft_world",       "name": "FT World",            "category": "finance",  "url": "https://www.ft.com/world?format=rss"},
    {"id": "economist",      "name": "The Economist",       "category": "finance",  "url": "https://www.economist.com/finance-and-economics/rss.xml"},
    {"id": "wsj_markets",    "name": "WSJ Markets",         "category": "finance",  "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml"},
    {"id": "wsj_economy",    "name": "WSJ Economy",         "category": "finance",  "url": "https://feeds.a.dj.com/rss/RSSWorldNews.xml"},
    {"id": "marketwatch",    "name": "MarketWatch",         "category": "finance",  "url": "https://feeds.marketwatch.com/marketwatch/topstories/"},
    {"id": "cnbc",           "name": "CNBC",                "category": "finance",  "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
    {"id": "reuters_finance","name": "Reuters Finance",     "category": "finance",  "url": "https://feeds.reuters.com/reuters/businessNews"},
    {"id": "bloomberg_tech", "name": "Bloomberg Tech",      "category": "finance",  "url": "https://feeds.bloomberg.com/technology/news.rss"},
    {"id": "federalreserve", "name": "Federal Reserve",     "category": "finance",  "url": "https://www.federalreserve.gov/feeds/press_all.xml"},
    {"id": "ecb",            "name": "ECB",                 "category": "finance",  "url": "https://www.ecb.europa.eu/rss/press.html"},
    {"id": "imf_blog",       "name": "IMF Blog",            "category": "finance",  "url": "https://www.imf.org/en/News/rss?language=eng"},
    {"id": "bis",            "name": "BIS Research",        "category": "finance",  "url": "https://www.bis.org/rss/research.rss"},
    {"id": "worldbank",      "name": "World Bank",          "category": "finance",  "url": "https://blogs.worldbank.org/feed"},
    {"id": "nber",           "name": "NBER",                "category": "finance",  "url": "https://www.nber.org/rss/new_research_feed.xml"},
    {"id": "project_syndicate","name":"Project Syndicate",  "category": "finance",  "url": "https://www.project-syndicate.org/rss"},
    {"id": "vox_econ",       "name": "Vox EU",              "category": "finance",  "url": "https://cepr.org/rss.xml"},
    # ── Politics / Geopolitics ────────────────────────────────────────────────
    {"id": "reuters",        "name": "Reuters",             "category": "politics", "url": "https://feeds.reuters.com/reuters/technology"},
    {"id": "bbc",            "name": "BBC News",            "category": "politics", "url": "https://feeds.bbci.co.uk/news/rss.xml"},
    {"id": "guardian",       "name": "The Guardian",        "category": "politics", "url": "https://www.theguardian.com/world/rss"},
    {"id": "ap",             "name": "AP News",             "category": "politics", "url": "https://rsshub.app/apnews/topics/technology"},
    {"id": "aljazeera",      "name": "Al Jazeera",          "category": "politics", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"id": "dw_news",        "name": "DW News",             "category": "politics", "url": "https://rss.dw.com/rdf/rss-en-all"},
    {"id": "france24",       "name": "France 24",           "category": "politics", "url": "https://www.france24.com/en/rss"},
    {"id": "politico",       "name": "Politico",            "category": "politics", "url": "https://www.politico.com/rss/politicopicks.xml"},
    {"id": "politico_eu",    "name": "Politico EU",         "category": "politics", "url": "https://www.politico.eu/feed/"},
    {"id": "thehill",        "name": "The Hill",            "category": "politics", "url": "https://thehill.com/feed/"},
    {"id": "axios",          "name": "Axios",               "category": "politics", "url": "https://api.axios.com/feed/"},
    {"id": "pbs_newshour",   "name": "PBS NewsHour",        "category": "politics", "url": "https://www.pbs.org/newshour/feeds/rss/headlines"},
    {"id": "rferl",          "name": "Radio Free Europe",   "category": "politics", "url": "https://www.rferl.org/api/zpqoyu$vusr"},
    {"id": "euractiv",       "name": "Euractiv",            "category": "politics", "url": "https://www.euractiv.com/feed/"},
    {"id": "foreignaffairs", "name": "Foreign Affairs",     "category": "politics", "url": "https://www.foreignaffairs.com/rss.xml"},
    {"id": "foreignpolicy",  "name": "Foreign Policy",      "category": "politics", "url": "https://foreignpolicy.com/feed/"},
    {"id": "cfr",            "name": "CFR",                 "category": "politics", "url": "https://www.cfr.org/rss/all"},
    {"id": "brookings",      "name": "Brookings",           "category": "politics", "url": "https://www.brookings.edu/feed/"},
    {"id": "rand",           "name": "RAND Corp",           "category": "politics", "url": "https://www.rand.org/news/press.rss"},
    {"id": "chathamhouse",   "name": "Chatham House",       "category": "politics", "url": "https://www.chathamhouse.org/rss.xml"},
    {"id": "crisisgroup",    "name": "Crisis Group",        "category": "politics", "url": "https://www.crisisgroup.org/rss"},
    {"id": "sipri",          "name": "SIPRI",               "category": "politics", "url": "https://www.sipri.org/rss.xml"},
    {"id": "iiss",           "name": "IISS",                "category": "politics", "url": "https://www.iiss.org/rss"},
    {"id": "understandingwar","name":"Inst. Study of War",  "category": "politics", "url": "https://www.understandingwar.org/rss.xml"},
    {"id": "bellingcat",     "name": "Bellingcat",          "category": "politics", "url": "https://www.bellingcat.com/feed/"},
    {"id": "intercepted",    "name": "The Intercept",       "category": "politics", "url": "https://theintercept.com/feed/?rss"},
    {"id": "kyivindependent","name": "Kyiv Independent",    "category": "politics", "url": "https://kyivindependent.com/feed/"},
    {"id": "meduza",         "name": "Meduza",              "category": "politics", "url": "https://meduza.io/rss/en/all"},
    {"id": "scmp",           "name": "South China Morning Post","category":"politics","url": "https://www.scmp.com/rss/91/feed"},
    {"id": "nikkei",         "name": "Nikkei Asia",         "category": "politics", "url": "https://asia.nikkei.com/rss/feed/nar"},
    {"id": "thediplomat",    "name": "The Diplomat",        "category": "politics", "url": "https://thediplomat.com/feed/"},
    {"id": "asiatimes",      "name": "Asia Times",          "category": "politics", "url": "https://asiatimes.com/feed/"},
    {"id": "middleeasteye",  "name": "Middle East Eye",     "category": "politics", "url": "https://www.middleeasteye.net/rss"},
    {"id": "haaretz",        "name": "Haaretz",             "category": "politics", "url": "https://www.haaretz.com/srv/haaretz-articles.rss"},
    {"id": "stimson",        "name": "Stimson Center",      "category": "politics", "url": "https://www.stimson.org/feed/"},
    {"id": "nyttech",        "name": "NYT Technology",      "category": "politics", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml"},
    {"id": "wapotech",       "name": "Washington Post",     "category": "politics", "url": "https://feeds.washingtonpost.com/rss/business/technology"},
]

NEWS_SOURCES = NEWS_SOURCES_TECH + NEWS_SOURCES_GENERAL

# ── Server ────────────────────────────────────────────────────────────────────

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))