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

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

from Cutiepii_Robot import dispatcher, REDIS
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd, cutiepii_msg


async def get_tag_alert_users(chat_id: int) -> list:
    """Get list of users who have tag alerts enabled"""
    users = REDIS.smembers(f"tagalert_{chat_id}")
    return [int(user_id) for user_id in users] if users else []


async def enable_tag_alert(chat_id: int, user_id: int):
    """Enable tag alerts for a user"""
    REDIS.sadd(f"tagalert_{chat_id}", user_id)


async def disable_tag_alert(chat_id: int, user_id: int):
    """Disable tag alerts for a user"""
    REDIS.srem(f"tagalert_{chat_id}", user_id)


async def is_tag_alert_enabled(chat_id: int, user_id: int) -> bool:
    """Check if user has tag alerts enabled"""
    return REDIS.sismember(f"tagalert_{chat_id}", user_id)


@cutiepii_msg(pattern=(filters.TEXT | filters.CAPTION) & filters.ChatType.GROUPS, group=15)
async def check_tags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check messages for user tags and send alerts"""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    if not message.text and not message.caption:
        return
    
    text = message.text or message.caption
    
    # Get users who have tag alerts enabled
    alert_users = await get_tag_alert_users(chat.id)
    
    if not alert_users:
        return
    
    # Check if any mentioned user has alerts enabled
    if message.entities or message.caption_entities:
        entities = message.entities or message.caption_entities
        
        for entity in entities:
            if entity.type == "mention":
                # Extract username
                username = text[entity.offset:entity.offset + entity.length].replace('@', '')
                
                # Check if this user has alerts enabled
                for alert_user_id in alert_users:
                    try:
                        alert_user = await context.bot.get_chat(alert_user_id)
                        if alert_user.username and alert_user.username.lower() == username.lower():
                            # Send alert to user
                            try:
                                link = f"https://t.me/{chat.username}/{message.message_id}" if chat.username else None
                                
                                alert_text = (
                                    f"🔔 <b>Tag Alert!</b>\n\n"
                                    f"You were mentioned by {user.mention_html()} in {chat.title}\n\n"
                                    f"<b>Message:</b> {text[:200]}{'...' if len(text) > 200 else ''}"
                                )
                                
                                if link:
                                    alert_text += f'\n\n<a href="{link}">View Message</a>'
                                
                                await context.bot.send_message(
                                    alert_user_id,
                                    alert_text,
                                    parse_mode=ParseMode.HTML
                                )
                            except Exception:
                                # User blocked bot or error occurred
                                pass
                    except Exception:
                        continue
            
            elif entity.type == "text_mention":
                # Direct user mention
                mentioned_user = entity.user
                
                if mentioned_user.id in alert_users:
                    try:
                        link = f"https://t.me/{chat.username}/{message.message_id}" if chat.username else None
                        
                        alert_text = (
                            f"🔔 <b>Tag Alert!</b>\n\n"
                            f"You were mentioned by {user.mention_html()} in {chat.title}\n\n"
                            f"<b>Message:</b> {text[:200]}{'...' if len(text) > 200 else ''}"
                        )
                        
                        if link:
                            alert_text += f'\n\n<a href="{link}">View Message</a>'
                        
                        await context.bot.send_message(
                            mentioned_user.id,
                            alert_text,
                            parse_mode=ParseMode.HTML
                        )
                    except Exception:
                        # User blocked bot or error occurred
                        pass


@cutiepii_cmd(command="tagalert")
async def tagalert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable/disable tag alerts"""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    
    # Only works in groups
    if chat.type not in ['group', 'supergroup']:
        await message.reply_text("This command only works in groups!")
        return
    
    if not args:
        # Show current status
        status = "enabled" if is_tag_alert_enabled(chat.id, user.id) else "disabled"
        await message.reply_text(
            f"Tag alerts are currently <b>{status}</b> for you in this group.\n\n"
            f"Use `/tagalert on` to enable\n"
            f"Use `/tagalert off` to disable",
            parse_mode=ParseMode.HTML
        )
        return
    
    if args[0].lower() in ["on", "yes", "enable"]:
        enable_tag_alert(chat.id, user.id)
        await message.reply_text(
            "✅ Tag alerts enabled!\n"
            "You will receive a private message when someone mentions you in this group.\n\n"
            "<b>Note:</b> Make sure you have started a private chat with me!",
            parse_mode=ParseMode.HTML
        )
    elif args[0].lower() in ["off", "no", "disable"]:
        disable_tag_alert(chat.id, user.id)
        await message.reply_text("❌ Tag alerts disabled!")
    else:
        await message.reply_text("Use `/tagalert on` or `/tagalert off`")


@cutiepii_cmd(command="tagalertall")
async def tagalert_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable tag alerts in all groups"""
    message = update.effective_message
    user = update.effective_user
    
    await message.reply_text(
        "⚠️ Tag alerts are configured per-group.\n\n"
        f"Use `/tagalert on` in each group where you want to receive tag alerts.",
        parse_mode=ParseMode.HTML
    )


# Handler registration


__mod_name__ = "Tag Alert"
__help__ = True
