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

from requests import get
from telegram import Update
from telegram.ext import CallbackContext
from telegram.error import BadRequest
from Cutiepii_Robot import CUTIEPII_PTB
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler


async def ud(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message
    args = context.args
    text = " ".join(args).lower()
    if not text:
        await msg.reply_text("Please enter keywords to search on ud!")
        return
    if text == "Cutiepii":
        await msg.reply_text(
            "Cutiepii is my owner so if you search him on urban dictionary you can't find the meaning because he is my husband and only me who know what's the meaning of!"
        )
        return
    try:
        results = get(
            f"http://api.urbandictionary.com/v0/define?term={text}").json()
        reply_text = f'Word: {text}\n\nDefinition: \n{results["list"][0]["definition"]}'
        reply_text += f'\n\nExample: \n{results["list"][0]["example"]}'
    except IndexError:
        reply_text = (
            f"Word: {text}\n\nResults: Sorry could not find any matching results!"
        )
    ignore_chars = "[]"
    reply = reply_text
    for chars in ignore_chars:
        reply = reply.replace(chars, "")
    if len(reply) >= 4096:
        reply = reply[:4096]  # max msg lenth of tg.
    try:
        await msg.reply_text(reply)
    except BadRequest as err:
        await msg.reply_text(f"Error! {err.message}")


CUTIEPII_PTB.add_handler(DisableAbleCommandHandler(["ud"], ud))

__command_list__ = ["ud"]
