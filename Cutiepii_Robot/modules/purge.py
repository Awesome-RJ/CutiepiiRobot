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

import time
import contextlib
import Cutiepii_Robot.modules.sql.purges_sql as sql

from asyncio import sleep
from telethon import events
from telethon.errors.rpcerrorlist import MessageDeleteForbiddenError
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CommandHandler, filters

from Cutiepii_Robot import telethn, CUTIEPII_PTB, BOT_ID, LOGGER
from Cutiepii_Robot.modules.helper_funcs.chat_status import can_delete
from Cutiepii_Robot.modules.sql.clear_cmd_sql import get_clearcmd
from Cutiepii_Robot.modules.helper_funcs.anonymous import user_admin
from Cutiepii_Robot.modules.helper_funcs.telethn.chatstatus import (
    can_delete_messages, user_is_admin, user_can_purge)


async def purge_messages(event):
    start = time.perf_counter()
    if event.sender_id is None:
        return

    if not await user_is_admin(user_id=event.sender_id,
                               message=event) and event.sender_id not in [
                                   1087968824
                               ]:
        await event.reply("ou Don't Have Permission To Delete Messages")
        return

    if not await user_can_purge(user_id=event.sender_id, message=event):
        await event.reply("You don't have the permission to delete messages")
        return

    if not await can_delete_messages(message=event):
        if event.chat.admin_rights is None:
            return await event.reply(
                "I'm not an admin, do you mind promoting me first?")
        if not event.chat.admin_rights.delete_messages:
            return await event.reply(
                "I don't have the permission to delete messages!")

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        await event.reply(
            "Reply to a message to select where to start purging from.")
        return
    message_id = reply_msg.id
    delete_to = event.message.id

    messages = [event.reply_to_msg_id]
    for msg_id in range(message_id, delete_to + 1):
        messages.append(msg_id)
        if len(messages) == 100:
            await event.client.delete_messages(event.chat_id, messages)
            messages = []

    try:
        await event.client.delete_messages(event.chat_id, messages)
    except:
        pass
    time_ = time.perf_counter() - start
    text = f"Purged Successfully in {time_:0.2f} Second(s)"
    prmsg = await event.respond(text, parse_mode='MarkdownV2')

    if cleartime := get_clearcmd(event.chat_id, "purge"):
        await sleep(cleartime.time)
        await prmsg.delete()


async def delete_messages(event):

    # async for user in telethn.iter_participants(
    #         event.chat_id, filter=ChannelParticipantsAdmins):
    #     LOGGER.debug(user)

    if event.sender_id is None:
        return

    if not await user_is_admin(user_id=event.sender_id,
                               message=event) and event.sender_id not in [
                                   1087968824
                               ]:
        await event.reply("ou Don't Have Permission To Delete Messages")
        return

    if not await user_can_purge(user_id=event.sender_id, message=event):
        await event.reply("You don't have the permission to delete messages")
        return

    message = await event.get_reply_message()
    if not message:
        await event.reply("Whadya want to delete?")
        return
    # LOGGER.debug(message.sender.id)
    # LOGGER.debug(BOT_ID)
    # # LOGGER.debug(event.sender_id.ChatAdminRights)
    # LOGGER.debug(event.chat.admin_rights)
    # LOGGER.debug(event.stringify())
    if not await can_delete_messages(message=event) and int(
            message.sender.id) != int(BOT_ID):
        if event.chat.admin_rights is None:
            await event.reply(
                "I'm not an admin, do you mind promoting me first?")
        elif not event.chat.admin_rights.delete_messages:
            await event.reply("I don't have the permission to delete messages!"
                              )
        return

    chat = await event.get_input_chat()
    await event.client.delete_messages(chat, message)
    try:
        await event.client.delete_messages(chat, event.message)
    except MessageDeleteForbiddenError:
        LOGGER.debug(
            f"error in deleting message {event.message.id} in {event.chat.id}")


@user_admin
async def purgefrom(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message
    chat = update.effective_chat
    bot = context.bot

    if can_delete(chat, bot.id):

        if msg.reply_to_message:

            message_id = msg.reply_to_message.message_id
            message_from = message_id - 1

            if sql.is_purgefrom(msg.chat_id, message_from):
                await msg.reply_text(
                    "The source and target are same, give me a range.")
                return

            sql.purgefrom(msg.chat_id, message_from)
            msg.reply_to_message.reply_text(
                "Message marked for deletion. Reply to another message with purgeto to delete all messages in between."
            )

        else:
            await msg.reply_text(
                "Reply to a message to let me know what to delete.")
            return ""

    return ""


async def purgeto_messages(event):
    start = time.perf_counter()

    if event.sender_id is None:
        return

    if not await user_is_admin(
            user_id=event.sender_id,
            message=event,
    ) and event.sender_id not in [1087968824]:
        await event.reply("ou Don't Have Permission To Delete Messages")
        return

    if not await can_delete_messages(message=event):
        await event.reply("Can't seem to purge the message")
        return

    reply_msg = await event.get_reply_message()
    if not reply_msg:
        await event.reply(
            "Reply to a message to select where to start purging from.")
        return

    x = sql.show_purgefrom(event.chat_id)
    for i in x:
        with contextlib.suppress(Exception):
            message_id = int(i.message_from)
            message_from_ids = [int(i.message_from)]
            for message_from in message_from_ids:
                sql.clear_purgefrom(Update.effective_message.chat_id,
                                    message_from)
    messages = [message_id]
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
    text = f"Purged Successfully in {time_:0.2f}s"
    await event.respond(text, parse_mode=ParseMode.MARKDOWN)


__help__ = """
*Admins only:*
➛ /del*:* deletes the message you replied to
➛ /purge*:* deletes all messages between this and the replied to message.
➛ /purge <number>*:* if replied to with a number, deletes that many messages from target message, if sent normally in group then delete from current to previous messages
➛ /purgefrom*:* marks a start point to purge from
➛ /purgeto*:* marks the end point, messages bet to and from are deleted
"""

#Telethon CMDs
PURGE_HANDLER = purge_messages, events.NewMessage(pattern=r"^[!/]purge(?!\S+)")
PURGETO_HANDLER = purgeto_messages, events.NewMessage(pattern="^[!/]purgeto$")
DEL_HANDLER = delete_messages, events.NewMessage(pattern="^[!/]del$")

#PTB CMDs
CUTIEPII_PTB.add_handler(
    CommandHandler("purgefrom", purgefrom, filters=filters.ChatType.GROUPS))

telethn.add_event_handler(*PURGE_HANDLER)
telethn.add_event_handler(*PURGETO_HANDLER)
telethn.add_event_handler(*DEL_HANDLER)

__mod_name__ = "Purges"
__command_list__ = ["del", "purge", "purgefrom", "purgeto"]
