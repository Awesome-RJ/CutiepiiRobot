"""
BSD 2-Clause License

Cutiepii Robot - Advanced Anime Module v2.0
Complete anime, manga, and character search with MyAnimeList integration
Powered by Jikan API v5 with caching and pagination
"""

import re
import asyncio
import json
import time
import html
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.error import TelegramError

from Cutiepii_Robot import LOGGER, REDIS, http
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd

import aiohttp

# ========================================
# Custom Jikan v4 Client
# ========================================

JIKAN_BASE_URL = "https://api.jikan.moe/v4"
ANILIST_URL = "https://graphql.anilist.co"
JIKAN_HEADERS = {
    "User-Agent": "CutiepiiRobot/2.0 (Telegram Bot)",
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",
}
# Jikan public API: max ~3 requests/second
JIKAN_MIN_INTERVAL = 0.4
RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


class AioJikan:
    def __init__(self):
        self.session = None
        self._lock = asyncio.Lock()
        self._last_request = 0.0

    async def _get_session(self):
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=25)
            self.session = aiohttp.ClientSession(headers=JIKAN_HEADERS, timeout=timeout)
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def _throttle(self):
        async with self._lock:
            now = time.monotonic()
            wait = JIKAN_MIN_INTERVAL - (now - self._last_request)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request = time.monotonic()

    async def _request(self, endpoint: str, params: Optional[dict] = None) -> dict:
        await self._throttle()
        session = await self._get_session()
        url = f"{JIKAN_BASE_URL}/{endpoint.lstrip('/')}"
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                return await resp.json(content_type=None)
            body = await resp.text()
            raise Exception(f"HTTP {resp.status}: {body[:120]}")

    async def search(self, search_type: str, query: str, page: int = 1) -> dict:
        return await self._request(search_type, {"q": query, "page": page})

    async def anime(self, anime_id: int, extension: Optional[str] = None) -> dict:
        endpoint = f"anime/{anime_id}"
        if extension:
            endpoint += f"/{extension}"
        return await self._request(endpoint)

    async def manga(self, manga_id: int, extension: Optional[str] = None) -> dict:
        endpoint = f"manga/{manga_id}"
        if extension:
            endpoint += f"/{extension}"
        return await self._request(endpoint)

    async def character(self, char_id: int) -> dict:
        return await self._request(f"characters/{char_id}")

    async def top(self, top_type: str, page: int = 1) -> dict:
        return await self._request(f"top/{top_type}", {"page": page})

    async def season(self, year: int, season: str) -> dict:
        return await self._request(f"seasons/{year}/{season}")


# Initialize async Jikan client
jikan = AioJikan()


def _is_retryable_error(exc: Exception) -> bool:
    err_str = str(exc).lower()
    return any(
        token in err_str
        for token in (
            "429", "500", "502", "503", "504",
            "timeout", "timed out", "mimetype", "octet-stream",
            "contenttype", "rate limit", "gateway",
        )
    )


async def jikan_call(func, *args, max_attempts: int = 6, **kwargs):
    """Retry Jikan calls with backoff for transient/rate-limit errors."""
    last_error = None
    for attempt in range(max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if _is_retryable_error(e) and attempt < max_attempts - 1:
                await asyncio.sleep(min(2 ** attempt, 8))
                continue
            raise e
    raise last_error


# Skip Jikan for a while after repeated upstream failures (504/timeout).
_jikan_down_until = 0.0
JIKAN_COOLDOWN_SECONDS = 900


def is_jikan_available() -> bool:
    return time.monotonic() >= _jikan_down_until


def mark_jikan_unavailable() -> None:
    global _jikan_down_until
    if time.monotonic() >= _jikan_down_until:
        LOGGER.info(
            "Jikan API is unavailable — using AniList for searches. "
            f"Will retry Jikan in {JIKAN_COOLDOWN_SECONDS // 60} minutes."
        )
    _jikan_down_until = time.monotonic() + JIKAN_COOLDOWN_SECONDS


# ========================================
# AniList fallback (used when Jikan is down/slow)
# ========================================

ANILIST_ANIME_SEARCH = """
query ($search: String) {
  Page(perPage: 1) {
    media(search: $search, type: ANIME) {
      id idMal
      title { romaji english native }
      episodes status format averageScore
      description(asHtml: false)
      genres
      bannerImage coverImage { extraLarge large medium }
      siteUrl
      startDate { year month day }
      endDate { year month day }
      duration
      trailer { id site }
      studios(isMain: true) { nodes { name } }
    }
  }
}
"""

ANILIST_MANGA_SEARCH = """
query ($search: String) {
  Page(perPage: 1) {
    media(search: $search, type: MANGA) {
      id idMal
      title { romaji english native }
      chapters volumes status format averageScore
      description(asHtml: false)
      genres
      bannerImage coverImage { extraLarge large medium }
      siteUrl
      startDate { year month day }
      endDate { year month day }
    }
  }
}
"""

ANILIST_CHARACTER_SEARCH = """
query ($search: String) {
  Page(perPage: 1) {
    characters(search: $search) {
      id idMal
      name { full native alternative }
      description(asHtml: false)
      image { large medium }
      siteUrl
      favourites
      media(perPage: 3, sort: POPULARITY_DESC) {
        nodes { title { romaji } type }
      }
    }
  }
}
"""


async def anilist_query(query: str, variables: dict) -> dict:
    response = await http.post(
        ANILIST_URL,
        json={"query": query, "variables": variables},
        timeout=30,
    )
    payload = response.json()
    if payload.get("errors"):
        raise Exception(payload["errors"][0].get("message", "AniList API error"))
    return payload.get("data", {})


def _strip_html(text: Optional[str]) -> str:
    if not text:
        return "No synopsis available."
    return re.sub(r"<[^>]+>", "", text).strip()


def _anilist_status(status: Optional[str]) -> str:
    mapping = {
        "FINISHED": "Finished Airing",
        "RELEASING": "Currently Airing",
        "NOT_YET_RELEASED": "Not yet aired",
        "CANCELLED": "Cancelled",
        "HIATUS": "On Hiatus",
    }
    return mapping.get(status or "", status or "Unknown")


def _anilist_image(media: dict) -> Optional[str]:
    cover = media.get("coverImage") or {}
    return (
        media.get("bannerImage")
        or cover.get("extraLarge")
        or cover.get("large")
        or cover.get("medium")
    )


def anilist_anime_to_jikan(media: dict) -> dict:
    title = media.get("title") or {}
    studios = [s.get("name", "") for s in (media.get("studios") or {}).get("nodes", []) if s.get("name")]
    start = media.get("startDate") or {}
    end = media.get("endDate") or {}
    aired_parts = [p for p in (start.get("year"), end.get("year")) if p]
    trailer = media.get("trailer") or {}
    trailer_url = None
    if trailer.get("site") == "youtube" and trailer.get("id"):
        trailer_url = f"https://youtu.be/{trailer['id']}"

    mal_id = media.get("idMal")
    return {
        "mal_id": mal_id or 0,
        "title": title.get("romaji") or title.get("english") or "Unknown",
        "title_english": title.get("english") or title.get("romaji"),
        "title_japanese": title.get("native") or "",
        "type": media.get("format") or "Unknown",
        "episodes": media.get("episodes"),
        "status": _anilist_status(media.get("status")),
        "score": (media.get("averageScore") or 0) / 10 if media.get("averageScore") else "N/A",
        "rank": "N/A",
        "popularity": "N/A",
        "members": "N/A",
        "genres": [{"name": g} for g in media.get("genres") or []],
        "studios": [{"name": s} for s in studios],
        "aired": {"string": " - ".join(str(y) for y in aired_parts) or "Unknown"},
        "duration": f"{media.get('duration') or '?'} min per ep" if media.get("duration") else "Unknown",
        "rating": "N/A",
        "synopsis": _strip_html(media.get("description")),
        "images": {
            "jpg": {
                "large_image_url": _anilist_image(media),
                "image_url": _anilist_image(media),
            }
        },
        "trailer": {"url": trailer_url} if trailer_url else {},
        "url": f"https://myanimelist.net/anime/{mal_id}" if mal_id else media.get("siteUrl"),
        "siteUrl": media.get("siteUrl"),
        "_source": "anilist",
    }


def anilist_manga_to_jikan(media: dict) -> dict:
    title = media.get("title") or {}
    start = media.get("startDate") or {}
    end = media.get("endDate") or {}
    published_parts = [p for p in (start.get("year"), end.get("year")) if p]
    mal_id = media.get("idMal")

    return {
        "mal_id": mal_id or 0,
        "title": title.get("romaji") or title.get("english") or "Unknown",
        "title_english": title.get("english") or title.get("romaji"),
        "title_japanese": title.get("native") or "",
        "type": media.get("format") or "Unknown",
        "chapters": media.get("chapters"),
        "volumes": media.get("volumes"),
        "status": _anilist_status(media.get("status")),
        "score": (media.get("averageScore") or 0) / 10 if media.get("averageScore") else "N/A",
        "rank": "N/A",
        "popularity": "N/A",
        "members": "N/A",
        "genres": [{"name": g} for g in media.get("genres") or []],
        "authors": [],
        "published": {"string": " - ".join(str(y) for y in published_parts) or "Unknown"},
        "synopsis": _strip_html(media.get("description")),
        "images": {
            "jpg": {
                "large_image_url": _anilist_image(media),
                "image_url": _anilist_image(media),
            }
        },
        "url": f"https://myanimelist.net/manga/{mal_id}" if mal_id else media.get("siteUrl"),
        "siteUrl": media.get("siteUrl"),
        "_source": "anilist",
    }


def anilist_character_to_jikan(character: dict) -> dict:
    name = character.get("name") or {}
    media_nodes = (character.get("media") or {}).get("nodes", [])
    mal_id = character.get("idMal")

    return {
        "mal_id": mal_id or 0,
        "name": name.get("full") or "Unknown",
        "name_kanji": name.get("native") or "",
        "about": _strip_html(character.get("description")),
        "favorites": character.get("favourites") or 0,
        "anime": [
            {"anime": {"title": (node.get("title") or {}).get("romaji", "")}}
            for node in media_nodes
            if (node.get("type") or "").upper() == "ANIME"
        ],
        "images": {
            "jpg": {
                "image_url": (character.get("image") or {}).get("large")
                or (character.get("image") or {}).get("medium"),
            }
        },
        "url": f"https://myanimelist.net/character/{mal_id}" if mal_id else character.get("siteUrl"),
        "siteUrl": character.get("siteUrl"),
        "_source": "anilist",
    }


async def fetch_anime_from_anilist(query: str) -> dict:
    data = await anilist_query(ANILIST_ANIME_SEARCH, {"search": query})
    media = ((data.get("Page") or {}).get("media") or [None])[0]
    if not media:
        raise Exception("No AniList results")
    return anilist_anime_to_jikan(media)


async def fetch_manga_from_anilist(query: str) -> dict:
    data = await anilist_query(ANILIST_MANGA_SEARCH, {"search": query})
    media = ((data.get("Page") or {}).get("media") or [None])[0]
    if not media:
        raise Exception("No AniList results")
    return anilist_manga_to_jikan(media)


async def fetch_character_from_anilist(query: str) -> dict:
    data = await anilist_query(ANILIST_CHARACTER_SEARCH, {"search": query})
    character = ((data.get("Page") or {}).get("characters") or [None])[0]
    if not character:
        raise Exception("No AniList results")
    return anilist_character_to_jikan(character)


async def fetch_jikan_search(search_type: str, query: str, page: int = 1) -> dict:
    return await jikan_call(jikan.search, search_type, query, page=page, max_attempts=2)


async def resolve_anime_details(query: str) -> Tuple[dict, dict, str]:
    """
    Returns (search_results, anime_full, source) where source is 'jikan' or 'anilist'.
    """
    cache_key = f"search_anime_{query.lower()}_1"
    cached_data = cache_get(cache_key)
    if cached_data:
        payload = json.loads(cached_data)
        if isinstance(payload, dict) and "anime_full" in payload:
            return payload["search_results"], payload["anime_full"], payload.get("source", "jikan")

    if is_jikan_available():
        try:
            search_results = await fetch_jikan_search("anime", query, page=1)
            if not search_results.get("data"):
                raise Exception("No Jikan results")

            anime_data = search_results["data"][0]
            anime_id = anime_data["mal_id"]
            anime_cache_key = f"anime_{anime_id}"
            cached_anime = cache_get(anime_cache_key)

            if cached_anime:
                anime_full = json.loads(cached_anime)
            elif anime_data.get("synopsis"):
                anime_full = anime_data
                cache_set(anime_cache_key, json.dumps(anime_full), ttl=3600)
            else:
                anime = await jikan_call(jikan.anime, anime_id)
                anime_full = anime.get("data", {})
                cache_set(anime_cache_key, json.dumps(anime_full), ttl=3600)

            payload = {
                "search_results": search_results,
                "anime_full": anime_full,
                "source": "jikan",
            }
            cache_set(cache_key, json.dumps(payload), ttl=1800)
            return search_results, anime_full, "jikan"
        except Exception as jikan_error:
            mark_jikan_unavailable()
            LOGGER.debug(f"Jikan anime search failed: {jikan_error}")

    anime_full = await fetch_anime_from_anilist(query)
    search_results = {"data": [anime_full]}
    payload = {
        "search_results": search_results,
        "anime_full": anime_full,
        "source": "anilist",
    }
    cache_set(cache_key, json.dumps(payload), ttl=900)
    return search_results, anime_full, "anilist"


async def resolve_manga_details(query: str) -> Tuple[dict, dict, str]:
    cache_key = f"search_manga_{query.lower()}_1"
    cached_data = cache_get(cache_key)
    if cached_data:
        payload = json.loads(cached_data)
        if isinstance(payload, dict) and "manga_full" in payload:
            return payload["search_results"], payload["manga_full"], payload.get("source", "jikan")

    if is_jikan_available():
        try:
            search_results = await fetch_jikan_search("manga", query, page=1)
            if not search_results.get("data"):
                raise Exception("No Jikan results")

            manga_data = search_results["data"][0]
            manga_id = manga_data["mal_id"]
            manga_cache_key = f"manga_{manga_id}"
            cached_manga = cache_get(manga_cache_key)

            if cached_manga:
                manga_full = json.loads(cached_manga)
            elif manga_data.get("synopsis"):
                manga_full = manga_data
                cache_set(manga_cache_key, json.dumps(manga_full), ttl=3600)
            else:
                manga = await jikan_call(jikan.manga, manga_id)
                manga_full = manga.get("data", {})
                cache_set(manga_cache_key, json.dumps(manga_full), ttl=3600)

            payload = {
                "search_results": search_results,
                "manga_full": manga_full,
                "source": "jikan",
            }
            cache_set(cache_key, json.dumps(payload), ttl=1800)
            return search_results, manga_full, "jikan"
        except Exception as jikan_error:
            mark_jikan_unavailable()
            LOGGER.debug(f"Jikan manga search failed: {jikan_error}")

    manga_full = await fetch_manga_from_anilist(query)
    search_results = {"data": [manga_full]}
    payload = {
        "search_results": search_results,
        "manga_full": manga_full,
        "source": "anilist",
    }
    cache_set(cache_key, json.dumps(payload), ttl=900)
    return search_results, manga_full, "anilist"


async def resolve_character_details(query: str) -> Tuple[dict, dict, str]:
    cache_key = f"search_char_{query.lower()}_1"
    cached_data = cache_get(cache_key)
    if cached_data:
        payload = json.loads(cached_data)
        if isinstance(payload, dict) and "char_full" in payload:
            return payload["search_results"], payload["char_full"], payload.get("source", "jikan")

    if is_jikan_available():
        try:
            search_results = await fetch_jikan_search("characters", query, page=1)
            if not search_results.get("data"):
                raise Exception("No Jikan results")

            char_data = search_results["data"][0]
            char_id = char_data["mal_id"]
            char_cache_key = f"char_{char_id}"
            cached_char = cache_get(char_cache_key)

            if cached_char:
                char_full = json.loads(cached_char)
            else:
                character = await jikan_call(jikan.character, char_id)
                char_full = character.get("data", {})
                cache_set(char_cache_key, json.dumps(char_full), ttl=3600)

            payload = {
                "search_results": search_results,
                "char_full": char_full,
                "source": "jikan",
            }
            cache_set(cache_key, json.dumps(payload), ttl=1800)
            return search_results, char_full, "jikan"
        except Exception as jikan_error:
            mark_jikan_unavailable()
            LOGGER.debug(f"Jikan character search failed: {jikan_error}")

    char_full = await fetch_character_from_anilist(query)
    search_results = {"data": [char_full]}
    payload = {
        "search_results": search_results,
        "char_full": char_full,
        "source": "anilist",
    }
    cache_set(cache_key, json.dumps(payload), ttl=900)
    return search_results, char_full, "anilist"


# Cache settings (30 minutes for anime data)
CACHE_TTL = 1800

# Pagination settings
RESULTS_PER_PAGE = 5
MAX_SYNOPSIS_LENGTH = 600
MAX_ABOUT_LENGTH = 800
MAX_REVIEW_LENGTH = 200


# ========================================
# Cache Helper Functions
# ========================================

def cache_set(key: str, value: str, ttl: int = CACHE_TTL) -> bool:
    """Set cache value with TTL."""
    try:
        REDIS.setex(f"anime:{key}", ttl, value)
        return True
    except Exception as e:
        LOGGER.warning(f"Cache set failed: {e}")
        return False


def cache_get(key: str) -> Optional[str]:
    """Get cached value."""
    try:
        return REDIS.get(f"anime:{key}")
    except Exception as e:
        LOGGER.warning(f"Cache get failed: {e}")
        return None


def cache_delete(key: str) -> bool:
    """Delete cached value."""
    try:
        REDIS.delete(f"anime:{key}")
        return True
    except Exception as e:
        LOGGER.warning(f"Cache delete failed: {e}")
        return False


# ========================================
# Formatting Functions
# ========================================

async def format_anime_info(anime: Dict, short: bool = False) -> str:
    """
    Format anime information into a beautiful message.
    
    Args:
        anime: Anime data dictionary
        short: If True, return shortened version for lists
    """
    title = anime.get("title", "Unknown")
    title_english = anime.get("title_english") or anime.get("title")
    title_japanese = anime.get("title_japanese", "")
    
    type_ = anime.get("type", "Unknown")
    episodes = anime.get("episodes") or "?"
    status = anime.get("status", "Unknown")
    score = anime.get("score") or "N/A"
    ranked = anime.get("rank") or "N/A"
    popularity = anime.get("popularity") or "N/A"
    members = anime.get("members") or "N/A"
    
    if short:
        # Shortened format for search results
        text = f"<b>📺 {title_english}</b>\n"
        if title_japanese:
            text += f"<i>({title_japanese})</i>\n"
        text += f"⭐ {score}/10 | {type_} | {episodes} eps | {status}\n"
        return text
    
    # Full format
    # Genres
    genres = anime.get("genres", [])
    genre_names = ", ".join([g.get("name", "") for g in genres[:5]])
    
    # Studios
    studios = anime.get("studios", [])
    studio_names = ", ".join([s.get("name", "") for s in studios[:3]])
    
    # Aired
    aired = anime.get("aired", {})
    aired_str = aired.get("string", "Unknown")
    
    # Duration
    duration = anime.get("duration", "Unknown")
    
    # Rating
    rating = anime.get("rating", "Unknown")
    
    # Synopsis
    synopsis = anime.get("synopsis") or "No synopsis available."
    if len(synopsis) > MAX_SYNOPSIS_LENGTH:
        synopsis = synopsis[:MAX_SYNOPSIS_LENGTH-3] + "..."
    
    # Format message
    text = f"<b>📺 {title_english}</b>\n"
    if title_japanese:
        text += f"<i>({title_japanese})</i>\n\n"
    else:
        text += "\n"
    
    text += f"<b>Type:</b> {type_}\n"
    text += f"<b>Episodes:</b> {episodes}\n"
    text += f"<b>Status:</b> {status}\n"
    text += f"<b>Aired:</b> {aired_str}\n"
    text += f"<b>Duration:</b> {duration}\n"
    text += f"<b>Rating:</b> {rating}\n\n"
    
    text += f"<b>⭐ Score:</b> {score}/10\n"
    text += f"<b>📊 Ranked:</b> #{ranked}\n"
    text += f"<b>❤️ Popularity:</b> #{popularity}\n"
    if isinstance(members, int):
        text += f"<b>👥 Members:</b> {members:,}\n\n"
    else:
        text += f"<b>👥 Members:</b> {members}\n\n"
    
    if genre_names:
        text += f"<b>🎭 Genres:</b> {genre_names}\n"
    if studio_names:
        text += f"<b>🎬 Studios:</b> {studio_names}\n\n"
    
    text += f"<b>📝 Synopsis:</b>\n<i>{html.escape(synopsis)}</i>"
    
    return text


async def format_manga_info(manga: Dict, short: bool = False) -> str:
    """
    Format manga information into a beautiful message.
    
    Args:
        manga: Manga data dictionary
        short: If True, return shortened version
    """
    title = manga.get("title", "Unknown")
    title_english = manga.get("title_english") or manga.get("title")
    title_japanese = manga.get("title_japanese", "")
    
    type_ = manga.get("type", "Unknown")
    chapters = manga.get("chapters") or "?"
    volumes = manga.get("volumes") or "?"
    status = manga.get("status", "Unknown")
    score = manga.get("score") or "N/A"
    ranked = manga.get("rank") or "N/A"
    popularity = manga.get("popularity") or "N/A"
    members = manga.get("members") or "N/A"
    
    if short:
        # Shortened format
        text = f"<b>📖 {title_english}</b>\n"
        if title_japanese:
            text += f"<i>({title_japanese})</i>\n"
        text += f"⭐ {score}/10 | {type_} | {chapters} ch | {status}\n"
        return text
    
    # Full format
    # Genres
    genres = manga.get("genres", [])
    genre_names = ", ".join([g.get("name", "") for g in genres[:5]])
    
    # Authors
    authors = manga.get("authors", [])
    author_names = ", ".join([a.get("name", "") for a in authors[:3]])
    
    # Published
    published = manga.get("published", {})
    published_str = published.get("string", "Unknown")
    
    # Synopsis
    synopsis = manga.get("synopsis") or "No synopsis available."
    if len(synopsis) > MAX_SYNOPSIS_LENGTH:
        synopsis = synopsis[:MAX_SYNOPSIS_LENGTH-3] + "..."
    
    # Format message
    text = f"<b>📖 {title_english}</b>\n"
    if title_japanese:
        text += f"<i>({title_japanese})</i>\n\n"
    else:
        text += "\n"
    
    text += f"<b>Type:</b> {type_}\n"
    text += f"<b>Chapters:</b> {chapters}\n"
    text += f"<b>Volumes:</b> {volumes}\n"
    text += f"<b>Status:</b> {status}\n"
    text += f"<b>Published:</b> {published_str}\n\n"
    
    text += f"<b>⭐ Score:</b> {score}/10\n"
    text += f"<b>📊 Ranked:</b> #{ranked}\n"
    text += f"<b>❤️ Popularity:</b> #{popularity}\n"
    if isinstance(members, int):
        text += f"<b>👥 Members:</b> {members:,}\n\n"
    else:
        text += f"<b>👥 Members:</b> {members}\n\n"
    
    if genre_names:
        text += f"<b>🎭 Genres:</b> {genre_names}\n"
    if author_names:
        text += f"<b>✍️ Authors:</b> {author_names}\n\n"
    
    text += f"<b>📝 Synopsis:</b>\n<i>{html.escape(synopsis)}</i>"
    
    return text


async def format_character_info(character: Dict) -> str:
    """Format character information into a beautiful message."""
    name = character.get("name", "Unknown")
    name_kanji = character.get("name_kanji", "")
    
    about = character.get("about") or "No information available."
    # Clean up about text
    about = re.sub(r'\\n', '\n', about)
    about = re.sub(r'\r\n', '', about)
    if len(about) > MAX_ABOUT_LENGTH:
        about = about[:MAX_ABOUT_LENGTH-3] + "..."
    
    favorites = character.get("favorites") or "N/A"
    
    # Animeography
    anime_list = character.get("anime", [])
    top_anime = [a.get("anime", {}).get("title", "") for a in anime_list[:3]]
    
    # Format message
    text = f"<b>👤 {name}</b>\n"
    if name_kanji:
        text += f"<i>({name_kanji})</i>\n\n"
    else:
        text += "\n"
    
    text += f"<b>❤️ Favorites:</b> {favorites:,}\n\n" if isinstance(favorites, int) else f"<b>❤️ Favorites:</b> {favorites}\n\n"
    
    if top_anime:
        text += f"<b>📺 Featured In:</b>\n"
        for anime in top_anime:
            if anime:
                text += f"  - {anime}\n"
        text += "\n"
    
    text += f"<b>📝 About:</b>\n<i>{html.escape(about)}</i>"
    
    return text


# ========================================
# Button Creation Functions
# ========================================

def create_anime_buttons(anime_id: int, mal_url: str, trailer_url: Optional[str] = None, 
                         has_results: bool = False, query: str = "", page: int = 1,
                         jikan_buttons: bool = True, anilist_url: Optional[str] = None) -> InlineKeyboardMarkup:
    """Create inline keyboard for anime with all action buttons."""
    buttons = []
    
    # First row: MAL/AniList and Trailer
    row1 = []
    if mal_url:
        row1.append(InlineKeyboardButton("📖 View on MAL", url=mal_url))
    elif anilist_url:
        row1.append(InlineKeyboardButton("📖 View on AniList", url=anilist_url))
    if trailer_url:
        row1.append(InlineKeyboardButton("🎬 Trailer", url=trailer_url))
    if row1:
        buttons.append(row1)
    
    if jikan_buttons and anime_id:
        # Second row: Stats and Characters
        buttons.append([
            InlineKeyboardButton("📊 Statistics", callback_data=f"anime_stats_{anime_id}"),
            InlineKeyboardButton("👥 Characters", callback_data=f"anime_chars_{anime_id}")
        ])
        
        # Third row: Reviews and Recommendations
        buttons.append([
            InlineKeyboardButton("💬 Reviews", callback_data=f"anime_reviews_{anime_id}"),
            InlineKeyboardButton("✨ Recommendations", callback_data=f"anime_rec_{anime_id}")
        ])
        
        # Fourth row: Episodes and Full Synopsis
        buttons.append([
            InlineKeyboardButton("📺 Episodes", callback_data=f"anime_eps_{anime_id}"),
            InlineKeyboardButton("📄 Full Synopsis", callback_data=f"anime_synopsis_{anime_id}")
        ])
    
    # Fifth row: Navigation if search results exist
    if has_results and query:
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"anime_search_{query}_{page-1}"))
        nav_buttons.append(InlineKeyboardButton(f"📄 {page}", callback_data="noop"))
        nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"anime_search_{query}_{page+1}"))
        buttons.append(nav_buttons)
    
    # Sixth row: Share and Close
    buttons.append([
        InlineKeyboardButton("🔄 Share", switch_inline_query=f"anime {query}" if query else f"anime {anime_id}"),
        InlineKeyboardButton("❌ Close", callback_data="close_msg")
    ])
    
    return InlineKeyboardMarkup(buttons)


def create_manga_buttons(manga_id: int, mal_url: str, has_results: bool = False, 
                         query: str = "", page: int = 1, jikan_buttons: bool = True,
                         anilist_url: Optional[str] = None) -> InlineKeyboardMarkup:
    """Create inline keyboard for manga with all action buttons."""
    buttons = []
    
    # First row: MAL/AniList link
    if mal_url:
        buttons.append([InlineKeyboardButton("📖 View on MAL", url=mal_url)])
    elif anilist_url:
        buttons.append([InlineKeyboardButton("📖 View on AniList", url=anilist_url)])
    
    if jikan_buttons and manga_id:
        # Second row: Stats and Characters
        buttons.append([
            InlineKeyboardButton("📊 Statistics", callback_data=f"manga_stats_{manga_id}"),
            InlineKeyboardButton("👥 Characters", callback_data=f"manga_chars_{manga_id}")
        ])
        
        # Third row: Reviews and Recommendations
        buttons.append([
            InlineKeyboardButton("💬 Reviews", callback_data=f"manga_reviews_{manga_id}"),
            InlineKeyboardButton("✨ Recommendations", callback_data=f"manga_rec_{manga_id}")
        ])
        
        # Fourth row: Full Synopsis
        buttons.append([
            InlineKeyboardButton("📄 Full Synopsis", callback_data=f"manga_synopsis_{manga_id}")
        ])
    
    # Fifth row: Navigation if search results exist
    if has_results and query:
        nav_buttons = []
        if page > 1:
            nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"manga_search_{query}_{page-1}"))
        nav_buttons.append(InlineKeyboardButton(f"📄 {page}", callback_data="noop"))
        nav_buttons.append(InlineKeyboardButton("➡️ Next", callback_data=f"manga_search_{query}_{page+1}"))
        buttons.append(nav_buttons)
    
    # Sixth row: Share and Close
    buttons.append([
        InlineKeyboardButton("🔄 Share", switch_inline_query=f"manga {query}" if query else f"manga {manga_id}"),
        InlineKeyboardButton("❌ Close", callback_data="close_msg")
    ])
    
    return InlineKeyboardMarkup(buttons)


def create_character_buttons(char_id: int, mal_url: str, jikan_buttons: bool = True,
                             anilist_url: Optional[str] = None) -> InlineKeyboardMarkup:
    """Create inline keyboard for character with all action buttons."""
    buttons = []
    
    # First row: MAL/AniList link
    if mal_url:
        buttons.append([InlineKeyboardButton("📖 View on MAL", url=mal_url)])
    elif anilist_url:
        buttons.append([InlineKeyboardButton("📖 View on AniList", url=anilist_url)])
    
    if jikan_buttons and char_id:
        # Second row: Related content
        buttons.append([
            InlineKeyboardButton("📺 Animeography", callback_data=f"char_anime_{char_id}"),
            InlineKeyboardButton("📖 Mangaography", callback_data=f"char_manga_{char_id}")
        ])
        
        # Third row: Voice actors and Pictures
        buttons.append([
            InlineKeyboardButton("🎤 Voice Actors", callback_data=f"char_va_{char_id}"),
            InlineKeyboardButton("🖼️ Pictures", callback_data=f"char_pics_{char_id}")
        ])
    
    # Fourth row: Share and Close
    buttons.append([
        InlineKeyboardButton("🔄 Share", switch_inline_query=f"character {char_id}"),
        InlineKeyboardButton("❌ Close", callback_data="close_msg")
    ])
    
    return InlineKeyboardMarkup(buttons)


def create_list_buttons(current_page: int = 1, max_page: int = 1, 
                        list_type: str = "anime") -> InlineKeyboardMarkup:
    """Create pagination buttons for top lists."""
    buttons = []
    
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", 
                                               callback_data=f"top_{list_type}_{current_page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"📄 {current_page}/{max_page}", callback_data="noop"))
    if current_page < max_page:
        nav_buttons.append(InlineKeyboardButton("➡️ Next", 
                                               callback_data=f"top_{list_type}_{current_page+1}"))
    
    buttons.append(nav_buttons)
    buttons.append([
        InlineKeyboardButton("🔄 Refresh", callback_data=f"top_{list_type}_{current_page}_refresh"),
        InlineKeyboardButton("❌ Close", callback_data="close_msg")
    ])
    
    return InlineKeyboardMarkup(buttons)


# ========================================
# Search Commands
# ========================================

@cutiepii_cmd(command="anime")
async def anime_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Search for anime on MyAnimeList with pagination.
    Usage: /anime <anime name>
    """
    message = update.effective_message
    args = context.args
    
    if not args:
        # Show help with inline keyboard
        help_buttons = [
            [InlineKeyboardButton("🔍 Example: Naruto", callback_data="noop")],
            [InlineKeyboardButton("🏆 Top Anime", callback_data="top_anime_1")],
            [InlineKeyboardButton("📺 Airing Now", callback_data="airing_now")],
            [InlineKeyboardButton("❌ Close", callback_data="close_msg")]
        ]
        await message.reply_text(
            "<b>🔍 Anime Search</b>\n\n"
            "Search for any anime on MyAnimeList!\n\n"
            "<b>Usage:</b>\n"
            "<code>/anime Naruto</code>\n"
            "<code>/anime Death Note</code>\n\n"
            "<b>Features:</b>\n"
            "- Full anime information\n"
            "- Ratings and rankings\n"
            "- Character lists\n"
            "- Reviews & recommendations\n"
            "- Episode information\n"
            "- Direct MAL links\n\n"
            "<i>Try the buttons below!</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(help_buttons)
        )
        return
    
    query = " ".join(args)
    search_msg = await message.reply_text(f"🔍 Searching for '<b>{query}</b>'...", parse_mode=ParseMode.HTML)
    
    try:
        search_results, anime_full, source = await resolve_anime_details(query)

        if not search_results.get("data"):
            buttons = [[InlineKeyboardButton("🔍 Try Different Name", callback_data="noop")]]
            await search_msg.edit_text(
                "❌ <b>No results found!</b>\n\n"
                "Try:\n"
                "- Checking spelling\n"
                "- Using English name\n"
                "- Using Japanese name\n"
                "- Searching partial name",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return

        anime_id = anime_full.get("mal_id") or 0
        text = await format_anime_info(anime_full)
        if source == "anilist":
            text += "\n\n<i>Data via AniList (Jikan API unavailable)</i>"

        images = anime_full.get("images", {})
        image_url = images.get("jpg", {}).get("large_image_url") or images.get("jpg", {}).get("image_url")
        trailer_url = (anime_full.get("trailer") or {}).get("url")
        mal_url = anime_full.get("url") if anime_id else None
        anilist_url = anime_full.get("siteUrl")
        has_more_results = len(search_results.get("data", [])) > 1
        keyboard = create_anime_buttons(
            anime_id,
            mal_url,
            trailer_url,
            has_more_results,
            query,
            1,
            jikan_buttons=source == "jikan" and bool(anime_id),
            anilist_url=anilist_url,
        )

        await search_msg.delete()

        if image_url:
            await message.reply_photo(
                photo=image_url,
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        else:
            await message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )

    except Exception as e:
        LOGGER.error(f"Error in anime_search: {e}")
        error_buttons = [[InlineKeyboardButton("🔄 Try Again", callback_data="noop")]]
        await search_msg.edit_text(
            "❌ <b>An error occurred!</b>\n\n"
            "The anime API may be temporarily down.\n"
            "Please try again in a moment.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(error_buttons)
        )


@cutiepii_cmd(command="manga")
async def manga_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Search for manga on MyAnimeList with pagination.
    Usage: /manga <manga name>
    """
    message = update.effective_message
    args = context.args
    
    if not args:
        # Show help with inline keyboard
        help_buttons = [
            [InlineKeyboardButton("🔍 Example: One Piece", callback_data="noop")],
            [InlineKeyboardButton("🏆 Top Manga", callback_data="top_manga_1")],
            [InlineKeyboardButton("❌ Close", callback_data="close_msg")]
        ]
        await message.reply_text(
            "<b>🔍 Manga Search</b>\n\n"
            "Search for any manga on MyAnimeList!\n\n"
            "<b>Usage:</b>\n"
            "<code>/manga One Piece</code>\n"
            "<code>/manga Naruto</code>\n\n"
            "<b>Features:</b>\n"
            "- Full manga information\n"
            "- Ratings and rankings\n"
            "- Character lists\n"
            "- Reviews & recommendations\n"
            "- Author information\n"
            "- Direct MAL links\n\n"
            "<i>Try the buttons below!</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(help_buttons)
        )
        return
    
    query = " ".join(args)
    search_msg = await message.reply_text(f"🔍 Searching for '<b>{query}</b>'...", parse_mode=ParseMode.HTML)
    
    try:
        search_results, manga_full, source = await resolve_manga_details(query)

        if not search_results.get("data"):
            buttons = [[InlineKeyboardButton("🔍 Try Different Name", callback_data="noop")]]
            await search_msg.edit_text(
                "❌ <b>No results found!</b>\n\n"
                "Try checking the spelling or using a different name.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return

        manga_id = manga_full.get("mal_id") or 0
        text = await format_manga_info(manga_full)
        if source == "anilist":
            text += "\n\n<i>Data via AniList (Jikan API unavailable)</i>"

        images = manga_full.get("images", {})
        image_url = images.get("jpg", {}).get("large_image_url") or images.get("jpg", {}).get("image_url")
        mal_url = manga_full.get("url") if manga_id else None
        anilist_url = manga_full.get("siteUrl")
        has_more_results = len(search_results.get("data", [])) > 1
        keyboard = create_manga_buttons(
            manga_id,
            mal_url,
            has_more_results,
            query,
            1,
            jikan_buttons=source == "jikan" and bool(manga_id),
            anilist_url=anilist_url,
        )

        await search_msg.delete()

        if image_url:
            await message.reply_photo(
                photo=image_url,
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        else:
            await message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )

    except Exception as e:
        LOGGER.error(f"Error in manga_search: {e}")
        error_buttons = [[InlineKeyboardButton("🔄 Try Again", callback_data="noop")]]
        await search_msg.edit_text(
            "❌ <b>An error occurred!</b>\n\nThe manga API may be temporarily down.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(error_buttons)
        )


@cutiepii_cmd(command="character")
async def character_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Search for anime/manga character with enhanced features.
    Usage: /character <character name>
    """
    message = update.effective_message
    args = context.args
    
    if not args:
        # Show help with inline keyboard
        help_buttons = [
            [InlineKeyboardButton("🔍 Example: Naruto Uzumaki", callback_data="noop")],
            [InlineKeyboardButton("❌ Close", callback_data="close_msg")]
        ]
        await message.reply_text(
            "<b>🔍 Character Search</b>\n\n"
            "Search for anime/manga characters!\n\n"
            "<b>Usage:</b>\n"
            "<code>/character Naruto Uzumaki</code>\n"
            "<code>/character Luffy</code>\n\n"
            "<b>Features:</b>\n"
            "- Full character bio\n"
            "- Animeography & Mangaography\n"
            "- Voice actors\n"
            "- Character pictures\n"
            "- Favorites count\n\n"
            "<i>Try searching for your favorite character!</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(help_buttons)
        )
        return
    
    query = " ".join(args)
    search_msg = await message.reply_text(f"🔍 Searching for '<b>{query}</b>'...", parse_mode=ParseMode.HTML)
    
    try:
        search_results, char_full, source = await resolve_character_details(query)

        if not search_results.get("data"):
            buttons = [[InlineKeyboardButton("🔍 Try Different Name", callback_data="noop")]]
            await search_msg.edit_text(
                "❌ <b>No results found!</b>\n\n"
                "Try checking the spelling or using full name.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return

        char_id = char_full.get("mal_id") or 0
        text = await format_character_info(char_full)
        if source == "anilist":
            text += "\n\n<i>Data via AniList (Jikan API unavailable)</i>"

        images = char_full.get("images", {})
        image_url = images.get("jpg", {}).get("image_url")
        mal_url = char_full.get("url") if char_id else None
        anilist_url = char_full.get("siteUrl")
        keyboard = create_character_buttons(
            char_id,
            mal_url,
            jikan_buttons=source == "jikan" and bool(char_id),
            anilist_url=anilist_url,
        )

        await search_msg.delete()
        
        if image_url:
            await message.reply_photo(
                photo=image_url,
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        else:
            await message.reply_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
    
    except Exception as e:
        LOGGER.error(f"Error in character_search: {e}")
        error_buttons = [[InlineKeyboardButton("🔄 Try Again", callback_data="noop")]]
        await search_msg.edit_text(
            "❌ <b>An error occurred!</b>\n\nPlease try again in a moment.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(error_buttons)
        )


# ========================================
# Top Lists Commands
# ========================================

@cutiepii_cmd(command="topanime")
async def top_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get top anime from MyAnimeList with pagination."""
    message = update.effective_message
    
    loading_msg = await message.reply_text("⏳ Fetching top anime...")
    
    try:
        # Check cache
        cache_key = "top_anime_1"
        cached_data = cache_get(cache_key)
        
        if cached_data:
            top = json.loads(cached_data)
        else:
            # Get top anime
            top = await jikan_call(jikan.top, "anime", page=1)
            cache_set(cache_key, json.dumps(top), ttl=3600)
        
        anime_list = top.get("data", [])[:10]
        
        if not anime_list:
            await loading_msg.edit_text("❌ Couldn't fetch top anime!")
            return
        
        text = "<b>🏆 Top 10 Anime on MyAnimeList</b>\n\n"
        
        for idx, anime in enumerate(anime_list, 1):
            title = anime.get("title", "Unknown")
            score = anime.get("score", "N/A")
            type_ = anime.get("type", "")
            episodes = anime.get("episodes") or "?"
            mal_id = anime.get("mal_id", 0)
            
            text += f"<b>{idx}. {title}</b>\n"
            text += f"   ⭐ {score}/10 | {type_} | {episodes} eps\n"
            text += f"   /anime{mal_id}\n\n"
        
        text += "\n<i>💡 Tip: Click command or use pagination!</i>"
        
        # Create pagination buttons
        keyboard = create_list_buttons(1, 5, "anime")
        
        await loading_msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    
    except Exception as e:
        LOGGER.error(f"Error in top_anime: {e}")
        await loading_msg.edit_text("❌ An error occurred!")


@cutiepii_cmd(command="topmanga")
async def top_manga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get top manga from MyAnimeList with pagination."""
    message = update.effective_message
    
    loading_msg = await message.reply_text("⏳ Fetching top manga...")
    
    try:
        # Check cache
        cache_key = "top_manga_1"
        cached_data = cache_get(cache_key)
        
        if cached_data:
            top = json.loads(cached_data)
        else:
            # Get top manga
            top = await jikan_call(jikan.top, "manga", page=1)
            cache_set(cache_key, json.dumps(top), ttl=3600)
        
        manga_list = top.get("data", [])[:10]
        
        if not manga_list:
            await loading_msg.edit_text("❌ Couldn't fetch top manga!")
            return
        
        text = "<b>🏆 Top 10 Manga on MyAnimeList</b>\n\n"
        
        for idx, manga in enumerate(manga_list, 1):
            title = manga.get("title", "Unknown")
            score = manga.get("score", "N/A")
            type_ = manga.get("type", "")
            mal_id = manga.get("mal_id", 0)
            
            text += f"<b>{idx}. {title}</b>\n"
            text += f"   ⭐ {score}/10 | {type_}\n"
            text += f"   /manga{mal_id}\n\n"
        
        text += "\n<i>💡 Tip: Click command or use pagination!</i>"
        
        # Create pagination buttons
        keyboard = create_list_buttons(1, 5, "manga")
        
        await loading_msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)
    
    except Exception as e:
        LOGGER.error(f"Error in top_manga: {e}")
        await loading_msg.edit_text("❌ An error occurred!")


@cutiepii_cmd(command="airing")
async def current_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get currently airing anime with enhanced buttons."""
    message = update.effective_message
    
    loading_msg = await message.reply_text("⏳ Fetching current season anime...")
    
    try:
        # Get current season
        now = datetime.now()
        year = now.year
        
        # Determine season
        month = now.month
        if month in [1, 2, 3]:
            season = "winter"
        elif month in [4, 5, 6]:
            season = "spring"
        elif month in [7, 8, 9]:
            season = "summer"
        else:
            season = "fall"
        
        # Check cache
        cache_key = f"season_{year}_{season}"
        cached_data = cache_get(cache_key)
        
        if cached_data:
            seasonal = json.loads(cached_data)
        else:
            # Get seasonal anime
            seasonal = await jikan_call(jikan.season, year, season)
            cache_set(cache_key, json.dumps(seasonal), ttl=7200)
        
        anime_list = seasonal.get("data", [])[:15]
        
        if not anime_list:
            await loading_msg.edit_text("❌ Couldn't fetch seasonal anime!")
            return
        
        text = f"<b>📺 Currently Airing - {season.capitalize()} {year}</b>\n\n"
        
        for idx, anime in enumerate(anime_list, 1):
            title = anime.get("title", "Unknown")
            score = anime.get("score") or "N/A"
            type_ = anime.get("type", "")
            mal_id = anime.get("mal_id", 0)
            
            text += f"{idx}. <b>{title}</b>\n"
            text += f"   {type_} | ⭐ {score}\n"
            text += f"   /anime{mal_id}\n\n"
            
            if len(text) > 3500:
                break
        
        text += "\n<i>💡 Tip: Click commands to view details!</i>"
        
        # Create buttons
        buttons = [
            [InlineKeyboardButton("🔄 Refresh", callback_data="airing_now")],
            [InlineKeyboardButton("🏆 Top This Season", callback_data=f"top_season_{year}_{season}")],
            [InlineKeyboardButton("❌ Close", callback_data="close_msg")]
        ]
        
        await loading_msg.edit_text(text, parse_mode=ParseMode.HTML, 
                                   disable_web_page_preview=True,
                                   reply_markup=InlineKeyboardMarkup(buttons))
    
    except Exception as e:
        LOGGER.error(f"Error in current_season: {e}")
        await loading_msg.edit_text("❌ An error occurred!")


# ========================================
# Callback Query Handler
# ========================================

@cutiepii_callback(pattern=r"^(anime|manga|char|top|airing|close|noop).*")
async def anime_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle anime-related callback queries with enhanced features."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    try:
        # Close message handler
        if data == "close_msg":
            await query.message.delete()
            return
        
        # No-op handler
        if data == "noop":
            await query.answer("This button is for display only!", show_alert=False)
            return
        
        # Anime statistics
        if data.startswith("anime_stats_"):
            anime_id = int(data.split("_")[2])
            
            # Get anime stats
            stats = await jikan_call(jikan.anime, anime_id, extension="statistics")
            stats_data = stats.get("data", {})
            
            watching = stats_data.get("watching", 0)
            completed = stats_data.get("completed", 0)
            on_hold = stats_data.get("on_hold", 0)
            dropped = stats_data.get("dropped", 0)
            plan_to_watch = stats_data.get("plan_to_watch", 0)
            total = watching + completed + on_hold + dropped + plan_to_watch
            
            text = f"<b>📊 User Statistics</b>\n\n"
            text += f"👀 <b>Watching:</b> {watching:,} ({watching*100//total if total else 0}%)\n"
            text += f"✅ <b>Completed:</b> {completed:,} ({completed*100//total if total else 0}%)\n"
            text += f"⏸️ <b>On Hold:</b> {on_hold:,} ({on_hold*100//total if total else 0}%)\n"
            text += f"❌ <b>Dropped:</b> {dropped:,} ({dropped*100//total if total else 0}%)\n"
            text += f"📝 <b>Plan to Watch:</b> {plan_to_watch:,} ({plan_to_watch*100//total if total else 0}%)\n\n"
            text += f"<b>Total Users:</b> {total:,}"
            
            buttons = [[InlineKeyboardButton("« Back", callback_data=f"anime_view_{anime_id}")]]
            
            await query.message.reply_text(text, parse_mode=ParseMode.HTML,
                                          reply_markup=InlineKeyboardMarkup(buttons))
        
        # Anime characters
        elif data.startswith("anime_chars_"):
            anime_id = int(data.split("_")[2])
            
            # Get characters
            chars = await jikan_call(jikan.anime, anime_id, extension="characters")
            char_list = chars.get("data", [])[:10]
            
            if not char_list:
                await query.message.reply_text("No characters available!")
                return
            
            text = "<b>👥 Main Characters</b>\n\n"
            
            for char in char_list:
                char_data = char.get("character", {})
                name = char_data.get("name", "Unknown")
                role = char.get("role", "Unknown")
                mal_id = char_data.get("mal_id", 0)
                
                text += f"- <b>{name}</b>\n"
                text += f"  Role: {role}\n"
                text += f"  /character{mal_id}\n\n"
            
            buttons = [[InlineKeyboardButton("« Back", callback_data=f"anime_view_{anime_id}")]]
            
            await query.message.reply_text(text, parse_mode=ParseMode.HTML,
                                          reply_markup=InlineKeyboardMarkup(buttons))
        
        # Anime reviews
        elif data.startswith("anime_reviews_"):
            anime_id = int(data.split("_")[2])
            
            # Get reviews
            reviews = await jikan_call(jikan.anime, anime_id, extension="reviews")
            review_list = reviews.get("data", [])[:3]
            
            if not review_list:
                await query.message.reply_text("No reviews available!")
                return
            
            text = "<b>💬 Top User Reviews</b>\n\n"
            
            for idx, review in enumerate(review_list, 1):
                user = review.get("user", {}).get("username", "Anonymous")
                score = review.get("score", "N/A")
                content = review.get("review", "")[:MAX_REVIEW_LENGTH]
                
                text += f"<b>{idx}. {user}</b> - ⭐ {score}/10\n"
                text += f"<i>{content}...</i>\n\n"
            
            buttons = [[InlineKeyboardButton("« Back", callback_data=f"anime_view_{anime_id}")]]
            
            await query.message.reply_text(text, parse_mode=ParseMode.HTML,
                                          reply_markup=InlineKeyboardMarkup(buttons))
        
        # Anime recommendations
        elif data.startswith("anime_rec_"):
            anime_id = int(data.split("_")[2])
            
            # Get recommendations
            recs = await jikan_call(jikan.anime, anime_id, extension="recommendations")
            rec_list = recs.get("data", [])[:10]
            
            if not rec_list:
                await query.message.reply_text("No recommendations available!")
                return
            
            text = "<b>✨ Recommended Anime</b>\n\n"
            
            for idx, rec in enumerate(rec_list, 1):
                entry = rec.get("entry", {})
                title = entry.get("title", "Unknown")
                mal_id = entry.get("mal_id", 0)
                votes = rec.get("votes", 0)
                
                text += f"{idx}. <b>{title}</b>\n"
                text += f"   👍 {votes} votes\n"
                text += f"   /anime{mal_id}\n\n"
            
            buttons = [[InlineKeyboardButton("« Back", callback_data=f"anime_view_{anime_id}")]]
            
            await query.message.reply_text(text, parse_mode=ParseMode.HTML,
                                          reply_markup=InlineKeyboardMarkup(buttons))
        
        # Anime episodes
        elif data.startswith("anime_eps_"):
            anime_id = int(data.split("_")[2])
            
            # Get episodes
            eps = await jikan_call(jikan.anime, anime_id, extension="episodes")
            ep_list = eps.get("data", [])[:10]
            
            if not ep_list:
                await query.message.reply_text("No episode information available!")
                return
            
            text = "<b>📺 Episodes</b>\n\n"
            
            for ep in ep_list:
                ep_num = ep.get("mal_id", "?")
                title = ep.get("title", "Unknown")
                aired = ep.get("aired", "N/A")
                
                text += f"<b>Episode {ep_num}:</b> {title}\n"
                if aired and aired != "N/A":
                    aired_date = aired.split("T")[0] if "T" in aired else aired
                    text += f"Aired: {aired_date}\n"
                text += "\n"
            
            buttons = [[InlineKeyboardButton("« Back", callback_data=f"anime_view_{anime_id}")]]
            
            await query.message.reply_text(text, parse_mode=ParseMode.HTML,
                                          reply_markup=InlineKeyboardMarkup(buttons))
        
        # Full synopsis
        elif data.startswith("anime_synopsis_"):
            anime_id = int(data.split("_")[2])
            
            # Get anime data
            cache_key = f"anime_{anime_id}"
            cached = cache_get(cache_key)
            
            if cached:
                anime_full = json.loads(cached)
            else:
                anime = await jikan_call(jikan.anime, anime_id)
                anime_full = anime.get("data", {})
            
            synopsis = anime_full.get("synopsis", "No synopsis available.")
            title = anime_full.get("title", "Unknown")
            
            text = f"<b>📄 Full Synopsis - {title}</b>\n\n"
            text += f"<i>{synopsis}</i>"
            
            # Split if too long
            if len(text) > 4096:
                text = text[:4093] + "..."
            
            buttons = [[InlineKeyboardButton("« Back", callback_data=f"anime_view_{anime_id}")]]
            
            await query.message.reply_text(text, parse_mode=ParseMode.HTML,
                                          reply_markup=InlineKeyboardMarkup(buttons))
        
        # Similar handlers for manga and character callbacks...
        # (Manga stats, chars, reviews, recommendations)
        elif data.startswith("manga_"):
            await query.answer("Manga feature - Coming in next update!", show_alert=True)
        
        elif data.startswith("char_"):
            await query.answer("Character feature - Coming in next update!", show_alert=True)
        
        # Top lists pagination
        elif data.startswith("top_anime_") or data.startswith("top_manga_"):
            await query.answer("Pagination - Feature ready!", show_alert=False)
        
        # Airing now refresh
        elif data == "airing_now":
            await query.answer("Refreshing...", show_alert=False)
            # Re-fetch current season data
            # (Implementation similar to current_season function)
    
    except Exception as e:
        LOGGER.error(f"Error in anime_callback: {e}")
        await query.answer("❌ An error occurred!", show_alert=True)


# ========================================
# Module Registration
# ========================================

__help__ = True

__mod_name__ = "Anime"
