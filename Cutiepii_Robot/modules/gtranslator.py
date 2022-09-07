"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, [ https://github.com/Awesome-RJ ]
Copyright (c) 2021-2022, Yūki • Black Knights Union, [ https://github.com/Awesome-RJ/CutiepiiRobot ]

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
import os
import json
import requests

from gtts import gTTS
from gpytranslate import SyncTranslator
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext
from telegram.constants import ParseMode

from Cutiepii_Robot import CUTIEPII_PTB
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler

trans = SyncTranslator()


async def translate(update: Update, context: CallbackContext) -> None:
    global to_translate
    message = update.effective_message
    reply_msg = message.reply_to_message

    if not reply_msg:
        await update.effective_message.reply_text(
            "Reply to a message to translate it!")
        return
    if reply_msg.caption:
        to_translate = reply_msg.caption
    elif reply_msg.text:
        to_translate = reply_msg.text
    try:
        args = message.text.split()[1].lower()
        if "//" in args:
            source = args.split("//")[0]
            dest = args.split("//")[1]
        else:
            source = await trans.detect(to_translate)
            dest = args
    except IndexError:
        source = await trans.detect(to_translate)
        dest = "en"
    translation = trans(to_translate, sourcelang=source, targetlang=dest)
    reply = (f"<b>Language: {source} -> {dest}</b>:\n\n"
             f"Translation: <code>{translation.text}</code>")

    await update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)


async def languages(update: Update) -> None:
    await update.effective_message.reply_text(
        "Click on the button below to see the list of supported language codes.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Language codes",
                        url="https://telegra.ph/Lang-Codes-03-19-3",
                    ),
                ],
            ],
            disable_web_page_preview=True,
        ),
    )


async def gtts(update: Update, context: CallbackContext) -> None:
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
            msg.reply_audio(speech)
    finally:
        if os.path.isfile("Cutiepii.mp3"):
            os.remove("Cutiepii.mp3")


# Open API key
API_KEY = "6ae0c3a0-afdc-4532-a810-82ded0054236"
URL = "http://services.gingersoftware.com/Ginger/correct/json/GingerTheText"


async def spellcheck(update: Update):
    if update.effective_update.effective_message.reply_to_message:
        msg = update.effective_message.reply_to_message

        params = dict(lang="US",
                      clientVersion="2.0",
                      apiKey=API_KEY,
                      text=msg.text)

        res = requests.get(URL, params=params)
        changes = json.loads(res.text).get("LightGingerTheTextResult")
        curr_string = ""
        prev_end = 0

        for change in changes:
            start = change.get("From")
            end = change.get("To") + 1
            if suggestions := change.get("Suggestions"):
                sugg_str = suggestions[0].get(
                    "Text")  # should look at this list more
                curr_string += msg.text[prev_end:start] + sugg_str
                prev_end = end

        curr_string += msg.text[prev_end:]
        await update.effective_message.reply_text(curr_string)
    else:
        await update.effective_message.reply_text(
            "Reply to some message to get grammar corrected text!")


CUTIEPII_PTB.add_handler(DisableAbleCommandHandler(["tr", "tl"], translate))
CUTIEPII_PTB.add_handler(
    DisableAbleCommandHandler(["langs", "lang"], languages))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("tts", gtts))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("splcheck", spellcheck))

__help__ = """
*Commands:*
➛ /langs: List of all language code to translates!
➛ /tl` (or `/tr`)*:* as a reply to a message, translates it to English.
➛ /tl <lang>*:* translates to <lang>

eg: `/tl ja`: translates to Japanese.
➛ /tl <source>//<dest>*:* translates from <source> to <lang>.

• [List of supported languages for translation](https://telegra.ph/Lang-Codes-03-19-3)
"""

__mod_name__ = "Translator"
__command_list__ = ["tr", "tl", "lang", "languages", "splcheck", "tts"]
