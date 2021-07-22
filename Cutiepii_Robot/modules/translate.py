import secrets
import string

import aiohttp
from cryptography.fernet import Fernet
from pyrogram import filters
from SungJinwooRobot import arq
from SungJinwooRobot import pgram as app

@app.on_message(filters.command("tr") & ~filters.edited)
async def tr(_, message):
    if len(message.command) != 2:
        return await message.reply_text("/tr [LANGUAGE_CODE]")
    lang = message.text.split(None, 1)[1]
    if not message.reply_to_message or not lang:
        return await message.reply_text(
            "Reply to a message with /tr [language code]"
            + "\nGet supported language list from here -"
            + " https://py-googletrans.readthedocs.io/en"
            + "/latest/#googletrans-languages"
        )
    if message.reply_to_message.text:
        text = message.reply_to_message.text
    elif message.reply_to_message.caption:
        text = message.reply_to_message.caption
    result = await arq.translate(text, lang)
    if not result.ok:
        return await message.reply_text(result.result)
    await message.reply_text(result.result.translatedText)
