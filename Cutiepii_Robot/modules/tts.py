import html
import re
from datetime import datetime
from typing import List
import random
from telegram import ChatAction
from gtts import gTTS
import time
from telegram import ChatAction
from feedparser import parse
import json
import urllib.request
import urllib.parse
import requests
from Cutiepii_Robot import (DEV_USERS, OWNER_ID, DRAGONS, SUPPORT_CHAT, DEMONS,
                          TIGERS, WOLVES, dispatcher, updater)
from Cutiepii_Robot.__main__ import STATS, TOKEN, USER_INFO
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.helper_funcs.filters import CustomFilters
from Cutiepii_Robot.modules.helper_funcs.chat_status import sudo_plus, user_admin
from telegram import MessageEntity, ParseMode, Update, constants
from telegram.error import BadRequest
from emoji import UNICODE_EMOJI
from telegram.ext import CallbackContext, CommandHandler, Filters, run_async
from telegram.utils.helpers import mention_html

@run_async
def tts(update: Update, context: CallbackContext):
    args = context.args
    current_time = datetime.strftime(datetime.now(), "%d.%m.%Y %H:%M:%S")
    filename = datetime.now().strftime("%d%m%y-%H%M%S%f")
    reply = " ".join(args)
    update.message.chat.send_action(ChatAction.RECORD_AUDIO)
    lang="ml"
    tts = gTTS(reply, lang)
    tts.save("k.mp3")
    with open("k.mp3", "rb") as f:
        linelist = list(f)
        linecount = len(linelist)
    if linecount == 1:
        update.message.chat.send_action(ChatAction.RECORD_AUDIO)
        lang = "en"
        tts = gTTS(reply, lang)
        tts.save("k.mp3")
    with open("k.mp3", "rb") as speech:
        update.message.reply_voice(speech, quote=False)

__command_list__ = ["tts"]
__handlers__ = [TTS_HANDLER]
