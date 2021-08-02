import os
import html
import requests
import json
import Cutiepii_Robot.modules.sql.chatbot_sql as sql

from time import sleep
from telegram import ParseMode
from Cutiepii_Robot import dispatcher, updater, SUPPORT_CHAT
from Cutiepii_Robot.modules.log_channel import gloggable
from telegram import Message, Chat, Update, Bot, MessageEntity
from telegram.error import BadRequest, RetryAfter, Unauthorized
from telegram.ext import CommandHandler, run_async, CallbackContext, MessageHandler, Filters
from Cutiepii_Robot.modules.helper_funcs.filters import CustomFilters
from Cutiepii_Robot.modules.helper_funcs.chat_status import user_admin
from telegram.utils.helpers import mention_html, mention_markdown, escape_markdown

@user_admin
@gloggable
def add_chat(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    is_cutiepii = sql.is_cutiepii(chat.id)
    if not is_cutiepii:
        sql.set_cutiepii(chat.id)
        msg.reply_text("Cutiepii AI successfully enabled for this chat!")
        message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#AI_ENABLED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        )
        return message
    msg.reply_text("Cutiepii AI is already enabled for this chat!")
    return ""


@user_admin
@gloggable
def remove_chat(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    is_cutiepii = sql.is_cutiepii(chat.id)
    if not is_cutiepii:
        msg.reply_text("Cutiepii AI isn't enabled here in the first place!")
        return ""
    sql.rem_cutiepii(chat.id)
    msg.reply_text("AI disabled successfully!")
    message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#AI_DISABLED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
    )
    return message

def chatbot(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if not update.effective_message.chat.type == "private":
        is_cutiepii = sql.is_cutiepii(chat_id)
        if not is_cutiepii:
            return
    message = update.message.text
    cutiepiiurl = requests.get('https://kuki.up.railway.app/cutiepii/chatbot?message='+message)
    cutiepii = json.loads(cutiepiiurl.text)
    cutiepii = cutiepii['reply']
    update.message.reply_text(cutiepii)

def list_cutiepii_chats(update: Update, context: CallbackContext):
    chats = sql.get_all_cutiepii_chats()
    text = "<b>cutiepii-Enabled Chats</b>\n"
    for chat in chats:
        try:
            x = context.bot.get_chat(int(*chat))
            name = x.title if x.title else x.first_name
            text += f"• <code>{name}</code>\n"
        except BadRequest:
            sql.rem_cutiepii(*chat)
        except Unauthorized:
            sql.rem_cutiepii(*chat)
        except RetryAfter as e:
            sleep(e.retry_after)
    update.effective_message.reply_text(text, parse_mode="HTML")

__help__ = f"""
Chatbot utilizes the cutiepii • YukiCloud API and allows Saitama to talk and provides a more interactive group chat experience.

*Commands:* 
*Admins only:*
   ➢ `/addchat`*:* Enables Chatbot mode in the chat.
   ➢ `/rmchat`*:* Disables Chatbot mode in the chat.

Reports bugs at @{SUPPORT_CHAT}

*Powered by cutiepii • YukiCloud API*
"""

ADD_CUTIEPII_HANDLER = CommandHandler("addchat", add_chat, run_async=True)
REMOVE_CUTIEPII_HANDLER = CommandHandler("rmchat", remove_chat, run_async=True)
CHATBOT_HANDLER = MessageHandler(
    Filters.text & (~Filters.regex(r"^#[^\s]+") & ~Filters.regex(r"^!")
                    & ~Filters.regex(r"^\/")), chatbot)
LIST_cutiepii_CHATS_HANDLER = CommandHandler(
    "cutiepiichats", list_cutiepii_chats, filters=CustomFilters.dev_filter, run_async=True)

dispatcher.add_handler(ADD_CUTIEPII_HANDLER)
dispatcher.add_handler(REMOVE_CUTIEPII_HANDLER)
dispatcher.add_handler(LIST_cutiepii_CHATS_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)

__handlers__ = [
    ADD_CUTIEPII_HANDLER,
    REMOVE_CUTIEPII_HANDLER,
    LIST_cutiepii_CHATS_HANDLER,
    CHATBOT_HANDLER,
]
