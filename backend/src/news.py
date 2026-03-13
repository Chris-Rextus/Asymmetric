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
)

CACHE_FILE = DATA_DIR / "news_cache.json"

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
}

# ── Source weights ────────────────────────────────────────────────────────────

SOURCE_WEIGHTS: dict[str, float] = {
    # primary infosec — highest signal
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
    # government — very high signal
    "cisa":             2.0,
    "cisa_ics":         2.0,
    "nist_nvd":         1.9,
    "msrc":             1.8,
    "ncsc":             1.7,
    "enisa":            1.5,
    "fbi":              1.8,
    "austracyber":      1.4,
    # tech — medium signal
    "arstechnica":      1.3,
    "theregister":      1.3,
    "wired":            1.2,
    "zdnet":            1.1,
    "techcrunch":       1.0,
    "hackernews_yc":    1.1,
    "technologyreview": 1.2,
    "verge":            0.9,
    # mainstream — lower signal for infosec
    "reuters":          1.0,
    "bbc":              0.9,
    "guardian":         0.9,
    "ap":               0.9,
    "nyttech":          0.8,
    "wapotech":         0.8,
    "ft":               0.8,
}

# ── Keyword scoring tiers ─────────────────────────────────────────────────────

KEYWORDS_CRITICAL = [
    "zero-day", "0day", "rce", "remote code execution", "actively exploited",
    "critical vulnerability", "emergency patch", "nation-state", "ransomware attack",
    "data breach", "mass exploitation", "supply chain attack",
]

KEYWORDS_HIGH = [
    "vulnerability", "exploit", "malware", "backdoor", "apt", "breach",
    "ransomware", "phishing", "trojan", "botnet", "spyware", "rootkit",
    "cve-", "patch tuesday", "zero trust", "incident response",
]

KEYWORDS_MEDIUM = [
    "security", "attack", "threat", "advisory", "patch", "update", "hack",
    "leaked", "exposed", "stolen", "cyber", "infosec", "pentest", "ctf",
    "bug bounty", "disclosure", "authentication", "encryption",
]

# ── Cache ─────────────────────────────────────────────────────────────────────

def _load_cache() -> list | None:
    if not CACHE_FILE.exists():
        return None
    raw       = json.loads(CACHE_FILE.read_text())
    cached_at = datetime.fromisoformat(raw["cached_at"])
    age       = datetime.now(timezone.utc) - cached_at
    if age > timedelta(minutes=NEWS_CACHE_TTL_MINUTES):
        return None
    return raw["items"]


def _save_cache(items: list) -> None:
    CACHE_FILE.write_text(json.dumps({
        "cached_at": datetime.now(timezone.utc).isoformat(),
        "items":     items,
    }, indent=2))

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
        return 10.0 * math.exp(-0.03 * age_hours)
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
    
# ── Fetch all ─────────────────────────────────────────────────────────────────

async def _fetch_all() -> list[dict]:
    async with httpx.AsyncClient() as client:
        tasks   = [_fetch_source(s, client) for s in NEWS_SOURCES]
        results = await asyncio.gather(*tasks)

    items = [item for sublist in results for item in sublist]
    items = _score_items(items)
    return items

# ── Public fetch ──────────────────────────────────────────────────────────────

async def fetch_feed() -> dict:
    cached = _load_cache()
    if cached is not None:
        return {"error": None, "items": cached, "from_cache": True}
    try:
        items = await _fetch_all()
        _save_cache(items)
        return {"error": None, "items": items, "from_cache": False}
    except Exception as e:
        return {"error": str(e), "items": []}