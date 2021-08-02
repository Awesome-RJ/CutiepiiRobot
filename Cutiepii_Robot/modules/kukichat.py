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
def add_kuki(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    is_kuki = sql.is_kuki(chat.id)
    if not is_kuki:
        sql.set_kuki(chat.id)
        msg.reply_text("Kuki AI successfully enabled for this chat!")
        message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"KUKI_ENABLED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        )
        return message
    msg.reply_text("Kuki AI is already enabled for this chat!")
    return ""


@user_admin
@gloggable
def rem_kuki(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    is_kuki = sql.is_kuki(chat.id)
    if not is_kuki:
        msg.reply_text("Kuki AI isn't enabled here in the first place!")
        return ""
    sql.rem_kuki(chat.id)
    msg.reply_text("AI disabled successfully!")
    message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"KUKI_DISABLED\n"
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

def list_kuki_chats(update: Update, context: CallbackContext):
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

ADD_KUKI_HANDLER = CommandHandler("addkuki", add_kuki, run_async=True)
REMOVE_KUKI_HANDLER = CommandHandler("rmkuki", rem_kuki, run_async=True)
CHATBOT_HANDLER = MessageHandler(
    Filters.text & (~Filters.regex(r"^#[^\s]+") & ~Filters.regex(r"^!")
                    & ~Filters.regex(r"^\/")), chatbot)
LIST_KUKI_CHATS_HANDLER = CommandHandler(
    "kukichats", list_kuki_chats, filters=CustomFilters.dev_filter, run_async=True)

dispatcher.add_handler(ADD_KUKI_HANDLER)
dispatcher.add_handler(REMOVE_KUKI_HANDLER)
dispatcher.add_handler(LIST_KUKI_CHATS_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)

__handlers__ = [
    ADD_KUKI_HANDLER,
    REMOVE_KUKI_HANDLER,
    LIST_KUKI_CHATS_HANDLER,
    CHATBOT_HANDLER,
]




