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

from time import sleep
from Cutiepii_Robot import CUTIEPII_PTB
from Cutiepii_Robot.modules.helper_funcs.chat_status import dev_plus
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user
from Cutiepii_Robot.modules.sql.users_sql import get_user_com_chats

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, RetryAfter, Forbidden
from telegram.ext import CallbackContext, CommandHandler


@dev_plus
async def get_user_common_chats(update: Update,
                                context: CallbackContext) -> None:
    bot, args = context.bot, context.args
    msg = update.effective_message
    user = extract_user(msg, args)
    if not user:
        await msg.reply_text("I share no common chats with the void.")
        return
    common_list = get_user_com_chats(user)
    if not common_list:
        await msg.reply_text("No common chats with this user!")
        return
    name = await bot.get_chat(user).first_name
    text = f"<b>Common chats with {name}</b>\n"
    for chat in common_list:
        try:
            chat_name = await bot.get_chat(chat).title
            await sleep(0.3)
            text += f"➛ <code>{chat_name}</code>\n"
        except (BadRequest, Forbidden):
            pass
        except RetryAfter as e:
            await sleep(e.retry_after)

    if len(text) < 4096:
        await msg.reply_text(text, parse_mode=ParseMode.HTML)
    else:
        with open("common_chats.txt", "w") as f:
            f.write(text)
        with open("common_chats.txt", "rb") as f:
            msg.reply_document(f)
        os.remove("common_chats.txt")


CUTIEPII_PTB.add_handler(CommandHandler("getchats", get_user_common_chats))
