"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Python 3.13+ audioop compatibility shim
try:
    import audioop
except ImportError:
    try:
        import audioop_lts as audioop
        import sys
        sys.modules['audioop'] = audioop
    except ImportError:
        try:
            import pyaudioop as audioop
            import sys
            sys.modules['audioop'] = audioop
        except ImportError:
            pass

# APScheduler entrypoint compatibility patch for Python 3.14+
try:
    import apscheduler.schedulers.base
    from apscheduler.triggers.date import DateTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.executors.asyncio import AsyncIOExecutor
    from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
    from apscheduler.jobstores.memory import MemoryJobStore

    apscheduler.schedulers.base.BaseScheduler._trigger_classes['date'] = DateTrigger
    apscheduler.schedulers.base.BaseScheduler._trigger_classes['interval'] = IntervalTrigger
    apscheduler.schedulers.base.BaseScheduler._trigger_classes['cron'] = CronTrigger
    apscheduler.schedulers.base.BaseScheduler._executor_classes['asyncio'] = AsyncIOExecutor
    apscheduler.schedulers.base.BaseScheduler._executor_classes['threadpool'] = ThreadPoolExecutor
    apscheduler.schedulers.base.BaseScheduler._executor_classes['processpool'] = ProcessPoolExecutor
    apscheduler.schedulers.base.BaseScheduler._jobstore_classes['memory'] = MemoryJobStore
except Exception:
    pass

import json
import logging
import os
import warnings

# Suppress BeautifulSoup GuessedAtParserWarning from wikipedia package
warnings.filterwarnings("ignore", category=UserWarning, module="wikipedia")
import sys
import time
import requests

# Patch requests to always include User-Agent for nekos.best and other APIs
_original_get = requests.get

STATIC_FALLBACKS = {
    # Original categories
    "baka": "https://cdn.nekos.life/baka/baka_007.gif",
    "bored": "https://i.giphy.com/t3ki9Q6EWipqM.gif",
    "highfive": "https://i.giphy.com/bp0fLrrlyFDoc.gif",
    "kick": "https://i.giphy.com/u2LJ0n4lx6jF6.gif",
    "shoot": "https://i.giphy.com/GE8UST5Chw5WM.gif",
    "think": "https://i.giphy.com/l0HlRnAWXxn0MhHKg.gif",
    "yeet": "https://i.giphy.com/5PhDdJQd2yG1MvHzJ6.gif",
    "kill": "https://i.giphy.com/11HeupdoJrGjQQ.gif",
    
    # Extra reaction categories to prevent ValueError crashes on DNS/API failure
    "waifu": "https://i.imgur.com/7j7mZ9r.png",
    "neko": "https://i.imgur.com/k9vE8Jc.png",
    "shinobu": "https://i.imgur.com/NpeM1oH.png",
    "megumin": "https://i.imgur.com/mO279qN.png",
    "bully": "https://i.giphy.com/l378bu6ZY3o3sxgf2.gif",
    "awoo": "https://i.giphy.com/V83V4p8vNu41y.gif",
    "lick": "https://i.giphy.com/JHXp5IRE3vQ1a.gif",
    "bonk": "https://i.giphy.com/qs425DSLTxJAQ.gif",
    "nom": "https://i.giphy.com/11fDMYeTusB5tK.gif",
    "glomp": "https://i.giphy.com/l41YfR4yv9wS5Nn44.gif",
    "cringe": "https://i.giphy.com/RJAjTowsU0K1a.gif",
    "pat": "https://i.giphy.com/5tmRhwTlUzfYIFKV4b.gif",
    "hug": "https://i.giphy.com/od5H3PmEG5EVq.gif",
    "cuddle": "https://i.giphy.com/lrr9rHuoJOE0w.gif",
    "kiss": "https://i.giphy.com/108M7gCS1JSoO4.gif",
    "slap": "https://i.giphy.com/Gf3AUz3eK6WGI.gif",
    "smug": "https://i.giphy.com/wW95fEq09hOI8.gif",
    "tickle": "https://i.giphy.com/3x1a9M2scT2lW.gif",
    "poke": "https://i.giphy.com/3o72FiXyc7eEYWpFAc.gif",
    "feed": "https://i.giphy.com/5Y2bU7QqvfMseXJgrY.gif",
    "bite": "https://i.giphy.com/3o7TKoHNh7VvF1x1e0.gif",
    "wink": "https://i.giphy.com/3o6gb2QV3meGEdZgM8.gif",
    "smile": "https://i.giphy.com/143v0Z4767T15u.gif",
    "wave": "https://i.giphy.com/3o7TKoWXm3okO1sC5y.gif",
    "dance": "https://i.giphy.com/3o7TKUo3mP6D09C96E.gif",
    "blush": "https://i.giphy.com/3o7TKoHNh7VvF1x1e0.gif",
    "happy": "https://i.giphy.com/11dU387B4q8HLO.gif",
    "cry": "https://i.giphy.com/yd1ydBggQ42w8.gif",
}

def custom_get(url, *args, **kwargs):
    headers = kwargs.get("headers", {})
    if "User-Agent" not in headers:
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    kwargs["headers"] = headers
    if "timeout" not in kwargs:
        kwargs["timeout"] = 10

    # Try original request first
    if "nekos.best/api" in url:
        try:
            resp = _original_get(url, *args, **kwargs)
            if resp.status_code == 200 and resp.text.strip().startswith("{"):
                return resp
        except Exception:
            pass

        # Fallback sequence:
        category = url.split("/")[-1].split("?")[0]

        # 1. Try OtakuGIFs
        otakugifs_reactions = {
            'bite', 'blush', 'cry', 'cuddle', 'dance', 'facepalm', 'handhold', 
            'happy', 'hug', 'kiss', 'laugh', 'poke', 'pout', 'punch', 'shrug', 
            'slap', 'sleep', 'smile', 'smug', 'stare', 'thumbsup', 'tickle', 
            'wave', 'wink', 'pat'
        }
        if category in otakugifs_reactions:
            try:
                r = _original_get(f"https://api.otakugifs.xyz/gif?reaction={category}&format=gif", headers=headers, timeout=5)
                if r.status_code == 200:
                    val = r.json().get("url")
                    if val:
                        class MockResponse:
                            def __init__(self, json_data, status_code):
                                import json
                                self._json = json_data
                                self.status_code = status_code
                                self.text = json.dumps(json_data)
                                self.content = self.text.encode('utf-8')
                            def json(self):
                                return self._json
                        return MockResponse({"results": [{"url": val, "anime_name": "Anime"}]}, 200)
            except Exception:
                pass

        # 2. Try Purrbot
        purrbot_categories = {
            "hug", "pat", "bite", "blush", "cry", "cuddle", "dance", 
            "feed", "kiss", "poke", "pout", "slap", "smile", "tickle", "neko",
            "lick", "wink"
        }
        if category in purrbot_categories:
            try:
                r = _original_get(f"https://api.purrbot.site/v2/img/sfw/{category}/gif", headers=headers, timeout=5)
                if r.status_code == 200:
                    val = r.json().get("link")
                    if val and not r.json().get("error"):
                        class MockResponse:
                            def __init__(self, json_data, status_code):
                                import json
                                self._json = json_data
                                self.status_code = status_code
                                self.text = json.dumps(json_data)
                                self.content = self.text.encode('utf-8')
                            def json(self):
                                return self._json
                        return MockResponse({"results": [{"url": val, "anime_name": "Anime"}]}, 200)
            except Exception:
                pass

        # 3. Try Nekos.life
        nekos_life_categories = {
            "hug", "pat", "cuddle", "feed", "kiss", "slap", "smug", "tickle", "neko", "baka",
            "waifu", "poke"
        }
        if category in nekos_life_categories:
            try:
                r = _original_get(f"https://nekos.life/api/v2/img/{category}", headers=headers, timeout=5)
                if r.status_code == 200:
                    val = r.json().get("url")
                    if val:
                        class MockResponse:
                            def __init__(self, json_data, status_code):
                                import json
                                self._json = json_data
                                self.status_code = status_code
                                self.text = json.dumps(json_data)
                                self.content = self.text.encode('utf-8')
                            def json(self):
                                return self._json
                        return MockResponse({"results": [{"url": val, "anime_name": "Anime"}]}, 200)
            except Exception:
                pass

        # 4. Try Nekos.fun
        nekos_fun_categories = {
            "kiss", "lick", "hug", "pat", "poke", "slap", "bite", "feed", "tickle", "cuddle",
            "smug", "neko", "waifu", "cry", "laugh", "blush", "smile", "wink", "wave", "happy",
            "bored"
        }
        if category in nekos_fun_categories:
            try:
                r = _original_get(f"https://nekos.fun/api/{category}", headers=headers, timeout=5)
                if r.status_code == 200:
                    val = r.json().get("image")
                    if val:
                        class MockResponse:
                            def __init__(self, json_data, status_code):
                                import json
                                self._json = json_data
                                self.status_code = status_code
                                self.text = json.dumps(json_data)
                                self.content = self.text.encode('utf-8')
                            def json(self):
                                return self._json
                        return MockResponse({"results": [{"url": val, "anime_name": "Anime"}]}, 200)
            except Exception:
                pass

        # 5. Use static fallback if available
        if category in STATIC_FALLBACKS:
            val = STATIC_FALLBACKS[category]
            class MockResponse:
                def __init__(self, json_data, status_code):
                    import json
                    self._json = json_data
                    self.status_code = status_code
                    self.text = json.dumps(json_data)
                    self.content = self.text.encode('utf-8')
                def json(self):
                    return self._json
            return MockResponse({"results": [{"url": val, "anime_name": "Anime"}]}, 200)

        # If everything fails, raise a ValueError with the original status code (or 404)
        raise ValueError("All fallback SFW APIs failed or are currently unavailable.")

    try:
        return _original_get(url, *args, **kwargs)
    except Exception as e:
        raise e
requests.get = custom_get

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import aiohttp
import telegram
import telegram.ext as tg

_original_init = telegram.InlineKeyboardButton.__init__

def _patched_init(self, text, callback_data=None, url=None, login_url=None, switch_inline_query=None, switch_inline_query_current_chat=None, callback_game=None, pay=None, web_app=None, **kwargs):
    if 'style' not in kwargs:
        is_help_or_settings = False
        if isinstance(callback_data, str):
            if callback_data.startswith(('help_', 'stngs_', 'usettings_', 'settings_')):
                is_help_or_settings = True
        
        if not is_help_or_settings:
            t = text.lower()
            if any(w in t for w in ['confirm', 'approve', 'yes', 'save', 'allow', 'accept', 'add', 'start', 'enable', 'turn on', 'unmute', 'unban']):
                kwargs['style'] = 'success'
            elif any(w in t for w in ['cancel', 'delete', 'no', 'close', 'remove', 'deny', 'reject', 'disable', 'turn off', 'mute', 'ban', 'stop', 'kill']):
                kwargs['style'] = 'danger'
            else:
                kwargs['style'] = 'primary'
    _original_init(self, text, callback_data=callback_data, url=url, login_url=login_url, switch_inline_query=switch_inline_query, switch_inline_query_current_chat=switch_inline_query_current_chat, callback_game=callback_game, pay=pay, web_app=web_app, **kwargs)

telegram.InlineKeyboardButton.__init__ = _patched_init

from telegram.ext import Application, ApplicationBuilder, Defaults
from telethon import TelegramClient
from telethon.sessions import MemorySession, StringSession
from motor import motor_asyncio
from odmantic import AIOEngine
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from redis import StrictRedis
from Python_ARQ import ARQ
from telegraph import Telegraph
import httpx
from httpx import AsyncClient, Timeout

StartTime = time.time()

def get_user_list(filename: str, key: str):
    """Load user lists from JSON file"""
    try:
        filepath = os.path.join(os.getcwd(), "Cutiepii_Robot", filename)
        with open(filepath, "r") as json_file:
            return json.load(json_file)[key]
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        return []

# Configure logging
FORMAT = "[CUTIEPII ROBOT] %(message)s"
logging.basicConfig(
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("log.txt", encoding="utf-8")
    ],
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
)

# Set logging levels for external libraries
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)
logging.getLogger('pyrogram').setLevel(logging.ERROR)
logging.getLogger('ptbcontrib.postgres_persistence.postgrespersistence').setLevel(logging.WARNING)
logging.getLogger('apscheduler').setLevel(logging.WARNING)
logging.getLogger('telethon').setLevel(logging.WARNING)

LOGGER = logging.getLogger(__name__)

# Check Python version
if sys.version_info[0] < 3 or sys.version_info[1] < 9:
    LOGGER.error(
        "You MUST have a Python version of at least 3.9! Bot quitting."
    )
    sys.exit(1)

# Check if running from environment variables or config file
ENV = bool(os.environ.get("ENV", False))

if ENV:
    # Load from environment variables
    TOKEN = os.environ.get("TOKEN")
    if not TOKEN:
        raise ValueError("TOKEN environment variable is required!")

    try:
        OWNER_ID = int(os.environ.get("OWNER_ID", 0))
        if OWNER_ID == 0:
            raise ValueError("OWNER_ID is required!")
    except ValueError:
        raise ValueError("OWNER_ID must be a valid integer!")

    # Required variables
    API_ID = os.environ.get("API_ID")
    API_HASH = os.environ.get("API_HASH")
    
    if not API_ID or not API_HASH:
        raise ValueError("API_ID and API_HASH are required!")
    
    DB_URL = os.environ.get("DATABASE_URL")
    if not DB_URL:
        raise ValueError("DATABASE_URL is required!")
    
    REDIS_URL = os.environ.get("REDIS_URL")
    if not REDIS_URL:
        raise ValueError("REDIS_URL is required!")
    
    # MongoDB is optional - bot works without it
    MONGO_DB_URL = os.environ.get("MONGO_DB_URL")

    # User lists with validation
    JOIN_LOGGER = os.environ.get("JOIN_LOGGER")
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME", "")
    MESSAGE_DUMP = os.environ.get("MESSAGE_DUMP")

    def parse_user_list(env_var: str, var_name: str) -> set:
        """Parse comma or space separated user ID list"""
        try:
            users = os.environ.get(env_var, "").replace(",", " ").split()
            return {int(x) for x in users if x.strip()}
        except ValueError:
            raise ValueError(f"{var_name} must contain valid integers!")

    SUDO_USERS = parse_user_list("SUDO_USERS", "SUDO_USERS")
    DEV_USERS = parse_user_list("DEV_USERS", "DEV_USERS")
    SUPPORT_USERS = parse_user_list("SUPPORT_USERS", "SUPPORT_USERS")
    WHITELIST_USERS = parse_user_list("WHITELIST_USERS", "WHITELIST_USERS")
    TIGER_USERS = parse_user_list("TIGER_USERS", "TIGER_USERS")
    BL_CHATS = parse_user_list("BL_CHATS", "BL_CHATS")

    # Optional variables with defaults
    INFOPIC = os.environ.get("INFOPIC", "False").lower() in ["true", "1", "yes"]
    GBAN_LOGS = os.environ.get("GBAN_LOGS")
    ERROR_LOGS = os.environ.get("ERROR_LOGS")
    WEBHOOK = os.environ.get("WEBHOOK", "False").lower() in ["true", "1", "yes"]
    URL = os.environ.get("URL", "")
    PORT = int(os.environ.get("PORT", 8443))
    CERT_PATH = os.environ.get("CERT_PATH")
    
    DONATION_LINK = os.environ.get("DONATION_LINK")
    LOAD = [x for x in os.environ.get("LOAD", "").split() if x]
    NO_LOAD = [x for x in os.environ.get("NO_LOAD", "").split() if x]
    DEL_CMDS = os.environ.get("DEL_CMDS", "False").lower() in ["true", "1", "yes"]
    STRICT_GBAN = os.environ.get("STRICT_GBAN", "False").lower() in ["true", "1", "yes"]
    WORKERS = int(os.environ.get("WORKERS", 8))
    BAN_STICKER = os.environ.get("BAN_STICKER", "CAADAgADOwADPPEcAXkko5EB3YGYAg")
    ALLOW_EXCL = os.environ.get("ALLOW_EXCL", "False").lower() in ["true", "1", "yes"]
    
    # API Keys
    CASH_API_KEY = os.environ.get("CASH_API_KEY")
    TIME_API_KEY = os.environ.get("TIME_API_KEY")
    PIXABAY_API = os.environ.get("PIXABAY_API")
    REM_BG_API_KEY = os.environ.get("REM_BG_API_KEY")
    IMGBB_API_KEY = os.environ.get("IMGBB_API_KEY")
    OPENWEATHERMAP_ID = os.environ.get("OPENWEATHERMAP_ID", "")
    GENIUS_API_TOKEN = os.environ.get("GENIUS_API_TOKEN")
    YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
    
    DOWNLOAD_DIRECTORY = os.environ.get("DOWNLOAD_DIRECTORY", "./downloads/")
    SUPPORT_CHAT = os.environ.get("SUPPORT_CHAT")
    BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
    BOT_NAME = os.environ.get("BOT_NAME", "Cutiepii Robot")
    
    STRING_SESSION = os.environ.get("STRING_SESSION")
    APP_ID = os.environ.get("APP_ID")
    APP_HASH = os.environ.get("APP_HASH")
    
    ALLOW_CHATS = os.environ.get("ALLOW_CHATS", "True")
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "cutiepii")
    BACKUP_PASS = os.environ.get("BACKUP_PASS", "")
    CUSTOM_CMD = os.environ.get("CUSTOM_CMD", "False").lower() in ["true", "1", "yes"]
    
    MONGO_DB = os.environ.get("MONGO_DB", "Cutiepii")
    ARQ_API_URL = os.environ.get("ARQ_API_URL", "")
    ARQ_API_KEY = os.environ.get("ARQ_API_KEY", "")
    GOOGLE_CHROME_BIN = os.environ.get("GOOGLE_CHROME_BIN", "/usr/bin/google-chrome")
    CHROME_DRIVER = os.environ.get("CHROME_DRIVER", "/usr/bin/chromedriver")
    OWNER_ID_LINK = os.environ.get("OWNER_ID_LINK", "")
    OWNER_NAME = os.environ.get("OWNER_NAME", "Owner")
    HELP_IMG = os.environ.get("HELP_IMG", "https://graph.org/file/help.jpg")
    GROUP_START_IMG = os.environ.get("GROUP_START_IMG", "https://files.catbox.moe/u65vv8.mp4")
    UPDATES_CHANNEL = os.environ.get("UPDATES_CHANNEL")
    BIND_ADDRESS = os.environ.get('BIND_ADDRESS', '0.0.0.0')
    
    # Redis configuration (alternative to REDIS_URL)
    REDIS_HOST = os.environ.get("REDIS_HOST")
    REDIS_PORT = os.environ.get("REDIS_PORT")
    REDIS_PASS = os.environ.get("REDIS_PASS")
    REDIS_DB = os.environ.get("REDIS_DB")

else:
    # Load from config file
    try:
        from Cutiepii_Robot.config import Development as Config
    except ImportError:
        LOGGER.error("Config file not found! Please create config.py or set ENV=True")
        sys.exit(1)

    TOKEN = Config.TOKEN
    
    try:
        OWNER_ID = int(Config.OWNER_ID)
    except (ValueError, AttributeError):
        raise ValueError("OWNER_ID must be a valid integer in config!")

    # Required config values
    for attr in ["API_ID", "API_HASH", "DATABASE_URL", "REDIS_URL"]:
        if not hasattr(Config, attr):
            raise ValueError(f"{attr} is required in config!")
    
    # MongoDB is optional - bot works without it

    JOIN_LOGGER = getattr(Config, "JOIN_LOGGER", None)
    OWNER_USERNAME = getattr(Config, "OWNER_USERNAME", "")
    MESSAGE_DUMP = getattr(Config, "MESSAGE_DUMP", None)
    ALLOW_CHATS = getattr(Config, "ALLOW_CHATS", True)
    
    def get_config_set(attr_name: str) -> set:
        """Safely get set from config"""
        value = getattr(Config, attr_name, [])
        try:
            return {int(x) for x in value} if value else set()
        except (ValueError, TypeError):
            raise ValueError(f"{attr_name} must contain valid integers!")
    
    SUDO_USERS = get_config_set("SUDO_USERS")
    DEV_USERS = get_config_set("DEV_USERS")
    SUPPORT_USERS = get_config_set("SUPPORT_USERS")
    WHITELIST_USERS = get_config_set("WHITELIST_USERS")
    TIGER_USERS = get_config_set("TIGER_USERS")
    BL_CHATS = get_config_set("BL_CHATS")

    INFOPIC = getattr(Config, "INFOPIC", False)
    GBAN_LOGS = getattr(Config, "GBAN_LOGS", None)
    ERROR_LOGS = getattr(Config, "ERROR_LOGS", None)
    WEBHOOK = getattr(Config, "WEBHOOK", False)
    URL = getattr(Config, "URL", "")
    PORT = getattr(Config, "PORT", 8443)
    CERT_PATH = getattr(Config, "CERT_PATH", None)
    API_ID = Config.API_ID
    API_HASH = Config.API_HASH
    DONATION_LINK = getattr(Config, "DONATION_LINK", None)
    STRICT_GBAN = getattr(Config, "STRICT_GBAN", False)
    WORKERS = getattr(Config, "WORKERS", 8)
    BAN_STICKER = getattr(Config, "BAN_STICKER", "CAADAgADOwADPPEcAXkko5EB3YGYAg")
    DOWNLOAD_DIRECTORY = getattr(Config, "DOWNLOAD_DIRECTORY", "./downloads/")
    LOAD = getattr(Config, "LOAD", [])
    NO_LOAD = getattr(Config, "NO_LOAD", [])
    CASH_API_KEY = getattr(Config, "CASH_API_KEY", None)
    TIME_API_KEY = getattr(Config, "TIME_API_KEY", None)
    PIXABAY_API = getattr(Config, "PIXABAY_API", None)
    # MongoDB is optional - bot works without it
    MONGO_DB_URL = getattr(Config, "MONGO_DB_URL", None)
    REDIS_URL = Config.REDIS_URL
    SUPPORT_CHAT = getattr(Config, "SUPPORT_CHAT", None)
    REM_BG_API_KEY = getattr(Config, "REM_BG_API_KEY", None)
    IMGBB_API_KEY = getattr(Config, "IMGBB_API_KEY", None)
    OPENWEATHERMAP_ID = getattr(Config, "OPENWEATHERMAP_ID", "")
    APP_ID = getattr(Config, "APP_ID", None)
    APP_HASH = getattr(Config, "APP_HASH", None)
    DB_URL = Config.DATABASE_URL
    BOT_USERNAME = getattr(Config, "BOT_USERNAME", "")
    STRING_SESSION = getattr(Config, "STRING_SESSION", None)
    GENIUS_API_TOKEN = getattr(Config, "GENIUS_API_TOKEN", None)
    YOUTUBE_API_KEY = getattr(Config, "YOUTUBE_API_KEY", None)
    ALLOW_EXCL = getattr(Config, "ALLOW_EXCL", False)
    ARQ_API_URL = getattr(Config, "ARQ_API_URL", "")
    ARQ_API_KEY = getattr(Config, "ARQ_API_KEY", "")
    GOOGLE_CHROME_BIN = getattr(Config, "GOOGLE_CHROME_BIN", "/usr/bin/google-chrome")
    CHROME_DRIVER = getattr(Config, "CHROME_DRIVER", "/usr/bin/chromedriver")
    BOT_NAME = getattr(Config, "BOT_NAME", "Cutiepii Robot")
    DEL_CMDS = getattr(Config, "DEL_CMDS", False)
    BOT_API_URL = getattr(Config, "BOT_API_URL", "https://api.telegram.org/bot")
    MONGO_DB = getattr(Config, "MONGO_DB", "Cutiepii")
    HELP_IMG = getattr(Config, "HELP_IMG", "https://graph.org/file/help.jpg")
    GROUP_START_IMG = getattr(Config, "GROUP_START_IMG", "https://files.catbox.moe/u65vv8.mp4")
    REMINDER_LIMIT = getattr(Config, "REMINDER_LIMIT", 20)
    DATABASE_NAME = getattr(Config, "DATABASE_NAME", "cutiepii")
    BACKUP_PASS = getattr(Config, "BACKUP_PASS", "")
    UPDATES_CHANNEL = getattr(Config, "UPDATES_CHANNEL", None)
    OWNER_ID_LINK = getattr(Config, "OWNER_ID_LINK", "")
    OWNER_NAME = getattr(Config, "OWNER_NAME", "Owner")
    CUSTOM_CMD = False
    REDIS_HOST = getattr(Config, "REDIS_HOST", None)
    REDIS_PORT = getattr(Config, "REDIS_PORT", None)
    REDIS_PASS = getattr(Config, "REDIS_PASS", None)
    REDIS_DB = getattr(Config, "REDIS_DB", None)
    BIND_ADDRESS = getattr(Config, "BIND_ADDRESS", "0.0.0.0")

# Add owner to privileged users
SUDO_USERS.add(OWNER_ID)
DEV_USERS.add(OWNER_ID)

# Initialize Redis
LOGGER.info("[CUTIEPII]: Connecting to Redis Database...")
try:
    REDIS = StrictRedis.from_url(REDIS_URL, decode_responses=True)
    REDIS.ping()
    LOGGER.info("[CUTIEPII]: ✅ Redis connection established successfully!")

    class RedisStr(str):
        def decode(self, encoding="utf-8", errors="strict"):
            return self

    class RedisDict(dict):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            cleaned = {}
            for k, v in self.items():
                k_str = k.decode("utf-8") if isinstance(k, bytes) else str(k)
                if isinstance(v, bytes):
                    v_val = RedisStr(v.decode("utf-8"))
                elif isinstance(v, str):
                    v_val = RedisStr(v)
                else:
                    v_val = v
                cleaned[k_str] = v_val
            self.clear()
            self.update(cleaned)

        def __getitem__(self, key):
            if isinstance(key, bytes):
                key = key.decode("utf-8")
            return super().__getitem__(key)

        def get(self, key, default=None):
            if isinstance(key, bytes):
                key = key.decode("utf-8")
            val = super().get(key, default)
            if val is default and isinstance(default, bytes):
                return RedisStr(default.decode("utf-8"))
            return val

    def wrap_redis_value(val):
        if val is None:
            return None
        if isinstance(val, bytes):
            return RedisStr(val.decode("utf-8"))
        if isinstance(val, str):
            return RedisStr(val)
        if isinstance(val, dict):
            return RedisDict(val)
        if isinstance(val, list):
            return [wrap_redis_value(v) for v in val]
        if isinstance(val, set):
            return {wrap_redis_value(v) for v in val}
        if isinstance(val, tuple):
            return tuple(wrap_redis_value(v) for v in val)
        return val

    class RedisWrapper:
        def __init__(self, client):
            self._client = client
        def __getattr__(self, name):
            attr = getattr(self._client, name)
            if callable(attr):
                def wrapper(*args, **kwargs):
                    res = attr(*args, **kwargs)
                    if name == "pipeline":
                        return RedisWrapper(res)
                    return wrap_redis_value(res)
                return wrapper
            return attr
        def __enter__(self):
            self._client.__enter__()
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            return self._client.__exit__(exc_type, exc_val, exc_tb)

    REDIS = RedisWrapper(REDIS)
except Exception as e:
    LOGGER.error(f"[CUTIEPII ERROR]: Redis connection failed: {e}")
    raise Exception("Redis database connection failed! Please check your REDIS_URL.")

# Telegram API URLs
TG_API = "https://api.telegram.org/bot"
TG_FILE_API = "https://api.telegram.org/file/bot"

# Startup messages
LOGGER.info("[CUTIEPII] 🤖 Cutiepii Robot is starting...")
LOGGER.info("[CUTIEPII] 📦 Python-Telegram-Bot v22.5")
LOGGER.info("[CUTIEPII] 👨‍💻 Project maintained by: github.com/Awesome-RJ")

# Initialize Telegraph
LOGGER.info("[CUTIEPII]: Setting up Telegraph...")
try:
    telegraph = Telegraph(domain='graph.org')
    telegraph.create_account(short_name="Cutiepii")
    LOGGER.info("[CUTIEPII]: ✅ Telegraph account created")
except Exception as e:
    LOGGER.warning(f"[CUTIEPII]: ⚠️ Telegraph setup failed: {e}")
    telegraph = None

# Initialize PTB Application
LOGGER.info("[CUTIEPII]: Initializing Telegram Bot...")
application: Application = (
    ApplicationBuilder()
    .token(TOKEN)
    .base_url(TG_API)
    .base_file_url(TG_FILE_API)
    .concurrent_updates(True)
    .defaults(Defaults(allow_sending_without_reply=True))
    .build()
)
updater = application
dispatcher = application

# Auto-fetch bot details dynamically from Telegram API
try:
    import telegram
    _temp_bot = telegram.Bot(token=TOKEN)
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    _bot_info = loop.run_until_complete(_temp_bot.get_me())
    BOT_USERNAME = _bot_info.username
    BOT_NAME = _bot_info.first_name
    LOGGER.info(f"[CUTIEPII]: ✅ Auto-fetched bot info: @{BOT_USERNAME} ({BOT_NAME})")
except Exception as e:
    LOGGER.error(f"[CUTIEPII ERROR]: Failed to auto-fetch bot username: {e}")

# Patch process_update to await handler.check_update() when it returns a coroutine
# (fixes RuntimeWarning: coroutine 'CustomCommandHandler.check_update' was never awaited)
_original_process_update = application.process_update

async def _patched_process_update(self, update):
    import asyncio
    from telegram.ext import ApplicationHandlerStop
    from telegram._utils.defaultvalue import DefaultValue
    from Cutiepii_Robot.modules.sql import SESSION
    _log = logging.getLogger("Cutiepii_Robot.application")
    application = self
    application._check_initialized()
    try:
        context = None
        any_blocking = False
        for handlers in application.handlers.values():
            try:
                for handler in handlers:
                    check = handler.check_update(update)
                    if asyncio.iscoroutine(check):
                        check = await check
                    if check is None or check is False:
                        continue
                    if context is None:
                        try:
                            context = application.context_types.context.from_update(update, application)
                        except Exception as exc:
                            _log.critical(
                                "Error while building CallbackContext for update %s. Update will not be processed.",
                                update, exc_info=exc,
                            )
                            return
                        await context.refresh_data()
                    coroutine = handler.handle_update(update, application, check, context)
                    from telegram.ext import ExtBot
                    block = getattr(handler, "block", True)
                    if not block or (block is DefaultValue and isinstance(application.bot, ExtBot) and application.bot.defaults and not application.bot.defaults.block):
                        application.create_task(coroutine, update=update, name=f"Application:{application.bot.id}:process_update_non_blocking:{handler}")
                    else:
                        any_blocking = True
                        await coroutine
                    break
            except ApplicationHandlerStop:
                _log.debug("Stopping further handlers due to ApplicationHandlerStop")
                break
            except Exception as exc:
                if await application.process_error(update=update, error=exc):
                    _log.debug("Error handler stopped further handlers.")
                    break
        if any_blocking:
            application._mark_for_persistence_update(update=update)
    finally:
        SESSION.remove()

type(application).process_update = _patched_process_update
LOGGER.info("[CUTIEPII]: ✅ PTB Application initialized")

# Initialize Telethon (v1.42.0+)
# Using MemorySession for bot token authentication
LOGGER.info("[CUTIEPII]: Starting Telethon client...")
try:
    telethn = TelegramClient(MemorySession(), API_ID, API_HASH)
    LOGGER.info("[CUTIEPII]: ✅ Telethon client ready (v1.42.0+)")
except Exception as e:
    LOGGER.error(f"[CUTIEPII]: ❌ Failed to initialize Telethon: {e}")
    # Fallback to None session for backward compatibility
    telethn = TelegramClient(None, API_ID, API_HASH)
    LOGGER.warning("[CUTIEPII]: ⚠️ Using fallback Telethon initialization")

# Initialize MongoDB (OPTIONAL - kept for compatibility with legacy modules)
# NOTE: New modules should use SQL (karma_sql, afk_sql, etc.)
if MONGO_DB_URL:
    LOGGER.info("[CUTIEPII]: MongoDB URL found, connecting...")
    try:
        mongodb = MongoClient(MONGO_DB_URL, serverSelectionTimeoutMS=5000)[MONGO_DB]
        motor = motor_asyncio.AsyncIOMotorClient(MONGO_DB_URL)
        db = motor[MONGO_DB]
        engine = AIOEngine(motor, MONGO_DB)
        # Test connection
        mongodb.list_collection_names()
        LOGGER.info("[CUTIEPII]: ✅ MongoDB connection established")
    except Exception as e:
        LOGGER.warning(f"[CUTIEPII]: ⚠️ MongoDB connection failed: {e}")
        LOGGER.warning("[CUTIEPII]: MongoDB is optional - SQL modules will work without it")
        mongodb = None
        motor = None
        db = None
        engine = None
else:
    LOGGER.info("[CUTIEPII]: MongoDB not configured (optional)")
    mongodb = None
    motor = None
    db = None
    engine = None

# Initialize aiohttp session
LOGGER.info("[CUTIEPII]: Initializing aiohttp session...")
aiohttpsession = aiohttp.ClientSession()
LOGGER.info("[CUTIEPII]: ✅ Aiohttp session created")

# Initialize ARQ Client
LOGGER.info("[CUTIEPII]: Initializing ARQ client...")
try:
    arq = ARQ(ARQ_API_URL, ARQ_API_KEY, aiohttpsession)
    LOGGER.info("[CUTIEPII]: ✅ ARQ client initialized")
except Exception as e:
    LOGGER.warning(f"[CUTIEPII]: ⚠️ ARQ client setup failed: {e}")
    arq = None

# Initialize HTTP client with improved configuration
timeout = Timeout(
    connect=10.0,  # Connection timeout
    read=40.0,     # Read timeout
    write=10.0,    # Write timeout
    pool=5.0       # Pool timeout
)
http = AsyncClient(
    http2=True,
    timeout=timeout,
    follow_redirects=True,
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
)

# Userbot placeholder (disabled)
ubot = None

# Process user lists
SUDO_USERS = list(SUDO_USERS)
DEV_USERS = list(DEV_USERS)
WHITELIST_USERS = list(WHITELIST_USERS)
SUPPORT_USERS = list(SUPPORT_USERS)
TIGER_USERS = list(TIGER_USERS)

# Bot information
BOT_ID = int(TOKEN.split(":")[0])
ELEVATED_USERS_FILE = os.path.join(os.getcwd(), "Cutiepii_Robot/elevated_users.json")

# Load custom command handler if enabled
from Cutiepii_Robot.modules.helper_funcs.handlers import CustomCommandHandler

if CUSTOM_CMD:
    tg.CommandHandler = CustomCommandHandler
    LOGGER.info("[CUTIEPII]: ✅ Custom command handler enabled")

LOGGER.info("[CUTIEPII]: 🚀 Initialization complete!")

# Monkey patch telegram.Bot to automatically convert and default messages to ParseMode.HTML rich text
try:
    import inspect
    import telegram
    import re
    import html
    from telegram.constants import ParseMode
    
    # Pre-compile regexes globally for maximum performance
    EMOJI_PATTERN = re.compile(
        r'[\u200d\u2300-\u27bf\U0001f300-\U0001f9ff\U0001f600-\U0001f64f\U0001f680-\U0001f6ff\U0001f1e0-\U0001f1ff\U0001f000-\U0001ffff\ufe0f]',
        re.UNICODE
    )
    RE_SPACES = re.compile(r' +')
    RE_LINE_STRIP = re.compile(r'^[ \t]+|[ \t]+$', re.MULTILINE)
    
    VALID_TAGS_PATTERN = re.compile(
        r'<(/)?(b|i|code|u|s|pre|blockquote|tg-spoiler|a|tg-emoji)(?:\s+[a-zA-Z\-]+(?:=(?:"[^"]*"|\'[^\']*\'|[^\s>]+))?)*\s*(/)?>',
        re.IGNORECASE
    )
    
    RE_INLINE_CODE = re.compile(r'`([^`\n]+)`')
    RE_BOLD_DOUBLE = re.compile(r'\*\*([^\*\n]+)\*\*')
    RE_BOLD_SINGLE = re.compile(r'\*([^\*\n]+)\*')
    RE_ITALIC = re.compile(r'_([^_\n]+)_')
    RE_STRIKE = re.compile(r'~~([^~\n]+)~~')
    RE_SPOILER = re.compile(r'\|\|([^\|\n]+)\|\|')

    def make_rich_text(text: str) -> str:
        if not isinstance(text, str) or not text:
            return text

        # Remove emojis globally from all replies as requested
        text = EMOJI_PATTERN.sub('', text)
        
        # Clean up consecutive spaces and trim each line
        text = RE_SPACES.sub(' ', text)
        text = RE_LINE_STRIP.sub('', text).strip()

        placeholders = []
        def tag_replacer(match):
            placeholders.append(match.group(0))
            return f"\x00P{len(placeholders)-1}\x00"
        
        # Temporarily substitute valid HTML tags with placeholders
        temp_text = VALID_TAGS_PATTERN.sub(tag_replacer, text)
        
        # Escape remaining raw '<' and '>' to prevent parse entity crashes
        temp_text = temp_text.replace('<', '&lt;').replace('>', '&gt;')
        
        # Restore valid tags
        for i, placeholder in enumerate(placeholders):
            temp_text = temp_text.replace(f"\x00P{i}\x00", placeholder)
            
        # Convert Markdown formatting to HTML
        temp_text = RE_INLINE_CODE.sub(r'<code>\1</code>', temp_text)
        temp_text = RE_BOLD_DOUBLE.sub(r'<b>\1</b>', temp_text)
        temp_text = RE_BOLD_SINGLE.sub(r'<b>\1</b>', temp_text)
        temp_text = RE_ITALIC.sub(r'<i>\1</i>', temp_text)
        temp_text = RE_STRIKE.sub(r'<s>\1</s>', temp_text)
        temp_text = RE_SPOILER.sub(r'<tg-spoiler>\1</tg-spoiler>', temp_text)
        
        return temp_text

    def patch_bot_method(method_name, text_arg_name):
        orig_method = getattr(telegram.Bot, method_name, None)
        if not orig_method:
            return
            
        sig = inspect.signature(orig_method)
        
        async def patched_method(self, *args, **kwargs):
            bound = sig.bind(self, *args, **kwargs)
            bound.apply_defaults()
            
            pm = bound.arguments.get('parse_mode')
            pm_val = getattr(pm, 'value', pm) if pm else None
            
            is_html = False
            if pm_val is None or pm_val in (ParseMode.MARKDOWN, 'Markdown', 'MARKDOWN'):
                bound.arguments['parse_mode'] = ParseMode.HTML
                is_html = True
            elif pm_val in (ParseMode.HTML, 'HTML', 'html'):
                is_html = True
                
            if is_html and text_arg_name in bound.arguments:
                val = bound.arguments[text_arg_name]
                if val and isinstance(val, str):
                    bound.arguments[text_arg_name] = make_rich_text(val)
                        
            return await orig_method(*bound.args, **bound.kwargs)
            
        setattr(telegram.Bot, method_name, patched_method)
        
    patch_bot_method('send_message', 'text')
    patch_bot_method('edit_message_text', 'text')
    patch_bot_method('send_photo', 'caption')
    patch_bot_method('send_audio', 'caption')
    patch_bot_method('send_document', 'caption')
    patch_bot_method('send_video', 'caption')
    patch_bot_method('send_voice', 'caption')
    patch_bot_method('send_animation', 'caption')
    patch_bot_method('edit_message_caption', 'caption')
    LOGGER.info("[CUTIEPII]: ✅ Rich text / HTML monkey patch applied successfully to all bot message methods")
except Exception as e:
    LOGGER.error(f"[CUTIEPII ERROR]: Failed to apply rich text / HTML monkey patch: {e}")
