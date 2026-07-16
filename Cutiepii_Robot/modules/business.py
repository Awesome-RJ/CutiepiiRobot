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
from telegram.ext import ContextTypes, BusinessConnectionHandler, MessageHandler, CommandHandler, filters
from telegram.constants import ParseMode

from Cutiepii_Robot import dispatcher, LOGGER, REDIS
from Cutiepii_Robot.modules.sql import business_sql as sql
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_business_connection, cutiepii_cmd, cutiepii_msg


@cutiepii_cmd(command="bizgreet", can_disable=False)
async def biz_greet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args

    if not args:
        current_greeting = sql.get_biz_greeting(user.id)
        if current_greeting:
            await message.reply_text(
                f"🏢 <b>Your Current Business Greeting:</b>\n\n<code>{html.escape(current_greeting)}</code>",
                parse_mode=ParseMode.HTML
            )
        else:
            await message.reply_text("You have not set any business greeting. Usage: `/bizgreet [greeting message]`")
        return

    greeting_text = " ".join(args).strip()
    sql.set_biz_greeting(user.id, greeting_text)
    await message.reply_text("✅ Business greeting message has been updated successfully!")


@cutiepii_cmd(command="biztrigger", can_disable=False)
async def biz_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args

    if len(args) < 2:
        await message.reply_text("Usage: `/biztrigger [keyword] [reply text]`")
        return

    keyword = args[0].lower().strip()
    reply = " ".join(args[1:]).strip()

    sql.add_biz_trigger(user.id, keyword, reply)
    await message.reply_text(f"✅ Business trigger for <code>{html.escape(keyword)}</code> added successfully!", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="biztriggers", can_disable=False)
async def biz_triggers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    triggers = sql.get_biz_triggers(user.id)
    if not triggers:
        await message.reply_text("You don't have any active business triggers.")
        return

    reply = "🏢 <b>Your Business Triggers:</b>\n\n"
    for t in triggers:
        reply += f"❍ <code>{html.escape(t.keyword)}</code> ➔ <i>{html.escape(t.reply[:100])}</i>\n"

    await message.reply_text(reply, parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="bizdeltrigger", can_disable=False)
async def biz_del_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args

    if not args:
        await message.reply_text("Usage: `/bizdeltrigger [keyword]`")
        return

    keyword = args[0].lower().strip()
    if sql.remove_biz_trigger(user.id, keyword):
        await message.reply_text(f"✅ Business trigger for <code>{html.escape(keyword)}</code> removed successfully!", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(f"Could not find a trigger for <code>{html.escape(keyword)}</code>.", parse_mode=ParseMode.HTML)


# Handler for business connection updates
@cutiepii_business_connection()
async def business_connection_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    connection = update.business_connection
    if not connection:
        return

    user_id = connection.user.id
    connection_id = connection.id

    if connection.is_enabled:
        sql.set_business_connection(user_id, connection_id)
        LOGGER.info(f"Telegram Business connected: User {user_id} connected bot via connection {connection_id}")
    else:
        sql.remove_business_connection(connection_id)
        LOGGER.info(f"Telegram Business disconnected for connection {connection_id}")


# Handler for business messages
@cutiepii_msg(pattern=filters.UpdateType.BUSINESS_MESSAGES)
async def business_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    biz_msg = update.business_message
    if not biz_msg:
        return

    connection_id = biz_msg.business_connection_id
    chat = biz_msg.chat
    sender = biz_msg.from_user
    text = biz_msg.text

    # Resolve business owner from Redis or DB (connection ID mapping)
    # To find which user owns this connection, we can look up config
    owner_config = sql.SESSION.query(sql.BusinessConfig).filter(sql.BusinessConfig.connection_id == connection_id).first()
    if not owner_config:
        return

    owner_id = owner_config.user_id

    # Avoid self-triggering
    if sender.id == owner_id:
        return

    # 1. Greeting Check
    greeting = sql.get_biz_greeting(owner_id)
    if greeting:
        is_greeted = REDIS.sismember(f"biz_greeted:{owner_id}", sender.id)
        if not is_greeted:
            REDIS.sadd(f"biz_greeted:{owner_id}", sender.id)
            # Set TTL to 1 day so we can greet them again if they return later
            REDIS.expire(f"biz_greeted:{owner_id}", 86400)
            try:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=greeting,
                    business_connection_id=connection_id
                )
            except Exception as e:
                LOGGER.error(f"Failed to send business greeting: {e}")

    # 2. Smart Triggers Check
    if text:
        trigger_reply = sql.match_biz_trigger(owner_id, text)
        if trigger_reply:
            try:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=trigger_reply,
                    business_connection_id=connection_id
                )
            except Exception as e:
                LOGGER.error(f"Failed to send business trigger reply: {e}")





__mod_name__ = "Business"
__help__ = True

__handlers__ = [
]
