import json
import html
import requests
from time import sleep

from requests.exceptions import (
RequestException, 
Timeout,
TooManyRedirects, 
ConnectionError, 
ReadTimeout, 
)
        
from telegram import Message, Update
from telegram.utils.helpers import mention_html, mention_markdown, escape_markdown
from telegram.error import BadRequest, RetryAfter, Unauthorized
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler
)

import Cutiepii_Robot.modules.redis.chatbot_redis as redis

from Cutiepii_Robot import dispatcher, SUPPORT_CHAT
from Cutiepii_Robot.modules.log_channel import gloggable
from Cutiepii_Robot.modules.helper_funcs.filters import CustomFilters
from Cutiepii_Robot.modules.helper_funcs.chat_status import user_admin, sudo_plus

@user_admin
@gloggable
def add_chat(update: Update, context: CallbackContext):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    is_enabled = redis.is_chatbot(chat.id)
    if chat.type == "private":
        msg.reply_text("You can't enable AI in PM.")
        return
    if not is_enabled:
        redis.set_chatbot(chat.id)
        msg.reply_text("Cutiepii successfully enabled for this chat!")
        message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"AI_ENABLED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        )
        return message
    msg.reply_text("Cutiepii is already enabled for this chat!")
    return ""

@user_admin
@gloggable
def rem_chat(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    is_enabled = redis.is_chatbot(chat.id)
    if chat.type == "private":
        msg.reply_text("You can't enable/disable AI in PM.")
        return
    if not is_enabled:
        msg.reply_text("Cutiepii isn't enabled here in the first place!")
        return ""
    redis.rem_chatbot(chat.id)
    msg.reply_text("ChatBot disabled successfully!")
    message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"AI_DISABLED\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
    )
    return message

def check_message(context: CallbackContext, message):
    reply_msg = message.reply_to_message

    if reply_msg:
        if reply_msg.from_user.id == context.bot.get_me().id:
            return True
    else:
        return False

def chatbot_talk(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    bot = context.bot   
    query = update.message.text     
    is_chatbot = redis.is_chatbot(chat_id)
    if not is_chatbot:
        return
    if not check_message(context, msg):
        return                
    try:
        api = "https://kukichatai.vercel.app/message="+query
        armin = requests.get(api)
        eren = json.loads(armin.text)
        bot.send_chat_action(chat_id, action="typing")
        mikasa = eren["reply"]
        sleep(0.3)
        msg.reply_text(mikasa)       
    except (RequestException, Timeout, TooManyRedirects, ConnectionError, ReadTimeout, BadRequest) as e:
        print(e)
        msg.reply_text(f"Encountered {e}! Report it at @{SUPPORT_CHAT} as soon as possible!")

@sudo_plus       
def list_chatbot_chats(update: Update, context: CallbackContext):
    chats = redis.list_chatbots()
    text = "<b>AI-Enabled Chats</b>\n"
    for chat in chats:
        try:
            x = context.bot.get_chat(chat)
            name = x.title or x.first_name
            text += f"• <code>{name}</code>\n"
        except BadRequest:
            redis.rem_chatbot(chat)
        except Unauthorized:
            redis.rem_chatbot(chat)
        except RetryAfter as e:
            sleep(e.retry_after)
    update.effective_message.reply_text(text, parse_mode="HTML")

    
__help__ = """
Chatbot utilizes the Kuki's api which allows Eren to talk and provide a more interactive group chat experience.
*Admins only Commands*:
  ➢ `/addchat`*:* Enables Chatbot mode in the chat.
  ➢ `/rmchat`*:* Disables Chatbot mode in the chat.
"""

__mod_name__ = "ChatBot"

ADD_CHAT_HANDLER = CommandHandler("addchat", add_chat, run_async=True)
REMOVE_CHAT_HANDLER = CommandHandler("rmchat", rem_chat, run_async=True)
CHATBOT_HANDLER = MessageHandler(
    Filters.text & (~Filters.regex(r"^#[^\s]+") & ~Filters.regex(r"^!")
                    & ~Filters.regex(r"^\/")), chatbot_talk, run_async=True)
LIST_AI_HANDLER = CommandHandler(["listchats", "listai", "listchatbots"], list_chatbot_chats, run_async=True)

dispatcher.add_handler(ADD_CHAT_HANDLER)
dispatcher.add_handler(REMOVE_CHAT_HANDLER)
dispatcher.add_handler(CHATBOT_HANDLER)
dispatcher.add_handler(LIST_AI_HANDLER)

__handlers__ = [
    ADD_CHAT_HANDLER,
    REMOVE_CHAT_HANDLER,
    CHATBOT_HANDLER,
    LIST_AI_HANDLER,
]