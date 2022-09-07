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
import datetime

from telethon import events
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from Cutiepii_Robot import telethn, CUTIEPII_PTB, LOGGER
from Cutiepii_Robot.modules.helper_funcs.chat_status import dev_plus

DEBUG_MODE = False


@dev_plus
async def debug(update: Update):
    global DEBUG_MODE
    message = update.effective_message
    args = message.text.split(" " or None, 1)
    LOGGER.debug(DEBUG_MODE)
    if len(args) > 1:
        if args[1] in ("yes", "on"):
            DEBUG_MODE = True
            await update.effective_message.reply_text("Debug mode is now on.")
        elif args[1] in ("no", "off"):
            DEBUG_MODE = False
            await update.effective_message.reply_text("Debug mode is now off.")
    elif DEBUG_MODE:
        await update.effective_message.reply_text("Debug mode is currently on."
                                                  )
    else:
        await update.effective_message.reply_text(
            "Debug mode is currently off.")


@telethn.on(events.NewMessage(pattern="[/!].*"))
async def i_do_nothing_yes(event):
    if DEBUG_MODE:
        LOGGER.debug(f"-{event.sender_id} ({event.chat_id}) : {event.text}")
        if os.path.exists("updates.txt"):
            with open("updates.txt", "r") as f:
                text = f.read()
            with open("updates.txt", "w+") as f:
                f.write(
                    f"{text}\n-{event.sender_id} ({event.chat_id}) : {event.text}"
                )
        else:
            with open("updates.txt", "w+") as f:
                f.write(
                    f"- {event.sender_id} ({event.chat_id}) : {event.text} | {datetime.datetime.now()}",
                )


support_chat = os.getenv("SUPPORT_CHAT")


@dev_plus
def logs(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    with open("log.txt", "rb") as f:
        context.bot.send_document(document=f, filename=f.name, chat_id=user.id)


CUTIEPII_PTB.add_handler(CommandHandler("logs", logs))
CUTIEPII_PTB.add_handler(CommandHandler("debug", debug))

__mod_name__ = "Debug"

__command_list__ = ["debug"]
