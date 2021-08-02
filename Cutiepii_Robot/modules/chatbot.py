
# Copyright (C) 2021 MoeZilla

# This file is part of Cutiepii (Telegram Bot)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import os
import html
import requests
import Cutiepii_Robot.modules.sql.kuki_sql as sql

from time import sleep
from telegram import ParseMode
from Cutiepii_Robot import dispatcher, updater
from Cutiepii_Robot.modules.log_channel import gloggable
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram.error import BadRequest, RetryAfter, Unauthorized
from telegram.ext import CommandHandler, run_async, CallbackContext, MessageHandler
from Cutiepii_Robot.modules.helper_funcs.filters import CustomFilters
from Cutiepii_Robot.modules.helper_funcs.chat_status import user_admin
from telegram.utils.helpers import mention_html, mention_markdown, escape_markdown

@user_admin
@gloggable
def add_chat(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    is_kuki = sql.is_kuki(chat.id)
    if not is_kuki:
        sql.set_kuki(chat.id)
        msg.reply_text("Cutiepii AI successfully enabled for this chat!")
        message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"Cutiepii_ENABLED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        )
        return message
    msg.reply_text("Cutiepii AI is already enabled for this chat!")
    return ""


@user_admin
@gloggable
def rem_chat(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    is_kuki = sql.is_kuki(chat.id)
    if not is_kuki:
        msg.reply_text("Cutiepii AI isn't enabled here in the first place!")
        return ""
    sql.rem_kuki(chat.id)
    msg.reply_text("Cutiepii AI disabled successfully!")
    message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"Cutiepii_DISABLED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
    )
    return message

def chatbot(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not update.effective_message.chat.type == "private":
        is_kuki = sql.is_kuki(chat_id)
        if not is_kuki:
            return
    message = update.message.text
    kukiurl = requests.get('https://kuki-yukicloud.up.railway.app/Kuki/chatbot?message='+message)
    Kuki = json.loads(kukiurl.text)
    kuki = Kuki['reply']
    update.message.reply_text(kuki)

def list_all_chats(update: Update, context: CallbackContext):
    chats = sql.get_all_kuki_chats()
    text = "<b>KUKI-Enabled Chats</b>\n"
    for chat in chats:
        try:
            x = context.bot.get_chat(int(*chat))
            name = x.title if x.title else x.first_name
            text += f"• <code>{name}</code>\n"
        except BadRequest:
            sql.rem_kuki(*chat)
        except Unauthorized:
            sql.rem_kuki(*chat)
        except RetryAfter as e:
            sleep(e.retry_after)
    update.effective_message.reply_text(text, parse_mode="HTML")

ADD_CHAT_HANDLER = CommandHandler("addchat", add_chat, run_async=True)
REMOVE_CHAR_HANDLER = CommandHandler("rmchat", rem_chat, run_async=True)
CHATBOT_HANDLER = MessageHandler(
    Filters.text & (~Filters.regex(r"^#[^\s]+") & ~Filters.regex(r"^!")
                    & ~Filters.regex(r"^\/")), chatbot)
LIST_ALL_CHATS_HANDLER = CommandHandler(
    "allchats", list_all_chats, filters=CustomFilters.dev_filter, run_async=True)

dispatcher.add_handler(ADD_CHAT_HANDLER)
dispatcher.add_handler(REMOVE_CHAR_HANDLER)
dispatcher.add_handler(LIST_ALL_CHATS_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)

__handlers__ = [
    ADD_CHAT_HANDLER,
    REMOVE_CHAT_HANDLER,
    LIST_ALL_CHATS_HANDLER,
    CHATBOT_HANDLER,
]



