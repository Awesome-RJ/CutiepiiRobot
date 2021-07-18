import logging
import os
import sys
import time
import spamwatch
from pyrogram import Client, errors
import telegram.ext as tg
from telethon import TelegramClient
from telethon.sessions import StringSession
from motor import motor_asyncio
from odmantic import AIOEngine
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from redis import StrictRedis
from Python_ARQ import ARQ
import aiohttp
from aiohttp import ClientSession
from ptbcontrib.postgres_persistence import PostgresPersistence
from pyrogram.errors.exceptions.bad_request_400 import PeerIdInvalid, ChannelInvalid

StartTime = time.time()

# enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)

LOGGER = logging.getLogger(__name__)
logging.getLogger('ptbcontrib.postgres_persistence.postgrespersistence').setLevel(logging.WARNING)

# if version < 3.6, stop bot.
if sys.version_info[0] < 3 or sys.version_info[1] < 6:
    LOGGER.error(
        "You MUST have a python version of at least 3.6! Multiple features depend on this. Bot quitting.",
    )
    quit(1)

ENV = bool(os.environ.get("ENV", False))

if ENV:
    TOKEN = os.environ.get("TOKEN", None)

    try:
        OWNER_ID = int(os.environ.get("OWNER_ID", None))
    except ValueError:
        raise Exception("Your OWNER_ID env variable is not a valid integer.")

    JOIN_LOGGER = os.environ.get("JOIN_LOGGER", None)
    OWNER_USERNAME = os.environ.get("OWNER_USERNAME", None)

    try:
        DRAGONS = set(int(x) for x in os.environ.get("DRAGONS", "").split())
        DEV_USERS = set(int(x) for x in os.environ.get("DEV_USERS", "").split())
    except ValueError:
        raise Exception("Your sudo or dev users list does not contain valid integers.")

    try:
        DEMONS = set(int(x) for x in os.environ.get("DEMONS", "").split())
    except ValueError:
        raise Exception("Your support users list does not contain valid integers.")

    try:
        WOLVES = set(int(x) for x in os.environ.get("WOLVES", "").split())
    except ValueError:
        raise Exception("Your whitelisted users list does not contain valid integers.")

    try:
        TIGERS = set(int(x) for x in os.environ.get("TIGERS", "").split())
    except ValueError:
        raise Exception("Your scout users list does not contain valid integers.")

    INFOPIC = bool(os.environ.get("INFOPIC", False))
    EVENT_LOGS = os.environ.get("EVENT_LOGS", None)
    WEBHOOK = bool(os.environ.get("WEBHOOK", False))
    URL = os.environ.get("URL", "")  # Does not contain token
    PORT = int(os.environ.get("PORT", 5000))
    CERT_PATH = os.environ.get("CERT_PATH")
    API_ID = os.environ.get("API_ID", None)
    API_HASH = os.environ.get("API_HASH", None)
    DB_URI = os.environ.get("DATABASE_URL")
    DONATION_LINK = os.environ.get("DONATION_LINK")
    LOAD = os.environ.get("LOAD", "").split()
    NO_LOAD = os.environ.get("NO_LOAD", "translation").split()
    DEL_CMDS = bool(os.environ.get("DEL_CMDS", False))
    STRICT_GBAN = bool(os.environ.get("STRICT_GBAN", False))
    WORKERS = int(os.environ.get("WORKERS", 8))
    BAN_STICKER = os.environ.get("BAN_STICKER", "CAADAgADOwADPPEcAXkko5EB3YGYAg")
    ALLOW_EXCL = os.environ.get("ALLOW_EXCL", False)
    TEMP_DOWNLOAD_DIRECTORY = os.environ.get("TEMP_DOWNLOAD_DIRECTORY", "./")
    CASH_API_KEY = os.environ.get("CASH_API_KEY", None)
    TIME_API_KEY = os.environ.get("TIME_API_KEY", None)
    WALL_API = os.environ.get("WALL_API", None)
    MONGO_URI = os.environ.get("MONGO_DB_URI", None)
    MONGO_PORT = int(os.environ.get("MONGO_PORT", None))
    MONGO_DB = os.environ.get("MONGO_DB", None)
    REDIS_URL = os.environ.get("REDIS_URI", None)
    BOT_ID = int(os.environ.get("BOT_ID", None))
    SUPPORT_CHAT = os.environ.get("SUPPORT_CHAT", None)
    SPAMWATCH_SUPPORT_CHAT = os.environ.get("SPAMWATCH_SUPPORT_CHAT", None)
    SPAMWATCH_API = os.environ.get("SPAMWATCH_API", None)
    ARQ_API_URL =  "https://thearq.tech"
    ARQ_API_KEY = "YIECCC-NAJARO-OLLREW-SJSRIP-ARQ"
    REM_BG_API_KEY = os.environ.get("REM_BG_API_KEY", None)
    OPENWEATHERMAP_ID = os.environ.get("OPENWEATHERMAP_ID", "")
    BOT_USERNAME = os.environ.get("BOT_USERNAME", "")
    STRING_SESSION = os.environ.get("STRING_SESSION", None)
    APP_ID = os.environ.get("APP_ID", None)
    APP_HASH = os.environ.get("APP_HASH", None)
    GENIUS_API_TOKEN = os.environ.get("GENIUS_API_TOKEN", None)
    ALLOW_CHATS = os.environ.get("ALLOW_CHATS", True)
    

    try:
        BL_CHATS = set(int(x) for x in os.environ.get("BL_CHATS", "").split())
    except ValueError:
        raise Exception("Your blacklisted chats list does not contain valid integers.")

else:
    from Cutiepii_Robot.config import Development as Config

    TOKEN = Config.TOKEN

    try:
        OWNER_ID = int(Config.OWNER_ID)
    except ValueError:
        raise Exception("Your OWNER_ID variable is not a valid integer.")

    JOIN_LOGGER = Config.JOIN_LOGGER
    OWNER_USERNAME = Config.OWNER_USERNAME
    ALLOW_CHATS = Config.ALLOW_CHATS
    try:
        DRAGONS = set(int(x) for x in Config.TITANSHIFTERS or [])
        DEV_USERS = set(int(x) for x in Config.ACKERMANS or [])
    except ValueError:
        raise Exception("Your sudo or dev users list does not contain valid integers.")

    try:
        DEMONS = set(int(x) for x in Config.ROYALS or [])
    except ValueError:
        raise Exception("Your support users list does not contain valid integers.")

    try:
        WOLVES = set(int(x) for x in Config.GARRISONS or [])
    except ValueError:
        raise Exception("Your whitelisted users list does not contain valid integers.")

    try:
        TIGERS = set(int(x) for x in Config.SCOUTS or [])
    except ValueError:
        raise Exception("Your scout users list does not contain valid integers.")

    EVENT_LOGS = Config.EVENT_LOGS
    WEBHOOK = Config.WEBHOOK
    URL = Config.URL
    PORT = Config.PORT
    CERT_PATH = Config.CERT_PATH
    API_ID = Config.API_ID
    API_HASH = Config.API_HASH

    DB_URI = Config.DATABASE_URL
    DONATION_LINK = Config.DONATION_LINK
    LOAD = Config.LOAD
    NO_LOAD = Config.NO_LOAD
    DEL_CMDS = Config.DEL_CMDS
    STRICT_GBAN = Config.STRICT_GBAN
    WORKERS = Config.WORKERS
    BAN_STICKER = Config.BAN_STICKER
    ALLOW_EXCL = Config.ALLOW_EXCL
    CASH_API_KEY = Config.CASH_API_KEY
    TIME_API_KEY = Config.TIME_API_KEY
    REDIS_URL = Config.REDIS_URL
    WALL_API = Config.WALL_API
    SUPPORT_CHAT = Config.SUPPORT_CHAT
    SPAMWATCH_SUPPORT_CHAT = Config.SPAMWATCH_SUPPORT_CHAT
    SPAMWATCH_API = Config.SPAMWATCH_API
    INFOPIC = Config.INFOPIC
    APP_ID = Config.APP_ID
    APP_HASH = Config.APP_HASH
    MONGO_URI = Config.MONGO_DB_URI
    MONGO_PORT = Config.MONGO_PORT
    MONGO_DB = Config.MONGO_DB
    ARQ_API = Config.ARQ_API
    BOT_ID = Config.BOT_ID
    TEMP_DOWNLOAD_DIRECTORY = Config.TEMP_DOWNLOAD_DIRECTORY

    try:
        BL_CHATS = set(int(x) for x in Config.BL_CHATS or [])
    except ValueError:
        raise Exception("Your blacklisted chats list does not contain valid integers.")
        

DRAGONS.add(OWNER_ID)
DEV_USERS.add(OWNER_ID)

REDIS = StrictRedis.from_url(REDIS_URL,decode_responses=True)

try:

    REDIS.ping()

    LOGGER.info("[CUTIEPII]: Connecting To Yūki • Data Center • Mumbai • Redis Database")

except BaseException:

    raise Exception("[CUTIEPII ERROR]: Your Yūki • Data Center • Mumbai • Redis Database Is Not Alive, Please Check Again.")

finally:

   REDIS.ping()

   LOGGER.info("[CUTIEPII]: Connection To The Yūki • Data Center • Mumbai • Redis Database Established Successfully!")
    

if not SPAMWATCH_API:
    sw = None
    LOGGER.warning("[CUTIEPII ERROR]: SpamWatch API key Is Missing! Recheck Your Config.")
else:
    try:
        sw = spamwatch.Client(SPAMWATCH_API)
    except:
        sw = None
        LOGGER.warning("[CUTIEPII ERROR]: Can't connect to SpamWatch!")

from Cutiepii_Robot.modules.sql import SESSION

# Credits Logger
print("[CUTIEPII] CUTIEPII Is Starting. | Yūki • Black Knights Union Project | Licensed Under GPLv3.")
print("[CUTIEPII] Cutie Cutie! Successfully Connected With A  Yūki • Data Center • Mumbai")
print("[CUTIEPII] Project Maintained By: github.com/Awesome-RJ (t.me/Awesome_Rj)")


updater = tg.Updater(TOKEN, workers=WORKERS, request_kwargs={"read_timeout": 10, "connect_timeout": 10}, use_context=True, persistence=PostgresPersistence(SESSION))
print("[CUTIEPII]: TELETHON CLIENT STARTING")
telethn = TelegramClient("CUTIEPII", API_ID, API_HASH)
dispatcher = updater.dispatcher
print("[CUTIEPII]: PYROGRAM CLIENT STARTING")
pgram = Client("CUTIEPIIPyro", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)
print("[CUTIEPII]: Connecting To Yūki • Data Center • Mumbai • MongoDB Database")
mongodb = MongoClient(MONGO_URI, MONGO_PORT)[MONGO_DB]
motor = motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = motor[MONGO_DB]
engine = AIOEngine(motor, MONGO_DB)
print("[INFO]: INITIALZING AIOHTTP SESSION")
aiohttpsession = ClientSession()
# ARQ Client
print("[INFO]: INITIALIZING ARQ CLIENT")
arq = ARQ(ARQ_API_URL, ARQ_API_KEY, aiohttpsession)
print("[CUTIEPII]: Connecting To Yūki • Data Center • Mumbai • PostgreSQL Database")
ubot = TelegramClient(StringSession(STRING_SESSION), APP_ID, APP_HASH)
print("[CUTIEPII]: Connecting To Yūki • Cutiepii Userbot (t.me/Awesome_Cutiepii)")

async def get_entity(client, entity):
    entity_client = client
    if not isinstance(entity, Chat):
        try:
            entity = int(entity)
        except ValueError:
            pass
        except TypeError:
            entity = entity.id
        try:
            entity = await client.get_chat(entity)
        except (PeerIdInvalid, ChannelInvalid):
            for pgram in apps:
                if pgram != client:
                    try:
                        entity = await pgram.get_chat(entity)
                    except (PeerIdInvalid, ChannelInvalid):
                        pass
                    else:
                        entity_client = pgram
                        break
            else:
                entity = await pgram.get_chat(entity)
                entity_client = pgram
    return entity, entity_client

apps = []
apps.append(pgram)

DRAGONS = list(DRAGONS) + list(DEV_USERS)
DEV_USERS = list(DEV_USERS)
WOLVES = list(WOLVES)
DEMONS = list(DEMONS)
TIGERS = list(TIGERS)

# Load at end to ensure all prev variables have been set
from Cutiepii_Robot.modules.helper_funcs.handlers import (
    CustomCommandHandler,
    CustomMessageHandler,
    CustomRegexHandler,
)

# make sure the regex handler can take extra kwargs
tg.RegexHandler = CustomRegexHandler
tg.CommandHandler = CustomCommandHandler
tg.MessageHandler = CustomMessageHandler
