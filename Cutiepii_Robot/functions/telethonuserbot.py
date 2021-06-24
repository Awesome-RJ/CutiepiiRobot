import sys

from telethon import TelegramClient
from telethon.sessions import StringSession

from Cutiepii_Robot.cutiepii.config import get_int_key, get_str_key

STRING_SESSION = get_str_key("STRING_SESSION", required=False)
API_ID = get_int_key("API_ID", required=False)
API_HASH = get_str_key("API_HASH", required=False)

ubot = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
try:
    ubot.start()
except BaseException:
    print("Userbot Error ! Have you added a STRING_SESSION in deploying??")
    sys.exit(1)
