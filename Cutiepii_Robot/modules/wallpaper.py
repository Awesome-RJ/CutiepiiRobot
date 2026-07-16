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

from random import randint
import requests

from telegram import Update
from telegram.ext import ContextTypes
CallbackContext = ContextTypes.DEFAULT_TYPE
from Cutiepii_Robot import PIXABAY_API, SUPPORT_CHAT, dispatcher, LOGGER, arq
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
from Cutiepii_Robot.modules.sql.clear_cmd_sql import get_clearcmd

@cutiepii_cmd(command="wall", can_disable=True)
async def wall(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    args = context.args
    msg_id = update.effective_message.message_id
    bot = context.bot
    query = " ".join(args)
    if not query:
        await msg.reply_text("Please enter a query!")
        return
    else:
        caption = query
        term = query.replace(" ", "+")
        wallpaper = None
        if arq:
            try:
                res = await arq.wall(query)
                if res.ok:
                    wallpapers = res.result
                    if wallpapers:
                        index = randint(0, len(wallpapers) - 1) if len(wallpapers) > 1 else 0
                        wallpaper = wallpapers[index].get("url_image")
            except Exception as e:
                LOGGER.warning(f"ARQ wallpaper search failed: {e}")

        if not wallpaper and PIXABAY_API:
            try:
                response = requests.get(f"https://pixabay.com/api/?key={PIXABAY_API}&q={term}&image_type=photo&per_page=200")
                if response.status_code == 200:
                    data = response.json()
                    wallpapers = data.get("hits")
                    if wallpapers:
                        index = randint(0, len(wallpapers) - 1) if len(wallpapers) > 1 else 0
                        wallpaper = wallpapers[index].get("largeImageURL")
            except Exception as e:
                LOGGER.warning(f"Pixabay search failed: {e}")

        if not wallpaper:
            try:
                response = requests.get(f"https://wallhaven.cc/api/v1/search?q={term}")
                if response.status_code == 200:
                    data = response.json()
                    wallpapers = data.get("data")
                    if wallpapers:
                        index = randint(0, len(wallpapers) - 1) if len(wallpapers) > 1 else 0
                        wallpaper = wallpapers[index].get("path")
            except Exception as e:
                LOGGER.warning(f"Wallhaven search failed: {e}")

        if not wallpaper:
            await msg.reply_text("No results found! Refine your search.")
            return
        else:
            wallpaper = wallpaper.replace("\\", "")
            
            import io
            import httpx
            img_bytes = None
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
                async with httpx.AsyncClient(timeout=20) as client:
                    response = await client.get(wallpaper, headers=headers)
                    if response.status_code == 200:
                        img_bytes = response.content
            except Exception as e:
                LOGGER.warning(f"Failed to download wallpaper locally: {e}")

            if img_bytes:
                photo_data = io.BytesIO(img_bytes)
                doc_data = io.BytesIO(img_bytes)
                filename = "wallpaper.jpg"
                if "." in wallpaper.split("/")[-1]:
                    filename = f"wallpaper.{wallpaper.split('.')[-1]}"
            else:
                photo_data = wallpaper
                doc_data = wallpaper
                filename = "wallpaper"

            delmsg_preview = await bot.send_photo(
                chat_id,
                photo=photo_data,
                caption="Preview",
                reply_to_message_id=msg_id,
                timeout=60,
            )
            delmsg = await bot.send_document(
                chat_id,
                document=doc_data,
                filename=filename,
                caption=caption,
                reply_to_message_id=msg_id,
                timeout=60,
            )

    cleartime = get_clearcmd(chat_id, "wall")

    if cleartime:
        # Schedule delete tasks (run_async removed in v20+)
        import asyncio
        async def _delete_task(msg):
            await asyncio.sleep(cleartime.time)
            try:
                await msg.delete()
            except:
                pass
        asyncio.create_task(_delete_task(delmsg_preview))
        asyncio.create_task(_delete_task(delmsg))

__mod_name__ = "Wallpaper"
