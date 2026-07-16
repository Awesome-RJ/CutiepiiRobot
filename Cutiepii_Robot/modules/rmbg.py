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

import io
import os
import requests

from datetime import datetime
from telethon import types
from telethon.tl import functions
from Cutiepii_Robot.modules.helper_funcs.decorators import register
from Cutiepii_Robot import DOWNLOAD_DIRECTORY, REM_BG_API_KEY, telethn, SUPPORT_CHAT

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


@register(pattern="^/rmbg")
async def _(event):
    if event.fwd_from:
        return
    if event.is_group and not await is_register_admin(
        event.input_chat, event.message.sender_id
    ):
        return
    start = datetime.now()
    message_id = event.message.id
    if event.reply_to_msg_id:
        message_id = event.reply_to_msg_id
        reply_message = await event.get_reply_message()
        if not reply_message or not reply_message.media:
            await event.reply("Please reply to an image or document sticker to remove background.")
            return
        await event.reply("Processing background removal...")
        try:
            downloaded_file_name = await telethn.download_media(
                reply_message, DOWNLOAD_DIRECTORY
            )
        except Exception as e:
            await event.reply(str(e))
            return
        
        image_content = None
        try:
            if REM_BG_API_KEY:
                res = ReTrieveFile(downloaded_file_name)
                contentType = res.headers.get("content-type")
                if "image" in contentType:
                    image_content = res.content
                else:
                    raise ValueError(res.content.decode("UTF-8"))
            else:
                from rembg import remove
                with open(downloaded_file_name, "rb") as f:
                    input_data = f.read()
                import asyncio
                loop = asyncio.get_event_loop()
                image_content = await loop.run_in_executor(None, remove, input_data)
        except Exception as e:
            await event.reply(f"Error removing background: {e}")
            return
        finally:
            if downloaded_file_name and os.path.exists(downloaded_file_name):
                os.remove(downloaded_file_name)
    else:
        HELP_STR = "use `/rmbg` as reply to a media"
        await event.reply(HELP_STR)
        return
    
    if image_content is None:
        await event.reply("Failed to process background removal.")
        return

    with io.BytesIO(image_content) as remove_bg_image:
        remove_bg_image.name = "rmbg.png"
        await telethn.send_file(
            event.chat_id,
            remove_bg_image,
            force_document=True,
            supports_streaming=False,
            allow_cache=False,
            reply_to=message_id,
        )
    end = datetime.now()
    ms = (end - start).seconds
    await event.reply("Background Removed in {} seconds".format(ms))


def ReTrieveFile(input_file_name):
    headers = {
        "X-API-Key": REM_BG_API_KEY,
    }
    with open(input_file_name, "rb") as f:
        files = {
            "image_file": (input_file_name, f),
        }
        res = requests.post(
            "https://api.remove.bg/v1.0/removebg",
            headers=headers,
            files=files,
            allow_redirects=True,
            stream=True,
        )
    return res
