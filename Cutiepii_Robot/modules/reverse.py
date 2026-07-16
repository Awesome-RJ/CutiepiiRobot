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
from typing import Union
import httpx
from telegram import (
    Animation,
    Document,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    PhotoSize,
    Sticker,
    Update
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
from Cutiepii_Robot.modules.sql.clear_cmd_sql import get_clearcmd

CATBOX_URL = 'https://catbox.moe/user/api.php'

class UnsupportedDocumentMimeType(Exception):
    def __init__(self, mime_type: str) -> None:
        self.mime_type = mime_type
        super().__init__(f"Unsupported MIME type: {self.mime_type}")

class STRINGS:
    PROCESSING = (
        "⏳ <b>Processing...</b>\n\n"
        "🔄 Please wait while we process your request."
    )
    
    USAGE = (
        "📕 <b>Usage:</b>\n"
        "🤖 <b>Command:</b> <code>/reverse (image_url)</code>\n"
        "▪ <i>image_url is optional.</i>\n"
        "▪ <i>Reply to a message containing media to search it.</i>\n"
        "▪ <i>If multiple media files are present, only the first one will be selected.</i>\n\n"
        "╭── 🗂️ <b>Supported Media Types:</b>\n"
        "├── 🎞️ <code>Animation (GIF)</code>\n"
        "├── 📄 <code>Document</code>\n"
        "├── 🖼️ <code>Photo</code>\n"
        "╰── 🏷️ <code>Sticker</code>"
    )
    
    UNSUPPORTED_DOCUMENT_TYPE = (
        "⚠️ <b>Unsupported Document Type:</b> <code>{unsupported_document_type}</code>\n\n"
        "╭── 🗂️ <b>Supported Document Types:</b>\n"
        "├── 🎞️ <code>Animation (GIF)</code>\n"
        "├── 📄 <code>Document</code>\n"
        "├── 🖼️ <code>Photo</code>\n"
        "╰── 🏷️ <code>Sticker</code>"
    )
    
    REPLIED_MESSAGE_HAS_NO_SUPPORTED_MEDIA = (
        "⚠️ <b>No supported media found!</b>\n\n"
        "ℹ️ The replied message does not contain any supported media types.\n\n"
        "╭── 🗂️ <b>Supported Media Types:</b>\n"
        "├── 🎞️ <code>Animation (GIF)</code>\n"
        "├── 📄 <code>Document</code>\n"
        "├── 🖼️ <code>Photo</code>\n"
        "╰── 🏷️ <code>Sticker</code>"
    )
    
    DOWNLOADING_MEDIA = "⏳ <b>Downloading media...</b>"
    FAILED_TO_DOWNLOAD_MEDIA = (
        "❌ <b>Failed to download media</b>\n\n"
        "⚠️ <b>Error:</b>\n"
        "<code>{error}</code>"
    )
    
    UPLOADING_MEDIA = "⏳ <b>Uploading media...</b>"
    FAILED_TO_UPLOAD_MEDIA = (
        "❌ <b>Failed to upload image</b>\n\n"
        "⚠️ <b>Error:</b>\n"
        "<code>{error}</code>"
    )
    
    GENERATING_LINKS = "<b>❍ Generating reverse search links...</b>"
    REVERSE_RESULT = "<b>Reverse search results for the image:</b>"

async def deletion(update: Update, context: ContextTypes.DEFAULT_TYPE, delmsg):
    chat = update.effective_chat
    cleartime = get_clearcmd(chat.id, "reverse")

    if cleartime:
        import asyncio
        async def _delete_task():
            await asyncio.sleep(cleartime.time)
            try:
                if isinstance(delmsg, list):
                    for m in delmsg:
                        await m.delete()
                else:
                    await delmsg.delete()
            except:
                pass
        asyncio.create_task(_delete_task())

async def download_media_to_memory(media: Union[Animation, Document, PhotoSize, Sticker]) -> io.BytesIO:
    file = await media.get_file()
    file_stream = io.BytesIO()
    await file.download_to_memory(file_stream)
    file_stream.seek(0)
    return file_stream

def extract_media(message: Message) -> tuple[str, Union[Animation, Document, PhotoSize, Sticker], str] | None:
    if message.animation:
        return (message.animation.file_name or "animation.gif", message.animation, message.animation.mime_type or "image/gif")
    elif message.document:
        if not message.document.mime_type or not message.document.mime_type.startswith("image/"):
            raise UnsupportedDocumentMimeType(mime_type=message.document.mime_type or "unknown")
        else:
            return (message.document.file_name or "image.jpg", message.document, message.document.mime_type)
    elif message.photo:
        return ("image.jpg", message.photo[-1], "image/jpeg")
    elif message.sticker:
        sticker_mime_type = "image/webp"
        if message.sticker.is_animated:
            sticker_mime_type = "application/x-tgsticker"
        elif message.sticker.is_video:
            sticker_mime_type = "video/webm"
        
        return ("sticker.webp", message.sticker, sticker_mime_type)
    else:
        return None


@cutiepii_cmd(command=['reverse', 'grs', 'pp', 'gis', 'lens', 'glens'], rate_limit_calls=20, rate_limit_window=60, add_error_handler=True)
async def reverse(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    
    status_msg = await message.reply_text(
        text=STRINGS.PROCESSING,
        parse_mode=ParseMode.HTML
    )
    
    file_name = None
    file = None
    mime_type = None
    url = None
    
    reply_msg = message.reply_to_message
    if reply_msg:
        try:
            res = extract_media(reply_msg)
            if res:
                file_name, media, mime_type = res
            else:
                media = None
        except UnsupportedDocumentMimeType as exc:
            await status_msg.edit_text(
                text=STRINGS.UNSUPPORTED_DOCUMENT_TYPE.format(unsupported_document_type=exc.mime_type),
                parse_mode=ParseMode.HTML
            )
            return
        
        if media is not None:
            await status_msg.edit_text(
                text=STRINGS.DOWNLOADING_MEDIA,
                parse_mode=ParseMode.HTML
            )
            
            try:
                file = await download_media_to_memory(media)
            except Exception as exc:
                await status_msg.edit_text(
                    text=STRINGS.FAILED_TO_DOWNLOAD_MEDIA.format(error=exc),
                    parse_mode=ParseMode.HTML
                )
                return
        else:
            await status_msg.edit_text(
                text=STRINGS.REPLIED_MESSAGE_HAS_NO_SUPPORTED_MEDIA,
                parse_mode=ParseMode.HTML
            )
            return
    else:
        url = context.args[0] if context.args else None
    
    # If we have an image URL, we don't upload it, we use it directly as the public url!
    if file is None and url is None:
        await status_msg.edit_text(
            text=STRINGS.USAGE,
            parse_mode=ParseMode.HTML
        )
        return
        
    if file is not None:
        await status_msg.edit_text(
            text=STRINGS.UPLOADING_MEDIA,
            parse_mode=ParseMode.HTML
        )
        try:
            async with httpx.AsyncClient(timeout=30) as async_client:
                files = {"fileToUpload": (file_name, file, mime_type)}
                data = {"reqtype": "fileupload"}
                response = await async_client.post(CATBOX_URL, data=data, files=files)
                
                if response.status_code != 200:
                    await status_msg.edit_text(
                        text=STRINGS.FAILED_TO_UPLOAD_MEDIA.format(error=f"HTTP status code {response.status_code}"),
                        parse_mode=ParseMode.HTML
                    )
                    return
                
                public_url = response.text.strip()
                if not public_url.startswith("http"):
                    await status_msg.edit_text(
                        text=STRINGS.FAILED_TO_UPLOAD_MEDIA.format(error=public_url),
                        parse_mode=ParseMode.HTML
                    )
                    return
        except Exception as exc:
            await status_msg.edit_text(
                text=STRINGS.FAILED_TO_UPLOAD_MEDIA.format(error=exc),
                parse_mode=ParseMode.HTML
            )
            return
    else:
        public_url = url

    await status_msg.edit_text(
        text=STRINGS.GENERATING_LINKS,
        parse_mode=ParseMode.HTML
    )

    google_url = f"https://lens.google.com/uploadbyurl?url={public_url}"
    yandex_url = f"https://yandex.com/images/search?rpt=imageview&url={public_url}"
    bing_url = f"https://www.bing.com/images/searchbyimage?cbir=sbi&imgurl={public_url}"
    tineye_url = f"https://tineye.com/search?url={public_url}"

    buttons = [
        [
            InlineKeyboardButton("Google Lens 🔍", url=google_url),
            InlineKeyboardButton("Yandex 🖼️", url=yandex_url)
        ],
        [
            InlineKeyboardButton("Bing 🔎", url=bing_url),
            InlineKeyboardButton("TinEye 👁️", url=tineye_url)
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(buttons)
    reply_msg = await msg_text_if_needed(status_msg, message, reply_markup)
    await deletion(update, context, reply_msg)

async def msg_text_if_needed(status_msg, message, reply_markup):
    try:
        await status_msg.delete()
    except Exception:
        pass
    return await message.reply_text(STRINGS.REVERSE_RESULT, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


__mod_name__ = "Reverse"
