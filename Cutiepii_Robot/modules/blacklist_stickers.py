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
import Cutiepii_Robot.modules.sql.blsticker_sql as sql

from typing import Optional
from Cutiepii_Robot import LOGGER, CUTIEPII_PTB
from Cutiepii_Robot.modules.connection import connected
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.helper_funcs.alternate import send_message
from Cutiepii_Robot.modules.helper_funcs.anonymous import user_admin
from Cutiepii_Robot.modules.helper_funcs.chat_status import user_not_admin
from Cutiepii_Robot.modules.helper_funcs.misc import split_message
from Cutiepii_Robot.modules.helper_funcs.string_handling import extract_time
from Cutiepii_Robot.modules.redis.approvals_redis import is_approved
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.warns import warn
from telegram import Update, ChatPermissions
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, filters, MessageHandler
from telegram.helpers import mention_html, mention_markdown
from telegram.constants import ParseMode, ChatType


def blackliststicker(update: Update, context: CallbackContext) -> None:
    global text
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    bot, args = context.bot, context.args

    sticker_list = f"<b>List blacklisted stickers currently in {chat.title}:</b>\n"

    all_stickerlist = sql.get_chat_stickers(chat.id)

    if len(args) > 0 and args[0].lower() == "copy":
        for trigger in all_stickerlist:
            sticker_list += f"<code>{html.escape(trigger)}</code>\n"
    elif len(args) == 0:
        for trigger in all_stickerlist:
            sticker_list += f" - <code>{html.escape(trigger)}</code>\n"

    split_text = split_message(sticker_list)
    for text in split_text:
        if (sticker_list ==
                f"<b>List blacklisted stickers currently in {chat.title}:</b>\n"
                .format(html.escape(chat.title))):
            send_message(
                update.effective_message,
                f"There are no blacklist stickers in <b>{html.escape(chat.title)}</b>!",
                parse_mode=ParseMode.HTML,
            )

            return
    send_message(update.effective_message, text, parse_mode=ParseMode.HTML)


@user_admin
async def add_blackliststicker(update: Update,
                               context: CallbackContext) -> None:
    bot = context.bot
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    words = msg.text.split(None, 1)
    bot = context.bot
    if conn := await connected(bot, chat, chat, user.id):
        chat_id = conn
        chat_name = CUTIEPII_PTB.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        chat_name = chat.title

    if len(words) > 1:
        text = words[1].replace("https://telegram.dog/addstickers/", "")
        to_blacklist = list(
            {
                trigger.strip()
                for trigger in text.split("\n") if trigger.strip()
            }, )

        added = 0
        for trigger in to_blacklist:
            try:
                get = await bot.getStickerSet(trigger)
                sql.add_to_stickers(chat_id, trigger.lower())
                added += 1
            except BadRequest:
                send_message(
                    msg,
                    f"Sticker `{trigger}` can not be found!",
                    parse_mode=ParseMode.MARKDOWN,
                )

        if added == 0:
            return

        if len(to_blacklist) == 1:
            send_message(
                msg,
                f"Sticker <code>{html.escape(to_blacklist[0])}</code> added to blacklist stickers in <b>{html.escape(chat_name)}</b>!",
                parse_mode=ParseMode.HTML,
            )

        else:
            send_message(
                msg,
                f"<code>{added}</code> stickers added to blacklist sticker in <b>{html.escape(chat_name)}</b>!",
                parse_mode=ParseMode.HTML,
            )

    elif msg.reply_to_message:
        added = 0
        trigger = msg.reply_to_message.sticker.set_name
        if trigger is None:
            send_message(msg, "Sticker is invalid!")
            return
        try:
            get = await bot.getStickerSet(trigger)
            sql.add_to_stickers(chat_id, trigger.lower())
            added += 1
        except BadRequest:
            send_message(
                msg,
                f"Sticker `{trigger}` can not be found!",
                parse_mode=ParseMode.MARKDOWN,
            )

        if added == 0:
            return

        send_message(
            msg,
            f"Sticker <code>{trigger}</code> added to blacklist stickers in <b>{html.escape(chat_name)}</b>!",
            parse_mode=ParseMode.HTML,
        )

    else:
        send_message(
            msg,
            "Tell me what stickers you want to add to the blacklist.",
        )


@user_admin
async def unblackliststicker(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    words = msg.text.split(None, 1)
    bot = context.bot
    if conn := await connected(bot, chat, chat, user.id):
        chat_id = conn
        chat_name = CUTIEPII_PTB.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            return
        chat_name = chat.title

    if len(words) > 1:
        text = words[1].replace("https://telegram.dog/addstickers/", "")
        to_unblacklist = list(
            {
                trigger.strip()
                for trigger in text.split("\n") if trigger.strip()
            }, )

        successful = 0
        for trigger in to_unblacklist:
            success = sql.rm_from_stickers(chat_id, trigger.lower())
            if success:
                successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                send_message(
                    msg,
                    f"Sticker <code>{html.escape(to_unblacklist[0])}</code> deleted from blacklist in <b>{html.escape(chat_name)}</b>!",
                    parse_mode=ParseMode.HTML,
                )

            else:
                send_message(
                    msg,
                    "This sticker is not on the blacklist...!",
                )

        elif successful == len(to_unblacklist):
            send_message(
                msg,
                f"Sticker <code>{successful}</code> deleted from blacklist in <b>{html.escape(chat_name)}</b>!",
                parse_mode=ParseMode.HTML,
            )

        elif not successful:
            send_message(
                msg,
                "None of these stickers exist, so they cannot be removed.",
                parse_mode=ParseMode.HTML,
            )

        else:
            send_message(
                msg,
                f"Sticker <code>{successful}</code> deleted from blacklist. {len(to_unblacklist) - successful} did not exist, so it's not deleted.",
                parse_mode=ParseMode.HTML,
            )

    elif msg.reply_to_message:
        trigger = msg.reply_to_message.sticker.set_name
        if trigger is None:
            send_message(msg, "Sticker is invalid!")
            return
        if success := sql.rm_from_stickers(chat_id, trigger.lower()):
            send_message(
                msg,
                f"Sticker <code>{trigger}</code> deleted from blacklist in <b>{chat_name}</b>!",
                parse_mode=ParseMode.HTML,
            )

        else:
            send_message(msg,
                         f"{trigger} not found on blacklisted stickers...!")
    else:
        send_message(
            msg,
            "Tell me what stickers you want to remove from the blacklist.",
        )


@loggable
@user_admin
async def blacklist_mode(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]
    bot, args = context.bot, context.args
    conn = await connected(bot, chat, chat, user.id, need_admin=True)
    if conn:
        chat = CUTIEPII_PTB.bot.getChat(conn)
        chat_id = conn
        chat_name = CUTIEPII_PTB.bot.getChat(conn).title
    else:
        if update.effective_message.chat.type == ChatType.PRIVATE:
            send_message(
                msg,
                "You can do this command in groups, not PM",
            )
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() in ["off", "nothing", "no"]:
            settypeblacklist = "turn off"
            sql.set_blacklist_strength(chat_id, 0, "0")
        elif args[0].lower() in ["del", "delete"]:
            settypeblacklist = "left, the message will be deleted"
            sql.set_blacklist_strength(chat_id, 1, "0")
        elif args[0].lower() == "warn":
            settypeblacklist = "warned"
            sql.set_blacklist_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeblacklist = "muted"
            sql.set_blacklist_strength(chat_id, 3, "0")
        elif args[0].lower() == "kick":
            settypeblacklist = "kicked"
            sql.set_blacklist_strength(chat_id, 4, "0")
        elif args[0].lower() == "ban":
            settypeblacklist = "banned"
            sql.set_blacklist_strength(chat_id, 5, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = """It looks like you are trying to set a temporary value to blacklist, but has not determined the time; use `/blstickermode tban <timevalue>`.
                                              Examples of time values: 4m = 4 minute, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                send_message(msg, teks, parse_mode=ParseMode.MARKDOWN)
                return
            settypeblacklist = f"temporary banned for {args[1]}"
            sql.set_blacklist_strength(chat_id, 6, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = """It looks like you are trying to set a temporary value to blacklist, but has not determined the time; use `/blstickermode tmute <timevalue>`.
                                              Examples of time values: 4m = 4 minute, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                send_message(msg, teks, parse_mode=ParseMode.MARKDOWN)
                return
            settypeblacklist = f"temporary muted for {args[1]}"
            sql.set_blacklist_strength(chat_id, 7, str(args[1]))
        else:
            send_message(
                msg,
                "I only understand off/del/warn/ban/kick/mute/tban/tmute!",
            )
            return
        if conn:
            text = f"Blacklist sticker mode changed, users will be `{settypeblacklist}` at *{chat_name}*!"

        else:
            text = f"Blacklist sticker mode changed, users will be `{settypeblacklist}`!"
        send_message(msg, text, parse_mode=ParseMode.MARKDOWN)
        return f"<b>{html.escape(chat.title)}:</b>\n<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\nChanged sticker blacklist mode. users will be {settypeblacklist}."

    getmode, getvalue = sql.get_blacklist_setting(chat.id)
    if getmode == 0:
        settypeblacklist = "not active"
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
        settypeblacklist = f"temporarily banned for {getvalue}"
    elif getmode == 7:
        settypeblacklist = f"temporarily muted for {getvalue}"
    if conn:
        text = f"Blacklist sticker mode is currently set to *{settypeblacklist}* in *{chat_name}*."

    else:
        text = f"Blacklist sticker mode is currently set to *{settypeblacklist}*."
    send_message(msg, text, parse_mode=ParseMode.MARKDOWN)
    return ""


@user_not_admin
async def del_blackliststicker(update: Update,
                               context: CallbackContext) -> None:
    bot = context.bot
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user
    to_match = message.sticker

    if not to_match or not to_match.set_name:
        return

    if is_approved(chat.id, user.id):  # ignore approved users
        return

    getmode, value = sql.get_blacklist_setting(chat.id)

    chat_filters = sql.get_chat_stickers(chat.id)
    for trigger in chat_filters:
        if to_match.set_name.lower() == trigger.lower():
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
                        f"Using sticker '{trigger}' which in blacklist stickers",
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
                        f"{mention_markdown(user.id, user.first_name)} muted because using '{trigger}' which in blacklist stickers",
                        parse_mode=ParseMode.MARKDOWN,
                    )

                    return
                elif getmode == 4:
                    await message.delete()
                    if res := chat.unban_member(update.effective_user.id):
                        await bot.sendMessage(
                            chat.id,
                            f"{mention_markdown(user.id, user.first_name)} kicked because using '{trigger}' which in blacklist stickers",
                            parse_mode=ParseMode.MARKDOWN,
                        )

                    return
                elif getmode == 5:
                    await message.delete()
                    chat.ban_member(user.id)
                    await bot.sendMessage(
                        chat.id,
                        f"{mention_markdown(user.id, user.first_name)} banned because using '{trigger}' which in blacklist stickers",
                        parse_mode=ParseMode.MARKDOWN,
                    )

                    return
                elif getmode == 6:
                    await message.delete()
                    bantime = await extract_time(message, value)
                    chat.ban_member(user.id, until_date=bantime)
                    await bot.sendMessage(
                        chat.id,
                        f"{mention_markdown(user.id, user.first_name)} banned for {value} because using '{trigger}' which in blacklist stickers",
                        parse_mode=ParseMode.MARKDOWN,
                    )

                    return
                elif getmode == 7:
                    await message.delete()
                    mutetime = await extract_time(message, value)
                    await bot.restrict_chat_member(
                        chat.id,
                        user.id,
                        permissions=ChatPermissions(can_send_messages=False),
                        until_date=mutetime,
                    )
                    await bot.sendMessage(
                        chat.id,
                        f"{mention_markdown(user.id, user.first_name)} muted for {value} because using '{trigger}' which in blacklist stickers",
                        parse_mode=ParseMode.MARKDOWN,
                    )

                    return
            except BadRequest as excp:
                if excp.message != "Message to delete not found":
                    LOGGER.exception("Error while deleting blacklist message.")
                break


def __import_data__(chat_id, data):
    # set chat blacklist
    blacklist = data.get("sticker_blacklist", {})
    for trigger in blacklist:
        sql.add_to_stickers(chat_id, trigger)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    blacklisted = sql.num_stickers_chat_filters(chat_id)
    return f"There are `{blacklisted} `blacklisted stickers."


def __stats__():
    return f"➛ {sql.num_stickers_filters()} blacklist stickers, across {sql.num_stickers_filter_chats()} chats."


__mod_name__ = "Stickers Blacklist"

CUTIEPII_PTB.add_handler(
    DisableAbleCommandHandler("blsticker", blackliststicker, admin_ok=True))
CUTIEPII_PTB.add_handler(
    DisableAbleCommandHandler("addblsticker", add_blackliststicker))
CUTIEPII_PTB.add_handler(
    CommandHandler(["unblsticker", "rmblsticker"], unblackliststicker))
CUTIEPII_PTB.add_handler(CommandHandler("blstickermode", blacklist_mode))
CUTIEPII_PTB.add_handler(
    MessageHandler(filters.Sticker.ALL & filters.ChatType.GROUPS,
                   del_blackliststicker))
