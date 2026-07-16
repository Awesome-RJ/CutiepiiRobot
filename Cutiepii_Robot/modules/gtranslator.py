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
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd, register
import os
import json
import html
import asyncio
import requests
import urllib.request

from gtts import gTTS
from datetime import datetime
from typing import List
from typing import Optional
from gpytranslate import SyncTranslator

from telethon import *
from telethon import events
from telethon.tl import functions
from telethon.tl import types
from telethon.tl.types import *

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode as PM, ChatAction
from telegram.ext import ContextTypes
from telegram.error import BadRequest, TimedOut, NetworkError
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility

from Cutiepii_Robot import *
from Cutiepii_Robot import dispatcher, telethn 
from Cutiepii_Robot.events import register
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.helper_funcs.alternate import typing_action, send_action

trans = SyncTranslator()

async def translate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    reply_msg = message.reply_to_message

    if not reply_msg:
        await message.reply_text("Reply to a message to translate it!")
        return

    to_translate = reply_msg.caption or reply_msg.text
    if not to_translate:
        await message.reply_text("No text found to translate.")
        return

    try:
        args = message.text.split()[1].lower()
        if "//" in args:
            source, dest = args.split("//", 1)
        else:
            source = await asyncio.to_thread(trans.detect, to_translate)
            dest = args
    except IndexError:
        source = await asyncio.to_thread(trans.detect, to_translate)
        dest = "en"

    try:
        translation = await asyncio.to_thread(
            trans, to_translate, sourcelang=source, targetlang=dest
        )
    except Exception as e:
        await message.reply_text(f"Translation failed: {html.escape(str(e))}", parse_mode=PM.HTML)
        return

    translated_text = html.escape(translation.text)
    if len(translated_text) > 3500:
        translated_text = translated_text[:3500] + "..."

    reply = (
        f"<b>Language: {html.escape(str(source))} → {html.escape(str(dest))}</b>:\n\n"
        f"Translation: <code>{translated_text}</code>"
    )

    try:
        await message.reply_text(reply, parse_mode=PM.HTML)
    except (TimedOut, NetworkError):
        try:
            await message.reply_text(translation.text[:4000])
        except Exception:
            await message.reply_text("Translation completed, but sending the reply timed out. Try again.")
    except BadRequest as e:
        if "Can't parse entities" in str(e):
            await message.reply_text(translation.text[:4000])
        else:
            raise

    
@cutiepii_cmd(command=["langs", "lang"], can_disable=True)
async def languages(update: Update, context: CallbackContext) -> None:
    await update.effective_message.reply_text(
        "Click on the button below to see the list of supported language codes.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Language codes",
                        url="https://te.legra.ph/Lang-Codes-03-19-3",
                    ),
                ],
            ],
        ),
        disable_web_page_preview=True,
    )


async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):
        return isinstance(
            (
                await telethn(functions.channels.GetParticipantRequest(chat, user))
            ).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerUser):
        return True


@register(pattern="^/stt$")
async def _(event):
    if event.fwd_from:
        return
    start = datetime.now()
    if not os.path.isdir(DOWNLOAD_DIRECTORY):
        os.makedirs(DOWNLOAD_DIRECTORY)

    if event.reply_to_msg_id:
        previous_message = await event.get_reply_message()
        required_file_name = await event.client.download_media(
            previous_message, DOWNLOAD_DIRECTORY
        )
        if IBM_WATSON_CRED_URL is None or IBM_WATSON_CRED_PASSWORD is None:
            await event.reply(
                "You need to set the required ENV variables for this module. \nModule stopping"
            )
        else:
            # await event.reply("Starting analysis")
            headers = {
                "Content-Type": previous_message.media.document.mime_type,
            }
            data = open(required_file_name, "rb").read()
            response = requests.post(
                IBM_WATSON_CRED_URL + "/v1/recognize",
                headers=headers,
                data=data,
                auth=("apikey", IBM_WATSON_CRED_PASSWORD),
            )
            r = response.json()
            if "results" in r:
                # process the json to appropriate string format
                results = r["results"]
                transcript_response = ""
                transcript_confidence = ""
                for alternative in results:
                    alternatives = alternative["alternatives"][0]
                    transcript_response += " " + str(alternatives["transcript"])
                    transcript_confidence += (
                        " " + str(alternatives["confidence"]) + " + "
                    )
                end = datetime.now()
                ms = (end - start).seconds
                if transcript_response != "":
                    string_to_show = "TRANSCRIPT: `{}`\nTime Taken: {} seconds\nConfidence: `{}`".format(
                        transcript_response, ms, transcript_confidence
                    )
                else:
                    string_to_show = "TRANSCRIPT: `Nil`\nTime Taken: {} seconds\n\n**No Results Found**".format(
                        ms
                    )
                await event.reply(string_to_show)
            else:
                await event.reply(r["error"])
            # now, remove the temporary file
            os.remove(required_file_name)
    else:
        await event.reply("Reply to a voice message, to get the text out of it.")

@send_action(ChatAction.RECORD_VOICE)
@cutiepii_cmd(command="tts", can_disable=True)
async def gtts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    reply = " ".join(context.args)
    if not reply:
        if msg.reply_to_message:
            reply = msg.reply_to_message.text
        else:
            return await msg.reply_text(
                "Reply to some message or enter some text to convert it into audio format!"
            )
        for x in "\n":
            reply = reply.replace(x, "")
    try:
        tts = gTTS(reply)
        tts.save("Cutiepii.mp3")
        with open("Cutiepii.mp3", "rb") as speech:
            await msg.reply_audio(speech)
    finally:
        if os.path.isfile("Cutiepii.mp3"):
            os.remove("Cutiepii.mp3")


# Open API key
API_KEY = ""
URL = "https://services.gingersoftware.com/Ginger/correct/json/GingerTheText"


@typing_action
@cutiepii_cmd(command="splcheck", can_disable=True)
async def spellcheck(update, _):
    if update.effective_update.effective_message.reply_to_message:
        msg = update.effective_message.reply_to_message

        params = dict(lang="US", clientVersion="2.0", apiKey=API_KEY, text=msg.text)

        res = requests.get(URL, params=params)
        changes = json.loads(res.text).get("LightGingerTheTextResult")
        curr_string = ""
        prev_end = 0

        for change in changes:
            start = change.get("From")
            end = change.get("To") + 1
            if suggestions := change.get("Suggestions"):
                sugg_str = suggestions[0].get("Text")  # should look at this list more
                curr_string += msg.text[prev_end:start] + sugg_str
                prev_end = end

        curr_string += msg.text[prev_end:]
        await update.effective_message.reply_text(curr_string)
    else:
        await update.effective_message.reply_text(
            "Reply to some message to get grammar corrected text!"
        )

# Handlers for tr/tl moved to translate.py to avoid duplicate responses
# dispatcher.add_handler(
#     DisableAbleCommandHandler(["tr", "tl"], translate)
# )

__help__ = True

__mod_name__ = "Translator"
__command_list__ = ["tr", "tl", "lang", "languages", "splcheck", "tts"]
