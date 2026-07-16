"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.
"""

import html
import random
import re
from datetime import datetime, timezone

import humanize
from telegram import MessageEntity, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes, filters

from Cutiepii_Robot import dispatcher, REDIS, LOGGER
from Cutiepii_Robot.modules.sql import afk_sql as sql
from Cutiepii_Robot.modules.sql.clear_cmd_sql import get_clearcmd
from Cutiepii_Robot.modules.helper_funcs.misc import delete
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot.modules.users import get_user_id
from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    AdminPerms,
)

# ========================================
# Random Messages Lists
# ========================================

random_afk_message = [
    "is now Away From Keyboard!",
    "has gone offline.",
    "is away.",
    "is busy right now."
]

random_afk_reply_message = [
    "is currently offline",
    "is away from keyboard",
    "is not available right now",
    "is busy"
]

random_back_online_message = [
    "Welcome back!",
    "Glad to see you again!",
    "Hope you had a good time!"
]

# ========================================
# Helper Functions
# ========================================

def parse_afk_reason(reason_str: str):
    """Parse media ID and actual reason from database reason string."""
    if not reason_str:
        return None, ""
    match = re.match(r"^\[media:(?P<media_id>[^\]]+)\](?P<reason>.*)", reason_str, re.DOTALL)
    if match:
        return match.group("media_id"), match.group("reason")
    return None, reason_str

def make_afk_reason(media_id: str, reason: str) -> str:
    """Format media ID and actual reason to store in database."""
    if media_id:
        return f"[media:{media_id}]{reason or ''}"
    return reason or ""

# ========================================
# Command Handlers
# ========================================

@cutiepii_msg(filters.Regex("(?i)^off") | filters.Regex("(?i)^brb"), friendly="afk", group=3)
@cutiepii_cmd(command=["afk", "brb"], group=3)
async def afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not user:  # ignore channels
        return

    if user.id in [777000, 1087968824, 13681768]:
        return

    # Check if user is already AFK
    afk_status = sql.check_afk_status(user.id)
    if afk_status:
        elapsed = datetime.now(timezone.utc) - afk_status.time.replace(tzinfo=timezone.utc)
        elapsed_str = humanize.naturaldelta(elapsed)
        random_msg = random.choice(random_back_online_message)

        reply_msgs = [
            f"{user.first_name} is now back online!",
            f"{user.first_name} has returned. AFK duration: {elapsed_str}.",
            f"Welcome back, {user.first_name}. {random_msg}.\nYou were AFK for {elapsed_str}."
        ]

        r = random.choice(reply_msgs)
        sql.remove_afk(user.id)
        delmsg = await msg.reply_text(r, parse_mode=ParseMode.MARKDOWN)
        
        cleartime = get_clearcmd(chat.id, "afk")
        if cleartime:
            context.application.create_task(delete(delmsg, cleartime.time))
        elif sql.is_afk_delete(chat.id):
            context.application.create_task(delete(delmsg, 11))
        return

    # Extract media attachments if they reply to media
    media_id = None
    if msg.reply_to_message:
        reply = msg.reply_to_message
        if reply.video:
            media_id = reply.video.file_id
        elif reply.photo:
            media_id = reply.photo[-1].file_id
        elif reply.animation:
            media_id = reply.animation.file_id
        elif reply.audio:
            media_id = reply.audio.file_id
        elif reply.voice:
            media_id = reply.voice.file_id
        elif reply.document:
            media_id = reply.document.file_id
        elif reply.video_note:
            media_id = reply.video_note.file_id

    # Extract reason
    afk_reason = None
    args = msg.text.split(None, 1)
    if len(args) > 1:
        afk_reason = args[1]
        if len(afk_reason) > 100:
            afk_reason = afk_reason[:100]

    db_reason = make_afk_reason(media_id, afk_reason)
    sql.set_afk(user.id, db_reason)
    fname = user.first_name

    random_msg = random.choice(random_afk_message)
    afk_message = f"{fname} is now Away From Keyboard!\n{random_msg}"
    if afk_reason:
        afk_message += f"\n<b>Reason:</b> {html.escape(afk_reason)}"

    try:
        delmsg = await msg.reply_text(afk_message, parse_mode=ParseMode.HTML)
        cleartime = get_clearcmd(chat.id, "afk")
        if cleartime:
            context.application.create_task(delete(delmsg, cleartime.time))
        elif sql.is_afk_delete(chat.id):
            context.application.create_task(delete(delmsg, 11))
    except BadRequest:
        pass


@cutiepii_msg(filters.ALL & ~filters.COMMAND, friendly="afk", group=7)
async def no_longer_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.effective_message
    chat = update.effective_chat

    if not user or not msg:
        return

    # Don't auto-clear if this message is trying to set AFK
    if msg.text:
        text_lower = msg.text.lower()
        if text_lower.startswith("/afk") or text_lower.startswith("/brb") or text_lower.startswith("off") or text_lower.startswith("brb"):
            return

    afk_status = sql.check_afk_status(user.id)
    if not afk_status:
        return

    res = sql.remove_afk(user.id)
    if res:
        if msg.new_chat_members:
            return
        elapsed = datetime.now(timezone.utc) - afk_status.time.replace(tzinfo=timezone.utc)
        time_away = humanize.naturaldelta(elapsed)
        random_msg = random.choice(random_back_online_message)

        reply_msgs = [
            f"{user.first_name} is now back online!",
            f"{user.first_name} has returned. **AFK duration**: {time_away}.",
            f"Welcome back, {user.first_name}. {random_msg}.\nYou were **AFK for {time_away}**."
        ]

        r = random.choice(reply_msgs)
        try:
            delmsg = await msg.reply_text(r, parse_mode=ParseMode.MARKDOWN)
            cleartime = get_clearcmd(chat.id, "afk")
            if cleartime:
                context.application.create_task(delete(delmsg, cleartime.time))
            elif sql.is_afk_delete(chat.id):
                context.application.create_task(delete(delmsg, 11))
        except BadRequest:
            pass


@cutiepii_msg(
    (filters.Entity(MessageEntity.MENTION) | filters.Entity(MessageEntity.TEXT_MENTION) & filters.ChatType.GROUPS),
    friendly='afk', group=8
)
async def reply_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    message = update.effective_message
    userc = update.effective_user
    if not userc or not message:
        return
    userc_id = userc.id

    # Check replies
    if message.reply_to_message:
        target = message.reply_to_message.from_user
        if target and target.id != userc_id:
            afk_status = sql.check_afk_status(target.id)
            if afk_status:
                await send_afk_info(message, target.first_name, afk_status)

    # Check mentions
    if message.entities:
        entities = message.parse_entities([MessageEntity.TEXT_MENTION, MessageEntity.MENTION])
        chk_users = []
        for ent, text in entities.items():
            user_id = None
            fst_name = ""
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name
            elif ent.type == MessageEntity.MENTION:
                user_id = await get_user_id(text)
                if user_id:
                    try:
                        target_chat = await bot.get_chat(user_id)
                        fst_name = target_chat.first_name
                    except Exception:
                        fst_name = text[1:]

            if user_id and user_id != userc_id and user_id not in chk_users:
                chk_users.append(user_id)
                afk_status = sql.check_afk_status(user_id)
                if afk_status:
                    await send_afk_info(message, fst_name, afk_status)


async def send_afk_info(msg, first_name: str, afk_status):
    """Format and send the AFK notification to the chat, displaying media if present."""
    elapsed = datetime.now(timezone.utc) - afk_status.time.replace(tzinfo=timezone.utc)
    elapsed_str = humanize.naturaldelta(elapsed)
    
    media_id, reason = parse_afk_reason(afk_status.reason)
    random_msg = random.choice(random_afk_reply_message)
    
    caption = f"{first_name} {random_msg}.\n<b>AFK for</b>: {elapsed_str}"
    if reason:
        caption += f"\n<b>Reason</b>: {html.escape(reason)}"
        
    chat = msg.chat
    try:
        if media_id:
            delmsg = await msg.reply_document(document=media_id, caption=caption, parse_mode=ParseMode.HTML)
        else:
            delmsg = await msg.reply_text(caption, parse_mode=ParseMode.HTML)
            
        cleartime = get_clearcmd(chat.id, "afk")
        if cleartime:
            import asyncio
            asyncio.create_task(delete(delmsg, cleartime.time))
        elif sql.is_afk_delete(chat.id):
            import asyncio
            asyncio.create_task(delete(delmsg, 11))
    except Exception:
        pass


@cutiepii_cmd(command="afkdel", group=30)
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def afk_del(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if not args:
        current = sql.is_afk_delete(chat.id)
        status = "Enabled" if current else "Disabled"
        await message.reply_text(
            f"Current AFK auto-delete status in <b>{html.escape(chat.title)}</b>: <b>{status}</b>.\n\n"
            f"To change this, use <code>/afkdel on</code> or <code>/afkdel off</code>.",
            parse_mode=ParseMode.HTML
        )
        return

    val = args[0].lower()
    if val in ["on", "yes", "enable", "true"]:
        sql.set_afk_delete(chat.id, True)
        await message.reply_text(f"Auto-deletion of AFK messages has been <b>enabled</b> in {html.escape(chat.title)}.", parse_mode=ParseMode.HTML)
    elif val in ["off", "no", "disable", "false"]:
        sql.set_afk_delete(chat.id, False)
        await message.reply_text(f"Auto-deletion of AFK messages has been <b>disabled</b> in {html.escape(chat.title)}.", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("Invalid argument. Use `/afkdel on` or `/afkdel off`.")


def __gdpr__(user_id):
    sql.rm_afk(user_id)


def __stats__():
    return f"- {len(REDIS.keys())} Total Keys in Redis Database."


__help__ = True

__mod_name__ = "AFK"