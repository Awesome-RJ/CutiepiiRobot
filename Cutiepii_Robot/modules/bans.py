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
from typing import Optional, Union

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Chat, ChatMember, Message, Update, User
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import filters, ContextTypes
from telegram.helpers import mention_html
from Cutiepii_Robot import (
    BAN_STICKER,
    DEV_USERS,
    ERROR_LOGS,
    SUDO_USERS,
    SUPPORT_USERS,
    OWNER_ID,
    WHITELIST_USERS,
    LOGGER,
    GBAN_LOGS,
    BOT_ID,
)

from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status, dev_plus
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user_and_text
from Cutiepii_Robot.modules.helper_funcs.string_handling import extract_time
from Cutiepii_Robot.modules.log_channel import loggable, gloggable
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd
from Cutiepii_Robot.modules.helper_funcs.admin_status import u_na_errmsg
from Cutiepii_Robot.modules.helper_funcs.chat_status import user_admin_no_reply


async def cannot_ban(user_id, message):
    await message.reply_text("<b>Action Denied</b>\nThe target user has administrator immunity and cannot be restricted.")

ban_myself = "<b>Action Denied</b>\nI cannot ban myself."

from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    bot_is_admin,
    user_is_admin,
)


async def ban_chat(bot, who: Chat, where_chat_id, reason=None) -> Union[str, bool]:
    try:
        await bot.ban_chat_sender_chat(where_chat_id, who.id)
    except BadRequest as excp:
        if excp.message != "Reply message not found":
            LOGGER.warning("error banning channel {}:{} in {} because: {}".format(
                    who.title, who.id, where_chat_id, excp.message))
            return False

    return (
        f"<b>Channel:</b> <a href=\"t.me/{who.username}\">{html.escape(who.title)}</a>"
        f"<b>Channel ID:</b> {who.id}"
        "" if reason is None else f"<b>Reason:</b> {reason}"
    )


async def ban_user(bot, who: ChatMember, where_chat_id, reason=None) -> Union[str, bool]:
    try:
        await bot.ban_chat_member(where_chat_id, who.user.id)
    except BadRequest as excp:
        if excp.message != "Reply message not found":
            LOGGER.warning("error banning user {}:{} in {} because: {}".format(
                    who.user.first_name, who.user.id, where_chat_id, excp.message))
            return False

    return (
        f"<b>User:</b> <a href=\"tg://user?id={who.user.id}\">{html.escape(who.user.first_name)}</a>"
        f"<b>User ID:</b> {who.user.id}"
        "" if reason is None else f"<b>Reason:</b> {reason}"
    )

async def unban_chat(bot, who: Chat, where_chat_id, reason=None) -> Union[str, bool]:
    try:
        await bot.unban_chat_sender_chat(where_chat_id, who.id)
    except BadRequest as excp:
        if excp.message != "Reply message not found":
            LOGGER.warning("error banning channel {}:{} in {} because: {}".format(
                    who.title, who.id, where_chat_id, excp.message))
            return False

    return (
        f"<b>Channel:</b> <a href=\"t.me/{who.username}\">{html.escape(who.title)}</a>"
        f"<b>Channel ID:</b> {who.id}"
        "" if reason is None else f"<b>Reason:</b> {reason}"
    )


async def unban_user(bot, who: ChatMember, where_chat_id, reason=None) -> Union[str, bool]:
    try:
        await bot.unban_chat_member(where_chat_id, who.user.id)
    except BadRequest as excp:
        if excp.message != "Reply message not found":
            LOGGER.warning("error banning user {}:{} in {} because: {}".format(
                    who.user.first_name, who.user.id, where_chat_id, excp.message))
            return False

    return (
        f"<b>User:</b> <a href=\"tg://user?id={who.user.id}\">{html.escape(who.user.first_name)}</a>"
        f"<b>User ID:</b> {who.user.id}"
        "" if reason is None else f"<b>Reason:</b> {reason}"
    )


@cutiepii_cmd(command=['ban', 'dban', 'sban', 'dsban'], rate_limit_calls=20, rate_limit_window=60, add_error_handler=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:  # sourcery no-metrics
    global delsilent
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args
    bot = context.bot

    if message.text.startswith(('/s', '!s', '>s')):
        silent = True
        if not await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            await message.reply_text("<b>Action Denied</b>\nI do not have the required delete messages permission in this chat.")
            return
    else:
        silent = False
    if message.text.startswith(('/d', '!d', '>d')):
        delban = True
        if not await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            await message.reply_text("<b>Action Denied</b>\nI do not have the required delete messages permission in this chat.")
            return
        if not await user_is_admin(update, user.id, perm = AdminPerms.CAN_DELETE_MESSAGES):
            await message.reply_text("<b>Action Denied</b>\nYou do not have the required delete messages permission in this chat.")
            return
    else:
        delban = False
    if message.text.startswith(('/ds', '!ds', '>ds')):
        delsilent = True
        if not await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            await message.reply_text("<b>Action Denied</b>\nI do not have the required delete messages permission in this chat.")
            return
        if not await user_is_admin(update, user.id, perm = AdminPerms.CAN_DELETE_MESSAGES):
            await message.reply_text("<b>Action Denied</b>\nYou do not have the required delete messages permission in this chat.")
            return

    if message.reply_to_message and message.reply_to_message.sender_chat:
        if message.reply_to_message.is_automatic_forward:
            await message.reply_text("This is a pretty bad idea, isn't it?")
            return

        if did_ban := await ban_chat(bot, message.reply_to_message.sender_chat, chat.id, reason = " ".join(args) or None):
            logmsg  = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#BANNED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
            logmsg += did_ban

            await message.reply_text("Channel {} was banned successfully from {}".format(
                html.escape(message.reply_to_message.sender_chat.title),
                html.escape(chat.title)
            ),
                parse_mode=ParseMode.HTML
            )

        else:
            await message.reply_text("Failed to ban channel")
            return ""

    user_id, reason = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text("<b>Invalid Command Usage</b>\nPlease specify a target user by replying to their message, mentioning their username, or providing their user ID.")
        return ''

    member = None
    chan = None
    try:
        member = await chat.get_member(user_id)
    except BadRequest:
        try:
            chan = await bot.get_chat(user_id)
        except BadRequest as excp:
            if excp.message != "Chat not found":
                raise
            await message.reply_text("<b>Action Denied</b>\nThe specified user or chat could not be found.")
            return ""

    if chan:
        if did_ban := await ban_chat(bot, chan, chat.id, reason = " ".join(args) or None):
            logmsg  = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#BANNED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
            logmsg += did_ban

            reply = "Channel {} was banned successfully from {}".format(
                html.escape(chan.title),
                html.escape(chat.title)
            )
            try:
                await bot.send_animation(
                    chat.id,
                    animation="https://files.catbox.moe/z44wak.mp4",
                    caption=reply,
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                await message.reply_text(
                    reply,
                    parse_mode=ParseMode.HTML,
                )

        else:
            await message.reply_text("Failed to ban channel")
            return ""

    elif user_id == BOT_ID:
        await message.reply_text(ban_myself)
        return ''

    elif await user_is_admin(update, user_id) and user.id not in DEV_USERS:
        await message.reply_text("This user has immunity and cannot be banned.")
        return ''


    elif did_ban := await ban_user(bot, member, chat.id, reason = " ".join(args) or None):
        logmsg  = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#BANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
        logmsg += did_ban

        reply = (
            f"<b>Ban Event</b>\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}"
        )
        if reason:
            reply += f"\n<b>Reason:</b> {html.escape(reason)}"

        try:
            await bot.send_animation(
                chat.id,
                animation="https://files.catbox.moe/z44wak.mp4",
                caption=reply,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Unban", callback_data=f"unbanb_unban={user_id}"
                            ),
                            InlineKeyboardButton(text="Delete", callback_data="unbanb_del"),
                        ]
                    ]
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await bot.send_message(
                chat.id,
                reply,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Unban", callback_data=f"unbanb_unban={user_id}"
                            ),
                            InlineKeyboardButton(text="Delete", callback_data="unbanb_del"),
                        ]
                    ]
                ),
                parse_mode=ParseMode.HTML,
            )
        return logmsg

    else:
        await message.reply_text("Failed to ban user")
        return ""

    if silent:
        if delsilent and message.reply_to_message:
            await message.reply_to_message.delete()
        await message.delete()
    elif delban and message.reply_to_message:
        await message.reply_to_message.delete()
    await context.bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker

    return logmsg


@cutiepii_cmd(command=['tban', 'stban', 'dtban', 'dstban'], rate_limit_calls=20, rate_limit_window=60, add_error_handler=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
async def temp_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args

    cmd_text = message.text.lstrip("/!")
    silent = False
    if message.text.startswith(('/s', '!s', '>s')) or cmd_text.startswith("st") or cmd_text.startswith("s"):
        silent = True
        if not await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            await message.reply_text("I don't have permission to delete messages here!")
            return log_message

    delban = False
    if message.text.startswith(('/d', '!d', '>d')) or cmd_text.startswith("dt") or cmd_text.startswith("d"):
        delban = True
        if not await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            await message.reply_text("I don't have permission to delete messages here!")
            return log_message
        if not await user_is_admin(update, user.id, perm = AdminPerms.CAN_DELETE_MESSAGES):
            await message.reply_text("You don't have permission to delete messages here!")
            return log_message

    user_id, reason = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text("⚠️ User not found\n\nI don't know who you're talking about, you're going to need to specify a user...")
        return log_message

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != 'User not found':
            raise
        await message.reply_text("I can't seem to find this user.")
        return log_message
    if user_id == bot.id:
        await message.reply_text(ban_myself)  
        return log_message

    elif await cannot_ban(user.id, user_id, message):
        return ''

    elif await user_is_admin(update, user_id) and user.id not in DEV_USERS:
        await message.reply_text("This user has immunity and cannot be banned.")
        return ''

    if not reason:
        if not silent:
            await message.reply_text("You haven't specified a time to ban this user for!")
        else:
            await message.delete()
        return log_message

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    bantime = await extract_time(message, time_val)

    if not bantime:
        return log_message

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        "#TEMP_BANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.first_name)}\n"
        f"<b>Time:</b> {time_val}"
    )
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        await chat.ban_member(user_id, until_date=bantime)

        if silent:
            if message.reply_to_message and (cmd_text.startswith("ds") or cmd_text.startswith("dts")):
                try:
                    await message.reply_to_message.delete()
                except Exception:
                    pass
            await message.delete()
            return log

        if delban and message.reply_to_message:
            try:
                await message.reply_to_message.delete()
            except Exception:
                pass

        await bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker

        reply_msg = (
            f"<b>╔━「 ❕ Temp Banned</b>\n"
            f"<b>- Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>- User:</b> {mention_html(member.user.id, html.escape(member.user.first_name))}\n"
            f"<b>- Time: {time_val}</b>"
        )

        if reason:
            reply_msg += f"\n<b>- Reason:</b> {html.escape(reason)}"

        try:
            await bot.send_animation(
                chat.id,
                animation="https://files.catbox.moe/z44wak.mp4",
                caption=reply_msg,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="🔄 Unban", callback_data=f"unbanb_unban={user_id}"
                            ),
                            InlineKeyboardButton(text="🗑️ Delete", callback_data="unbanb_del"),
                        ]
                    ]
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await bot.send_message(
                chat.id,
                reply_msg,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="🔄 Unban", callback_data=f"unbanb_unban={user_id}"
                            ),
                            InlineKeyboardButton(text="🗑️ Delete", callback_data="unbanb_del"),
                        ]
                    ]
                ),
                parse_mode=ParseMode.HTML,
            )

        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found" or excp.message == "Message can't be deleted":
            # Do not reply
            await message.reply_text(
                f"Banned! User will be banned for {time_val}.", do_quote=False
            )
            return log
        else:
            await bot.send_message(GBAN_LOGS, str(update))
            await bot.send_message(GBAN_LOGS, 
                "ERROR banning user {} in chat {} ({}) due to {}".format(
                user_id,
                chat.title,
                chat.id,
                excp.message)
            )
            await message.reply_text("Well damn, I can't ban that user.")

    return log_message



@cutiepii_cmd(command=['kick', 'skick', 'dkick', 'dskick', 'punch'], rate_limit_calls=25, rate_limit_window=60, add_error_handler=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
async def kick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    log_message = ""
    bot, args = context.bot, context.args

    silent = message.text[1] == 's' or message.text[2] == 's'
    delete = message.text[1] == 'd'
    if message.reply_to_message and message.reply_to_message.sender_chat:
        await message.reply_text("This command doesn't work on channels, but I can ban them if u want.")
        return log_message

    user_id, reason = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text("⚠️ User not found\n\nI don't know who you're talking about, you're going to need to specify a user...")
        return log_message

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != 'User not found':
            raise
        await message.reply_text("I can't seem to find this user.")
        return log_message
    if user_id == bot.id:
        await message.reply_text("Yeahhh I'm not gonna do that.")
        return log_message

    elif await user_is_admin(update, user_id) and user.id not in DEV_USERS:
        await message.reply_text("This user has immunity and cannot be banned.")
        return ''

    if delete and message.reply_to_message:
        if await user_is_admin(update, message.from_user.id, perm=AdminPerms.CAN_DELETE_MESSAGES):
            if await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
                await message.reply_to_message.delete()
            else:
                await update.effective_message.reply_text(
                    f"I can't perform this action due to missing permissions;\n"
                    f"Make sure i am an admin and {AdminPerms.CAN_DELETE_MESSAGES.name.lower().replace('is_', 'am ').replace('_', ' ')}!")
                return
        else:
            return await u_na_errmsg(message, AdminPerms.CAN_DELETE_MESSAGES)

    if await chat.unban_member(user_id):
        if not silent:
            msg = f"{mention_html(member.user.id, member.user.first_name)} was kicked by {mention_html(user.id, user.first_name)} in {message.chat.title}"
            if reason:
                msg += f"\n<b>Reason</b>: <code>{reason}</code>"
            try:
                await bot.send_animation(
                    chat.id,
                    animation="https://files.catbox.moe/g6yqyd.mp4",
                    caption=msg,
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                await bot.send_sticker(chat.id, BAN_STICKER)  # banhammer marie sticker
                await bot.send_message(
                    chat.id,
                    msg,
                    parse_mode=ParseMode.HTML,
                )

        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#KICKED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
        )
        if reason:
            log += f"\n<b>Reason:</b> {reason}"

        return log

    else:
        await message.reply_text("Well damn, I can't kick that user.")

    return log_message


@cutiepii_cmd(command=['kickme', 'punchme'], filters=filters.ChatType.GROUPS)
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def kickme(update: Update, _: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    user_id = update.effective_message.from_user.id
    user = update.effective_message.from_user
    chat = update.effective_chat
    if await user_is_admin(update.effective_chat, user_id):
        await update.effective_message.reply_text("Haha you're stuck with us here.")
        return ''

    res = await update.effective_chat.unban_member(user_id)  # unban on current user = kick
    if res:
        await update.effective_message.reply_text("*kicks you out of the group*")

        log = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#KICKED\n"
            "self kick"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
        )

        return log

    else:
        await update.effective_message.reply_text("Huh? I can't :/")


@cutiepii_cmd(command='unban', rate_limit_calls=20, rate_limit_window=60, add_error_handler=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:  # sourcery no-metrics
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    args = context.args
    bot = context.bot

    if message.reply_to_message and message.reply_to_message.sender_chat:
        if message.reply_to_message.is_automatic_forward:
            await message.reply_text("This command doesn't work like this!")
            return

        if did_ban := await unban_chat(bot, message.reply_to_message.sender_chat, chat.id, reason = " ".join(args) or None):
            logmsg  = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#UNBANNED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
            logmsg += did_ban

            await message.reply_text("Channel {} was unbanned successfully from {}".format(
                html.escape(message.reply_to_message.sender_chat.title),
                html.escape(chat.title)
            ),
                parse_mode=ParseMode.HTML
            )

        else:
            await message.reply_text("Failed to unban channel")
            return ""

    user_id, reason = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text("⚠️ User not found\n\nI don't know who you're talking about, you're going to need to specify a user...")
        return ''

    member = None
    chan = None
    try:
        member = await chat.get_member(user_id)
    except BadRequest:
        try:
            chan = await bot.get_chat(user_id)
        except BadRequest as excp:
            if excp.message != "Chat not found":
                raise
            await message.reply_text("Can't seem to find this person.")
            return ""

    if chan:
        if did_ban := await unban_chat(bot, chan, chat.id, reason = " ".join(args) or None):
            logmsg  = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#UNBANNED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
            logmsg += did_ban

            await message.reply_text("Channel {} was unbanned successfully from {}".format(
                html.escape(chan.title),
                html.escape(chat.title)
            ),
                parse_mode=ParseMode.HTML
            )

        else:
            await message.reply_text("Failed to unban channel")
            return ""

    elif user_id == BOT_ID:
        await message.reply_text(ban_myself)
        return ''

    elif await user_is_admin(update, user_id):
        await message.reply_text("This user is an admin, so is not banned.")
        return ''

    elif member.status not in ["banned", "kicked"]:
        await message.reply_text("This user isn't banned!")
        return ''

    elif did_ban := await unban_user(bot, member, chat.id, reason = " ".join(args) or None):
        logmsg  = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
        logmsg += did_ban

        await message.reply_text("User {} was unbanned successfully by {} from <b>{}</b>".format(
            mention_html(member.user.id, member.user.first_name),
            mention_html(user.id, user.first_name),
            html.escape(chat.title),
        ),
            parse_mode=ParseMode.HTML
        )

    else:
        await message.reply_text("Failed to unban user")
        return ""

    return logmsg


WHITELISTED_USERS = [OWNER_ID] + DEV_USERS + SUDO_USERS + WHITELIST_USERS


@cutiepii_cmd(command=['selfunban', 'roar'])
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@gloggable
async def selfunban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    message = update.effective_message
    user = update.effective_user
    bot, args = context.bot, context.args
    if user.id not in WHITELISTED_USERS:
        return

    try:
        chat_id = int(args[0])
    except:
        await message.reply_text("Give a valid chat ID.")
        return

    chat = await bot.get_chat(chat_id)

    try:
        member = await chat.get_member(user.id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user.")
            return
        else:
            raise

    if member.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
        await message.reply_text("Aren't you already in the chat??")
        return

    await chat.unban_member(user.id)
    await message.reply_text("Yep, I have unbanned you.")

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNBANNED\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

    return log

@cutiepii_callback(pattern=r"unbanb_")
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_no_reply
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
async def unbanb_btn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    query = update.callback_query
    chat = update.effective_chat
    user = update.effective_user
    if query.data != "unbanb_del":
        splitter = query.data.split("=")
        query_match = splitter[0]
        if query_match == "unbanb_unban":
            user_id = splitter[1]
            if not await user_is_admin(chat, int(user.id)):
                await bot.answer_callback_query(
                    query.id,
                    text="⚠️ You don't have enough rights to unmute people",
                    show_alert=True,
                )
                return ""
            member = None
            try:
                member = await chat.get_member(user_id)
            except BadRequest:
                pass
            await chat.unban_member(user_id)
            unbanned_name = (member.user.first_name or member.user.username or "User") if member else "User"
            unbanned_mention = mention_html(member.user.id, unbanned_name) if member else f'<a href="tg://user?id={user_id}">User</a>'
            try:
                await query.message.edit_text(
                    f"{unbanned_mention} [<code>{user_id}</code>] was unbanned By {mention_html(user.id, user.first_name or user.username or 'Admin')} in {html.escape(chat.title)}",
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                try:
                    await bot.answer_callback_query(
                        query.id,
                        text=f"User unbanned successfully!",
                        show_alert=True,
                    )
                except Exception:
                    pass
            await bot.answer_callback_query(query.id, text="Unbanned!")
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNBANNED\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name or user.username or 'Admin')}\n"
                f"<b>User:</b> {unbanned_mention}"
            )

    else:
        if not await user_is_admin(chat, int(user.id)):
            await bot.answer_callback_query(
                query.id,
                text="⚠️ You don't have enough rights to delete this message.",
                show_alert=True,
            )
            return ""
        try:
            await query.message.delete()
        except Exception:
            pass
        try:
            await bot.answer_callback_query(query.id, text="Deleted!")
        except Exception:
            pass
        return ""

@cutiepii_cmd(command='banme', filters=filters.ChatType.GROUPS, rate_limit_calls=5, rate_limit_window=300)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def banme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_message.from_user.id
    chat = update.effective_chat
    user = update.effective_user
    res = await update.effective_chat.ban_member(user_id)
    if res:
        try:
            await update.effective_message.reply_animation(
                animation="https://files.catbox.moe/2oev71.mp4",
                caption="You're too cute to get banned... so why are you trying?",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await update.effective_message.reply_text("You're too cute to get banned... so why are you trying?")
        return (
            "<b>{}:</b>"
            "\n#BANME"
            "\n<b>User:</b> {}"
            "\n<b>ID:</b> <code>{}</code>".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                user_id,
            )
        )

    else:
        await update.effective_message.reply_text("Huh? I can't :/")


@cutiepii_cmd(command='snipe', filters=filters.User(SUDO_USERS))
@dev_plus
async def snipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    bot = context.bot
    try:
        chat_id = str(args[0])
        del args[0]
    except TypeError:
        await update.effective_message.reply_text("Please give me a chat to echo to!")
    to_send = " ".join(args)
    if len(to_send) >= 2:
        try:
            await bot.send_message(int(chat_id), str(to_send))
        except TelegramError:
            LOGGER.warning("Couldn't send to group %s", chat_id)
            await update.effective_message.reply_text(
                "Couldn't send the message. Perhaps I'm not part of that group?"
            )


@cutiepii_cmd(command=['listban', 'listunban'], rate_limit_calls=10, rate_limit_window=60, add_error_handler=True)
@loggable
async def list_moderation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    message = update.effective_message
    args = context.args

    # Check if caller is admin/sudo
    user = update.effective_user
    if user.id != OWNER_ID and user.id not in DEV_USERS:
        await message.reply_text("This command is only for developers and bot owners!")
        return ""

    command = message.text.split()[0][1:].split("@")[0].lower()
    
    user_id = None
    group_inputs = []

    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        group_inputs = args
    else:
        if len(args) < 2:
            await message.reply_text(f"<b>Usage</b>\n<code>/{command} [user_id/username] [group_id1] [group_id2] ...</code>", parse_mode=ParseMode.HTML)
            return ""
        user_id, _ = await extract_user_and_text(message, args[:1])
        group_inputs = args[1:]

    if not user_id:
        await message.reply_text("<b>Action Denied</b>\nCould not find the target user to moderate.")
        return ""

    success_groups = []
    failed_groups = []

    await message.reply_chat_action("typing")

    action = "ban" if command == "listban" else "unban"

    for grp in group_inputs:
        grp = grp.strip()
        try:
            chat_id = int(grp)
        except ValueError:
            if not grp.startswith("@"):
                grp = "@" + grp
            chat_id = grp

        try:
            if action == "ban":
                await bot.ban_chat_member(chat_id, user_id)
            else:
                await bot.unban_chat_member(chat_id, user_id)
            success_groups.append(str(chat_id))
        except Exception as e:
            failed_groups.append(f"{grp} (Error: {e})")

    reply = (
        f"<b>Multi-Group Moderation Report ({action.upper()})</b>\n\n"
        f"<b>Target User ID:</b> <code>{user_id}</code>\n"
    )
    if success_groups:
        reply += f"<b>Successful in:</b> {', '.join(success_groups)}\n"
    if failed_groups:
        reply += f"<b>Failed in:</b>\n" + "\n".join(f"- {f}" for f in failed_groups)

    await message.reply_text(reply, parse_mode=ParseMode.HTML)
    return ""


__help__ = True

__mod_name__ = "Bans/Mutes"
