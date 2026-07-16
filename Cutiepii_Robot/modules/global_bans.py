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
import time
import contextlib

from datetime import datetime
from io import BytesIO
from typing import Optional

from telegram import Update, Chat
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import ContextTypes, filters
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility
from telegram.helpers import mention_html

from Cutiepii_Robot.modules.helper_funcs.admin_status import user_admin_check, user_is_admin, AdminPerms, u_na_errmsg, bot_is_admin
from .log_channel import loggable
from .sql.users_sql import get_user_com_chats
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from Cutiepii_Robot.modules.helper_funcs.misc import send_to_list
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot import (
    DEV_USERS,
    GBAN_LOGS,
    GBAN_LOGS,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    WHITELIST_USERS,
    dispatcher,
    LOGGER,
    SUPPORT_CHAT,
)
from Cutiepii_Robot.modules.helper_funcs.chat_status import support_plus

import Cutiepii_Robot.modules.sql.global_bans_sql as sql


GBAN_ENFORCE_GROUP = -1

GBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
    "Can't remove chat owner",
}

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
    "Peer_id_invalid",
    "User not found",
}


@cutiepii_cmd(command="gban")
@support_plus
async def gban(update: Update, context: CallbackContext):  # sourcery no-metrics
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    user_id, reason = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(
            "⚠️ User not found\n\nI don't know who you're talking about, you're going to need to specify a user..."
        )
        return

    elif int(user_id) in DEV_USERS:
        await message.reply_text(
            "That user is part of my Developers\nI can't act against our own."
        )
        return

    elif int(user_id) in SUDO_USERS:
        await message.reply_text(
            "I spy, with my little eye... a Sudo! Why are you guys turning on each other?"
        )
        return

    elif int(user_id) in SUPPORT_USERS:
        await message.reply_text(
            "OOOH someone's trying to gban a Support User! *grabs popcorn*"
        )
        return

    elif int(user_id) in WHITELIST_USERS:
        await message.reply_text("That's a Whitelisted user! They cannot be banned!")
        return


    elif int(user_id) in (777000, 1087968824, 136817688):
        await message.reply_text("Huh, why would I gban Telegram bots?")
        return

    elif user_id == bot.id:
        await message.reply_text("Go find someone else to play with noob.")
        return

    try:
        user_chat = await bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            return

        await message.reply_text("I can't seem to find this user.")
        return ""
    if user_chat.type != "private":
        await message.reply_text("That's not a user!")
        return

    if sql.is_user_gbanned(user_id):

        if not reason:
            await message.reply_text(
                "This user is already gbanned; I'd change the reason, but you haven't given me one..."
            )
            return

        if old_reason := sql.update_gban_reason(
            user_id, user_chat.username or user_chat.first_name, reason
        ):
            await message.reply_text(
                "This user is already gbanned, for the following reason:\n"
                "<code>{}</code>\n"
                "I've gone and updated it with your new reason!".format(
                    html.escape(old_reason)
                ),
                parse_mode=ParseMode.HTML,
            )

        else:
            await message.reply_text(
                "This user is already gbanned, but had no reason set; I've gone and updated it!"
            )

        return

    logmsg = await message.reply_text("Blowing the dust off the BANHAMMER!")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != "private":
        chat_origin = "<b>{} ({})</b>\n".format(html.escape(chat.title), chat.id)
    else:
        chat_origin = "<b>{}</b>\n".format(chat.id)

    log_message = (
        "#GBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Banned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Banned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>"
    )

    if reason:
        if chat.type == chat.SUPERGROUP and chat.username:
            log_message += f'\n<b>Reason:</b> <a href="https://t.me/{chat.username}/{message.message_id}">{reason}</a>'
        else:
            log_message += f"\n<b>Reason:</b> <code>{reason}</code>"

    if GBAN_LOGS:
        try:
            await bot.send_message(GBAN_LOGS, log_message, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        except BadRequest:
            await bot.send_message(
                    GBAN_LOGS,
                    log_message
                    + "\n\nFormatting has been disabled due to an unexpected error.",
                    disable_web_page_preview=True
            )

    else:
        await send_to_list(bot, SUDO_USERS + SUPPORT_USERS, log_message, html=True)

    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_user_com_chats(user_id)
    gbanned_chats = 0

    for chat_item in chats:
        chat_id = int(chat_item)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            await bot.ban_chat_member(chat_id, user_id)
            gbanned_chats += 1

        except BadRequest as excp:
            if excp.message not in GBAN_ERRORS:
                await message.reply_text(f"Could not gban due to: {excp.message}")
                if GBAN_LOGS:
                    await bot.send_message(
                        GBAN_LOGS,
                        f"Could not gban due to {excp.message}",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    await send_to_list(
                        bot,
                        SUDO_USERS + SUPPORT_USERS,
                        f"Could not gban due to: {excp.message}",
                    )
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    if GBAN_LOGS:
        await logmsg.edit_text(
            log_message + f"\n<b>Chats affected:</b> <code>{gbanned_chats}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await send_to_list(
            bot,
            SUDO_USERS + SUPPORT_USERS,
            f"Gban complete! (User banned in <code>{gbanned_chats}</code> chats)",
            html=True,
        )

    end_time = time.time()
    gban_time = round((end_time - start_time), 2)

    if gban_time > 60:
        gban_time = round((gban_time / 60), 2)
    await message.reply_text("Done! Gbanned.\n<b>ID:</b> <code>{}</code>".format(user_id))
    try:
        await bot.send_message(
            user_id,
            "#GBAN"
            "You have been marked as Malicious and as such have been banned from any future groups we manage."
            f"\n<b>Reason:</b> <code>{html.escape(reason)}</code>"
            f"\n</b>Appeal Chat:</b> @{SUPPORT_CHAT}",
            parse_mode=ParseMode.HTML,
        )
    except:
        pass  # bot probably blocked by user


@cutiepii_cmd(command="ungban")
@support_plus
async def ungban(update: Update, context: CallbackContext):  # sourcery no-metrics
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    user_id = await extract_user(message, args)

    if not user_id:
        await message.reply_text(
            "⚠️ User not found\n\nI don't know who you're talking about, you're going to need to specify a user..."
        )
        return

    user_chat = await bot.get_chat(user_id)
    if user_chat.type != "private":
        await message.reply_text("That's not a user!")
        return

    if not sql.is_user_gbanned(user_id):
        await message.reply_text("This user is not gbanned!")
        return

    pre = await message.reply_text(
        f"I'll give {user_chat.first_name} a second chance, globally."
    )

    start_time = time.time()
    datetime_fmt = "%H:%M - %d-%m-%Y"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != "private":
        chat_origin = f"<b>{html.escape(chat.title)} ({chat.id})</b>\n"
    else:
        chat_origin = f"<b>{chat.id}</b>\n"

    log_message = (
        f"#UNGBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Unbanned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Unbanned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>"
    )

    if GBAN_LOGS:
        try:
            await bot.send_message(GBAN_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest:
            await bot.send_message(
                GBAN_LOGS,
                log_message
                + "\n\nFormatting has been disabled due to an unexpected error.",
            )
    else:
        await send_to_list(bot, SUDO_USERS + SUPPORT_USERS, log_message, html=True)

    chats = get_user_com_chats(user_id)
    ungbanned_chats = 0

    for chat_item in chats:
        chat_id = int(chat_item)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status == "kicked":
                await bot.unban_chat_member(chat_id, user_id)
                ungbanned_chats += 1

        except BadRequest as excp:
            if excp.message not in UNGBAN_ERRORS:
                await message.reply_text(f"Could not un-gban due to: {excp.message}")
                if GBAN_LOGS:
                    await bot.send_message(
                        GBAN_LOGS,
                        f"Could not un-gban due to: {excp.message}",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    await bot.send_message(
                        OWNER_ID, f"Could not un-gban due to: {excp.message}"
                    )
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    if GBAN_LOGS:
        await pre.edit_text(
            log_message + f"\n<b>Chats affected:</b> {ungbanned_chats}",
            parse_mode=ParseMode.HTML,
        )
    else:
        await send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "un-gban complete!")

    end_time = time.time()
    ungban_time = round((end_time - start_time), 2)

    if ungban_time > 60:
        ungban_time = round((ungban_time / 60), 2)
        text = (f"Person has been un-gbanned. Took {ungban_time} min")
    else:
        text = (f"Person has been un-gbanned. Took {ungban_time} sec")

    try:
         await message.reply_text(text)
    except BadRequest:
        await context.bot.send_message(
            chat_id=chat.id,
            text=text
    )


@cutiepii_cmd(command="gbanlist")
@support_plus
async def gbanlist(update: Update, _):
    banned_users = sql.get_gban_list()

    if not banned_users:
        await update.effective_message.reply_text(
            "There aren't any gbanned users! You're kinder than I expected..."
        )
        return

    banfile = "Screw these guys.\n"
    for user in banned_users:
        banfile += f"[x] {user['name']} - {user['user_id']}\n"
        if user["reason"]:
            banfile += f"Reason: {user['reason']}\n"

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        await update.effective_message.reply_document(
            document=output,
            filename="gbanlist.txt",
            caption="Here is the list of currently gbanned users.",
        )


async def check_and_ban(update, user_id, should_message=True):
    # from tg_bot import SPB_MODE
    chat = update.effective_chat  # type: Optional[Chat]
    if not await bot_is_admin(chat, AdminPerms.CAN_RESTRICT_MEMBERS):
        return
    if sql.is_user_gbanned(user_id):
        await update.effective_chat.ban_member(user_id)
        if should_message:
            text = (
                f"<b>Alert</b>: this user is globally banned.\n"
                f"<code>*bans them from here*</code>.\n"
                f"<b>Appeal chat</b>: @{SUPPORT_CHAT}\n"
                f"<b>User ID</b>: <code>{user_id}</code>"
            )
            user = sql.get_gbanned_user(user_id)
            if user.reason:
                text += f"\n<b>Ban Reason:</b> <code>{html.escape(user.reason)}</code>"
            try:
                await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)
            except BadRequest:
                await update.effective_chat.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    parse_mode=ParseMode.HTML)

@cutiepii_msg((filters.ALL & filters.ChatType.GROUPS), can_disable=False, group=GBAN_ENFORCE_GROUP)
async def enforce_gban(update: Update, context: CallbackContext):
    # Not using @restrict handler to avoid spamming - just ignore if can't gban.
    bot = context.bot
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    do_gban = sql.does_chat_gban(chat.id)
    try:

        if user and not await user_is_admin(update, user.id, channels=True):
            if do_gban:
                await check_and_ban(update, user.id)
            return

        if msg.new_chat_members:
            new_members = msg.new_chat_members
            for mem in new_members:
                if do_gban:
                    await check_and_ban(update, mem.id)

        # if msg.reply_to_message:
        #     user = msg.reply_to_message.from_user
        #     if user and not await user_is_admin(update, user.id, channels = True):
        #         check_and_ban(update, user.id, should_message=False)
        #         welcome_fed(update, chat, user.id)
    except Forbidden as e:
        err_msg = "\n".join([
            "An error has happened with enforce_gban:",
            str(e),
            str(user.id),
            str(chat.id),
            str(msg.message_id)
        ])
        await dispatcher.bot.send_message(GBAN_LOGS, err_msg, parse_mode=ParseMode.HTML)


@cutiepii_cmd(command=["antispam", "gbanstat"])
@user_admin_check()
@loggable
async def gbanstat(update: Update, context: CallbackContext) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if len(args) > 0:
        if not await user_is_admin(update, user.id, perm=AdminPerms.CAN_CHANGE_INFO):
            await message.reply_text("You don't have enough rights!")
            return await u_na_errmsg(message, AdminPerms.CAN_CHANGE_INFO)

        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            await update.effective_message.reply_text(
                "Antispam is now enabled ✅ "
                "I am now protecting your group from potential remote threats!")
            logmsg = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#ANTISPAM_TOGGLED\n"
                f"Antispam has been <b>enabled</b>\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            )
            return logmsg
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            await update.effective_message.reply_text(
                "I've disabled gbans in this group. GBans won't affect your users "
                "anymore. You'll be less protected from any trolls and spammers "
                "though!"
            )
            logmsg = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#ANTISPAM_TOGGLED\n"
                f"Antispam has been <b>disabled</b>\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            )
            return logmsg

    else:
        await update.effective_message.reply_text(
            "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
            "Your current setting is: {}\n"
            "When True, any gbans that happen will also happen in your group. "
            "When False, they won't, leaving you at the possible mercy of "
            "spammers.".format(sql.does_chat_gban(update.effective_chat.id))
        )
        return ''


def __stats__():
    return f"- {sql.num_gbanned_users()} gbanned users."


def __user_info__(user_id):
    if user_id in (777000, 1087968824):
        return ""

    is_gbanned = sql.is_user_gbanned(user_id)

    if user_id in [777000, 1087968824]:
        return ""
    if user_id == dispatcher.bot.id:
        return ""
    if int(user_id) in SUDO_USERS + WHITELIST_USERS:
        return ""
    if is_gbanned:
        text = "\nㅤGbanned: <b>{}</b>"
        text = text.format("Yes")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += f"\nㅤ<b>Reason:</b> <code>{html.escape(user.reason)}</code>"
        text += "\nㅤ<b>Appeal Chat:</b> @{SUPPORT_CHAT}"
    else:
        text = ""
    return text


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


async def __chat_settings__(chat_id, _):
    return f"This chat is enforcing *gbans*: `{sql.does_chat_gban(chat_id)}`."


__mod_name__ = 'AntiSpam'

__help__ = True
