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

import os
import time
import html
import aiohttp
import asyncio
import datetime
import tempfile

from urllib.parse import quote as urlencode
from decimal import Decimal
from datetime import timedelta
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from Cutiepii_Robot import pgram

session = aiohttp.ClientSession()
progress_callback_data = {}


def format_bytes(size):
    size = int(size)
    # 2**10 = 1024
    power = 1024
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]+'B'}"


def return_progress_string(current, total):
    filled_length = int(30 * current // total)
    return '[' + '=' * filled_length + ' ' * (30 - filled_length) + ']'


def calculate_eta(current, total, start_time):
    if not current:
        return '00:00:00'
    end_time = time.time()
    elapsed_time = end_time - start_time
    seconds = (elapsed_time * (total / current)) - elapsed_time
    thing = ''.join(str(timedelta(seconds=seconds)
                        ).split('.')[:-1]).split(', ')
    thing[-1] = thing[-1].rjust(8, '0')
    return ', '.join(thing)


@pgram.on_message(filters.command("whatanime", prefixes=(["!", "/"])))
async def whatanime(c: Client, m: Message):
    media = m.photo or m.animation or m.video or m.document
    if not media:
        reply = m.reply_to_message
        if not getattr(reply, 'empty', True):
            media = reply.photo or reply.animation or reply.video or reply.document
    if not media:
        await m.reply_text('Please reply it to a Photo or Gif or Video to work')
        return
    with tempfile.TemporaryDirectory() as tempdir:
        reply = await m.reply_text("Downloading media...")
        path = await c.download_media(media, file_name=os.path.join(tempdir, '0'), progress=progress_callback, progress_args=(reply,))
        new_path = os.path.join(tempdir, '1.png')
        proc = await asyncio.create_subprocess_exec('ffmpeg', '-i', path, '-frames:v', '1', new_path)
        await proc.communicate()
        await reply.edit_text("Uploading media to Trace.moe and finding results...")
        with open(new_path, 'rb') as file:
            async with session.post('https://api.trace.moe/search?anilistInfo', data={"image": file}) as resp:
                json = await resp.json()
    if isinstance(json, str):
        await reply.edit_text(html.escape(json))
    else:
        try:
            match = json.get("result")
        except StopIteration:
            await reply.edit_text("No match")
        else:
            match = match[0]
            title_native = match["anilist"]["title"]["native"]
            title_english = match["anilist"]["title"]["english"]
            title_romaji = match["anilist"]["title"]["romaji"]            
            anilist_id = match["anilist"]["id"]
            episode = match["episode"]
            similarity = match["similarity"]
            synonyms = match["anilist"]["synonyms"]
            is_adult = match["anilist"]["isAdult"]
            from_time = str(datetime.timedelta(seconds=match["from"])).split(
                '.', 1)[0].rjust(8, '0')
            to_time = str(datetime.timedelta(seconds=match["to"])).split(
                '.', 1)[0].rjust(8, '0')
            text = f"<b>Anime Name:</b> {title_english}"
            if title_native:
                text += f" ({title_native}) \n "
            if synonyms:
                synonyms.sort()
                syn = ", ".join(synonyms)
                text += f"\n<b>Related:</b> {syn}"

            if is_adult:
                text += "\n<b>NSFW:</b> True"
            text += f'\n<b>Similarity:</b> {(Decimal(similarity) * 100).quantize(Decimal(".01"))}%\n'
            if episode:
                text += f"<b>Episode:</b> {episode}"
            text += f"\n<b>Scene Timestamp:</b> from {from_time} to {to_time}\n"
           
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "More Info", url="https://anilist.co/anime/{}".format(anilist_id))         
            ]])

            async def _send_preview():
                with tempfile.NamedTemporaryFile() as file:
                    async with session.get(match["video"]) as resp:
                        while True:
                            chunk = await resp.content.read(10)
                            if not chunk:
                                break
                            file.write(chunk)
                    file.seek(0)
                    try:
                        await m.reply_video(file.name, caption=text, reply_markup=keyboard)
                        await reply.delete()
                    except Exception:
                        await reply.reply_text('Cannot send preview :/')
            await _send_preview()


async def progress_callback(current, total, reply):
    message_identifier = (reply.chat.id, reply.message_id)
    last_edit_time, prevtext, start_time = progress_callback_data.get(
        message_identifier, (0, None, time.time()))
    if current == total:
        try:
            progress_callback_data.pop(message_identifier)
        except KeyError:
            pass
    elif (time.time() - last_edit_time) > 1:
        if last_edit_time:
            download_speed = format_bytes(
                (total - current) / (time.time() - start_time))
        else:
            download_speed = '0 B'
        text = f'''Downloading...
<code>{return_progress_string(current, total)}</code>
<b>Total Size:</b> {format_bytes(total)}
<b>Downladed Size:</b> {format_bytes(current)}
<b>Download Speed:</b> {download_speed}/s
<b>ETA:</b> {calculate_eta(current, total, start_time)}'''
        if prevtext != text:
            await reply.edit_text(text)
            prevtext = text
            last_edit_time = time.time()
            progress_callback_data[message_identifier] = last_edit_time, prevtext, start_time
