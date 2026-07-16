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
import logging
from uuid import uuid4
from asyncio import sleep
from typing import List
from pydantic import BaseModel

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler, filters, CallbackQueryHandler

from Cutiepii_Robot import telethn, dispatcher, BOT_ID, LOGGER
from Cutiepii_Robot.modules.log_channel import loggable
import Cutiepii_Robot.modules.sql.purges_sql as sql
from Cutiepii_Robot.modules.sql.clear_cmd_sql import get_clearcmd
from Cutiepii_Robot.modules.helper_funcs.chat_status import (
    is_user_admin_callback_query,
    bot_admin,
    can_delete,
)
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    user_is_admin,
)
from Cutiepii_Robot.modules.helper_funcs.telethn.chatstatus import (
    can_delete_messages,
    user_can_purge
)
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, register

"""
@register(pattern='(?:(s)?purge|p)', groups_only=True, no_args=True)
async def purge_messages(event: NewMessage.Event):
    start = time.perf_counter()
    if event.from_id is None:
        return

    if not await user_is_admin(
            user_id=event.sender_id, message=event) and event.from_id not in [
                1087968824
            ]:
        await event.reply("Only Admins are allowed to use this command")
        return

    if not await user_can_purge(user_id=event.sender_id, message=event):
        await event.reply("You don't have the permission to delete messages")
        return

    if not await can_delete_messages(message=event):
        if event.chat.admin_rights is None:
            return await event.reply("I'm not an admin, do you mind promoting me first?")
        elif not event.chat.admin_rights.delete_messages:
            return await event.reply("I don't have the permission to delete messages!")

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        await event.reply(
            "Reply to a message to select where to start purging from.")
        return
    messages = []
    message_id = reply_msg.id
    delete_to = event.message.id

    messages.append(event.reply_to_msg_id)
    for msg_id in range(message_id, delete_to + 1):
        messages.append(msg_id)
        if len(messages) == 100:
            await event.client.delete_messages(event.chat_id, messages)
            messages = []

    try:
        await event.client.delete_messages(event.chat_id, messages)
    except:
        pass
    if not event.pattern_match.group(1):
        time_ = time.perf_counter() - start
        text = f"Purged Successfully in {time_:0.2f} Second(s)"
        prmsg = await event.respond(text, parse_mode='markdown')

        cleartime = get_clearcmd(event.chat_id, "purge")

        if cleartime:
            await sleep(cleartime.time)
            await prmsg.delete()
"""

class DeleteMessageCallback(BaseModel):
    purge_id: str
    chat_id: int
    message_ids: List[int]

DEL_MSG_CB_MAP: List[DeleteMessageCallback] = []

@cutiepii_callback(pattern=r"purge.*")
@is_user_admin_callback_query
@bot_admin_check(AdminPerms.CAN_DELETE_MESSAGES)
@user_admin_check(AdminPerms.CAN_DELETE_MESSAGES, allow_mods = True)
@loggable
async def purge_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    message = update.effective_message
    data = query.data
    purge_id = data.split("_")[-1]
    if data == "purge_cancel":
        await message.edit_text("<b>Purge Cancelled</b>\nThe message purge request has been cancelled.", parse_mode=ParseMode.HTML)
        return f"#PURGE_CANCELLED \n<b>Admin:</b> {query.from_user.first_name}\n<b>Chat:</b> {update.effective_chat.title}\n"

    for entry in DEL_MSG_CB_MAP:
        if entry.purge_id == purge_id:
            try:
                await context.bot.delete_messages(chat_id=entry.chat_id, message_ids=entry.message_ids)
                await query.edit_message_text(text="<b>Purge Completed</b>\nThe message purge has been completed successfully.", parse_mode=ParseMode.HTML)
                return f"#PURGE_COMPLETED \n<b>Admin:</b> {query.from_user.first_name}\n<b>Chat:</b> {update.effective_chat.title}\n<b>Messages:</b> {len(entry.message_ids)}\n"
            except BadRequest as e:
                if e.message == "Too many message identifiers specified":
                    for msg_id in entry.message_ids:
                        with contextlib.suppress(BadRequest):
                            await context.bot.delete_message(chat_id=entry.chat_id, message_id=msg_id)
                    await query.edit_message_text(text="<b>Purge Completed</b>\nThe message purge has been completed successfully.", parse_mode=ParseMode.HTML)
                    return f"#PURGE_COMPLETED \n<b>Admin:</b> {query.from_user.first_name}\n<b>Chat:</b> {update.effective_chat.title}\n<b>Messages:</b> {len(entry.message_ids)}\n"
                await query.edit_message_text(text="<b>Error</b>\nFailed to execute the message purge.", parse_mode=ParseMode.HTML)
                return f"#PURGE_FAILED \n<b>Admin:</b> {query.from_user.first_name}\n<b>Chat:</b> {update.effective_chat.title}\n"
    await query.edit_message_text(text="<b>Error</b>\nFailed to locate the purge configuration or target ID.", parse_mode=ParseMode.HTML)
    return f"#PURGE_FAILED \n<b>Admin:</b> {query.from_user.first_name}\n<b>Chat:</b> {update.effective_chat.title}\n"


@cutiepii_cmd(command='purge')
@bot_admin
@user_admin_check(AdminPerms.CAN_DELETE_MESSAGES, allow_mods = True)
@loggable
async def purge_messages_botapi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    message_id_from = update.effective_message.reply_to_message.message_id if update.effective_message.reply_to_message else None
    
    n = None
    if context.args:
        try:
            n = int(context.args[0])
        except ValueError:
            pass

    if not message_id_from:
        await update.effective_message.reply_text("<b>Invalid Command Usage</b>\nPlease reply to a message to define where to start purging from.", parse_mode=ParseMode.HTML)
        return
    messages_to_delete = []
    try:
        if n is not None:
            if n < 1:
                await update.effective_message.reply_text("<b>Invalid Argument</b>\nPlease specify a numeric value greater than zero.", parse_mode=ParseMode.HTML)
                return
            n = min(n, 1000)  # Safe upper limit
            messages_to_delete.extend(iter(range(message_id_from, message_id_from + n)))
            messages_to_delete.append(update.effective_message.message_id)
        else:
            message_id_to = update.effective_message.message_id
            messages_to_delete.extend(iter(range(message_id_from, message_id_to + 1)))

        entry = DeleteMessageCallback(chat_id=chat_id, message_ids=messages_to_delete, purge_id=str(uuid4()))
        DEL_MSG_CB_MAP.append(entry)
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Confirm",
                        callback_data=f"purge_confirm_{entry.purge_id}",
                    ),
                    InlineKeyboardButton(
                        text="Cancel", callback_data="purge_cancel"
                    ),
                ]
            ]
        )
        try:
            await update.effective_message.reply_text(
                f"<b>Confirm Message Purge</b>\nAre you sure you want to purge {len(messages_to_delete)} message(s) from <b>{html.escape(update.effective_chat.title)}</b>? This action cannot be undone.",
                reply_markup=buttons,
                parse_mode=ParseMode.HTML,
            )
        except BadRequest as e:
            if "message to be replied" in str(e).lower() or "not found" in str(e).lower():
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"<b>Confirm Message Purge</b>\nAre you sure you want to purge {len(messages_to_delete)} message(s) from <b>{html.escape(update.effective_chat.title)}</b>? This action cannot be undone.",
                    reply_markup=buttons,
                    parse_mode=ParseMode.HTML,
                )
            else:
                raise
        return f"#PURGE_ATTEMPT \n<b>Admin:</b> {update.effective_user.first_name} \n<b>Messages:</b> {len(messages_to_delete)}\n"
    except Exception as e:
        LOGGER.exception(e)
        with contextlib.suppress(Exception):
            await update.effective_message.reply_text("<b>Error</b>\nAn error occurred while performing the message purge.", parse_mode=ParseMode.HTML)

@cutiepii_cmd(command='spurge')
@bot_admin
@user_admin_check(AdminPerms.CAN_DELETE_MESSAGES, allow_mods = True)
@loggable
async def spurge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message

    if chat.type == "private":
        await message.reply_text("<b>Action Denied</b>\nThis command can only be used in group chats.", parse_mode=ParseMode.HTML)
        return ""

    reply_to = message.reply_to_message
    if not reply_to:
        await message.reply_text("<b>Invalid Command Usage</b>\nPlease reply to a message to define where to start silent purging from.", parse_mode=ParseMode.HTML)
        return ""

    message_id_from = reply_to.message_id
    message_id_to = message.message_id

    messages_to_delete = list(range(message_id_from, message_id_to + 1))

    try:
        chunks = [messages_to_delete[i:i + 100] for i in range(0, len(messages_to_delete), 100)]
        for chunk in chunks:
            try:
                await context.bot.delete_messages(chat_id=chat.id, message_ids=chunk)
            except BadRequest as e:
                if e.message == "Too many message identifiers specified":
                    for msg_id in chunk:
                        with contextlib.suppress(BadRequest):
                            await context.bot.delete_message(chat_id=chat.id, message_id=msg_id)
    except Exception as e:
        LOGGER.exception(e)
        with contextlib.suppress(Exception):
            await message.reply_text("<b>Error</b>\nAn error occurred while performing the silent purge.", parse_mode=ParseMode.HTML)
        return ""

    return f"#SILENT_PURGE \n<b>Admin:</b> {update.effective_user.first_name} \n<b>Messages:</b> {len(messages_to_delete)}\n"

@register(pattern='(del|d)', groups_only=True, no_args=True)
async def delete_messages(event):
    if event.from_id is None:
        return

    if not await user_is_admin(
        user_id=event.sender_id, message=event
    ) and event.from_id not in [1087968824]:
        await event.reply("<b>Action Denied</b>\nOnly administrators are authorized to use this command.", parse_mode=ParseMode.HTML)
        return

    if not await user_can_purge(user_id=event.sender_id, message=event):
        await event.reply("<b>Action Denied</b>\nYou do not have the required permissions to delete messages.", parse_mode=ParseMode.HTML)
        return

    message = await event.get_reply_message()
    me = await telethn.get_me()
    BOT_ID = me.id

    if not await can_delete_messages(message=event)\
        and message\
            and not int(message.sender.id) == int(BOT_ID):
        if event.chat.admin_rights is None:
            return await event.reply(
                "<b>Action Denied</b>\nI am not an administrator. Please promote me to administrator with delete message permissions.",
                parse_mode=ParseMode.HTML
                )
        elif not event.chat.admin_rights.delete_messages:
            return await event.reply(
                "<b>Action Denied</b>\nI do not have the required delete messages permission.",
                parse_mode=ParseMode.HTML
                )

    if not message:
        await event.reply("<b>Invalid Command Usage</b>\nPlease reply to the message you wish to delete.", parse_mode=ParseMode.HTML)
        return
    chat = await event.get_input_chat()
    await event.client.delete_messages(chat, message)
    try:
        await event.client.delete_messages(chat, event.message)
    except MessageDeleteForbiddenError:
        print("error in deleting message {} in {}".format(event.message.id, event.chat.id))
        pass


@cutiepii_cmd(command='purgefrom')
@bot_admin_check(AdminPerms.CAN_DELETE_MESSAGES)
@user_admin_check(AdminPerms.CAN_DELETE_MESSAGES, allow_mods = True)
async def purgefrom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    bot = context.bot

    if await can_delete(chat, bot.id):

        if msg.reply_to_message:

            message_id = msg.reply_to_message.message_id
            message_from = message_id - 1

            if sql.is_purgefrom(msg.chat_id, message_from):
                await msg.reply_text("<b>Invalid Range</b>\nThe source and target messages are identical. Please specify a range.", parse_mode=ParseMode.HTML)
                return

            sql.purgefrom(msg.chat_id, message_from)
            await msg.reply_to_message.reply_text("<b>Purge Start Marked</b>\nMessage has been marked for deletion. Reply to another message with <code>/purgeto</code> to execute the purge.", parse_mode=ParseMode.HTML)

        else:
            await msg.reply_text("<b>Invalid Command Usage</b>\nPlease reply to a message to mark the start of the purge.", parse_mode=ParseMode.HTML)
            return ""

    return ""


@register(pattern='(purgeto|pt)', groups_only=True, no_args=True)
@bot_admin_check(AdminPerms.CAN_DELETE_MESSAGES)
@user_admin_check(AdminPerms.CAN_DELETE_MESSAGES, allow_mods = True)
async def purgeto_messages(event):
    start = time.perf_counter()
    if event.from_id is None:
        return

    if not await user_is_admin(
        user_id=event.sender_id, message=event,
    ) and event.from_id not in [1087968824]:
        await event.reply("<b>Action Denied</b>\nOnly administrators are authorized to use this command.", parse_mode=ParseMode.HTML)
        return

    if not await can_delete_messages(message=event):
        await event.reply("<b>Error</b>\nUnable to perform the purge action.", parse_mode=ParseMode.HTML)
        return

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        await event.reply("<b>Invalid Command Usage</b>\nPlease reply to a message to define where to end the purge.", parse_mode=ParseMode.HTML)
        return

    messages = []

    x = sql.show_purgefrom(event.chat_id)
    for i in x:
        try:
            message_id = int(i.message_from)
            message_from_ids = []
            message_from_ids.append(int(i.message_from))
            for message_from in message_from_ids:
                sql.clear_purgefrom(event.chat_id, message_from)
        except:
            pass
    messages.append(message_id)
    delete_to = reply_msg.id

    for msg_id in range(message_id, delete_to + 1):
        messages.append(msg_id)
        if len(messages) == 100:
            await event.client.delete_messages(event.chat_id, messages)
            messages = []
    LOGGER.debug(messages)
    try:
        await event.client.delete_messages(event.chat_id, messages)
    except:
        pass
    time_ = time.perf_counter() - start
    text = f"<b>Purge Completed</b>\nSuccessfully purged messages in {time_:0.2f} seconds."
    await event.respond(text, parse_mode=ParseMode.HTML)


@register(pattern="^/purgeuser(?:@Cutiepii_Robot)?$")
async def purge_user_messages(event):
    if not event.is_group:
        await event.reply("<b>Action Denied</b>\nThis command can only be used in group chats.", parse_mode=ParseMode.HTML)
        return

    # Check if sender is admin and has delete permission
    permissions = await event.client.get_permissions(event.chat_id, event.message.sender_id)
    if not permissions.is_admin or not permissions.delete_messages:
        await event.reply("<b>Action Denied</b>\nOnly administrators with delete messages permission can use this command.", parse_mode=ParseMode.HTML)
        return

    # Check if bot is admin and has delete permission
    bot_perms = await event.client.get_permissions(event.chat_id, event.client.get_me().id)
    if not bot_perms.is_admin or not bot_perms.delete_messages:
        await event.reply("<b>Action Denied</b>\nI require the delete messages permission to execute this command.", parse_mode=ParseMode.HTML)
        return

    reply = await event.get_reply_message()
    if not reply:
        await event.reply("<b>Invalid Command Usage</b>\nPlease reply to a message of the user whose messages you want to purge.", parse_mode=ParseMode.HTML)
        return

    target_user_id = reply.sender_id
    status_msg = await event.reply("<b>Purge In Progress</b>\nSearching and deleting recent messages from the user...", parse_mode=ParseMode.HTML)

    # Fetch last 100 messages in the chat
    to_delete = [event.message.id]
    async for msg in event.client.iter_messages(event.chat_id, limit=100):
        if msg.sender_id == target_user_id:
            to_delete.append(msg.id)

    try:
        await event.client.delete_messages(event.chat_id, to_delete)
        await status_msg.edit(f"<b>Purge Completed</b>\nSuccessfully purged {len(to_delete) - 1} messages.", parse_mode=ParseMode.HTML)
        await sleep(3)
        await status_msg.delete()
    except Exception as e:
        await status_msg.edit(f"<b>Error</b>\nFailed to purge messages: {html.escape(str(e))}", parse_mode=ParseMode.HTML)


__help__ = True

__mod_name__ = "Purges"
