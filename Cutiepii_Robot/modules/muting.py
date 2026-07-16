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
import re
import sys

from typing import Optional
from telegram import Chat, ChatPermissions, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes
from telegram.helpers import mention_html
from telegram import User

from Cutiepii_Robot import (
    DEV_USERS,
    SUDO_USERS,
    SUPPORT_USERS,
    OWNER_ID,
    WHITELIST_USERS,
    LOGGER,
    dispatcher,
)
from Cutiepii_Robot.modules.log_channel import loggable

from Cutiepii_Robot.modules.connection import connected
from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status, is_user_ban_protected, can_delete
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from Cutiepii_Robot.modules.helper_funcs.string_handling import extract_time
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    user_is_admin,
    bot_is_admin,
    u_na_errmsg,
)
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd


MEDIA_PERMISSIONS = ChatPermissions(can_send_messages=True,
                                     can_send_audios=True,
                                     can_send_documents=True,
                                     can_send_photos=True,
                                     can_send_videos=True,
                                     can_send_video_notes=True,
                                     can_send_voice_notes=True,
                                     can_send_polls=True,
                                     can_send_other_messages=True,
                                     can_add_web_page_previews=True)

NOMEDIA_PERMISSIONS = ChatPermissions(can_send_messages=True,
                                     can_send_audios=False,
                                     can_send_documents=False,
                                     can_send_photos=False,
                                     can_send_videos=False,
                                     can_send_video_notes=False,
                                     can_send_voice_notes=False,
                                     can_send_polls=False,
                                     can_send_other_messages=False,
                                     can_add_web_page_previews=False)


async def check_user(user_id: int, bot, chat: Chat) -> Optional[str]:
    if not user_id:
        return "<b>User Not Found</b>\nPlease specify a user to mute."

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            return "<b>Error</b>\nCould not find specified user."
        else:
            raise

    if user_id == bot.id:
        return "<b>Action Denied</b>\nI cannot mute myself."

    if await is_user_ban_protected(chat, user_id):
        return "<b>Action Denied</b>\nAdministrators cannot be muted."

    if user_id in [777000, 1087968824]:
        return "<b>Action Denied</b>\nTelegram system accounts cannot be muted."

    return None



@cutiepii_cmd(command=['mute', 'dmute', 'smute', 'dsmute'], rate_limit_calls=15, rate_limit_window=60, add_error_handler=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    delete = message.text[1] == 'd'
    user_id, reason = await extract_user_and_text(message, args)
    reply = await check_user(user_id, bot, chat)

    silent = False
    if message.text.startswith("/s") or message.text.startswith("!s"):
        silent = True
        if not await can_delete(chat, context.bot.id):
            return ""

    if reply:
        await message.reply_text(reply)
        return ""

    if delete and message.reply_to_message:
        if await user_is_admin(update, message.from_user.id, perm=AdminPerms.CAN_DELETE_MESSAGES):
            if await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
                await message.reply_to_message.delete()
            else:
                await update.effective_message.reply_text(
                    "<b>Action Denied</b>\n"
                    f"I require the '{AdminPerms.CAN_DELETE_MESSAGES.name.lower().replace('is_', '').replace('_', ' ')}' permission to perform this action.",
                    parse_mode=ParseMode.HTML
                )
                return
        else:
            return await u_na_errmsg(message, AdminPerms.CAN_DELETE_MESSAGES)

    member = await chat.get_member(user_id)

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#MUTE\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}\n"
    )

    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    member_can_send = member.can_send_messages if member.status == ChatMemberStatus.RESTRICTED else True
    if member_can_send is None or member_can_send:
        chat_permissions = ChatPermissions(can_send_messages=False)
        await bot.restrict_chat_member(chat.id, user_id, chat_permissions)
        mutemsg = (
            f"<b>Mute Event</b>\n"
            f"User: {mention_html(member.user.id, member.user.first_name)}\n"
            f"Admin: {mention_html(user.id, user.first_name)}\n")
        if reason:
            mutemsg += f"Reason: <code>{html.escape(reason)}</code>"

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "Unmute", callback_data="cb_unmute({})".format(user_id)
                    )
                ]
            ]
        )

        if not silent:
            try:
                await bot.send_animation(
                    chat.id,
                    animation="https://files.catbox.moe/gyx2a4.mp4",
                    caption=mutemsg,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                await bot.send_message(
                    chat.id,
                    mutemsg,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.HTML,
                )
        else:
            await message.delete()
        return log

    else:
        if not silent:
            await message.reply_text("<b>Information</b>\nThis user is already muted.", parse_mode=ParseMode.HTML)
        else:
            await message.delete()

    return ""



@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True, noreply=True)
@loggable
@cutiepii_callback(pattern=r"cb_unmute")
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    match = re.match(r"cb_unmute\((.+?)\)", query.data)
    if match and await user_is_admin(update, user.id, perm=AdminPerms.CAN_RESTRICT_MEMBERS):

        bot = context.bot
        user_id = match[1]
        user_member = await chat.get_member(user_id)

        if user_member.status in [ChatMemberStatus.BANNED, ChatMemberStatus.LEFT]:
            await query.answer(
                "This user is not a member of this chat.", show_alert=True
            )

        elif not (user_member.status == ChatMemberStatus.RESTRICTED and not (
                user_member.can_send_messages
                and (user_member.can_send_audios or user_member.can_send_documents or 
                     user_member.can_send_photos or user_member.can_send_videos or
                     user_member.can_send_video_notes or user_member.can_send_voice_notes)
                and user_member.can_send_other_messages
                and user_member.can_add_web_page_previews
            )):
            try:
                await update.effective_message.edit_text("This user is not muted.")
            except Exception:
                try:
                    await query.answer("This user is not muted.", show_alert=True)
                except Exception:
                    pass
        else:
            chat_permissions = ChatPermissions(
                can_send_messages=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
            try:
                await bot.restrict_chat_member(chat.id, int(user_id), chat_permissions)
            except BadRequest:
                pass

            try:
                await update.effective_message.delete()
            except Exception:
                pass

            unmutemsg = f"User {mention_html(user_member.user.id, user_member.user.first_name)} has been unmuted by {mention_html(user.id, user.first_name)}."
            try:
                await bot.send_animation(
                    chat.id,
                    animation="https://files.catbox.moe/vpzudb.mp4",
                    caption=unmutemsg,
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                await bot.send_message(
                    chat.id,
                    unmutemsg,
                    parse_mode=ParseMode.HTML,
                )

            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNMUTE\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
            )
    else:
        await query.answer("Action Denied\nYou do not have administrator privileges.", show_alert=True)


@cutiepii_cmd(command='unmute', rate_limit_calls=20, rate_limit_window=60, add_error_handler=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
async def unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    silent = False
    if message.text.startswith("/s") or message.text.startswith("!s"):
        silent = True
        if not await can_delete(chat, context.bot.id):
            return ""

    user_id = await extract_user(message, args)
    reason = " ".join(args[1:]) if len(args) > 1 else ""

    if not user_id:
        if silent:
            await message.delete()
        else:
            await message.reply_text(
                "<b>Invalid Command Usage</b>\nPlease specify a username or reply to a user's message to unmute them.",
                parse_mode=ParseMode.HTML
            )
        return ""

    member = await chat.get_member(int(user_id))

    if member.status in [ChatMemberStatus.BANNED, ChatMemberStatus.LEFT]:
        await message.reply_text(
            "<b>Error</b>\nThis user is not a member of this chat.",
            parse_mode=ParseMode.HTML
        )
        return ""

    is_restricted = member.status == ChatMemberStatus.RESTRICTED
    has_right = (
        (
            member.can_send_messages is not False
            and (member.can_send_audios is not False or member.can_send_documents is not False or
                 member.can_send_photos is not False or member.can_send_videos is not False or
                 member.can_send_video_notes is not False or member.can_send_voice_notes is not False)
            and member.can_send_other_messages is not False
            and member.can_add_web_page_previews is not False
        ) if is_restricted else True
    )
    if has_right:
        if not silent:
            await message.reply_text("<b>Information</b>\nThis user is not muted.", parse_mode=ParseMode.HTML)
        return ""

    chat_permissions = ChatPermissions(
        can_send_messages=True,
        can_invite_users=True,
        can_pin_messages=True,
        can_send_polls=True,
        can_change_info=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
    )
    try:
        await bot.restrict_chat_member(chat.id, int(user_id), chat_permissions)
    except BadRequest:
        pass

    unmutemsg = "{} was unmuted by {} in <b>{}</b>".format(
        mention_html(member.user.id, member.user.first_name), mention_html(user.id, user.first_name), message.chat.title
    )
    if reason:
        unmutemsg += "\n<b>Reason</b>: <code>{}</code>".format(reason)
    
    if not silent:
        try:
            await bot.send_animation(
                chat.id,
                animation="https://files.catbox.moe/vpzudb.mp4",
                caption=unmutemsg,
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await bot.send_message(
                chat.id,
                unmutemsg,
                parse_mode=ParseMode.HTML,
            )
    else:
        await message.delete()
    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNMUTE\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
    )

@cutiepii_cmd(command=['tmute', 'tempmute', 'stmute', 'dtmute', 'dstmute'], rate_limit_calls=15, rate_limit_window=60, add_error_handler=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
async def temp_mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    cmd_text = message.text.lstrip("/!")
    delete = cmd_text.startswith("d")
    user_id, reason = await extract_user_and_text(message, args)
    reply = await check_user(user_id, bot, chat)

    silent = False
    if message.text.startswith("/s") or message.text.startswith("!s") or cmd_text.startswith("s") or cmd_text.startswith("ts") or (cmd_text.startswith("ds") and len(cmd_text) > 2):
        # Handle cases like /stmute, /dstmute, /s, !s
        silent = True
        if not await can_delete(chat, context.bot.id):
            return ""

    if reply:
        await message.reply_text(reply)
        return ""

    if delete and message.reply_to_message:
        if await user_is_admin(update, message.from_user.id, perm=AdminPerms.CAN_DELETE_MESSAGES):
            if await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
                await message.reply_to_message.delete()
            else:
                await update.effective_message.reply_text(
                    "<b>Action Denied</b>\n"
                    f"I require the '{AdminPerms.CAN_DELETE_MESSAGES.name.lower().replace('is_', '').replace('_', ' ')}' permission to perform this action.",
                    parse_mode=ParseMode.HTML
                )
                return
        else:
            return await u_na_errmsg(message, AdminPerms.CAN_DELETE_MESSAGES)

    member = await chat.get_member(user_id)

    if not reason:
        if not silent:
            await message.reply_text("<b>Invalid Command Usage</b>\nPlease specify a duration for the temporary mute.", parse_mode=ParseMode.HTML)
        else:
            await message.delete()
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = await extract_time(message, time_val)

    if not mutetime:
        return ""

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#TEMP MUTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}\n"
        f"<b>Time:</b> {time_val}"
    )
    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    try:
        await bot.restrict_chat_member(
            chat.id, user_id, ChatPermissions(can_send_messages=False), until_date=mutetime
        )
        if not silent:
            msg = (
                f"<b>Temporary Mute Event</b>\n"
                f"User: {mention_html(member.user.id, member.user.first_name)}\n"
                f"Admin: {mention_html(user.id, user.first_name)}\n"
                f"Duration: {time_val}\n"
            )

            if reason:
                msg += f"Reason: <code>{html.escape(reason)}</code>"
            try:
                await bot.send_animation(
                    chat.id,
                    animation="https://files.catbox.moe/gyx2a4.mp4",
                    caption=msg,
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                await bot.send_message(chat.id, msg, parse_mode=ParseMode.HTML)
        else:
            await message.delete()
        return log

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            if not silent:
                await message.reply_text(f"Temporary Mute Event\nDuration: {time_val}", do_quote=False)
            else:
                await message.delete()
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR muting user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            if not silent:
                await message.reply_text("<b>Error</b>\nFailed to mute the specified user.", parse_mode=ParseMode.HTML)
            else:
                await message.delete()

    return ""

@cutiepii_cmd(command=['trestrict', 'temprestrict'], rate_limit_calls=10, rate_limit_window=60, add_error_handler=True, can_disable=True, admin_ok=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
async def temp_nomedia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    bot = context.bot
    args = context.args

    conn = await connected(bot, chat, chat, user.id)
    if not conn is False:
        chatD = await dispatcher.bot.get_chat(conn)
    else:
        if chat.type == "private":
            sys.exit(1)
        else:
            chatD = chat

    user_id, reason = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text("<b>User Not Found</b>\nPlease specify a user to restrict.", parse_mode=ParseMode.HTML)
        return ""

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("<b>Error</b>\nCould not find specified user.", parse_mode=ParseMode.HTML)
            return ""
        else:
            raise

    if await user_is_admin(update, user_id, member):
        await message.reply_text("<b>Action Denied</b>\nAdministrators cannot be restricted.", parse_mode=ParseMode.HTML)
        return ""

    if user_id == bot.id:
        await message.reply_text("<b>Action Denied</b>\nI cannot restrict myself.", parse_mode=ParseMode.HTML)
        return ""

    if not reason:
        await message.reply_text("<b>Invalid Command Usage</b>\nPlease specify a duration for the temporary restriction.", parse_mode=ParseMode.HTML)
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = await extract_time(message, time_val)

    if not mutetime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP RESTRICTED" \
          "\n<b>- Admin:</b> {}" \
          "\n<b>- User:</b> {}" \
          "\n<b>- ID:</b> <code>{}</code>" \
          "\n<b>- Time:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                       mention_html(member.user.id, member.user.first_name), user_id, time_val)
    if reason:
        log += "\n<b>- Reason:</b> {}".format(reason)

    try:
        member_can_send = member.can_send_messages if member.status == ChatMemberStatus.RESTRICTED else True
        if member_can_send is None or member_can_send:
            await context.bot.restrict_chat_member(chatD.id, user_id, NOMEDIA_PERMISSIONS, until_date=mutetime)
            await message.reply_text(f"<b>Temporary Media Restriction</b>\nUser: {mention_html(member.user.id, member.user.first_name)}\nAdmin: {mention_html(user.id, user.first_name)}\nDuration: {time_val}", parse_mode=ParseMode.HTML)
            return log
        else:
            await message.reply_text(f"<b>Information</b>\nThis user is already restricted in <b>{html.escape(chatD.title)}</b>.", parse_mode=ParseMode.HTML)

    except BadRequest as excp:
        if excp.message == "Reply message not found" or excp.message == "Message can't be deleted":
            # Do not reply
            await message.reply_text(f"Temporary Media Restriction\nDuration: {time_val}", do_quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR muting user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            await message.reply_text("<b>Error</b>\nFailed to restrict the specified user.", parse_mode=ParseMode.HTML)

    return ""


@cutiepii_cmd(command='unrestrict', rate_limit_calls=20, rate_limit_window=60, add_error_handler=True, can_disable=True, admin_ok=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
async def media(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    bot = context.bot
    args = context.args

    conn = await connected(bot, chat, chat, user.id)
    if not conn is False:
        chatD = await dispatcher.bot.get_chat(conn)
    else:
        if chat.type == "private":
            sys.exit(1)
        else:
            chatD = chat

    user_id = await extract_user(message, args)
    if not user_id:
        await message.reply_text("<b>Invalid Command Usage</b>\nPlease specify a username or reply to a user's message to lift restrictions.", parse_mode=ParseMode.HTML)
        return ""

    member = await chatD.get_member(int(user_id))

    if member.status not in (ChatMemberStatus.BANNED, ChatMemberStatus.LEFT):
        is_restricted = member.status == ChatMemberStatus.RESTRICTED
        has_right = (
            (
                member.can_send_messages and (member.can_send_audios or member.can_send_documents or
                member.can_send_photos or member.can_send_videos or member.can_send_video_notes or
                member.can_send_voice_notes) and member.can_send_other_messages and member.can_add_web_page_previews
            ) if is_restricted else True
        )
        if has_right:
            await message.reply_text(f"<b>Information</b>\nThis user already has the right to send media in <b>{html.escape(chatD.title)}</b>.", parse_mode=ParseMode.HTML)
        else:
            await context.bot.restrict_chat_member(chatD.id, int(user_id), MEDIA_PERMISSIONS)
            reply = "<b>Media Restriction Lifted</b>\nUser: {}\nAdmin: {}".format(mention_html(member.user.id, member.user.first_name), mention_html(user.id, user.first_name))
            await message.reply_text(reply,  parse_mode=ParseMode.HTML)
            return "<b>{}:</b>" \
                   "\n#UNRESTRICTED" \
                   "\n<b>- Admin:</b> {}" \
                   "\n<b>- User:</b> {}" \
                   "\n<b>- ID:</b> <code>{}</code>".format(html.escape(chatD.title),
                                                           mention_html(user.id, user.first_name),
                                                           mention_html(member.user.id, member.user.first_name), user_id)
    else:
        await message.reply_text("<b>Error</b>\nThis user is not a member of this chat.", parse_mode=ParseMode.HTML)

    return ""


@cutiepii_cmd(command=['restrict', 'nomedia'], rate_limit_calls=15, rate_limit_window=60, add_error_handler=True, can_disable=True, admin_ok=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
async def nomedia(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    bot = context.bot
    args = context.args

    conn = await connected(bot, chat, chat, user.id)
    if not conn is False:
        chatD = await dispatcher.bot.get_chat(conn)
    else:
        if chat.type == "private":
            sys.exit(1)
        else:
            chatD = chat

    user_id = await extract_user(message, args)
    if not user_id:
        await message.reply_text("<b>Invalid Command Usage</b>\nPlease specify a username or reply to a user's message to restrict media.", parse_mode=ParseMode.HTML)
        return ""

    if user_id == bot.id:
        await message.reply_text("<b>Action Denied</b>\nI cannot restrict myself.", parse_mode=ParseMode.HTML)
        return ""

    member = await chatD.get_member(int(user_id))

    if member:
        if await user_is_admin(update, user_id, member=member):
            await message.reply_text("<b>Action Denied</b>\nAdministrators cannot be restricted.", parse_mode=ParseMode.HTML)

        elif (member.can_send_messages if member.status == ChatMemberStatus.RESTRICTED else True) is None or (member.can_send_messages if member.status == ChatMemberStatus.RESTRICTED else True):
            await context.bot.restrict_chat_member(chatD.id, user_id, NOMEDIA_PERMISSIONS)
            reply = "<b>Media Restricted</b>\nUser: {}\nAdmin: {}".format(mention_html(member.user.id, member.user.first_name), mention_html(user.id, user.first_name))
            await message.reply_text(reply, parse_mode=ParseMode.HTML)
            return "<b>{}:</b>" \
                   "\n#RESTRICTED" \
                   "\n<b>- Admin:</b> {}" \
                   "\n<b>- User:</b> {}" \
                   "\n<b>- ID:</b> <code>{}</code>".format(html.escape(chatD.title),
                                              mention_html(user.id, user.first_name),
                                              mention_html(member.user.id, member.user.first_name), user_id)

        else:
            await message.reply_text(f"<b>Information</b>\nThis user is already restricted in <b>{html.escape(chatD.title)}</b>.", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(f"<b>Error</b>\nThis user is not a member of <b>{html.escape(chatD.title)}</b>.", parse_mode=ParseMode.HTML)

    return ""


# Handlers now registered via decorators

__mod_name__ = "Muting"
