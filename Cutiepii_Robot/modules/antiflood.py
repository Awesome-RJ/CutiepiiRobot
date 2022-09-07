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

import contextlib
import html
import re

from typing import Optional
from telegram import Update, ChatPermissions
from telegram.error import BadRequest
from telegram.constants import ParseMode, ChatType
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, filters, MessageHandler
from telegram.helpers import mention_html

from Cutiepii_Robot import CUTIEPII_PTB, WHITELIST_USERS
from Cutiepii_Robot.modules.helper_funcs.anonymous import user_admin
from Cutiepii_Robot.modules.helper_funcs.chat_status import (
    bot_admin,
    user_admin_no_reply,
    is_user_admin,
)
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.sql import antiflood_sql as sql
from Cutiepii_Robot.modules.connection import connected
from Cutiepii_Robot.modules.helper_funcs.alternate import send_message
from Cutiepii_Robot.modules.helper_funcs.string_handling import extract_time
from Cutiepii_Robot.modules.sql.approve_sql import is_approved

FLOOD_GROUP = 3


@loggable
async def check_flood(update: Update, context: CallbackContext) -> str:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    msg = update.effective_message  # type: Optional[Message]
    if not user:  # ignore channels
        return ""

    # ignore admins and whitelists
    if ((await is_user_admin(update, user.id)) or user.id in WHITELIST_USERS):
        sql.update_flood(chat.id, None)
        return ""
    # ignore approved users
    if is_approved(chat.id, user.id):
        sql.update_flood(chat.id, None)
        return
    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        if getmode == 1:
            chat.ban_member(user.id)
            execstrings = "Banned"
            tag = "BANNED"
        elif getmode == 2:
            chat.ban_member(user.id)
            chat.unban_member(user.id)
            execstrings = "Kicked"
            tag = "KICKED"
        elif getmode == 3:
            await context.bot.restrict_chat_member(
                chat.id,
                user.id,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "Muted"
            tag = "MUTED"
        elif getmode == 4:
            bantime = await extract_time(msg, getvalue)
            chat.ban_member(user.id, until_date=bantime)
            execstrings = f"Banned for {getvalue}"
            tag = "TBAN"
        elif getmode == 5:
            mutetime = await extract_time(msg, getvalue)
            await context.bot.restrict_chat_member(
                chat.id,
                user.id,
                until_date=mutetime,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = f"Muted for {getvalue}"
            tag = "TMUTE"
        send_message(msg, f"Beep Boop! Boop Beep!\n{execstrings}!")
        return f"<b>{tag}:</b>\n#{html.escape(chat.title)}\n<b>User:</b> {mention_html(user.id, user.first_name)}\nFlooded the group."

    except BadRequest:
        await msg.reply_text(
            "I can't restrict people here, give me permissions first! Until then, I'll disable anti-flood.",
        )
        sql.set_flood(chat.id, 0)
        return f"<b>{chat.title}:</b>\n#INFO\nDon't have enough permission to restrict users so automatically disabled anti-flood"


@user_admin_no_reply
@bot_admin
async def flood_button(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    query = update.callback_query
    user = update.effective_user
    if match := re.match(r"unmute_flooder\((.+?)\)", query.data):
        user_id = match[1]
        chat = update.effective_chat.id
        with contextlib.suppress(Exception):
            await bot.restrict_chat_member(
                chat,
                (user_id),
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            await update.effective_message.edit_text(
                f"Unmuted by {mention_html(user.id, user.first_name)}.",
                parse_mode=ParseMode.HTML,
            )


@user_admin
@loggable
async def set_flood(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = await connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat_id = conn
        chat_name = await CUTIEPII_PTB.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == ChatType.PRIVATE:
            send_message(
                msg,
                "This command is meant to use in group not in PM",
            )
            return ""
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if len(args) >= 1:
        val = args[0].lower()
        if val in ["off", "no", "0"]:
            sql.set_flood(chat_id, 0)
            if conn:
                await message.reply_text(
                    f"Antiflood has been disabled in {chat_name}.")
            else:
                await update.effective_message.reply_text(
                    "Antiflood has been disabled.")
        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat_id, 0)
                if conn:
                    await message.reply_text(
                        f"Antiflood has been disabled in {chat_name}.")

                else:
                    await update.effective_message.reply_text(
                        "Antiflood has been disabled.")
                return f"<b>{html.escape(chat_name)}:</b>\n#SETFLOOD\n<b>Admin:</b> {mention_html(user.id, user.first_name)}\nDisable antiflood."

            if amount <= 3:
                send_message(
                    message,
                    "Antiflood must be either 0 (disabled) or number greater than 3!",
                )
                return ""
            sql.set_flood(chat_id, amount)
            if conn:
                await message.reply_text(
                    f"Anti-flood has been set to {amount} in chat: {chat_name}"
                )
            else:
                await message.reply_text(
                    f"Successfully updated anti-flood limit to {amount}!")
            return f"<b>{html.escape(chat_name)}:</b>\n#SETFLOOD\n<b>Admin:</b> {mention_html(user.id, user.first_name)}\nSet antiflood to <code>{amount}</code>."

        else:
            await update.effective_message.reply_text(
                "Invalid argument please use a number, 'off' or 'no'")
    else:
        await message.reply_text(
            "Use `/setflood number` to enable anti-flood.\nOr use `/setflood off` to disable antiflood!.",
            parse_mode=ParseMode.MARKDOWN,
        )
    return ""


async def flood(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message

    conn = await connected(context.bot,
                           update,
                           chat,
                           user.id,
                           need_admin=False)
    if conn:
        chat_id = conn
        chat_name = CUTIEPII_PTB.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == ChatType.PRIVATE:
            send_message(
                msg,
                "This command is meant to use in group not in PM",
            )
            return
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        text = await msg.reply_text(
            f"I'm not enforcing any flood control in {chat_name}!",
        ) if conn else await msg.reply_text(
            "I'm not enforcing any flood control here!")
    elif conn:
        text = await msg.reply_text(
            f"I'm currently restricting members after {limit} consecutive messages in {chat_name}."
        )

    else:
        text = await msg.reply_text(
            f"I'm currently restricting members after {limit} consecutive messages."
        )


@user_admin
async def set_flood_mode(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    args = context.args

    conn = await connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = CUTIEPII_PTB.bot.getChat(conn)
        chat_id = conn
        chat_name = CUTIEPII_PTB.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == ChatType.PRIVATE:
            send_message(
                msg,
                "This command is meant to use in group not in PM",
            )
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() == "ban":
            settypeflood = "ban"
            sql.set_flood_strength(chat_id, 1, "0")
        elif args[0].lower() == "kick":
            settypeflood = "kick"
            sql.set_flood_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeflood = "mute"
            sql.set_flood_strength(chat_id, 3, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = (
                    "It looks like you tried to set time value for antiflood "
                    "but you didn't specified time; Try, `/setfloodmode tban <timevalue>`."
                    "Examples of time value: "
                    "4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks.")
                send_message(msg, teks, parse_mode=ParseMode.MARKDOWN)
                return
            settypeflood = f"tban for {args[1]}"
            sql.set_flood_strength(chat_id, 4, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = (
                    "It looks like you tried to set time value for antiflood "
                    "but you didn't specified time; Try, `/setfloodmode tmute <timevalue>`."
                    "Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."
                )
                send_message(msg, teks, parse_mode=ParseMode.MARKDOWN)
                return
            settypeflood = f"tmute for {args[1]}"
            sql.set_flood_strength(chat_id, 5, str(args[1]))
        else:
            send_message(
                msg,
                "I only understand ban/kick/mute/tban/tmute!",
            )
            return
        if conn:
            text = await msg.reply_text(
                f"Exceeding consecutive flood limit will result in {settypeflood} in {chat_name}!"
            )

        else:
            text = await msg.reply_text(
                f"Exceeding consecutive flood limit will result in {settypeflood}!"
            )

        return f"<b>{settypeflood}:</b>\n<b>Admin:</b> {html.escape(chat.title)}\nHas changed antiflood mode. User will {mention_html(user.id, user.first_name)}."

    getmode, getvalue = sql.get_flood_setting(chat.id)
    if getmode == 1:
        settypeflood = "ban"
    elif getmode == 2:
        settypeflood = "kick"
    elif getmode == 3:
        settypeflood = "mute"
    elif getmode == 4:
        settypeflood = f"tban for {getvalue}"
    elif getmode == 5:
        settypeflood = f"tmute for {getvalue}"
    if conn:
        text = await msg.reply_text(
            f"Sending more messages than flood limit will result in {settypeflood} in {chat_name}."
        )

    else:
        text = await msg.reply_text(
            f"Sending more message than flood limit will result in {settypeflood}."
        )

    return ""


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "Not enforcing to flood control."
    return f"Antiflood has been set to`{limit}`."


__help__ = """
Antiflood allows you to take action on users that send more than x messages in a row. Exceeding the set flood \
will result in restricting that user.
 This will mute users if they send more than 10 messages in a row, bots are ignored.
➛ /flood*:* Get the current flood control setting

• *Admins only:*
➛ /setflood <int/'no'/'off">*:* enables or disables flood control
 *Example:* `/setflood 10`
➛ /setfloodmode <ban/kick/mute/tban/tmute> <value>*:* Action to perform when user have exceeded flood limit. ban/kick/mute/tmute/tban

• *Note:*
 • Value must be filled for tban and tmute!!
 It can be:
 `5m` = 5 minutes
 `6h` = 6 hours
 `3d` = 3 days
 `1w` = 1 week
"""

__mod_name__ = "Anti-Flood"

CUTIEPII_PTB.add_handler(
    MessageHandler(
        filters.ALL & (~filters.StatusUpdate.ALL) & filters.ChatType.GROUPS,
        check_flood))
CUTIEPII_PTB.add_handler(
    CommandHandler("setflood", set_flood, filters=filters.ChatType.GROUPS))
CUTIEPII_PTB.add_handler(CommandHandler(
    "setfloodmode", set_flood_mode))  # , filters.ChatType.GROUPS)
CUTIEPII_PTB.add_handler(
    CallbackQueryHandler(flood_button, pattern=r"unmute_flooder"))
CUTIEPII_PTB.add_handler(
    CommandHandler("flood", flood, filters=filters.ChatType.GROUPS))
