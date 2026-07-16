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
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, ChatMemberHandler
from telegram.constants import ParseMode

from Cutiepii_Robot import dispatcher, LOGGER, DEV_USERS, SUDO_USERS
from Cutiepii_Robot.modules.sql import blacklist_chats_sql as sql
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_chatmember, cutiepii_cmd, cutiepii_msg


@cutiepii_cmd(command=["blacklist_chat", "blacklistchat"], filters=filters.User(DEV_USERS + SUDO_USERS))
async def blacklist_chat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("Please provide a chat ID to blacklist.")
        return

    chat_id = args[0].strip()
    sql.blacklist_chat(chat_id)
    await message.reply_text(f"✅ Chat <code>{chat_id}</code> has been blacklisted. The bot will leave it if added.", parse_mode=ParseMode.HTML)
    
    # Try to leave right away if the bot is in this chat
    try:
        await context.bot.leave_chat(int(chat_id))
    except Exception:
        pass


@cutiepii_cmd(command=["whitelist_chat", "whitelistchat"], filters=filters.User(DEV_USERS + SUDO_USERS))
async def whitelist_chat_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("Please provide a chat ID to whitelist.")
        return

    chat_id = args[0].strip()
    if sql.whitelist_chat(chat_id):
        await message.reply_text(f"✅ Chat <code>{chat_id}</code> has been whitelisted.", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("This chat was not blacklisted.")


@cutiepii_cmd(command="blacklisted_chats", filters=filters.User(DEV_USERS + SUDO_USERS))
async def blacklisted_chats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chats = sql.get_all_blacklisted_chats()

    if not chats:
        await message.reply_text("There are no blacklisted chats.")
        return

    reply = "🚫 <b>Blacklisted Chats:</b>\n\n" + "\n".join(f"❍ <code>{c}</code>" for c in chats)
    await message.reply_text(reply, parse_mode=ParseMode.HTML)


# Auto-leave when added or when receiving messages in blacklisted chats
@cutiepii_msg(pattern=filters.ALL & ~filters.ChatType.PRIVATE, group=100)
@cutiepii_chatmember(group=0)
async def check_blacklisted_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat:
        return

    if sql.is_chat_blacklisted(chat.id):
        LOGGER.info(f"Auto-leaving blacklisted chat: {chat.title} ({chat.id})")
        try:
            await context.bot.send_message(chat.id, "This chat is blacklisted by the bot developers. Leaving...")
        except Exception:
            pass
        try:
            await context.bot.leave_chat(chat.id)
        except Exception as e:
            LOGGER.error(f"Failed to leave blacklisted chat {chat.id}: {e}")


__mod_name__ = "Blacklist Chats"
__help__ = True

__handlers__ = [
]
