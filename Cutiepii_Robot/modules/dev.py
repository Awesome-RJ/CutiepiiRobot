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

import re
import os
import subprocess
import sys
import asyncio

from Cutiepii_Robot import CUTIEPII_PTB, DEV_USERS, telethn, OWNER_ID
from Cutiepii_Robot.modules.helper_funcs.chat_status import dev_plus
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import TelegramError
from telegram.ext import CallbackContext, CommandHandler
from telegram.constants import ParseMode
from telegram.ext import CallbackQueryHandler
from statistics import mean
from time import monotonic as time
from asyncio import sleep
from telethon import events


async def leave_cb(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    callback = update.callback_query
    if callback.from_user.id not in DEV_USERS:
        callback.answer(text="This isn't for you", show_alert=True)
        return

    match = re.match(r"leavechat_cb_\((.+?)\)", callback.data)
    chat = int(match[1])
    await bot.leave_chat(chat_id=chat)
    callback.answer(text="Left chat")


@dev_plus
async def allow_groups(update: Update, context: CallbackContext) -> None:
    args = context.args
    if not args:
        state = "off" if ALLOW_CHATS else "Lockdown is " + "on"
        await update.effective_message.reply_text(f"Current state: {state}")
        return
    if args[0].lower() in ["off", "no"]:
        ALLOW_CHATS = True
    elif args[0].lower() in ["yes", "on"]:
        ALLOW_CHATS = False
    else:
        await update.effective_message.reply_text(
            "Format: /lockdown Yes/No or Off/On")
        return
    await update.effective_message.reply_text("Done! Lockdown value toggled.")


class Store:

    def __init__(self, func):
        self.func = func
        self.calls = []
        self.time = time()
        self.lock = asyncio.Lock()

    def average(self):
        return round(mean(self.calls), 2) if self.calls else 0

    def __repr__(self):
        return f"<Store func={self.func.__name__}, average={self.average()}>"

    async def __call__(self, event):
        async with self.lock:
            if not self.calls:
                self.calls = [0]
            if time() - self.time > 1:
                self.time = time()
                self.calls.append(1)
            else:
                self.calls[-1] += 1
        await self.func(event)


async def nothing(event):
    pass


messages = Store(nothing)
inline_queries = Store(nothing)
callback_queries = Store(nothing)

telethn.add_event_handler(messages, events.NewMessage())
telethn.add_event_handler(inline_queries, events.InlineQuery())
telethn.add_event_handler(callback_queries, events.CallbackQuery())


@telethn.on(events.NewMessage(pattern=r"/getstats", from_users=OWNER_ID))
async def getstats(event):
    await event.reply(
        f"**__CUTIEPII EVENT STATISTICS__**\n**Average messages:** {messages.average()}/s\n**Average Callback Queries:** {callback_queries.average()}/s\n**Average Inline Queries:** {inline_queries.average()}/s",
        parse_mode="md")


@dev_plus
async def pip_install(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    args = context.args
    if not args:
        await update.effective_message.reply_text("Enter a package name.")
        return
    if len(args) >= 1:
        cmd = f"py -m pip install {' '.join(args)}"
        process = subprocess.Popen(
            cmd.split(" "),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
        )
        stdout, stderr = process.communicate()
        reply = ""
        stderr = stderr.decode()
        if stdout := stdout.decode():
            reply += f"*Stdout*\n`{stdout}`\n"
        if stderr:
            reply += f"*Stderr*\n`{stderr}`\n"

        await message.reply_text(text=reply, parse_mode=ParseMode.MARKDOWN)


@dev_plus
async def leave(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    if args := context.args:
        chat_id = str(args[0])
        leave_msg = " ".join(args[1:])
        try:
            await context.bot.send_message(chat_id, leave_msg)
            await bot.leave_chat(int(chat_id))
            await update.effective_message.reply_text("Left chat.")
        except TelegramError:
            await update.effective_message.reply_text(
                "Failed to leave chat for some reason.")
    else:
        chat = update.effective_chat
        # user = update.effective_user
        kb = [[
            InlineKeyboardButton(text="I am sure of this action.",
                                 callback_data=f"leavechat_cb_({chat.id})")
        ]]

        await update.effective_message.reply_text(
            f"I'm going to leave {chat.title}, press the button below to confirm",
            reply_markup=InlineKeyboardMarkup(kb))


@dev_plus
async def gitpull(update: Update):
    sent_msg = await update.effective_message.reply_text(
        "Pulling all changes from remote and then attempting to restart.")
    subprocess.Popen("git pull", stdout=subprocess.PIPE, shell=True)

    sent_msg_text = sent_msg.text + "\n\nChanges pulled...I guess.. Restarting in "

    for i in reversed(range(5)):
        sent_msg.edit_text(sent_msg_text + str(i + 1))
        await sleep(1)

    sent_msg.edit_text("Restarted.")

    os.system("restart.bat")
    os.execv("start.bat", sys.argv)


@dev_plus
async def restart(update: Update):
    await update.effective_message.reply_text(
        "Exiting all Processes and starting a new Instance!")
    process = subprocess.run("pkill python3 && python3 -m Cutiepii_Robot",
                             shell=True,
                             check=True)
    process.communicate()


CUTIEPII_PTB.add_handler(CommandHandler("install", pip_install))
CUTIEPII_PTB.add_handler(CommandHandler("leave", leave))
CUTIEPII_PTB.add_handler(CommandHandler("gitpull", gitpull))
CUTIEPII_PTB.add_handler(CommandHandler("reboot", restart))
CUTIEPII_PTB.add_handler(CommandHandler("lockdown", allow_groups))
CUTIEPII_PTB.add_handler(
    CallbackQueryHandler(leave_cb, pattern=r"leavechat_cb_"))

__mod_name__ = "Dev"
