"""
MIT License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021 Awesome-RJ
Copyright (c) 2021, Yūki • Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

This file is part of @Cutiepii_Robot (Telegram Bot)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is

furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import aiohttp

from asyncio import sleep
from datetime import datetime

from pyrogram import filters
from pyrogram.errors import PeerIdInvalid

from Cutiepii_Robot import pgram, BOT_USERNAME


class AioHttp:
    @staticmethod
    async def get_json(link):
        async with aiohttp.ClientSession() as session, session.get(link) as resp:
            return await resp.json()

    @staticmethod
    async def get_text(link):
        async with aiohttp.ClientSession() as session, session.get(link) as resp:
            return await resp.text()

    @staticmethod
    async def get_raw(link):
        async with aiohttp.ClientSession() as session, session.get(link) as resp:
            return await resp.read()


@pgram.on_message(filters.command("spwinfo", f"spwinfo@{BOT_USERNAME}") & ~filters.edited & ~filters.bot)
async def lookup(client, message):
    cmd = message.command
    if not message.reply_to_message and len(cmd) == 1:
        get_user = message.from_user.id
    elif len(cmd) == 1:
        if message.reply_to_message.forward_from:
            get_user = message.reply_to_message.forward_from.id
        else:
            get_user = message.reply_to_message.from_user.id
    elif len(cmd) > 1:
        get_user = cmd[1]
        try:
            get_user = int(cmd[1])
        except ValueError:
            pass
    try:
        user = await client.get_chat(get_user)
    except PeerIdInvalid:
        await message.reply_text("I don't know that User.")
        sleep(2)
        return
    url = f"https://api.intellivoid.net/spamprotection/v1/lookup?query={user.id}"
    a = await AioHttp().get_json(url)
    response = a["success"]
    if response is True:
        date = a["results"]["last_updated"]
        stats = "**◢ Intellivoid• SpamProtection Info**:\n"
        stats += f' ❍ **Updated on**: `{datetime.fromtimestamp(date).strftime("%Y-%m-%d %I:%M:%S %p")}`\n'
        stats += (
            f" ❍ **Chat Info**: [Link](t.me/SpamProtectionBot/?start=00_{user.id})\n"
        )

        if a["results"]["attributes"]["is_potential_spammer"] is True:
            stats += " ❍ **User**: `USERxSPAM`\n"
        elif a["results"]["attributes"]["is_operator"] is True:
            stats += " ❍ **User**: `USERxOPERATOR`\n"
        elif a["results"]["attributes"]["is_agent"] is True:
            stats += " ❍ **User**: `USERxAGENT`\n"
        elif a["results"]["attributes"]["is_whitelisted"] is True:
            stats += " ❍ **User**: `USERxWHITELISTED`\n"

        stats += f' ❍ **Type**: `{a["results"]["entity_type"]}`\n'
        stats += (
            f' ❍ **Language**: `{a["results"]["language_prediction"]["language"]}`\n'
        )
        stats += f' ❍ **Language Probability**: `{a["results"]["language_prediction"]["probability"]}`\n'
        stats += "**Spam Prediction**:\n"
        stats += f' ❍ **Ham Prediction**: `{a["results"]["spam_prediction"]["ham_prediction"]}`\n'
        stats += f' ❍ **Spam Prediction**: `{a["results"]["spam_prediction"]["spam_prediction"]}`\n'
        stats += f'**Blacklisted**: `{a["results"]["attributes"]["is_blacklisted"]}`\n'
        if a["results"]["attributes"]["is_blacklisted"] is True:
            stats += (
                f' ❍ **Reason**: `{a["results"]["attributes"]["blacklist_reason"]}`\n'
            )
            stats += f' ❍ **Flag**: `{a["results"]["attributes"]["blacklist_flag"]}`\n'
        stats += f'**PTID**:\n`{a["results"]["private_telegram_id"]}`\n'
        await message.reply_text(stats, disable_web_page_preview=True)
    else:
        await message.reply_text("`Cannot reach SpamProtection API`")
        await sleep(3)
