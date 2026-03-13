# backend/src/main.py

import webbrowser
import asyncio
import httpx

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse, Response

from src import youtube
from src import x_scraper
from src import telegram
from src import reddit
from config import HOST, PORT, CLIENT_SECRET_FILE, FOLLOWING_FILE, DATA_DIR

app = FastAPI(title="infosec-feed")

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  
    allow_methods=["GET", "DELETE"],
    allow_headers=["*"],
)

# ── Feed ──────────────────────────────────────────────────────────────────────

@app.get("/api/feed")
async def get_feed(platform: str = Query(default="all")):

    yt_result = {"error": None, "items": []}
    x_result  = {"error": None, "items": []}
    tg_result = {"error": None, "items": []}
    rd_result = {"error": None, "items": []}

    if platform in ("all", "youtube"):
        yt_result = await asyncio.to_thread(youtube.fetch_feed)

    if platform in ("all", "x"):
        x_result = await x_scraper.fetch_feed()

    if platform in ("all", "telegram"):
        tg_result = await telegram.fetch_feed()

    if platform in ("all", "reddit"):
        rd_result = await reddit.fetch_feed()

    items = yt_result["items"] + x_result["items"] + tg_result["items"] + rd_result["items"]
    items.sort(key=lambda i: i["published"], reverse=True)

    return {
        "items": items,
        "meta": {
            "youtube":  {"error": yt_result.get("error"),  "from_cache": yt_result.get("from_cache")},
            "x":        {"error": x_result.get("error"),   "from_cache": x_result.get("from_cache")},
            "telegram": {"error": tg_result.get("error"),  "from_cache": tg_result.get("from_cache")},
            "reddit":   {"error": rd_result.get("error"),  "from_cache": rd_result.get("from_cache")},
        },
    }


# ── Telegram Channels ─────────────────────────────────────────────────────────

@app.get("/api/telegram/channels")
async def get_telegram_channels():

    result   = await telegram.fetch_feed()
    channels = telegram.get_channels_summary(result["items"])
    return {
        "channels":   channels,
        "error":      result.get("error"),
        "from_cache": result.get("from_cache"),
    }


@app.get("/api/telegram/channel/{channel_id:path}")
async def get_telegram_channel_messages(channel_id: str):
    result   = await telegram.fetch_feed()
    messages = [i for i in result["items"] if i["channel_id"] == channel_id]
    return {
        "messages": messages,
        "error":    result.get("error"),
    }


@app.get("/api/proxy/image")
async def proxy_image(url: str = Query(...)):
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers={"Referer": "https://t.me"}, timeout=10)
    return Response(content=r.content, media_type=r.headers.get("content-type", "image/jpeg"))

# ── Status ────────────────────────────────────────────────────────────────────

@app.get("/api/status")
def get_status():

    return {
        "youtube": {
            "authenticated":  youtube.is_authenticated(),
            "has_client_secret": CLIENT_SECRET_FILE.exists(),
        },
        "x": {
            "has_following_file": FOLLOWING_FILE.exists(),
            "handle_count": len(x_scraper.load_handles()),
        },
    }


# ── YouTube OAuth ─────────────────────────────────────────────────────────────


REDIRECT_URI = "http://localhost:8000/auth/youtube/callback"

@app.get("/auth/youtube")
def youtube_auth():

    if not CLIENT_SECRET_FILE.exists():
        return JSONResponse(
            {"error": "client_secret.json not found"},
            status_code=400,
        )
    
    flow = youtube.build_auth_flow(REDIRECT_URI)
    auth_url, state = youtube.get_auth_url(flow)
    youtube._flow_store[state] = flow   

    return RedirectResponse(auth_url)


@app.get("/auth/youtube/callback")
def youtube_callback(code: str = Query(...), state: str = Query(...)):

    youtube.save_token_from_code(code, REDIRECT_URI, state)
    return RedirectResponse("http://localhost:5173")


# ── Open in browser ───────────────────────────────────────────────────────────

@app.get("/api/open")
def open_url(url: str = Query(...)):

    webbrowser.open(url)
    return {"ok": True}


# ── Cache ─────────────────────────────────────────────────────────────────────

@app.delete("/api/cache")
def clear_cache():

    cleared = []

    for cache_file in [
        DATA_DIR / "yt_cache.json",
        DATA_DIR / "x_cache.json",
        DATA_DIR / "telegram_cache.json",
        DATA_DIR / "reddit_cache.json",
    ]:
        if cache_file.exists():
            cache_file.unlink()
            cleared.append(cache_file.name)

    return {"cleared": cleared}