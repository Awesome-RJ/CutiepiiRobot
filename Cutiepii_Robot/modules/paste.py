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

import os
import re

import aiofiles
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from Cutiepii_Robot.utils.pastebin import paste
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd

pattern = re.compile(
    r"^text/|json$|yaml$|xml$|toml$|x-sh$|x-shellscript$"
)


@cutiepii_cmd(command="paste")
async def paste_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    
    if not message.reply_to_message:
        return await message.reply_text(
            "Reply To A Message With /paste"
        )
    m = await message.reply_text("Pasting...")
    
    if message.reply_to_message.text:
        content = str(message.reply_to_message.text)
    elif message.reply_to_message.document:
        document = message.reply_to_message.document
        if document.file_size > 1048576:
            return await m.edit_text(
                "You can only paste files smaller than 1MB."
            )
        if not document.mime_type or not pattern.search(document.mime_type):
            return await m.edit_text("Only text files can be pasted.")
        
        file = await context.bot.get_file(document.file_id)
        doc = await file.download_to_drive()
        
        async with aiofiles.open(doc, mode="r", encoding="utf-8", errors="ignore") as f:
            content = await f.read()
        os.remove(doc)
    else:
        return await m.edit_text("Reply to a text message or document.")
    
    link = await paste(content)
    if link.startswith("Error"):
        return await m.edit_text(link)

    button = InlineKeyboardMarkup([[InlineKeyboardButton(text="Paste Link 🔗", url=link)]])
    await m.edit_text(f"Pasted successfully!", reply_markup=button)


__mod_name__ = "Paste"
