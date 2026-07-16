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
import Cutiepii_Robot.modules.sql.rules_sql as rules_sql

from typing import Optional

from Cutiepii_Robot import BOT_USERNAME, BAN_STICKER, DEV_USERS, OWNER_ID, SUDO_USERS, WHITELIST_USERS, dispatcher
from Cutiepii_Robot.modules.helper_funcs.extraction import (
    extract_text,
    extract_user,
    extract_user_and_text,
)
from Cutiepii_Robot.modules.helper_funcs.filters import CustomFilters
from Cutiepii_Robot.modules.helper_funcs.alternate import send_message
from Cutiepii_Robot.modules.helper_funcs.misc import split_message
from Cutiepii_Robot.modules.helper_funcs.string_handling import split_quotes
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.connection import connected
from Cutiepii_Robot.modules.sql import warns_sql as sql
from Cutiepii_Robot.modules.sql.approve_sql import is_approved
import datetime
from telegram import (
    CallbackQuery,
    Chat,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    Update,
    User,
    ChatPermissions,
)
from telegram.constants import ParseMode, ChatMemberStatus, MessageLimit
from telegram.error import BadRequest
from telegram.ext import (
    ContextTypes,
    ApplicationHandlerStop as DispatcherHandlerStop,
    filters,
)
from telegram.helpers import mention_html
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, cutiepii_msg

from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    bot_is_admin,
    user_is_admin,
)

WARN_HANDLER_GROUP = 9
CURRENT_WARNING_FILTER_STRING = "<b>Warning Filters</b>\nCurrent warning filters active in this chat:\n"
WARNS_GROUP = 2

async def warn_immune(message, update, uid, warner):

    if await user_is_admin(update, uid):
        if uid == OWNER_ID:
            await message.reply_text("<b>Action Denied</b>\nThe creator of this bot is immune to warnings.", parse_mode=ParseMode.HTML)
            return True
        if uid in DEV_USERS:
            await message.reply_text("<b>Action Denied</b>\nDeveloper accounts are immune to warnings.", parse_mode=ParseMode.HTML)
            return True
        if uid in SUDO_USERS:
            await message.reply_text("<b>Action Denied</b>\nSudo accounts are immune to warnings.", parse_mode=ParseMode.HTML)
            return True
        else:
            await message.reply_text("<b>Action Denied</b>\nAdministrators are immune to warnings.", parse_mode=ParseMode.HTML)
            return True

    if uid in WHITELIST_USERS:
        if warner:
            await message.reply_text("<b>Action Denied</b>\nWhitelisted users are immune to warnings.", parse_mode=ParseMode.HTML)
            return True
        else:
            await message.reply_text(
                "<b>Action Denied</b>\nA whitelisted user has triggered an auto-warn filter, but they are immune to warnings.",
                parse_mode=ParseMode.HTML
            )
            return True
    else:
        return False


async def warn(
    user: User, update: Update, reason: str, message: Message, warner: User = None
) -> Optional[str]:  # sourcery no-metrics
    chat = update.effective_chat
    if await warn_immune(message=message, update=update, uid=user.id, warner=warner):
        return

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Automated warn filter."

    limit, soft_warn, warn_mode = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    
    if num_warns == 3:
        try:
            until_date = datetime.datetime.now() + datetime.timedelta(hours=1)
            await chat.restrict_member(
                user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
        except Exception as e:
            LOGGER.error(f"Failed to mute user on 3rd warn: {e}")
            
        keyboard = [[
            InlineKeyboardButton("Remove Warn", callback_data="rm_warn({})".format(user.id))
        ]]
        rules = rules_sql.get_rules(chat.id)
        if rules: 
            keyboard[0].append(InlineKeyboardButton("Rules", url="t.me/{}?start={}".format(BOT_USERNAME, chat.id)))

        reply = (
            f"<b>Mute Event (3rd Warning)</b>\n"
            f"User: {mention_html(user.id, user.first_name)}\n"
            f"Warnings: 3/{limit} (Muted for 1 hour)"
        )
        if reason:
            reply += f"\nReason: {html.escape(reason)}"
        
        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN_MUTE\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>3/{limit} - Muted for 1 hour!</code>"
        )
        
    elif num_warns >= 5:
        sql.reset_warns(user.id, chat.id)
        try:
            until_date = datetime.datetime.now() + datetime.timedelta(days=1)
            await chat.ban_member(user.id, until_date=until_date)
        except Exception as e:
            LOGGER.error(f"Failed to ban user on 5th warn: {e}")

        await message.get_bot().send_sticker(chat.id, BAN_STICKER)
        keyboard = None
        reply = (
            f"<b>Ban Event (5th Warning)</b>\n"
            f"User: {mention_html(user.id, user.first_name)}\n"
            f"Warnings: {num_warns}/{limit} (Banned for 24 hours)"
        )
        if reason:
            reply += f"\nReason: {html.escape(reason)}"

        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN_BAN\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>{num_warns}/{limit} - Banned for 24 hours!</code>"
        )
        
    elif num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            await chat.unban_member(user.id)
            reply = (
                f"<b>Kick Event</b>\n"
                f"User: {mention_html(user.id, user.first_name)}\n"
                f"Warnings: {limit} (Exceeded limit)"
            )
        else:  # ban
            await chat.ban_member(user.id)
            reply = (
                f"<b>Ban Event</b>\n"
                f"User: {mention_html(user.id, user.first_name)}\n"
                f"Warnings: {limit} (Exceeded limit)"
            )

        for warn_reason in reasons:
            reply += f"\n- {html.escape(warn_reason)}"

        await message.get_bot().send_sticker(chat.id, BAN_STICKER)
        keyboard = None
        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN_BAN\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>{num_warns}/{limit} - executed!</code>"
        )
        
    else:
        keyboard = [[
            InlineKeyboardButton("Remove Warn", callback_data="rm_warn({})".format(user.id))
            ]]
        rules = rules_sql.get_rules(chat.id)
        if rules: 
            keyboard[0].append(InlineKeyboardButton("Rules", url="t.me/{}?start={}".format(BOT_USERNAME, chat.id)))

        reply = (
            f"<b>Warning Event</b>\n"
            f"User: {mention_html(user.id, user.first_name)}\n"
            f"Warnings: {num_warns}/{limit}"
        )
        if reason:
            reply += f"\nReason: {html.escape(reason)}"
        if rules:
            reply += '\n\nPlease read the group rules to avoid further actions.'

        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User ID:</b> <code>{user.id}</code>\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>{num_warns}/{limit}</code>"
        )

    try:
        await message.reply_text(reply, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    except BadRequest as excp:
        if excp.message == "Reply message not found" or excp.message == "Message can't be deleted":
            await message.reply_text(
                reply, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML, do_quote=False
            )
        else:
            raise
    return log_reason


async def swarn(
    user: User, update: Update, reason: str, message: Message, dels, warner: User = None,
) -> str:  # sourcery no-metrics
    if await warn_immune(message=message, update=update, uid=user.id, warner=warner):
        return
    chat = update.effective_chat

    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Automated warn filter."

    limit, soft_warn, warn_mode = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            await chat.unban_member(user.id)
            reply = (
                f"<b>Kick Event</b>\n"
                f"User: {mention_html(user.id, user.first_name)}\n"
                f"Warnings: {limit} (Exceeded limit)"
            )

        else:  # ban
            await chat.ban_member(user.id)
            reply = (
                f"<b>Ban Event</b>\n"
                f"User: {mention_html(user.id, user.first_name)}\n"
                f"Warnings: {limit} (Exceeded limit)"
            )

        for warn_reason in reasons:
            reply += f"\n- {html.escape(warn_reason)}"

        await message.get_bot().send_sticker(chat.id, BAN_STICKER)  # Saitama's sticker
        keyboard = None
        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN_BAN\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User ID:</b> <code>{user.id}</code>\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>{num_warns}/{limit}</code>"
        )

    else:
        keyboard_btns = [[
            InlineKeyboardButton("Remove Warn", callback_data="rm_warn({})".format(user.id))
            ]]
        rules = rules_sql.get_rules(chat.id)
        if rules: 
            keyboard_btns[0].append(InlineKeyboardButton("Rules", url="t.me/{}?start={}".format(BOT_USERNAME, chat.id)))
        keyboard = InlineKeyboardMarkup(keyboard_btns)

        reply = (
            f"<b>Warning Event</b>\n"
            f"User: {mention_html(user.id, user.first_name)}\n"
            f"Warnings: {num_warns}/{limit}"
        )
        if reason:
            reply += f"\nReason: {html.escape(reason)}"

        if rules:
            reply += "\n\nPlease read the group rules to avoid further actions."

        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User ID:</b> <code>{user.id}</code>\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>{num_warns}/{limit} - executed!</code>"
        )

    try:
        if dels:
            if message.reply_to_message:
                await message.reply_to_message.delete()
        await message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML, allow_sending_without_reply=True)
        await message.delete()
    except BadRequest as excp:
        if excp.message == "Reply message not found" or excp.message == "Message can't be deleted":
            if message.reply_to_message:
                await message.reply_to_message.delete()
            await message.reply_text(
                reply, reply_markup=keyboard, parse_mode=ParseMode.HTML, do_quote=False
            )
            await message.delete()
        else:
            raise
    return log_reason


async def dwarn(
    user: User, update: Update, reason: str, message: Message, warner: User = None
) -> str:  # sourcery no-metrics
    if await warn_immune(message=message, update=update, uid=user.id, warner=warner):
        return
    chat = update.effective_chat
    if warner:
        warner_tag = mention_html(warner.id, warner.first_name)
    else:
        warner_tag = "Automated warn filter."

    limit, soft_warn, warn_mode = sql.get_warn_setting(chat.id)
    num_warns, reasons = sql.warn_user(user.id, chat.id, reason)
    if num_warns >= limit:
        sql.reset_warns(user.id, chat.id)
        if soft_warn:  # kick
            await chat.unban_member(user.id)
            reply = (
                f"<b>Kick Event</b>\n"
                f"User: {mention_html(user.id, user.first_name)}\n"
                f"Warnings: {limit} (Exceeded limit)"
            )
        else:  # ban
            await chat.ban_member(user.id)
            reply = (
                f"<b>Ban Event</b>\n"
                f"User: {mention_html(user.id, user.first_name)}\n"
                f"Warnings: {limit} (Exceeded limit)"
            )

        for warn_reason in reasons:
            reply += f"\n- {html.escape(warn_reason)}"

        await message.get_bot().send_sticker(chat.id, BAN_STICKER)  # Saitama's sticker
        keyboard = None
        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN_BAN\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>{num_warns}/{limit} - executed!</code>"
        )

    else:
        keyboard_btns = [[
            InlineKeyboardButton("Remove Warn", callback_data="rm_warn({})".format(user.id))
            ]]
        rules = rules_sql.get_rules(chat.id)
        if rules: 
            keyboard_btns[0].append(InlineKeyboardButton("Rules", url="t.me/{}?start={}".format(BOT_USERNAME, chat.id)))
        keyboard = InlineKeyboardMarkup(keyboard_btns)

        reply = (
            f"<b>Warning Event</b>\n"
            f"User: {mention_html(user.id, user.first_name)}\n"
            f"Warnings: {num_warns}/{limit}"
        )
        if reason:
            reply += f"\nReason: {html.escape(reason)}"
        if rules:
            reply += "\n\nPlease read the group rules to avoid further actions."
        
        log_reason = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#WARN\n"
            f"<b>Admin:</b> {warner_tag}\n"
            f"<b>User:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>Reason:</b> {reason}\n"
            f"<b>Counts:</b> <code>{num_warns}/{limit} - executed!</code>"
        )

    try:
        if message.reply_to_message:
            await message.reply_to_message.delete()
        await message.reply_text(reply, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    except BadRequest as excp:
        if excp.message == "Reply message not found" or excp.message == "Message can't be deleted":
            if message.reply_to_message:
                await message.reply_to_message.delete()
            await message.reply_text(
                reply, reply_markup=keyboard, parse_mode=ParseMode.HTML, do_quote=False
            )
        else:
            raise
    return log_reason

@cutiepii_callback(pattern=r"rm_warn")
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, noreply=True)
@loggable
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    user = update.effective_user
    match = re.match(r"rm_warn\((.+?)\)", query.data)
    if match:
        user_id = match[1]
        chat = update.effective_chat
        if not await user_is_admin(update, int(user.id)):
            await query.answer(text="Action Denied\nYou do not have administrator privileges to remove warnings.", show_alert=True)
            return ""
        res = sql.remove_warn(user_id, chat.id)
        if res:
            admin_member = await chat.get_member(user.id)
            is_anon = getattr(admin_member, "is_anonymous", False) is True
            await update.effective_message.edit_text(
                "Warning removed by <b>{}</b>.".format(
                    "anonymous admin" if is_anon else mention_html(user.id, user.first_name)
                ),
                parse_mode=ParseMode.HTML,
            )
            user_member = await chat.get_member(user_id)
            return "<b>{}:</b>" \
                   "\n#UNWARN" \
                   "\n<b>Admin:</b> {}" \
                   "\n<b>User:</b> {} (<code>{}</code>)".format(html.escape(chat.title),
                                                                "anonymous admin" if is_anon else mention_html(user.id, user.first_name),
                                                                mention_html(user_member.user.id, user_member.user.first_name),
                                                                user_member.user.id)
        else:
            await update.effective_message.edit_text(
                "This user does not have any active warnings.",
                parse_mode=ParseMode.HTML)

    return ""

@cutiepii_cmd(command='warn', filters=filters.ChatType.GROUPS, rate_limit_calls=30, rate_limit_window=60, add_error_handler=True)
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    warner = update.effective_user
    user_id, reason = await extract_user_and_text(message, args)

    if (message.reply_to_message and message.reply_to_message.sender_chat) or (user_id and user_id < 0):
        await message.reply_text("<b>Action Denied</b>\nWarning commands cannot be applied to channels. You may ban the channel instead.", parse_mode=ParseMode.HTML)
        return ""

    if message.text.startswith('/s') or message.text.startswith('!s') or message.text.startswith('>s'):
        silent = True
        if not await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            return ""
    else:
        silent = False
    if message.text.startswith('/d') or message.text.startswith('!d') or message.text.startswith('>d'):
        delban = True
        if not await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            return ""
    else:
        delban = False
    if message.text.startswith('/ds') or message.text.startswith('!ds') or message.text.startswith('>ds'):
        delsilent = True
        if not await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
            return ""
    else:
        delsilent = False
    if silent:
        dels = False
        if user_id:
            if (
                message.reply_to_message
                and message.reply_to_message.from_user.id == user_id
            ):
                return await swarn(
                    message.reply_to_message.from_user,
                    update,
                    reason,
                    message,
                    dels,
                    warner,
                )
            else:
                return await swarn((await chat.get_member(user_id)).user, update, reason, message, dels, warner)
        else:
            await message.reply_text("<b>Error</b>\nInvalid user ID specified.", parse_mode=ParseMode.HTML)
    if delsilent:
        dels = True
        if user_id:
            if (
                message.reply_to_message
                and message.reply_to_message.from_user.id == user_id
            ):
                return await swarn(
                    message.reply_to_message.from_user,
                    update,
                    reason,
                    message,
                    dels,
                    warner,
                )
            else:
                return await swarn((await chat.get_member(user_id)).user, update, reason, message, dels, warner)
        else:
            await message.reply_text("<b>Error</b>\nInvalid user ID specified.", parse_mode=ParseMode.HTML)
    elif delban:
        if user_id:
            if (
                message.reply_to_message
                and message.reply_to_message.from_user.id == user_id
            ):
                return await dwarn(
                    message.reply_to_message.from_user,
                    update,
                    reason,
                    message,
                    warner,
                )
            else:
                return await dwarn((await chat.get_member(user_id)).user, update, reason, message, warner)
        else:
            await message.reply_text("<b>Error</b>\nInvalid user ID specified.", parse_mode=ParseMode.HTML)
    else:
        if user_id:
            if (
                message.reply_to_message
                and message.reply_to_message.from_user.id == user_id
            ):
                return await warn(
                    message.reply_to_message.from_user,
                    update,
                    reason,
                    message.reply_to_message,
                    warner,
                )
            else:
                return await warn((await chat.get_member(user_id)).user, update, reason, message, warner)
        else:
            await message.reply_text("<b>Error</b>\nInvalid user ID specified.", parse_mode=ParseMode.HTML)
    return ""

@cutiepii_cmd(command=["unwarn", "rmwarn"], filters=filters.ChatType.GROUPS)
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def rm_last_warn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
     args = context.args
     message = update.effective_message
     chat = update.effective_chat
     user = update.effective_user
 
     user_id = await extract_user(message, args)
 
     if user_id:
          sql.remove_warn(user_id, chat.id)
          await message.reply_text("<b>Warning Removed</b>\nThe latest warning has been successfully removed.", parse_mode=ParseMode.HTML)
          member = await chat.get_member(user_id)
          unwarned = member.user
          return (
              f"<b>{html.escape(chat.title)}:</b>\n"
              f"#UNWARN\n"
              f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
              f"<b>User:</b> {mention_html(unwarned.id, unwarned.first_name)}"
          )
     else:
          await message.reply_text("<b>User Not Found</b>\nPlease specify a user to remove a warning from.", parse_mode=ParseMode.HTML)
     return ""

@cutiepii_cmd(command=['resetwarn', 'resetwarns', 'rmwarns'], filters=filters.ChatType.GROUPS)
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def reset_warns(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if user_id:= await extract_user(message, args):
        sql.reset_warns(user_id, chat.id)
        member = await chat.get_member(user_id)
        warned = member.user
        await message.reply_html("<b>Warnings Reset</b>\n{} reset the warnings of {} in <b>{}</b>.".format(mention_html(user.id, user.first_name), mention_html(warned.id, warned.first_name), html.escape(chat.title)))
        return (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#RESETWARNS\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(warned.id, warned.first_name)}\n"
            f"<b>User ID:</b> <code>{warned.id}</code>"
        )
    else:
        await message.reply_text("<b>User Not Found</b>\nPlease specify a user to reset warnings for.", parse_mode=ParseMode.HTML)
    return ""


@cutiepii_cmd(command='warns', filters=filters.ChatType.GROUPS)
async def warns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    user_id = await extract_user(message, args) or update.effective_user.id
    result = sql.get_warns(user_id, chat.id)
    
    try:
        member = await chat.get_member(user_id)
        target_user = member.user
    except Exception:
        target_user = update.effective_user

    if result and result[0] != 0:
        num_warns, reasons = result
        limit, soft_warn, warn_mode = sql.get_warn_setting(chat.id)

        if reasons:
            text = (
                f"<b>Warnings Status</b>\nUser {mention_html(target_user.id, target_user.first_name)} has {num_warns}/{limit} warnings for the following reasons:"
            )
            for reason in reasons:
                text += f"\n- {reason}"

            msgs = split_message(text)
            for msg in msgs:
                await update.effective_message.reply_html(msg)
        else:
            await update.effective_message.reply_html(
                f"<b>Warnings Status</b>\nUser {mention_html(target_user.id, target_user.first_name)} has {num_warns}/{limit} warnings, but no reasons were recorded."
            )
    else:
        await update.effective_message.reply_html(f"<b>Warnings Status</b>\n{mention_html(target_user.id, target_user.first_name)} does not have any active warnings in <b>{html.escape(chat.title)}</b>.")

@cutiepii_cmd(command='addwarn', filters=filters.ChatType.GROUPS)
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
async def add_warn_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message

    args = msg.text.split(
        None, 1
    )

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) < 2:
        return

    keyword = extracted[0].lower()
    content = extracted[1]

    sql.add_warn_filter(chat.id, keyword, content)

    await update.effective_message.reply_text(f"<b>Warning Filter Added</b>\nWarning filter for keyword <code>{html.escape(keyword)}</code> has been added successfully.", parse_mode=ParseMode.HTML)
    raise DispatcherHandlerStop


@cutiepii_cmd(command=['nowarn', 'stopwarn'], filters=filters.ChatType.GROUPS)
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def remove_warn_filter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message

    args = msg.text.split(
        None, 1
    )

    if len(args) < 2:
        return

    extracted = split_quotes(args[1])

    if len(extracted) < 1:
        return

    to_remove = extracted[0]

    chat_filters = sql.get_chat_warn_triggers(chat.id)

    if not chat_filters:
        await msg.reply_html(f"<b>Warning Filters</b>\nNo warning filters are active in <b>{html.escape(chat.title)}</b>.")
        return

    for filt in chat_filters:
        if filt == to_remove:
            sql.remove_warn_filter(chat.id, to_remove)
            await msg.reply_text("<b>Warning Filter Removed</b>\nWarning filter has been removed successfully.", parse_mode=ParseMode.HTML)
            raise DispatcherHandlerStop

    await msg.reply_text(
        "<b>Warning Filter Not Found</b>\nThe specified keyword is not an active warning filter. Use <code>/warnlist</code> to view active filters.",
        parse_mode=ParseMode.HTML
    )

@cutiepii_cmd(command=['warnlist', 'warnfilters'], filters=filters.ChatType.GROUPS)
async def list_warn_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    all_handlers = sql.get_chat_warn_triggers(chat.id)

    if not all_handlers:
        await update.effective_message.reply_html(
            f"<b>Warning Filters</b>\nNo warning filters are active in <b>{html.escape(chat.title)}</b>.\n\n"
            f"Use <code>/warned</code> to view the list of warned users."
        )
        return

    filter_list = CURRENT_WARNING_FILTER_STRING
    for keyword in all_handlers:
        entry = f" - {html.escape(keyword)}\n"
        if len(entry) + len(filter_list) > MessageLimit.MAX_TEXT_LENGTH:
            await update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)
            filter_list = entry
        else:
            filter_list += entry

    if filter_list != CURRENT_WARNING_FILTER_STRING:
        # Append help tip to the final list message
        filter_list += f"\nUse <code>/warned</code> to view the list of warned users."
        await update.effective_message.reply_text(filter_list, parse_mode=ParseMode.HTML)


@cutiepii_cmd(command=['warned', 'warnslist'], filters=filters.ChatType.GROUPS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def list_warned_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    warned_list = sql.get_chat_warns(chat.id)

    if not warned_list:
        await update.effective_message.reply_html(f"<b>Warned Users</b>\nNo users currently have warnings in <b>{html.escape(chat.title)}</b>.")
        return

    limit, _, _ = sql.get_warn_setting(chat.id)
    text = f"<b>Warned Users</b>\nList of warned users in <b>{html.escape(chat.title)}</b>:\n"
    for user_warn in warned_list:
        try:
            member = await chat.get_member(user_warn.user_id)
            user_name = member.user.first_name
        except Exception:
            user_name = f"User {user_warn.user_id}"
        
        text += f"\n- {mention_html(user_warn.user_id, user_name)}: <code>{user_warn.num_warns}/{limit}</code> warns"
        if user_warn.reasons:
            # Filter out None values and clean reasons list
            clean_reasons = [r for r in user_warn.reasons if r]
            if clean_reasons:
                reasons_str = ", ".join(clean_reasons)
                text += f" (Reasons: <i>{html.escape(reasons_str)}</i>)"

    msgs = split_message(text)
    for msg in msgs:
        await update.effective_message.reply_html(msg)

@cutiepii_msg((CustomFilters.has_text & filters.ChatType.GROUPS), group=WARNS_GROUP)
@loggable
async def reply_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if not user:
        return

    if user.id == 777000:
        return
    if is_approved(chat.id, user.id):
        return

    chat_warn_filters = sql.get_chat_warn_triggers(chat.id)
    to_match = await extract_text(message)
    if not to_match:
        return ""

    for keyword in chat_warn_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            warn_filter = sql.get_warn_filter(chat.id, keyword)
            return await warn(user, update, warn_filter.reply, message)
    return ""

@cutiepii_cmd(command='warnlimit', filters=filters.ChatType.GROUPS, rate_limit_calls=5, rate_limit_window=60, add_error_handler=True)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@loggable
async def set_warn_limit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    if args:
        if args[0].isdigit():
            if int(args[0]) < 3:
                await msg.reply_text("<b>Invalid Limit</b>\nThe minimum warning limit is 3.", parse_mode=ParseMode.HTML)
            elif int(args[0]) > 9999:
                 await msg.reply_text("<b>Invalid Limit</b>\nThe warning limit specified is too large.", parse_mode=ParseMode.HTML)
            else:
                sql.set_warn_limit(chat.id, int(args[0]))
                await msg.reply_html(f"<b>Warn Limit Updated</b>\nWarn limit for <b>{html.escape(chat.title)}</b> has been set to <code>{args[0]}</code>.")
                return (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#SET_WARN_LIMIT\n"
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                    f"Set the warn limit to <code>{args[0]}</code>"
                )
        else:
            await msg.reply_text("<b>Invalid Argument</b>\nPlease specify a numeric value for the warn limit.", parse_mode=ParseMode.HTML)
    else:
        limit, soft_warn, warn_mode = sql.get_warn_setting(chat.id)

        await msg.reply_html("<b>Warn Limit Status</b>\nThe current warning limit is <code>{}</code>.\n\nTo change the limit, use <code>/warnlimit [number]</code>.".format(limit))
    return ""


@cutiepii_cmd(command=["warnmode", "setwarnmode", "strongwarn"], filters=filters.ChatType.GROUPS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def set_warn_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = context.args

    conn = await connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = await dispatcher.bot.get_chat(conn)
        chat_id = conn
        chat_name = chat.title
    else:
        if update.effective_message.chat.type == 'private':
            await send_message(update.effective_message, "<b>Action Denied</b>\nThis command can only be used in group chats.", parse_mode=ParseMode.HTML)
            return ""
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title

    if args:
        if args[0].lower() in ("kick", "soft"):
            sql.set_warn_mode(chat_id, 1)
            text = "<b>Warn Mode Updated</b>\nExceeding the warn limit will now result in a <b>kick</b> in <b>{}</b>. Users can rejoin immediately.".format(html.escape(chat_name))
            await send_message(update.effective_message, text, parse_mode=ParseMode.HTML)
            return "<b>{}:</b>\n" \
                   "<b>Admin:</b> {}\n" \
                   "Has changed the final warning to kick.".format(html.escape(chat_name),
                                                                            mention_html(user.id, user.first_name))

        elif args[0].lower() in ("ban", "banned", "hard"):
            sql.set_warn_mode(chat_id, 2)
            text = "<b>Warn Mode Updated</b>\nExceeding the warn limit will now result in a <b>ban</b> in <b>{}</b>.".format(html.escape(chat_name))
            await send_message(update.effective_message, text, parse_mode=ParseMode.HTML)
            return "<b>{}:</b>\n" \
                   "<b>Admin:</b> {}\n" \
                   "Has changed the final warning to banned.".format(html.escape(chat_name),
                                                                                  mention_html(user.id,
                                                                                               user.first_name))

        elif args[0].lower() in ("mute"):
            sql.set_warn_mode(chat_id, 3)
            text = "<b>Warn Mode Updated</b>\nExceeding the warn limit will now result in a <b>mute</b> in <b>{}</b>.".format(html.escape(chat_name))
            await send_message(update.effective_message, text, parse_mode=ParseMode.HTML)
            return "<b>{}:</b>\n" \
                   "<b>Admin:</b> {}\n" \
                   "Has changed the final warning to mute.".format(html.escape(chat_name),
                                                                                  mention_html(user.id,
                                                                                               user.first_name))

        else:
            await send_message(update.effective_message, "<b>Invalid Mode</b>\nUnrecognized warn mode. Please specify <code>kick</code>, <code>ban</code>, or <code>mute</code>.", parse_mode=ParseMode.HTML)
    else:
        limit, soft_warn, warn_mode = sql.get_warn_setting(chat_id)
        text = ""
        if not soft_warn:
            if not warn_mode:
                text = "Warns are currently set to <b>kick</b> users when they exceed the limits in <b>{}</b>.".format(html.escape(chat_name))
            elif warn_mode == 1:
                text = "Warns are currently set to <b>kick</b> users when they exceed the limits in <b>{}</b>.".format(html.escape(chat_name))
            elif warn_mode == 2:
                text = "Warns are currently set to <b>ban</b> users when they exceed the limits in <b>{}</b>.".format(html.escape(chat_name))
            elif warn_mode == 3:
                text = "Warns are currently set to <b>mute</b> users when they exceed the limits in <b>{}</b>.".format(html.escape(chat_name))
            await send_message(update.effective_message, text,
                           parse_mode=ParseMode.HTML)
        else:
            text = "Warns are currently set to <b>ban</b> users when they exceed the limits in <b>{}</b>.".format(html.escape(chat_name))
            await send_message(update.effective_message, text,
                           parse_mode=ParseMode.HTML)
    return ""


def __stats__():
    return (
        f"- {sql.num_warns()} overall warns, across {sql.num_warn_chats()} chats.\n"
        f"- {sql.num_warn_filters()} warn filters, across {sql.num_warn_filter_chats()} chats."
    )


async def __import_data__(chat_id, data):
    for user_id, count in data.get("warns", {}).items():
        for _ in range(int(count)):
            sql.warn_user(user_id, chat_id)


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


async def __chat_settings__(chat_id, user_id):
    num_warn_filters = sql.num_warn_chat_filters(chat_id)
    limit, soft_warn = sql.get_warn_setting(chat_id)
    return (
        f"This chat has `{num_warn_filters}` warn filters. "
        f"It takes `{limit} - executed!` warns before the user gets *{'kicked' if soft_warn else 'banned'}*."
    )

__help__ = True

__mod_name__ = "Warnings"
