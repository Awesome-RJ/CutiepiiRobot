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

import html
import asyncio
import re
from datetime import datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from telethon import events, Button, custom
from Cutiepii_Robot import SUDO_USERS, DEV_USERS, dispatcher, telethn
from Cutiepii_Robot.events import register
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd, register
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user
import Cutiepii_Robot.modules.sql.userinfo_sql as sql

MAX_MESSAGE_LENGTH = 4096

@cutiepii_cmd(command='me', rate_limit_calls=40, rate_limit_window=60, add_error_handler=True)
async def about_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    bot = context.bot
    message = update.effective_message
    user_id = await extract_user(message, args)

    user = await bot.get_chat(user_id) if user_id else message.from_user
    info = sql.get_user_me_info(user.id)

    if info:
        await update.effective_message.reply_text(
            f"*{user.first_name}*:\n{escape_markdown(info)}",
            parse_mode=ParseMode.MARKDOWN,
        )
    elif message.reply_to_message:
        username = message.reply_to_message.from_user.first_name
        await update.effective_message.reply_text(
            f"{username} hasn't set an info message about themselves yet!"
        )
    else:
        await update.effective_message.reply_text(
            "You haven't set an info message about yourself yet!"
        )


@cutiepii_cmd(command='setme', rate_limit_calls=40, rate_limit_window=60, add_error_handler=True)
async def set_about_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    message = update.effective_message
    user_id = message.from_user.id
    if user_id in (777000, 1087968824):
        await message.reply_text("Don't set info for Telegram bots!")
        return
    if message.reply_to_message:
        repl_message = message.reply_to_message
        repl_user_id = repl_message.from_user.id
        if repl_user_id == bot.id and (user_id in SUDO_USERS or user_id in DEV_USERS):
            user_id = repl_user_id

    text = message.text
    info = text.split(None, 1)

    if len(info) == 2:
        if len(info[1]) < MAX_MESSAGE_LENGTH // 4:
            sql.set_user_me_info(user_id, info[1])
            if user_id == bot.id:
                await message.reply_text("Updated my info!")
            else:
                await message.reply_text("Updated your info!")
        else:
            await message.reply_text(
                "The info needs to be under {} characters! You have {}.".format(
                    MAX_MESSAGE_LENGTH // 4, len(info[1])
                )
            )
    else:
        await message.reply_text(
            "You haven't set an info message about yourself yet!\n\nUsage: /setme [info text]"
        )


@cutiepii_cmd(command='bio', rate_limit_calls=40, rate_limit_window=60, add_error_handler=True)
async def about_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    bot = context.bot
    message = update.effective_message

    user_id = await extract_user(message, args)
    user = await bot.get_chat(user_id) if user_id else message.from_user
    info = sql.get_user_bio(user.id)

    if info:
        await update.effective_message.reply_text(
            "*{}*:\n{}".format(user.first_name, escape_markdown(info)),
            parse_mode=ParseMode.MARKDOWN,
        )
    elif message.reply_to_message:
        username = user.first_name
        await update.effective_message.reply_text(
            f"{username} hasn't had a message set about themselves yet!"
        )
    else:
        await update.effective_message.reply_text(
            "You haven't had a bio set about yourself yet!"
        )


@cutiepii_cmd(command='setbio', rate_limit_calls=40, rate_limit_window=60, add_error_handler=True)
async def set_about_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    sender_id = update.effective_user.id
    bot = context.bot

    if message.reply_to_message:
        repl_message = message.reply_to_message
        user_id = repl_message.from_user.id
        if user_id in (777000, 1087968824):
            await message.reply_text("Don't set bio for Telegram bots!")
            return

        if user_id == message.from_user.id:
            await message.reply_text(
                "Ha, you can't set your own bio! You're at the mercy of others here..."
            )
            return

        if user_id in [777000, 1087968824] and sender_id not in DEV_USERS:
            await message.reply_text("You are not authorised")
            return

        if user_id == bot.id and sender_id not in DEV_USERS:
            await message.reply_text("Erm... yeah, I only trust Eagle Union to set my bio.")
            return

        text = message.text
        bio = text.split(
            None, 1
        )  # use python's maxsplit to only remove the cmd, hence keeping newlines.

        if len(bio) == 2:
            if len(bio[1]) < MAX_MESSAGE_LENGTH // 4:
                sql.set_user_bio(user_id, bio[1])
                await message.reply_text(
                    "Updated {}'s bio!".format(repl_message.from_user.first_name)
                )
            else:
                await message.reply_text(
                    "Bio needs to be under {} characters! You tried to set {}.".format(
                        MAX_MESSAGE_LENGTH // 4, len(bio[1])
                    )
                )
        else:
            await message.reply_text("Please provide a text to set the bio!")
    else:
        await message.reply_text("Reply to someone to set their bio!")


def __user_info__(user_id):
    bio = html.escape(sql.get_user_bio(user_id) or "")
    me = html.escape(sql.get_user_me_info(user_id) or "")
    if bio and me:
        return f"\n<b>About user:</b>\n{me}\n<b>What others say:</b>\n{bio}\n"
    elif bio:
        return f"\n<b>What others say:</b>\n{bio}\n"
    elif me:
        return f"\n<b>About user:</b>\n{me}\n"
    else:
        return "\n"


edit_time = 5
file1 = "https://te.legra.ph/file/11cfb0be7163d32c51259.jpg"
file2 = "https://te.legra.ph/file/444028d9b3daccc947a2d.jpg"
file3 = "https://te.legra.ph/file/fdf47498b208bc63000b4.jpg"
file4 = "https://te.legra.ph/file/e8f3310b943b8b8699dcd.jpg"
file5 = "https://te.legra.ph/file/401cb7f6216764ebab161.jpg"

@register(pattern="/myinfo")
async def proboyx(event):
    chat = await event.get_chat()
    betsy = event.sender.first_name
    button = [[custom.Button.inline("Click Here", data="information")]]
    on = await telethn.send_file(event.chat_id, file=file2, caption=f"♡ Hey {betsy}, I'm Cutiepii\n♡ I'm Created By [Black Knights Union](https://t.me/Black_Knights_Union_Support)\n♡ Click The Button Below To Get Your Info", buttons=button)

    await asyncio.sleep(edit_time)
    ok = await telethn.edit_message(event.chat_id, on, file=file3, buttons=button) 

    await asyncio.sleep(edit_time)
    ok2 = await telethn.edit_message(event.chat_id, ok, file=file5, buttons=button)

    await asyncio.sleep(edit_time)
    ok3 = await telethn.edit_message(event.chat_id, ok2, file=file1, buttons=button)
    
    await asyncio.sleep(edit_time)
    ok4 = await telethn.edit_message(event.chat_id, ok3, file=file2, buttons=button)
    
    await asyncio.sleep(edit_time)
    ok5 = await telethn.edit_message(event.chat_id, ok4, file=file1, buttons=button)
    
    await asyncio.sleep(edit_time)
    ok6 = await telethn.edit_message(event.chat_id, ok5, file=file3, buttons=button)
    
    await asyncio.sleep(edit_time)
    ok7 = await telethn.edit_message(event.chat_id, ok6, file=file5, buttons=button)

    await asyncio.sleep(edit_time)
    ok7 = await telethn.edit_message(event.chat_id, ok6, file=file4, buttons=button)

@telethn.on(events.callbackquery.CallbackQuery(data=re.compile(b"information")))
async def callback_query_handler(event):
    try:
        boy = event.sender_id
        PRO = await telethn.get_entity(boy)
        NEKO = "YOUR DETAILS BY NEKO \n\n"
        NEKO += f"FIRST NAME : {PRO.first_name} \n"
        NEKO += f"LAST NAME : {PRO.last_name}\n"
        NEKO += f"YOU BOT : {PRO.bot} \n"
        NEKO += f"RESTRICTED : {PRO.restricted} \n"
        NEKO += f"USER ID : {boy}\n"
        NEKO += f"USERNAME : {PRO.username}\n"
        await event.answer(NEKO, alert=True)
    except Exception as e:
        await event.reply(f"{e}")


__mod_name__ = "Bios/Abouts"
__help__ = True
__command_list__ = ["me", "setme", "bio", "setbio", "myinfo"]
