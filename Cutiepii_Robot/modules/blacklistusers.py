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
import Cutiepii_Robot.modules.sql.blacklistusers_sql as sql

from Cutiepii_Robot import (
    DEV_USERS,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    TIGER_USERS,
    WHITELIST_USERS,
    CUTIEPII_PTB,
)
from Cutiepii_Robot.modules.helper_funcs.chat_status import dev_plus
from Cutiepii_Robot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from Cutiepii_Robot.modules.log_channel import gloggable
from telegram import Update
from telegram.error import BadRequest
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CommandHandler, filters
from telegram.helpers import mention_html

BLACKLISTWHITELIST = [
    OWNER_ID
] + DEV_USERS + SUDO_USERS + WHITELIST_USERS + SUPPORT_USERS
BLABLEUSERS = [OWNER_ID] + DEV_USERS


@dev_plus
@gloggable
async def bl_user(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id, reason = await extract_user_and_text(message, args)

    if not user_id:
        await update.effective_message.reply_text("I doubt that's a user.")
        return ""

    if user_id == bot.id:
        await update.effective_message.reply_text(
            "How am I supposed to do my work if I am ignoring myself?")
        return ""

    if user_id in BLACKLISTWHITELIST:
        await update.effective_message.reply_text(
            "No!\nNoticing Disasters is my job.")
        return ""

    try:
        target_user = await bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await update.effective_message.reply_text(
                "I can't seem to find this user.")
            return ""
        raise

    sql.blacklist_user(user_id, reason)
    await update.effective_message.reply_text(
        "I shall ignore the existence of this user!")
    log_message = (
        f"#BLACKLIST\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(target_user.id, html.escape(target_user.first_name))}"
    )
    if reason:
        log_message += f"\n<b>Reason:</b> {reason}"

    return log_message


@dev_plus
@gloggable
async def unbl_user(update: Update, context: CallbackContext) -> str:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    user_id = extract_user(message, args)

    if not user_id:
        await update.effective_message.reply_text("I doubt that's a user.")
        return ""

    if user_id == bot.id:
        await update.effective_message.reply_text("I always notice myself.")
        return ""

    try:
        target_user = await bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await update.effective_message.reply_text(
                "I can't seem to find this user.")
            return ""
        raise

    if sql.is_user_blacklisted(user_id):

        sql.unblacklist_user(user_id)
        await update.effective_message.reply_text("*notices user*")
        log_message = (
            f"#UNBLACKLIST\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(target_user.id, html.escape(target_user.first_name))}"
        )

        return log_message
    await update.effective_message.reply_text(
        "I am not ignoring them at all though!")
    return ""


@dev_plus
async def bl_users(context: CallbackContext):
    users = []
    bot = context.bot
    for each_user in sql.BLACKLIST_USERS:
        user = await bot.get_chat(each_user)
        if reason := sql.get_reason(each_user):
            users.append(
                f"➛ {mention_html(user.id, html.escape(user.first_name))} :- {reason}",
            )
        else:
            users.append(
                f"➛ {mention_html(user.id, html.escape(user.first_name))}")

    message = "<b>Blacklisted Users</b>\n" + (
        "\n".join(users) if users else "Noone is being ignored as of yet.")

    await message.reply_text(message, parse_mode=ParseMode.HTML)


def __user_info__(user_id):
    is_blacklisted = sql.is_user_blacklisted(user_id)

    text = "Blacklisted: <b>{}</b>"
    if user_id in [777000, 1087968824]:
        return ""
    if user_id == 1241223850:
        return ""
    if (user_id) in SUDO_USERS + TIGER_USERS + WHITELIST_USERS:
        return ""
    if is_blacklisted:
        text = text.format("Yes")
        if reason := sql.get_reason(user_id):
            text += f"\nReason: <code>{reason}</code>"
    else:
        text = text.format("No")

    return text


CUTIEPII_PTB.add_handler(
    CommandHandler("ignore", unbl_user, filters=filters.User(OWNER_ID)))
CUTIEPII_PTB.add_handler(
    CommandHandler("notice", unbl_user, filters=filters.User(OWNER_ID)))
CUTIEPII_PTB.add_handler(
    CommandHandler("ignoredlist", bl_users, filters=filters.User(OWNER_ID)))

__mod_name__ = "Blacklisting Users"
