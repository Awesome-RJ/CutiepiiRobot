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
from telegram.ext import ContextTypes, ChatBoostHandler, CommandHandler, filters
from telegram.constants import ParseMode
from telegram.helpers import mention_html

from Cutiepii_Robot import dispatcher, LOGGER, telethn
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import Channel, Chat
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_chat_boost, cutiepii_cmd


@cutiepii_cmd(command=["boosts", "boost"], filters=filters.ChatType.GROUPS, can_disable=False)
async def chat_boosts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    
    boost_count = 0
    boost_level = 0
    try:
        # Fetch and cache entity to resolve access_hash for Telethon
        entity = await telethn.get_entity(chat.id)
        if isinstance(entity, Channel):
            full_channel = await telethn(GetFullChannelRequest(channel=entity))
            full_chat = full_channel.full_chat
            boost_count = getattr(full_chat, 'boosts_applied', 0) or getattr(full_chat, 'boosts_count', 0) or 0
            boost_level = getattr(full_chat, 'level', 0) or 0
        elif isinstance(entity, Chat):
            boost_count = 0
            boost_level = 0
    except Exception as e:
        LOGGER.exception(f"Failed to fetch chat boost status via Telethon: {e}")
        try:
            full_chat = await context.bot.get_chat(chat.id)
            boost_count = getattr(full_chat, 'unrestrict_boost_count', 0) or 0
        except Exception:
            pass
    
    reply = (
        f"⭐️ <b>CHAT BOOST STATUS:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🚀 <b>Group Name:</b> {html.escape(chat.title)}\n"
        f"📈 <b>Current Level:</b> <code>Level {boost_level}</code>\n"
        f"💎 <b>Total Boosts:</b> <code>{boost_count} boosts</code>\n\n"
        f"📊 <b>LEVEL BENEFITS:</b>\n"
    )
    
    if boost_level >= 1:
        reply += "❍ 🎥 Increased video quality & duration (4 min → 8 min)\n"
        reply += "❍ 🎨 Custom emoji reactions enabled\n"
    if boost_level >= 2:
        reply += "❍ 🎙️ Audio/Video transcription support\n"
        reply += "❍ 🎭 Enhanced animations\n"
    if boost_level >= 3:
        reply += "❍ 🎭 Custom background wallpaper\n"
        reply += "❍ 🏷️ Profile badges\n"
    if boost_level == 0:
        reply += "❍ No level benefits active yet. Boost the group to unlock premium features!\n"
        
    reply += (
        f"\n🔗 <b>Boost Link:</b> <a href='https://t.me/c/{str(chat.id).replace('-100', '')}?boost'>Boost Group</a>\n\n"
        f"<i>To boost, users must have Telegram Premium.</i>"
    )
    
    await message.reply_text(reply, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@cutiepii_chat_boost()
async def chat_boost_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    boost_update = update.chat_boost
    if not boost_update:
        return
        
    chat = boost_update.chat
    boost = boost_update.boost
    
    source = boost.source
    source_name = "Premium User"
    if source.source == "gift_code":
        source_name = "Gift Subscription"
    elif source.source == "giveaway":
        source_name = "Giveaway Winner"
        
    user = source.user
    user_mention = mention_html(user.id, user.first_name) if user else "Anonymous User"
    
    alert = (
        f"🚀 <b>Group Boosted!</b> 🚀\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"Thank you {user_mention} for boosting <b>{html.escape(chat.title)}</b>!\n"
        f"❍ <b>Boost Type:</b> <code>{source_name}</code>\n"
        f"❍ <b>Boost ID:</b> <code>{boost.boost_id}</code>\n"
        f"❍ <b>Expiration:</b> {boost.expiration_date.strftime('%Y-%m-%d') if boost.expiration_date else 'Never'}\n\n"
        f"Your contribution helps unlock premium group features!"
    )
    
    try:
        await context.bot.send_message(chat.id, alert, parse_mode=ParseMode.HTML)
    except Exception as e:
        LOGGER.error(f"Failed to send boost alert in {chat.id}: {e}")




__mod_name__ = "Boosts"
__help__ = True

__handlers__ = [
]
