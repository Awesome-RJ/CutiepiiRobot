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
import contextlib
import sys

from typing import Optional
from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, User, Bot, Chat, ChatPermissions, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.helpers import mention_html

from Cutiepii_Robot import (
    DEV_USERS,
    SUDO_USERS,
    SUPPORT_USERS,
    OWNER_ID,
    WHITELIST_USERS,
    CUTIEPII_PTB,
    LOGGER,
)
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.connection import connected
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user
from Cutiepii_Robot.modules.helper_funcs.chat_status import is_user_admin, connection_status
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user_and_text
from Cutiepii_Robot.modules.helper_funcs.string_handling import extract_time
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
)

MEDIA_PERMISSIONS = ChatPermissions(can_send_messages=True,
                                    can_send_media_messages=True,
                                    can_send_polls=True,
                                    can_send_other_messages=True,
                                    can_add_web_page_previews=True)

NOMEDIA_PERMISSIONS = ChatPermissions(can_send_messages=True,
                                      can_send_media_messages=False,
                                      can_send_polls=False,
                                      can_send_other_messages=False,
                                      can_add_web_page_previews=False)


async def check_user(user_id: int, bot: Bot, update: Update) -> Optional[str]:
    if not user_id:
        return "⚠️ User not found\n\nYou don't seem to be referring to a user or the ID specified is incorrect.."

    try:
        member = await update.effective_chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == 'User not found':
            return "I can't seem to find this user"
        raise
    if user_id == bot.id:
        return "I'm not gonna MUTE myself, How high are you?"

    if await is_user_admin(update, user_id,
                           member) and user_id not in DEV_USERS:
        if user_id == OWNER_ID:
            return "I'd never ban my owner."
        if user_id in SUDO_USERS:
            return "My sudos are ban immune"
        if user_id in SUPPORT_USERS:
            return "My support users are ban immune"
        if user_id in WHITELIST_USERS:
            return "Bring an order from My Devs to fight a Whitelist user."
        return "Can't. Find someone else to mute but not this one."

    return None


@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def mute(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    user_id, reason = await extract_user_and_text(message, args)
    reply = await check_user(user_id, bot, update)

    if reply:
        await message.reply_text(reply)
        return ""

    member = await chat.get_member(user_id)

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#MUTE\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}\n"
    )

    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    if member.can_send_messages is None or member.can_send_messages:
        chat_permissions = ChatPermissions(can_send_messages=False)
        await bot.restrict_chat_member(chat.id, user_id, chat_permissions)
        mutemsg = (
            f"<b>╔━「 Mute Event</b>\n"
            f"<b>➛ Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>➛ User:</b> {mention_html(member.user.id, member.user.first_name)}\n"
        )
        if reason:
            mutemsg += f"<b>➛ Reason</b>: <code>{reason}</code>"

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("[► 🔊 Unmute ◄]",
                                 callback_data=f"cb_unmute({user_id})")
        ]])

        await context.bot.send_message(chat.id,
                                       mutemsg,
                                       reply_markup=keyboard,
                                       parse_mode=ParseMode.HTML)

        return log
    await message.reply_text("⚠️ This user is already muted! ⚠️")

    return ""


@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def button(update: Update, context: CallbackContext) -> str:
    query: Optional[CallbackQuery] = update.callback_query
    user: Optional[User] = update.effective_user
    chat = update.effective_chat
    admeme = chat.get_member(user.id)
    match = re.match(r"cb_unmute\((.+?)\)", query.data)
    if match and admeme.status == "administrator":

        bot = context.bot
        user_id = match[1]
        chat: Optional[Chat] = update.effective_chat
        user_member = await chat.get_member(user_id)

        if user_member.status in ["kicked", "left"]:
            user_member.reply_text(
                "This user isn't even in the chat, unmuting them won't make them talk more than they "
                "already do!")

        elif (user_member.can_send_messages
              and user_member.can_send_media_messages
              and user_member.can_send_other_messages
              and user_member.can_add_web_page_previews):
            update.effective_message.edit_tex(
                "This user already has the right to speak.")
        else:
            chat_permissions = ChatPermissions(
                can_send_messages=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            )
            with contextlib.suppress(BadRequest):
                await bot.restrict_chat_member(chat.id, (user_id),
                                               chat_permissions)
            await update.effective_message.edit_text(
                f"Yep! User {mention_html(admeme.user.id, admeme.user.first_name)} can start talking again in {chat.title}!",
                parse_mode=ParseMode.HTML,
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNMUTE\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
            )


@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def unmute(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    user = update.effective_user

    user_id, reason = await extract_user_and_text(message, args)
    if not user_id:
        await message.reply_text(
            "You'll need to either give me a username to unmute, or reply to someone to be unmuted."
        )
        return ""

    member = chat.get_member(user.id)

    if member.status in ["kicked", "left"]:
        await message.reply_text(
            "This user isn't even in the chat, unmuting them won't make them talk more than they "
            "already do!")

    elif (member.can_send_messages and member.can_send_media_messages
          and member.can_send_other_messages
          and member.can_add_web_page_previews):
        await message.reply_text("This user already has the right to speak.")
    else:
        chat_permissions = ChatPermissions(
            can_send_messages=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_send_polls=True,
            can_change_info=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
        )
        with contextlib.suppress(BadRequest):
            await bot.restrict_chat_member(chat.id, (user_id),
                                           chat_permissions)
        unmutemsg = "{} was unmuted by {} in <b>{}</b>".format(
            mention_html(member.user.id, member.user.first_name),
            user.first_name, message.chat.title)
        if reason:
            unmutemsg += "\n<b>Reason</b>: <code>{}</code>".format(reason)
        await bot.sendMessage(
            chat.id,
            unmutemsg,
            parse_mode=ParseMode.HTML,
        )
        return (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#UNMUTE\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}"
        )
    return ""


@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def temp_mute(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    user = update.effective_user

    user_id, reason = await extract_user_and_text(message, args)
    reply = await check_user(user_id, bot, update)

    if reply:
        await message.reply_text(reply)
        return ""

    member = await chat.get_member(user_id)

    if not reason:
        await message.reply_text(
            "You haven't specified a time to mute this user for!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    mutetime = await extract_time(message, time_val)

    if not mutetime:
        return ""

    log = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#TEMP MUTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(member.user.id, member.user.first_name)}\n"
        f"<b>Time:</b> {time_val}")
    if reason:
        log += f"\n<b>Reason:</b> {reason}"

    try:
        if member.can_send_messages is None or member.can_send_messages:
            chat_permissions = ChatPermissions(can_send_messages=False)
            await bot.restrict_chat_member(chat.id,
                                           user_id,
                                           chat_permissions,
                                           until_date=mutetime)

            msg = (
                f"Yep! Temporary Muted {mention_html(member.user.id, member.user.first_name)} from talking for <code>{time_val}</code> in {chat.title}\n"
                f"by {mention_html(user.id, html.escape(user.first_name))}", )

            await bot.sendMessage(
                chat.id,
                f"Muted <b>{html.escape(member.user.first_name)}</b> for {time_val}!\n<b>Reason</b>: <code>{reason}</code>",
                parse_mode=ParseMode.HTML,
            )
            return log
        await message.reply_text("This user is already muted.")

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            await message.reply_text(f"Muted for {time_val}!", quote=False)
            return log
        LOGGER.warning(update)
        LOGGER.exception(
            "ERROR muting user %s in chat %s (%s) due to %s",
            user_id,
            chat.title,
            chat.id,
            excp.message,
        )
        await message.reply_text("Well damn, I can't mute that user.")

    return ""


@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def temp_nomedia(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    bot = context.bot
    args = context.args

    conn = await connected(bot, chat, chat, user.id)
    if conn is not False:
        chatD = await CUTIEPII_PTB.bot.getChat(conn)
    elif chat.type == "private":
        sys.exit(1)
    else:
        chatD = chat

    user_id, reason = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(chat.id,
                                 "You don't seem to be referring to a user.")
        return ""

    try:
        member = await chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        await message.reply_text(chat.id, "I can't seem to find this user")
        return ""
    if await is_user_admin(update, user_id, member):
        await message.reply_text(chat.id,
                                 "I really wish I could restrict admins...")
        return ""

    if user_id == bot.id:
        await message.reply_text(
            chat.id, "I'm not gonna RESTRICT myself, are you crazy?")
        return ""

    if not reason:
        await message.reply_text(
            chat.id, "You haven't specified a time to restrict this user for!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    reason = split_reason[1] if len(split_reason) > 1 else ""
    mutetime = await extract_time(message, time_val)

    if not mutetime:
        return ""

    log = f"<b>{html.escape(chat.title)}:</b>\n#TEMP RESTRICTED\n<b>➛ Admin:</b> {mention_html(user.id, user.first_name)}\n<b>➛ User:</b> {mention_html(member.user.id, member.user.first_name)}\n<b>➛ ID:</b> <code>{user_id}</code>\n<b>➛ Time:</b> {time_val}"

    if reason:
        log += f"\n<b>➛ Reason:</b> {reason}"

    try:
        if member.can_send_messages is None or member.can_send_messages:
            await context.bot.restrict_chat_member(chat.id,
                                                   user_id,
                                                   NOMEDIA_PERMISSIONS,
                                                   until_date=mutetime)
            await message.reply_text(
                chat.id, "Restricted from sending media for {} in {}!").format(
                    time_val, chatD.title)
            return log
        await message.reply_text(
            chat.id,
            "This user is already restricted in {}.").format(chatD.title)

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            await message.reply_text(
                chat.id,
                f"Restricted for {time_val} in {chatD.title}!",
                quote=False)
            return log
        LOGGER.warning(update)
        LOGGER.exception("ERROR muting user %s in chat %s (%s) due to %s",
                         user_id, chat.title, chat.id, excp.message)
        await message.reply_text(chat.id,
                                 "Well damn, I can't restrict that user.")

    return ""


@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def media(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    bot = context.bot
    args = context.args

    conn = await connected(bot, chat, chat, user.id)
    if conn is not False:
        chatD = await CUTIEPII_PTB.bot.getChat(conn)
    elif chat.type == "private":
        sys.exit(1)
    else:
        chatD = chat

    user_id = extract_user(message, args)
    if not user_id:
        await message.reply_text(
            chat.id,
            "You'll need to either give me a username to unrestrict, or reply to someone to be unrestricted."
        )
        return ""

    member = chatD.get_member((user_id))

    if member.status in ['kicked', 'left']:
        await message.reply_text(
            chat.id,
            "This user isn't even in the chat, unrestricting them won't make them send anything than they "
            "already do!")

    elif member.can_send_messages and member.can_send_media_messages \
                and member.can_send_other_messages and member.can_add_web_page_previews:
        await message.reply_text(
            chat.id,
            "This user already has the rights to send anything in {}.").format(
                chatD.title)
    else:
        await context.bot.restrict_chat_member(chatD.id, (user_id),
                                               NOMEDIA_PERMISSIONS)
        keyboard = []
        reply = (chat.id, "Yep, {} can send media again in {}!").format(
            mention_html(member.user.id, member.user.first_name), chatD.title)
        await message.reply_text(reply, parse_mode=ParseMode.HTML)
        return f"<b>{html.escape(chatD.title)}:</b>\n#UNRESTRICTED\n<b>➛ Admin:</b> {mention_html(user.id, user.first_name)}\n<b>➛ User:</b> {mention_html(member.user.id, member.user.first_name)}\n<b>➛ ID:</b> <code>{user_id}</code>"

    return ""


@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def nomedia(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]
    bot = context.bot
    args = context.args

    conn = await connected(bot, chat, chat, user.id)
    if conn is not False:
        chatD = await CUTIEPII_PTB.bot.getChat(conn)
    elif chat.type == "private":
        sys.exit(1)
    else:
        chatD = chat

    user_id = extract_user(message, args)
    if not user_id:
        await message.reply_text(
            chat.id,
            "You'll need to either give me a username to restrict, or reply to someone to be restricted."
        )
        return ""

    if user_id == bot.id:
        await message.reply_text(chat.id, "I'm not restricting myself!")
        return ""

    if member := chatD.get_member((user_id)):
        if await is_user_admin(update, user_id, member=member):
            await message.reply_text(chat.id,
                                     "Afraid I can't restrict admins!")

        elif member.can_send_messages is None or member.can_send_messages:
            await context.bot.restrict_chat_member(chatD.id, user_id,
                                                   NOMEDIA_PERMISSIONS)
            keyboard = []
            reply = (chat.id,
                     "{} is restricted from sending media in {}!").format(
                         mention_html(member.user.id, member.user.first_name),
                         chatD.title)
            await message.reply_text(reply, parse_mode=ParseMode.HTML)
            return f"<b>{html.escape(chatD.title)}:</b>\n#RESTRICTED\n<b>➛ Admin:</b> {mention_html(user.id, user.first_name)}\n<b>➛ User:</b> {mention_html(member.user.id, member.user.first_name)}\n<b>➛ ID:</b> <code>{user_id}</code>"

        else:
            await message.reply_text(chat.id,
                                     "This user is already restricted in {}!")
    else:
        await message.reply_text(chat.id, "This user isn't in the {}!").format(
            chatD.title)

    return ""


CUTIEPII_PTB.add_handler(CommandHandler("mute", mute))
CUTIEPII_PTB.add_handler(CommandHandler("unmute", unmute))
CUTIEPII_PTB.add_handler(CommandHandler(['tmute', 'tempmute'], temp_mute))
CUTIEPII_PTB.add_handler(
    DisableAbleCommandHandler(["trestrict", "temprestrict"],
                              temp_nomedia,
                              admin_ok=True))
CUTIEPII_PTB.add_handler(
    DisableAbleCommandHandler(["restrict", "nomedia"], nomedia, admin_ok=True))
CUTIEPII_PTB.add_handler(
    DisableAbleCommandHandler("unrestrict", media, admin_ok=True))
CUTIEPII_PTB.add_handler(CallbackQueryHandler(button, pattern=r"cb_unmute"))

__mod_name__ = "Muting"
