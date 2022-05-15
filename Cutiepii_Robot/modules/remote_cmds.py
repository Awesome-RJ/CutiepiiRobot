"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2022, Yūki • Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

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

from telegram import Update, ChatPermissions
from telegram.error import BadRequest, TelegramError
from telegram.ext import CallbackContext

from Cutiepii_Robot import LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
from Cutiepii_Robot.modules.helper_funcs.chat_status import dev_plus
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user_and_text
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    AdminPerms,
    bot_is_admin,
)

RBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to punch it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can punch group administrators",
    "Channel_private",
    "Not in the chat",
}

RUNBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to punch it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can punch group administrators",
    "Channel_private",
    "Not in the chat",
}

RKICK_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to punch it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can punch group administrators",
    "Channel_private",
    "Not in the chat",
}

RMUTE_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to punch it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can punch group administrators",
    "Channel_private",
    "Not in the chat",
}

RUNMUTE_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to punch it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can punch group administrators",
    "Channel_private",
    "Not in the chat",
}

@cutiepii_cmd(command='rban')
@dev_plus
async def rban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        await message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return
    if not chat_id:
        await message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = await bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message != 'Chat not found':
            raise
        await message.reply_text(
            "Chat not found! Make sure you entered a valid chat ID and I'm part of that chat."
        )

        return
    if chat.type == "private":
        await message.reply_text("I'm sorry, but that's a private chat!")
        return

    if not bot_is_admin(chat, AdminPerms.CAN_RESTRICT_MEMBERS):
        await message.reply_text(
            "I can't unrestrict people there! Make sure I'm admin and can unban users."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != 'User not found':
            raise
        await message.reply_text("I can't seem to find this user")
        return
    if member.status in ["creator", "administrator"]:
        await message.reply_text("I really wish I could ban admins...")
        return

    if user_id == bot.id:
        await message.reply_text("I'm not gonna BAN myself, are you crazy?")
        return

    try:
        chat.ban_member(user_id)
        await message.reply_text("Banned from chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            await message.reply_text("Banned!", quote=False)
        elif excp.message in RBAN_ERRORS:
            await message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR banning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await message.reply_text("Well damn, I can't ban that user.")

@cutiepii_cmd(command='runban')
@dev_plus
async def runban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        await message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return
    if not chat_id:
        await message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = await bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message != 'Chat not found':
            raise
        await message.reply_text(
            "Chat not found! Make sure you entered a valid chat ID and I'm part of that chat."
        )
        return

    if chat.type == "private":
        await message.reply_text("I'm sorry, but that's a private chat!")
        return

    if not bot_is_admin(chat, AdminPerms.CAN_RESTRICT_MEMBERS):
        await message.reply_text(
            "I can't unrestrict people there! Make sure I'm admin and can unban users."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != 'User not found':
            raise
        await message.reply_text("I can't seem to find this user there")
        return
    if member.status not in ("left", "kicked"):
        await message.reply_text(
            "Why are you trying to remotely unban someone that's already in that chat?"
        )
        return

    if user_id == bot.id:
        await message.reply_text("I'm not gonna UNBAN myself, I'm an admin there!")
        return

    try:
        chat.unban_member(user_id)
        await message.reply_text("Yep, this user can join that chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            await message.reply_text("Unbanned!", quote=False)
        elif excp.message in RUNBAN_ERRORS:
            await message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR unbanning user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await message.reply_text("Well damn, I can't unban that user.")

@cutiepii_cmd(command=['rpunch', 'rkick'])
@dev_plus
async def rkick(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        await message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return
    if not chat_id:
        await message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = await bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message != "Chat not found":
            raise

        await message.reply_text(
            "Chat not found! Make sure you entered a valid chat ID and I'm part of that chat."
        )
        return
    if chat.type == "private":
        await message.reply_text("I'm sorry, but that's a private chat!")
        return

    if not bot_is_admin(chat, AdminPerms.CAN_RESTRICT_MEMBERS):
        await message.reply_text(
            "I can't unrestrict people there! Make sure I'm admin and can unban users."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        await message.reply_text("I can't seem to find this user")
        return
    if member.status in ["creator", "administrator"]:
        await message.reply_text("I really wish I could punch admins...")
        return

    if user_id == bot.id:
        await message.reply_text("I'm not gonna punch myself, are you crazy?")
        return

    try:
        chat.unban_member(user_id)
        await message.reply_text("Punched from chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            await message.reply_text("Punched!", quote=False)
        elif excp.message in RKICK_ERRORS:
            await message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR punching user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await message.reply_text("Well damn, I can't punch that user.")

@cutiepii_cmd(command='rmute')
@dev_plus
async def rmute(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        await message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return
    if not chat_id:
        await message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = await bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message != "Chat not found":
            raise

        await message.reply_text(
            "Chat not found! Make sure you entered a valid chat ID and I'm part of that chat."
        )
        return
    if chat.type == "private":
        await message.reply_text("I'm sorry, but that's a private chat!")
        return

    if not bot_is_admin(chat, AdminPerms.CAN_RESTRICT_MEMBERS):
        await message.reply_text(
            "I can't unrestrict people there! Make sure I'm admin and can unban users."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        await message.reply_text("I can't seem to find this user")
        return
    if member.status in ["creator", "administrator"]:
        await message.reply_text("I really wish I could mute admins...")
        return

    if user_id == bot.id:
        await message.reply_text("I'm not gonna MUTE myself, are you crazy?")
        return

    try:
        await bot.restrict_chat_member(
            chat.id, user_id, permissions=ChatPermissions(can_send_messages=False)
        )
        await message.reply_text("Muted from the chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            await message.reply_text("Muted!", quote=False)
        elif excp.message in RMUTE_ERRORS:
            await message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR mute user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await message.reply_text("Well damn, I can't mute that user.")

@cutiepii_cmd(command='runmute')
@dev_plus
async def runmute(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message

    if not args:
        await message.reply_text("You don't seem to be referring to a chat/user.")
        return

    user_id, chat_id = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return
    if not chat_id:
        await message.reply_text("You don't seem to be referring to a chat.")
        return

    try:
        chat = await bot.get_chat(chat_id.split()[0])
    except BadRequest as excp:
        if excp.message != "Chat not found":
            raise

        await message.reply_text(
            "Chat not found! Make sure you entered a valid chat ID and I'm part of that chat."
        )
        return
    if chat.type == "private":
        await message.reply_text("I'm sorry, but that's a private chat!")
        return

    if not bot_is_admin(chat, AdminPerms.CAN_RESTRICT_MEMBERS):
        await message.reply_text(
            "I can't unrestrict people there! Make sure I'm admin and can unban users."
        )
        return

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message != "User not found":
            raise

        await message.reply_text("I can't seem to find this user there")
        return
    if member.status not in ("left", "kicked") and (
        member.can_send_messages
        and member.can_send_media_messages
        and member.can_send_other_messages
        and member.can_add_web_page_previews
    ):
        await message.reply_text("This user already has the right to speak in that chat.")
        return

    if user_id == bot.id:
        await message.reply_text("I'm not gonna UNMUTE myself, I'm an admin there!")
        return

    try:
        await bot.restrict_chat_member(
            chat.id,
            int(user_id),
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        await message.reply_text("Yep, this user can talk in that chat!")
    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            await message.reply_text("Unmuted!", quote=False)
        elif excp.message in RUNMUTE_ERRORS:
            await message.reply_text(excp.message)
        else:
            LOGGER.warning(update)
            LOGGER.exception(
                "ERROR unmnuting user %s in chat %s (%s) due to %s",
                user_id,
                chat.title,
                chat.id,
                excp.message,
            )
            await message.reply_text("Well damn, I can't unmute that user.")

# https://github.com/el0xren/tgbot/commits/master/tg_bot/modules/misc.py
# ported from tgbot, thanks to el0xren
@cutiepii_cmd(command='recho')
@dev_plus
async def recho(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message
    try:
        chat_id = str(args[0])
        del args[0]
    except TypeError as excp:
        await message.reply_text("Please give me a chat ID.")
    to_send = " ".join(args)
    if len(to_send) >= 2:
        try:
            await bot.sendMessage(int(chat_id), to_send)
        except TelegramError:
            await message.reply_text("Couldn't send the message. Perhaps I'm not part of that group?")
