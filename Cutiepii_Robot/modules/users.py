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

import contextlib

from io import BytesIO
from asyncio import sleep

from telegram import Update
from telegram.error import BadRequest, TelegramError
from telegram.ext import MessageHandler, CommandHandler, CallbackContext, filters

import Cutiepii_Robot.modules.sql.users_sql as sql
from Cutiepii_Robot import CUTIEPII_PTB, LOGGER

USERS_GROUP = 4
CHAT_GROUP = 10


async def get_user_id(username):
    # ensure valid userid
    if len(username) <= 5:
        return None

    if username.startswith("@"):
        username = username[1:]

    users = sql.get_userid_by_name(username)

    if not users:
        return None

    if len(users) == 1:
        return users[0]["_id"]
    for user_obj in users:
        try:
            userdat = await CUTIEPII_PTB.bot.get_chat(user_obj["_id"])
            if userdat.username == username:
                return userdat.id

        except BadRequest as excp:
            if excp.message != "Chat not found":
                LOGGER.exception("Error extracting user ID")

    return None


async def broadcast(update: Update, context: CallbackContext) -> None:
    to_send = await update.effective_message.text.split(None, 1)
    if len(to_send) >= 2:
        chats_ = sql.get_all_chats() or []
        failed = 0
        for chat in chats_:
            try:
                await context.bot.sendMessage(int(chat["chat_id"]), to_send[1])
                sleep(0.1)
            except TelegramError:
                failed += 1
                LOGGER.warning(
                    "Couldn't send broadcast to %s, group name %s",
                    str(chat["chat_id"]),
                    str(chat["chat_name"]),
                )

        await update.effective_message.reply_text(
            f"Broadcast complete. {failed} groups failed to receive the message, probably due to being kicked."
        )


async def log_user(update: Update, _: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message

    sql.update_user(msg.from_user.id, msg.from_user.username, chat.id,
                    chat.title)

    if rep := msg.reply_to_message:
        sql.update_user(
            rep.from_user.id,
            rep.from_user.username,
            chat.id,
            chat.title,
        )

        if rep.forward_from:
            sql.update_user(
                rep.forward_from.id,
                rep.forward_from.username,
            )

        if rep.entities:
            for entity in rep.entities:
                if entity.type in ["text_mention", "mention"]:
                    with contextlib.suppress(AttributeError):
                        sql.update_user(entity.user.id, entity.user.username)
        if rep.sender_chat and not rep.is_automatic_forward:
            sql.update_user(
                rep.sender_chat.id,
                rep.sender_chat.username,
                chat.id,
                chat.title,
            )

    if msg.forward_from:
        sql.update_user(msg.forward_from.id, msg.forward_from.username)

    if msg.entities:
        for entity in msg.entities:
            if entity.type in ["text_mention", "mention"]:
                with contextlib.suppress(AttributeError):
                    sql.update_user(entity.user.id, entity.user.username)
    if msg.sender_chat and not msg.is_automatic_forward:
        sql.update_user(msg.sender_chat.id, msg.sender_chat.username, chat.id,
                        chat.title)

    if msg.new_chat_members:
        for user in msg.new_chat_members:
            if user.id == msg.from_user.id:  # we already added that in the first place
                continue
            sql.update_user(user.id, user.username, chat.id, chat.title)


async def chats(update: Update, context: CallbackContext) -> None:
    all_chats = sql.get_all_chats() or []
    chatfile = "List of chats.\n0. Chat name | Chat ID | Members count\n"
    P = 1
    for chat in all_chats:
        with contextlib.suppress(Exception):
            curr_chat = await context.bot.getChat(chat.chat_id)
            chat_members = curr_chat.get_member_count(context.bot.id)
            chatfile += f"{P}. {chat.chat_name} | {chat.chat_id} | {chat_members}\n"
            P += 1
    with BytesIO(str.encode(chatfile)) as output:
        output.name = "glist.txt"
        await update.effective_message.reply_document(
            document=output,
            filename="glist.txt",
            caption="Here be the list of groups in my database.",
        )


def build_keyboard_alternate(buttons):
    keyb = []
    for btn in buttons:
        if btn[2] and keyb:
            keyb[-1].append(InlineKeyboardButton(btn[0], url=btn[1]))
        else:
            keyb.append([InlineKeyboardButton(btn[0], url=btn[1])])

    return keyb


"""
async def chat_checker(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    if (
        await update.effective_message.chat.get_member(bot.id).can_send_messages
        is False
    ):
        await bot.leaveChat(update.effective_message.chat.id)
"""


def __user_info__(user_id):
    if user_id in [777000, 1087968824]:
        return """╘═━「 Groups count: <code>???</code> 」"""
    if user_id == 1241223850:
        return """╘═━「 Groups count: <code>???</code> 」"""
    num_chats = sql.get_user_num_chats(user_id)
    return f"""╘═━「 Groups count: <code>{num_chats}</code> 」"""


def __stats__():
    return f"➛ {sql.num_users()} users, across {sql.num_chats()} chats"


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


CUTIEPII_PTB.add_handler(
    CommandHandler(["broadcastall", "broadcastusers", "broadcastgroups"],
                   broadcast))
CUTIEPII_PTB.add_handler(
    MessageHandler(filters.ALL & filters.ChatType.GROUPS, log_user))
#CUTIEPII_PTB.add_handler(MessageHandler(filters.ALL & filters.ChatType.GROUPS, chat_checker))
CUTIEPII_PTB.add_handler(CommandHandler("groups", chats))

__mod_name__ = "Users"
