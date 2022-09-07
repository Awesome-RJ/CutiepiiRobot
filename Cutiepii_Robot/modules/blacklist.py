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
import re
from telegram import ChatPermissions, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, filters, MessageHandler
from telegram.helpers import mention_html
from telegram.constants import ParseMode, ChatType

import Cutiepii_Robot.modules.sql.blacklist_sql as sql
from Cutiepii_Robot import CUTIEPII_PTB, LOGGER
from Cutiepii_Robot.modules.connection import connected
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.helper_funcs.alternate import send_message
from Cutiepii_Robot.modules.helper_funcs.anonymous import user_admin
from Cutiepii_Robot.modules.helper_funcs.chat_status import user_not_admin

from Cutiepii_Robot.modules.helper_funcs.extraction import extract_text
from Cutiepii_Robot.modules.helper_funcs.misc import split_message
from Cutiepii_Robot.modules.helper_funcs.string_handling import extract_time
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.redis.approvals_redis import is_approved
from Cutiepii_Robot.modules.warns import warn
from Cutiepii_Robot.modules.helper_funcs.anonymous import AdminPerms

BLACKLIST_GROUP = 11


@user_admin
async def blacklist(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    if conn := await connected(context.bot,
                               update,
                               chat,
                               user.id,
                               need_admin=False):
        chat_id = conn
        chat_name = CUTIEPII_PTB.bot.getChat(conn).title
    else:
        if chat.type == "private":
            return
        chat_id = update.effective_chat.id
        chat_name = chat.title

    filter_list = f"Current blacklisted words in <b>{chat_name}</b>:\n"

    all_blacklisted = sql.get_chat_blacklist(chat_id)

    if len(args) > 0 and args[0].lower() == "copy":
        for trigger in all_blacklisted:
            filter_list += f"<code>{html.escape(trigger)}</code>\n"
    else:
        for trigger in all_blacklisted:
            filter_list += f" - <code>{html.escape(trigger)}</code>\n"

    # for trigger in all_blacklisted:
    #     filter_list += " - <code>{}</code>\n".format(html.escape(trigger))

    split_text = split_message(filter_list)
    for text in split_text:
        if (filter_list ==
                f"Current blacklisted words in <b>{html.escape(chat_name)}</b>:\n"
            ):
            send_message(
                update.effective_message,
                f"No blacklisted words in <b>{html.escape(chat_name)}</b>!",
                parse_mode=ParseMode.HTML,
            )

            return
        send_message(update.effective_message, text, parse_mode=ParseMode.HTML)


@user_admin(AdminPerms.CAN_DELETE_MESSAGES)
async def add_blacklist(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    words = msg.text.split(None, 1)

    if conn := await connected(context.bot, update, chat, user.id):
        chat_id = conn
        chat_name = CUTIEPII_PTB.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        chat_name = chat.title
    chat_name = html.escape(chat_name)

    if len(words) > 1:
        text = words[1]
        to_blacklist = list({
            trigger.strip()
            for trigger in text.split("\n") if trigger.strip()
        })

        for trigger in to_blacklist:
            sql.add_to_blacklist(chat_id, trigger.lower())

        if len(to_blacklist) == 1:
            send_message(
                update.effective_message,
                f"Added blacklist <code>{html.escape(to_blacklist[0])}</code> in chat: <b>{chat_name}</b>!",
                parse_mode=ParseMode.HTML)

        else:
            send_message(
                update.effective_message,
                f"Added blacklist trigger: <code>{len(to_blacklist)}</code> in <b>{chat_name}</b>!",
                parse_mode=ParseMode.HTML)

    else:
        send_message(
            update.effective_message,
            "Tell me which words you would like to add in blacklist.",
        )


@user_admin
async def unblacklist(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    words = msg.text.split(None, 1)

    if conn := await connected(context.bot, update, chat, user.id):
        chat_id = conn
        chat_name = CUTIEPII_PTB.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        chat_name = chat.title

    if len(words) > 1:
        text = words[1]
        to_unblacklist = list({
            trigger.strip()
            for trigger in text.split("\n") if trigger.strip()
        })
        successful = 0
        for trigger in to_unblacklist:
            success = sql.rm_from_blacklist(chat_id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                send_message(
                    msg,
                    f"Removed <code>{html.escape(to_unblacklist[0])}</code> from blacklist in <b>{html.escape(chat_name)}</b>!",
                    parse_mode=ParseMode.HTML,
                )

            else:
                send_message(msg, "This is not a blacklist trigger!")

        elif successful == len(to_unblacklist):
            send_message(
                msg,
                f"Removed <code>{successful}</code> from blacklist in <b>{html.escape(chat_name)}</b>!",
                parse_mode=ParseMode.HTML,
            )

        elif not successful:
            send_message(
                msg,
                "None of these triggers exist so it can't be removed.".format(
                    successful,
                    len(to_unblacklist) - successful),
                parse_mode=ParseMode.HTML,
            )

        else:
            send_message(
                msg,
                f"Removed <code>{successful}</code> from blacklist. {len(to_unblacklist) - successful} did not exist, so were not removed.",
                parse_mode=ParseMode.HTML,
            )

    else:
        send_message(
            msg,
            "Tell me which words you would like to remove from blacklist!",
        )


@loggable
@user_admin
async def blacklist_mode(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
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
                "This command can be only used in group not in PM",
            )
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() in ("off", "nothing", "no"):
            settypeblacklist = "do nothing"
            sql.set_blacklist_strength(chat_id, 0, "0")
        elif args[0].lower() in ("del", "delete"):
            settypeblacklist = "will delete blacklisted message"
            sql.set_blacklist_strength(chat_id, 1, "0")
        elif args[0].lower() == "warn":
            settypeblacklist = "warn the sender"
            sql.set_blacklist_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeblacklist = "mute the sender"
            sql.set_blacklist_strength(chat_id, 3, "0")
        elif args[0].lower() == "kick":
            settypeblacklist = "kick the sender"
            sql.set_blacklist_strength(chat_id, 4, "0")
        elif args[0].lower() == "ban":
            settypeblacklist = "ban the sender"
            sql.set_blacklist_strength(chat_id, 5, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = (
                    "It looks like you tried to set time value for blacklist "
                    "but you didn't specified time; Try, `/blacklistmode tban <timevalue>`."
                    "Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."
                )
                send_message(msg, teks, parse_mode=ParseMode.MARKDOWN)
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                teks = (
                    "Invalid time value!"
                    "Example of time value: `4m = 4 minutes`, `3h = 3 hours`, `6d = 6 days`, `5w = 5 weeks`."
                )
                send_message(msg, teks, parse_mode=ParseMode.MARKDOWN)
                return ""
            settypeblacklist = "temporarily ban for {}".format(args[1])
            sql.set_blacklist_strength(chat_id, 6, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = (
                    "It looks like you tried to set time value for blacklist "
                    "but you didn't specified time; Try, `/blacklistmode tmute <timevalue>`."
                    "Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."
                )
                send_message(msg, teks, parse_mode=ParseMode.MARKDOWN)
                return ""
            restime = extract_time(msg, args[1])
            if not restime:
                teks = (
                    "Invalid time value!"
                    "Example of time value: `4m = 4 minutes`, `3h = 3 hours`, `6d = 6 days`, `5w = 5 weeks`."
                )
                send_message(msg, teks, parse_mode=ParseMode.MARKDOWN)
                return ""
            settypeblacklist = "temporarily mute for {}".format(args[1])
            sql.set_blacklist_strength(chat_id, 7, str(args[1]))
        else:
            send_message(
                msg,
                "I only understand: off/del/warn/ban/kick/mute/tban/tmute!",
            )
            return ""
        if conn:
            text = "Changed blacklist mode: `{}` in *{}*!".format(
                settypeblacklist, chat_name)
        else:
            text = "Changed blacklist mode: `{}`!".format(settypeblacklist)
        send_message(msg, text, parse_mode=ParseMode.MARKDOWN)
        return ("<b>{}:</b>\n"
                "<b>Admin:</b> {}\n"
                "Changed the blacklist mode. will {}.".format(
                    html.escape(chat.title),
                    mention_html(user.id, html.escape(user.first_name)),
                    settypeblacklist,
                ))
    getmode, getvalue = sql.get_blacklist_setting(chat.id)
    if getmode == 0:
        settypeblacklist = "do nothing"
    elif getmode == 1:
        settypeblacklist = "delete"
    elif getmode == 2:
        settypeblacklist = "warn"
    elif getmode == 3:
        settypeblacklist = "mute"
    elif getmode == 4:
        settypeblacklist = "kick"
    elif getmode == 5:
        settypeblacklist = "ban"
    elif getmode == 6:
        settypeblacklist = "temporarily ban for {}".format(getvalue)
    elif getmode == 7:
        settypeblacklist = "temporarily mute for {}".format(getvalue)
    if conn:
        text = "Current blacklistmode: *{}* in *{}*.".format(
            settypeblacklist, chat_name)
    else:
        text = "Current blacklistmode: *{}*.".format(settypeblacklist)
    send_message(msg, text, parse_mode=ParseMode.MARKDOWN)
    return ""


def findall(p, s):
    i = s.find(p)
    while i != -1:
        yield i
        i = s.find(p, i + 1)


@user_not_admin
async def del_blacklist(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    bot = context.bot
    to_match = extract_text(message)

    if not to_match:
        return

    if is_approved(chat.id, user.id):
        return

    getmode, value = sql.get_blacklist_setting(chat.id)

    chat_filters = sql.get_chat_blacklist(chat.id)
    for trigger in chat_filters:
        pattern = f"( |^|[^\\w]){re.escape(trigger)}( |$|[^\\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            try:
                if getmode == 0:
                    return
                if getmode == 1:
                    await message.delete()
                elif getmode == 2:
                    await message.delete()
                    warn(
                        update.effective_user,
                        chat,
                        f"Using blacklisted trigger: {trigger}",
                        message,
                        update.effective_user,
                    )

                    return
                elif getmode == 3:
                    await message.delete()
                    await bot.restrict_chat_member(
                        chat.id,
                        update.effective_user.id,
                        permissions=ChatPermissions(can_send_messages=False),
                    )
                    await bot.sendMessage(
                        chat.id,
                        f"Muted {user.first_name} for using Blacklisted word: <code>{html.escape(to_match)}</code>!\nBlacklist caused by trigger: <code>{html.escape(trigger)}</code>",
                        disable_web_page_preview=True,
                        parse_mode=ParseMode.HTML,
                    )
                    return
                elif getmode == 4:
                    await message.delete()
                    if res := chat.unban_member(update.effective_user.id):
                        await bot.sendMessage(
                            chat.id,
                            f"Kicked {user.first_name} for using Blacklisted word: <code>{html.escape(to_match)}</code>!\nBlacklist caused by trigger: <code>{html.escape(trigger)}</code>",
                            disable_web_page_preview=True,
                            parse_mode=ParseMode.HTML,
                        )
                    return
                elif getmode == 5:
                    await message.delete()
                    chat.ban_member(user.id)
                    await bot.sendMessage(
                        chat.id,
                        f"Banned {user.first_name} for using Blacklisted word: <code>{html.escape(to_match)}</code>!\nBlacklist caused by trigger: <code>{html.escape(trigger)}</code>",
                        disable_web_page_preview=True,
                        parse_mode=ParseMode.HTML,
                    )
                    return
                elif getmode == 6:
                    await message.delete()
                    bantime = await extract_time(message, value)
                    chat.ban_member(user.id, until_date=bantime)
                    await bot.sendMessage(
                        chat.id,
                        f"Banned {user.first_name} until '{value}' for using Blacklisted word: <code>{html.escape(to_match)}</code>!\nBlacklist caused by trigger: <code>{html.escape(trigger)}</code>",
                        disable_web_page_preview=True,
                        parse_mode=ParseMode.HTML,
                    )
                    return
                elif getmode == 7:
                    await message.delete()
                    mutetime = await extract_time(message, value)
                    await bot.restrict_chat_member(
                        chat.id,
                        user.id,
                        until_date=mutetime,
                        permissions=ChatPermissions(can_send_messages=False),
                    )
                    await bot.sendMessage(
                        chat.id,
                        f"Muted {user.first_name} until '{value}' for using Blacklisted word: <code>{html.escape(to_match)}</code>!\nBlacklist caused by trigger: <code>{html.escape(trigger)}</code>",
                        disable_web_page_preview=True,
                        parse_mode=ParseMode.HTML,
                    )
                    return
            except BadRequest as excp:
                if excp.message != "Message to delete not found":
                    LOGGER.exception("Error while deleting blacklist message.")
            break


def __import_data__(chat_id, data):
    # set chat blacklist
    blacklist = data.get("blacklist", {})
    for trigger in blacklist:
        sql.add_to_blacklist(chat_id, trigger)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    blacklisted = sql.num_blacklist_chat_filters(chat_id)
    return f"There are {blacklisted} blacklisted words."


def __stats__():
    return f"➛ {sql.num_blacklist_filters()} blacklist triggers, across {sql.num_blacklist_filter_chats()} chats."


__help__ = """
Blacklists are used to stop certain triggers from being said in a group. Any time the trigger is mentioned, the message will immediately be deleted. A good combo is sometimes to pair this up with warn filters!

NOTE: Blacklists do not affect group admins.

➛ /blacklist*:* View the current blacklisted words.

Admins only:
➛ /addblacklist <triggers>*:* Add a trigger to the blacklist. Each line is considered one trigger, so using different lines will allow you to add multiple triggers.
➛ /unblacklist <triggers>*:* Remove triggers from the blacklist. Same newline logic applies here, so you can remove multiple triggers at once.
➛ /blacklistmode <off/del/warn/ban/kick/mute/tban/tmute>*:* Action to perform when someone sends blacklisted words.

Blacklist sticker is used to stop certain stickers. Whenever a sticker is sent, the message will be deleted immediately.

NOTE: Blacklist stickers do not affect the group admin

➛ /blsticker*:* See current blacklisted sticker

Only admin:
➛ /addblsticker <sticker link>*:* Add the sticker trigger to the black list. Can be added via reply sticker
➛ /unblsticker <sticker link>*:* Remove triggers from blacklist. The same newline logic applies here, so you can delete multiple triggers at once
➛ /rmblsticker <sticker link>*:* Same as above
➛ /blstickermode <delete/ban/tban/mute/tmute>*:* sets up a default action on what to do if users use blacklisted stickers

Note:
<sticker link> can be https://telegram.dog/addstickers/<stickerpackname> or just <sticker> or reply to the sticker message
"""

__mod_name__ = "Blacklists"

CUTIEPII_PTB.add_handler(
    DisableAbleCommandHandler("blacklist", blacklist, admin_ok=True))
CUTIEPII_PTB.add_handler(CommandHandler("addblacklist", add_blacklist))
CUTIEPII_PTB.add_handler(CommandHandler("unblacklist", unblacklist))
CUTIEPII_PTB.add_handler(CommandHandler("blacklistmode", blacklist_mode))
CUTIEPII_PTB.add_handler(
    MessageHandler(
        (filters.TEXT | filters.COMMAND | filters.Sticker.ALL | filters.PHOTO)
        & filters.ChatType.GROUPS, del_blacklist))
