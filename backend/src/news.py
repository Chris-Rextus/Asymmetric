# backend/src/news.py

import json
import asyncio
import xml.etree.ElementTree as ET
import re
import math
import httpx

from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from difflib import SequenceMatcher

from config import (
    DATA_DIR,
    NEWS_CACHE_TTL_MINUTES,
    NEWS_MAX_ITEMS_PER_SOURCE,
    NEWS_SOURCES,
    NEWS_SOURCES_TECH,
    NEWS_SOURCES_GENERAL,
)

CACHE_FILE         = DATA_DIR / "news_cache.json"
CACHE_FILE_TECH    = DATA_DIR / "news_cache_tech.json"
CACHE_FILE_GENERAL = DATA_DIR / "news_cache_general.json"

HEADERS = {
    "User-Agent":      "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Accept":          "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
    "Accept-Language": "en-US,en;q=0.5",
}

# ── Namespaces ────────────────────────────────────────────────────────────────

NS = {
    "atom":    "http://www.w3.org/2005/Atom",
    "media":   "http://search.yahoo.com/mrss/",
    "dc":      "http://purl.org/dc/elements/1.1/",
    "content": "http://purl.org/rss/1.0/modules/content/",
}

# ── Topic taxonomy ────────────────────────────────────────────────────────────

TOPICS: dict[str, list[str]] = {
    "ransomware":      ["ransomware", "ransom", "lockbit", "blackcat", "clop", "conti", "ryuk", "revil"],
    "vulnerability":   ["cve-", "vulnerability", "zero-day", "0day", "patch tuesday", "rce", "remote code", "buffer overflow", "sql injection", "xss"],
    "breach":          ["breach", "data breach", "leaked", "exposed", "stolen", "compromised", "exfiltrated", "dump"],
    "malware":         ["malware", "trojan", "backdoor", "rootkit", "spyware", "infostealer", "botnet", "worm", "virus", "dropper"],
    "apt":             ["apt", "nation-state", "state-sponsored", "espionage", "lazarus", "cozy bear", "fancy bear", "sandworm", "volt typhoon", "hafnium"],
    "phishing":        ["phishing", "spear-phishing", "smishing", "vishing", "social engineering", "credential harvesting"],
    "critical_infra":  ["critical infrastructure", "ics", "scada", "ot security", "power grid", "water treatment", "industrial control"],
    "cloud":           ["cloud security", "aws", "azure", "gcp", "s3 bucket", "misconfigured", "kubernetes", "docker"],
    "ai_security":     ["ai security", "llm", "artificial intelligence", "machine learning", "chatgpt", "deepfake", "prompt injection"],
    "privacy":         ["privacy", "gdpr", "surveillance", "tracking", "data collection", "facial recognition", "biometric"],
    "crypto":          ["cryptocurrency", "bitcoin", "ethereum", "blockchain", "defi", "nft", "crypto theft", "smart contract"],
    "geopolitics":     ["russia", "china", "iran", "north korea", "ukraine", "taiwan", "cyberwar", "cyber espionage", "geopolit"],
    "exploit":         ["exploit", "poc", "proof of concept", "metasploit", "weaponized", "in the wild", "actively exploited"],
    "mobile":          ["android", "ios", "iphone", "mobile security", "app store", "google play", "mobile malware"],
    "supply_chain":    ["supply chain", "solarwinds", "dependency", "npm package", "pypi", "open source", "third-party"],
    "regulation":      ["regulation", "compliance", "sec", "ftc", "gdpr", "nist", "executive order", "legislation", "law"],
    "sanctions":     ["sanctions", "export control", "ofac", "embargo", "blacklist"],
    "central_banks": ["federal reserve", "fed rate", "ecb", "interest rate", "monetary policy", "quantitative", "jerome powell", "lagarde"],
    "elections":     ["election", "vote", "ballot", "poll", "democrat", "republican", "congress", "parliament", "candidate"],
    "war":           ["war", "conflict", "military", "troops", "missile", "drone strike", "invasion", "nato", "ukraine", "gaza"],
    "trade":         ["tariff", "trade war", "import", "export", "wto", "supply chain", "manufacturing", "reshoring"],
    "inflation":     ["inflation", "cpi", "deflation", "interest rate", "recession", "gdp", "unemployment", "stagflation"],
    "energy":        ["oil", "gas", "opec", "energy", "pipeline", "lng", "nuclear", "solar", "renewable", "grid"],
    "usa":           ["united states", "washington", "white house", "pentagon", "congress", "senate", "biden", "trump", "cia", "nsa", "doj", "state department", "american"],
    "china":         ["china", "beijing", "xi jinping", "pla", "ccp", "chinese", "taiwan strait", "hong kong", "bri", "belt and road", "huawei", "tiktok", "prc"],
    "russia":        ["russia", "moscow", "putin", "kremlin", "fsb", "svr", "gru", "russian", "wagner", "ukraine war", "nato expansion", "gazprom"],
    "europe":        ["european union", "eu ", "brussels", "nato", "germany", "france", "uk", "britain", "macron", "scholz", "european parliament"],
    "middleeast":    ["israel", "iran", "saudi arabia", "gaza", "hamas", "hezbollah", "houthi", "irgc", "mossad", "riyadh", "tehran", "opec"],
    "nuclear":       ["nuclear", "icbm", "warhead", "nonproliferation", "iaea", "enrichment", "deterrence", "new start", "hypersonic"],
}

# ── Source weights ────────────────────────────────────────────────────────────

SOURCE_WEIGHTS: dict[str, float] = {
    # infosec — high signal
    "krebs":            2.0,
    "bleepingcomputer": 1.9,
    "thehackernews":    1.7,
    "darkreading":      1.6,
    "schneier":         1.8,
    "unit42":           1.8,
    "googleprojectzero":1.9,
    "mandiant":         1.8,
    "checkpointres":    1.7,
    "recordedfuture":   1.7,
    "sentinelone":      1.6,
    "crowdstrike":      1.6,
    "sophos":           1.5,
    "malwarebytes":     1.5,
    "exploitdb":        1.8,
    "packetstorm":      1.7,
    "securityweek":     1.5,
    "troyhunt":         1.6,
    # government
    "cisa":             2.0,
    "cisa_ics":         2.0,
    "nist_nvd":         1.9,
    "msrc":             1.8,
    "ncsc":             1.7,
    "enisa":            1.5,
    "fbi":              1.8,
    "austracyber":      1.4,
    # geopolitics / politics — high signal
    "foreignaffairs":   1.9,
    "foreignpolicy":    1.8,
    "bellingcat":       1.9,
    "understandingwar": 1.9,
    "kyivindependent":  1.7,
    "meduza":           1.7,
    "crisisgroup":      1.8,
    "cfr":              1.8,
    "rand":             1.7,
    "chathamhouse":     1.8,
    "sipri":            1.7,
    "iiss":             1.7,
    "stimson":          1.6,
    "intercepted":      1.5,
    "scmp":             1.6,
    "thediplomat":      1.6,
    "nikkei":           1.5,
    "asiatimes":        1.4,
    "middleeasteye":    1.5,
    "haaretz":          1.5,
    "rferl":            1.6,
    "aljazeera":        1.4,
    "kyivindependent":  1.7,
    "dw_news":          1.4,
    "france24":         1.4,
    "euractiv":         1.6,
    "politico":         1.6,
    "politico_eu":      1.6,
    "thehill":          1.4,
    "pbs_newshour":     1.4,
    "axios":            1.5,
    "brookings":        1.7,
    # finance / economics — high signal
    "economist":        1.9,
    "ft":               1.8,
    "ft_markets":       1.8,
    "ft_world":         1.8,
    "ft_economy":       1.8,
    "wsj_markets":      1.8,
    "wsj_economy":      1.8,
    "federalreserve":   1.9,
    "ecb":              1.8,
    "imf_blog":         1.8,
    "bis":              1.7,
    "nber":             1.7,
    "worldbank":        1.6,
    "project_syndicate":1.7,
    "marketwatch":      1.5,
    "cnbc":             1.4,
    "reuters_finance":  1.6,
    "vox_econ":         1.6,
    # tech — medium
    "arstechnica":      1.3,
    "theregister":      1.3,
    "wired":            1.2,
    "zdnet":            1.1,
    "techcrunch":       1.0,
    "hackernews_yc":    1.1,
    "technologyreview": 1.3,
    "verge":            0.9,
    # mainstream — baseline
    "reuters":          1.4,
    "bbc":              1.3,
    "guardian":         1.3,
    "ap":               1.3,
    "nyttech":          1.2,
    "wapotech":         1.2,
    "chathamhouse":     1.8,
}

# ── Keyword scoring tiers ─────────────────────────────────────────────────────

KEYWORDS_CRITICAL = [
    # infosec
    "zero-day", "0day", "rce", "remote code execution", "actively exploited",
    "critical vulnerability", "emergency patch", "ransomware attack",
    "data breach", "mass exploitation", "supply chain attack",
    # geopolitics / war
    "military invasion", "nuclear strike", "coup", "assassination",
    "war declaration", "state of emergency", "martial law",
    # economics
    "market crash", "bank collapse", "sovereign default", "financial crisis",
    "emergency rate cut", "hyperinflation", "stock market crash",
]

KEYWORDS_HIGH = [
    # infosec
    "vulnerability", "exploit", "malware", "backdoor", "apt", "breach",
    "ransomware", "phishing", "trojan", "botnet", "cve-", "zero trust",
    # geopolitics
    "nation-state", "sanctions", "military", "conflict", "nato", "invasion",
    "espionage", "intelligence", "treaty", "diplomatic", "ceasefire",
    "nuclear", "missile", "drone strike", "insurgency", "coup",
    # economics / finance
    "interest rate", "federal reserve", "inflation", "recession", "gdp",
    "tariff", "trade war", "central bank", "imf", "world bank",
    "bond yield", "currency", "deficit", "debt ceiling", "oil price",
]

KEYWORDS_MEDIUM = [
    # infosec
    "security", "attack", "threat", "advisory", "patch", "cyber", "hack",
    "leaked", "exposed", "stolen", "encryption", "authentication",
    # politics
    "election", "government", "parliament", "president", "minister",
    "policy", "legislation", "congress", "senate", "vote", "protest",
    "opposition", "referendum", "bilateral", "multilateral",
    # economics
    "market", "economy", "growth", "unemployment", "trade", "export",
    "import", "investment", "revenue", "budget", "fiscal", "monetary",
    "supply chain", "energy", "oil", "gas", "commodities", "stocks",
    # general signal
    "breaking", "exclusive", "report", "investigation", "leak", "revealed",
]
# ── Cache ─────────────────────────────────────────────────────────────────────

def _load_cache_file(path) -> list | None:
    if not path.exists():
        return None
    raw       = json.loads(path.read_text())
    cached_at = datetime.fromisoformat(raw["cached_at"])
    age       = datetime.now(timezone.utc) - cached_at
    if age > timedelta(minutes=NEWS_CACHE_TTL_MINUTES):
        return None
    return raw["items"]

def _save_cache_file(path, items: list) -> None:
    path.write_text(json.dumps({
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "items":     items,
    }, indent=2))

# ── Normalization (only for All view) ─────────────────────────────────────────

MAX_PER_SOURCE_IN_FEED   = 8
MAX_PER_CATEGORY_IN_FEED = {
    "infosec":    60,
    "tech":       40,
    "government": 30,
    "finance":    60,
    "politics":   60,
}

def _normalize(items: list[dict]) -> list[dict]:
    from collections import defaultdict
    by_source: dict[str, list] = defaultdict(list)
    for item in items:
        by_source[item["source_id"]].append(item)

    capped: list[dict] = []
    for source_items in by_source.values():
        source_items.sort(key=lambda x: x["score"], reverse=True)
        capped.extend(source_items[:MAX_PER_SOURCE_IN_FEED])

    by_category: dict[str, list] = defaultdict(list)
    for item in capped:
        by_category[item["category"]].append(item)

    normalized: list[dict] = []
    for cat, cat_items in by_category.items():
        cat_items.sort(key=lambda x: x["score"], reverse=True)
        limit = MAX_PER_CATEGORY_IN_FEED.get(cat, 60)
        normalized.extend(cat_items[:limit])

    normalized.sort(key=lambda x: x["score"], reverse=True)
    return normalized

# ── Date parsing ──────────────────────────────────────────────────────────────

def _parse_date(raw: str) -> str:

    if not raw:
        return datetime.now(timezone.utc).isoformat()
    try:
        return parsedate_to_datetime(raw).isoformat()
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(raw.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            pass
    return raw

# ── Fetch by source list ──────────────────────────────────────────────────────

async def _fetch_sources(sources: list[dict]) -> list[dict]:
    async with httpx.AsyncClient() as client:
        tasks   = [_fetch_source(s, client) for s in sources]
        results = await asyncio.gather(*tasks)
    items = [item for sublist in results for item in sublist]
    return _score_items(items)

# ── Public fetch functions ────────────────────────────────────────────────────

async def fetch_feed() -> dict:
    """All sources combined, normalized."""
    cached = _load_cache_file(CACHE_FILE)
    if cached is not None:
        return {"error": None, "items": cached, "from_cache": True}
    try:
        tech    = await _fetch_sources(NEWS_SOURCES_TECH)
        general = await _fetch_sources(NEWS_SOURCES_GENERAL)
        all_items = _score_items(tech + general)
        normalized = _normalize(all_items)
        _save_cache_file(CACHE_FILE, normalized)
        return {"error": None, "items": normalized, "from_cache": False}
    except Exception as e:
        return {"error": str(e), "items": []}

async def fetch_tech() -> dict:
    """Tech + infosec only, no normalization."""
    cached = _load_cache_file(CACHE_FILE_TECH)
    if cached is not None:
        return {"error": None, "items": cached, "from_cache": True}
    try:
        items = await _fetch_sources(NEWS_SOURCES_TECH)
        _save_cache_file(CACHE_FILE_TECH, items)
        return {"error": None, "items": items, "from_cache": False}
    except Exception as e:
        return {"error": str(e), "items": []}

async def fetch_general() -> dict:
    """Finance + politics only, no normalization."""
    cached = _load_cache_file(CACHE_FILE_GENERAL)
    if cached is not None:
        return {"error": None, "items": cached, "from_cache": True}
    try:
        items = await _fetch_sources(NEWS_SOURCES_GENERAL)
        _save_cache_file(CACHE_FILE_GENERAL, items)
        return {"error": None, "items": items, "from_cache": False}
    except Exception as e:
        return {"error": str(e), "items": []}

# ── Image extraction ──────────────────────────────────────────────────────────

def _extract_image(item: ET.Element, desc_html: str) -> str:
    for tag in ("media:thumbnail", "media:content"):
        el = item.find(tag, NS)
        if el is not None:
            url = el.get("url", "")
            if url:
                return url
    enc = item.find("enclosure")
    if enc is not None:
        mime = enc.get("type", "")
        if mime.startswith("image"):
            return enc.get("url", "")
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc_html)
    if m:
        return m.group(1)
    return ""

# ── Topic detection ───────────────────────────────────────────────────────────

def _detect_topics(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for topic, keywords in TOPICS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(topic)
    return found

# ── Keyword scoring ───────────────────────────────────────────────────────────

def _keyword_score(text: str) -> tuple[float, list[str]]:
    text_lower = text.lower()
    score      = 0.0
    found      = []

    for kw in KEYWORDS_CRITICAL:
        if kw in text_lower:
            score += 3.0
            found.append(kw)

    for kw in KEYWORDS_HIGH:
        if kw in text_lower and kw not in found:
            score += 1.5
            found.append(kw)

    for kw in KEYWORDS_MEDIUM:
        if kw in text_lower and kw not in found:
            score += 0.5
            found.append(kw)

    return min(score, 10.0), found[:8]  

# ── Recency scoring ───────────────────────────────────────────────────────────

def _recency_score(published_iso: str) -> float:
    try:
        pub = datetime.fromisoformat(published_iso)
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - pub).total_seconds() / 3600
        # exponential decay: full score <6h, half at 24h, near zero at 168h
        return 10.0 * math.exp(-0.02 * age_hours)
    except Exception:
        return 0.0
    
# ── Trending detection ────────────────────────────────────────────────────────

def _find_trending(items: list[dict]) -> set[str]:
    """Return IDs of articles whose titles are similar to 2+ other articles within 12h."""
    trending_ids: set[str] = set()
    recent = [
        i for i in items
        if _recency_score(i["published"]) > 3.0  # within ~24h
    ]

    for i, a in enumerate(recent):
        matches = 0
        for b in recent[i + 1:]:
            if a["source_id"] == b["source_id"]:
                continue
            ratio = SequenceMatcher(
                None,
                a["title"].lower()[:80],
                b["title"].lower()[:80],
            ).ratio()
            if ratio > 0.45:
                matches += 1
                trending_ids.add(b["id"])
        if matches >= 1:
            trending_ids.add(a["id"])

    return trending_ids

# ── Scoring ───────────────────────────────────────────────────────────────────

def _score_items(items: list[dict]) -> list[dict]:
    trending_ids = _find_trending(items)

    for item in items:
        text         = f"{item['title']} {item['description']}"
        kw_score, kw = _keyword_score(text)
        rec_score    = _recency_score(item["published"])
        src_weight   = SOURCE_WEIGHTS.get(item["source_id"], 1.0)
        trend_bonus  = 2.5 if item["id"] in trending_ids else 0.0

        item["score"]         = round((rec_score + kw_score) * src_weight + trend_bonus, 2)
        item["keywords"]      = kw
        item["topics"]        = _detect_topics(text)
        item["is_trending"]   = item["id"] in trending_ids

    items.sort(key=lambda x: x["score"], reverse=True)
    return items

# ── RSS parser ────────────────────────────────────────────────────────────────


def _parse_rss(xml_text: str, source: dict) -> list[dict]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []

    items_out = []
    is_atom   = "atom" in root.tag or root.tag == f"{{{NS['atom']}}}feed"

    if is_atom:
        entries = root.findall(f"{{{NS['atom']}}}entry")
        for entry in entries[:NEWS_MAX_ITEMS_PER_SOURCE]:
            title = (entry.findtext(f"{{{NS['atom']}}}title") or "").strip()

            link = ""
            for lel in entry.findall(f"{{{NS['atom']}}}link"):
                if lel.get("rel", "alternate") == "alternate":
                    link = lel.get("href", "")
                    break
            if not link:
                lel = entry.find(f"{{{NS['atom']}}}link")
                if lel is not None:
                    link = lel.get("href", "")

            pub_raw = (
                entry.findtext(f"{{{NS['atom']}}}published") or
                entry.findtext(f"{{{NS['atom']}}}updated") or ""
            )
            published  = _parse_date(pub_raw)
            content_el = entry.find(f"{{{NS['atom']}}}content")
            summary_el = entry.find(f"{{{NS['atom']}}}summary")
            desc_html  = ""
            if content_el is not None:
                desc_html = content_el.text or ""
            elif summary_el is not None:
                desc_html = summary_el.text or ""

            desc_clean = re.sub(r"<[^>]+>", "", desc_html).strip()[:400]
            thumbnail  = _extract_image(entry, desc_html)
            items_out.append(_make_item(source, title, link, published, desc_clean, thumbnail))

    else:
        channel = root.find("channel")
        if channel is None:
            channel = root
        for item in channel.findall("item")[:NEWS_MAX_ITEMS_PER_SOURCE]:
            title     = (item.findtext("title") or "").strip()
            link      = (item.findtext("link")  or "").strip()
            pub_raw   = (
                item.findtext("pubDate") or
                item.findtext(f"{{{NS['dc']}}}date") or ""
            )
            published  = _parse_date(pub_raw)
            desc_html  = (
                item.findtext(f"{{{NS['content']}}}encoded") or
                item.findtext("description") or ""
            )
            desc_clean = re.sub(r"<[^>]+>", "", desc_html).strip()[:400]
            thumbnail  = _extract_image(item, desc_html)
            items_out.append(_make_item(source, title, link, published, desc_clean, thumbnail))

    return items_out


def _make_item(source: dict, title: str, link: str, published: str,
               description: str, thumbnail: str) -> dict:
    return {
        "platform":    "news",
        "id":          link,
        "title":       title,
        "author":      source["name"],
        "avatar":      "",
        "thumbnail":   thumbnail,
        "url":         link,
        "published":   published,
        "description": description,
        "source_id":   source["id"],
        "source_name": source["name"],
        "category":    source["category"],
        # filled by _score_items
        "score":       0.0,
        "keywords":    [],
        "topics":      [],
        "is_trending": False,
    }

# ── Fetch one source ──────────────────────────────────────────────────────────

async def _fetch_source(source: dict, client: httpx.AsyncClient) -> list[dict]:
    try:
        r = await client.get(
            source["url"], headers=HEADERS, timeout=12, follow_redirects=True,
        )
        if r.status_code != 200:
            print(f"[news] {source['id']} returned {r.status_code}")
            return []
        return _parse_rss(r.text, source)
    except Exception as e:
        print(f"[news] {source['id']} error: {e}")
        return []
    