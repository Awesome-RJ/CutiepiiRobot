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

import html
import contextlib
import Cutiepii_Robot.modules.sql.moderators_sql as sql

from Cutiepii_Robot import CUTIEPII_PTB
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.helper_funcs.anonymous import user_admin
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user
from Cutiepii_Robot.modules.log_channel import loggable
from telegram import Update
from telegram.ext import CallbackContext
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.helpers import mention_html


@loggable
@user_admin
async def mod(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    user_id = extract_user(message, args)
    if not user_id:
        await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user!"
        )
        return ""
    with contextlib.suppress(BadRequest):
        member = await chat.get_member(user_id)

    if member.status in ("administrator", "creator"):
        await message.reply_text("No need to Modertor an Admin!")
        return ""
    if sql.is_modd(message.chat_id, user_id):
        await message.reply_text(
            f"[{member.user['first_name']}](tg://user?id={member.user['id']}) is already moderator in {chat_title}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return ""
    sql.mod(message.chat_id, user_id)
    await message.reply_text(
        f"[{member.user['first_name']}](tg://user?id={member.user['id']}) has been moderator in {chat_title}",
        parse_mode=ParseMode.MARKDOWN,
    )
    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#MODERATOR\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}")

    return log_message


@loggable
@user_admin
async def dismod(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    user_id = extract_user(message, args)
    if not user_id:
        await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user!"
        )
        return ""
    try:
        member = await chat.get_member(user_id)
    except BadRequest:
        return ""
    if member.status in ("administrator", "creator"):
        await update.effective_message.reply_text("This Is User Admin")
        return ""
    if not sql.is_modd(message.chat_id, user_id):
        await message.reply_text(
            f"{member.user['first_name']} isn't moderator yet!")
        return ""
    sql.dismod(message.chat_id, user_id)
    await message.reply_text(
        f"{member.user['first_name']} is no longer moderator in {chat_title}.")
    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNMODERTOR\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}")

    return log_message


@user_admin
async def modd(update: Update):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    msg = "The following users are Moderator.\n"
    modd_users = sql.list_modd(message.chat_id)
    for i in modd_users:
        member = chat.get_member(int(i.user_id))
        msg += f"{member.user['first_name']}\n"
    if msg.endswith("moderator.\n"):
        await message.reply_text(f"No users are Moderator in {chat_title}.")
        return ""
    await message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


async def modr(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user_id = extract_user(message, args)
    member = await chat.get_member(user_id)
    if not user_id:
        await message.reply_text(
            "I don't know who you're talking about, you're going to need to specify a user!"
        )
        return ""
    if sql.is_modd(message.chat_id, user_id):
        await message.reply_text(
            f"{member.user['first_name']} is an moderator user.")
    else:
        await message.reply_text(
            f"{member.user['first_name']} is not an moderator user.")


__mod_name__ = "Moderation"

CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("addmod", mod))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("rmmod", dismod))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("modlist", modd))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("modcheck", modr))

__command_list__ = [
    "addmod",
    "rmmod",
    "modlist",
    "modcheck",
]
