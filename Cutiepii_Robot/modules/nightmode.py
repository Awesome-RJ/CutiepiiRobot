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
import datetime
import pytz
import re
from apscheduler.schedulers.asyncio import AsyncIOScheduler 
from telegram import Update, ChatPermissions
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Cutiepii_Robot import OWNER_ID, dispatcher, LOGGER, REDIS
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
)


async def close_chat(chat_id: int):
    try:
        await dispatcher.bot.send_message(
            chat_id, "<b>Night Mode Activated</b>\n\nThis group is now read-only to prevent night spam. Sleep well!", parse_mode=ParseMode.HTML
        )
        await dispatcher.bot.set_chat_permissions(
            chat_id, ChatPermissions(can_send_messages=False)
        )
        LOGGER.info(f"[NIGHTMODE]: Closed chat {chat_id}")
    except Exception as e:
        LOGGER.error(f"[NIGHTMODE ERROR]: Failed to close chat {chat_id}: {e}")


async def open_chat(chat_id: int):
    try:
        await dispatcher.bot.send_message(
            chat_id, "<b>Good Morning</b>\n\nNight Mode has ended. You can now chat normally.", parse_mode=ParseMode.HTML
        )
        await dispatcher.bot.set_chat_permissions(
            chat_id, ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        LOGGER.info(f"[NIGHTMODE]: Opened chat {chat_id}")
    except Exception as e:
        LOGGER.error(f"[NIGHTMODE ERROR]: Failed to open chat {chat_id}: {e}")


@cutiepii_cmd(command="nightmode", filters=None, can_disable=False)
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
async def nightmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if chat.type == "private":
        await message.reply_text("<b>Action Denied</b>\nThis command can only be used in group chats.", parse_mode=ParseMode.HTML)
        return

    if not args:
        status = REDIS.get(f"nightmode_active:{chat.id}")
        status = status.decode("utf-8") if status else "false"
        hours = REDIS.get(f"nightmode_hours:{chat.id}")
        hours = hours.decode("utf-8") if hours else "23:00 07:00"

        if status == "true":
            await message.reply_text(
                f"<b>Night Mode Status</b>\nNight Mode is currently <b>Enabled</b>.\nStrict Night Hours: <code>{hours}</code> (Asia/Kolkata timezone).",
                parse_mode=ParseMode.HTML
            )
        else:
            await message.reply_text("<b>Night Mode Status</b>\nNight Mode is currently <b>Disabled</b> for this chat.", parse_mode=ParseMode.HTML)
        return

    action = args[0].lower().strip()
    if action == "off":
        REDIS.set(f"nightmode_active:{chat.id}", "false")
        await message.reply_text("<b>Night Mode Updated</b>\nNight Mode has been disabled for this chat.", parse_mode=ParseMode.HTML)
        await open_chat(chat.id)
        
        # Log to log channel
        import Cutiepii_Robot.modules.sql.log_channel_sql as log_sql
        log_channel = log_sql.get_chat_log_channel(chat.id)
        if log_channel:
            admin_user = update.effective_user
            admin_mention = f"<a href='tg://user?id={admin_user.id}'>{html.escape(admin_user.first_name)}</a>"
            log_txt = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#NIGHTMODE\n"
                f"<b>Admin:</b> {admin_mention}\n"
                f"<b>Status:</b> Disabled"
            )
            try:
                await context.bot.send_message(log_channel, log_txt, parse_mode=ParseMode.HTML)
            except Exception as e:
                LOGGER.error(f"Failed to send nightmode off log: {e}")
        return

    if len(args) < 2:
        # Compatibility with legacy `/nightmode on` (defaults to 23:59 to 06:00)
        if action == "on":
            close_time = "23:59"
            open_time = "05:58"
        else:
            await message.reply_text(
                "<b>Usage</b>\n"
                "- <code>/nightmode [HH:MM] [HH:MM]</code>: Set night mode hours (e.g. <code>23:00 07:00</code>)\n"
                "- <code>/nightmode off</code>: Disable night mode",
                parse_mode=ParseMode.HTML
            )
            return
    else:
        close_time = args[0].strip()
        open_time = args[1].strip()

    time_pattern = re.compile(r"^\d{2}:\d{2}$")
    if not time_pattern.match(close_time) or not time_pattern.match(open_time):
        await message.reply_text("<b>Invalid Format</b>\nInvalid time format. Please use 24-hour format: <code>HH:MM</code> (e.g., <code>23:00 07:00</code>).", parse_mode=ParseMode.HTML)
        return

    REDIS.set(f"nightmode_active:{chat.id}", "true")
    REDIS.set(f"nightmode_hours:{chat.id}", f"{close_time} {open_time}")

    await message.reply_text(
        f"<b>Night Mode Configured</b>\n\n"
        f"Status: <b>Enabled</b>\n"
        f"Close Time: <code>{close_time}</code> (Asia/Kolkata timezone)\n"
        f"Open Time: <code>{open_time}</code> (Asia/Kolkata timezone)\n\n"
        f"The chat will automatically become read-only during these hours.",
        parse_mode=ParseMode.HTML
    )

    # Log to log channel
    import Cutiepii_Robot.modules.sql.log_channel_sql as log_sql
    log_channel = log_sql.get_chat_log_channel(chat.id)
    if log_channel:
        admin_user = update.effective_user
        admin_mention = f"<a href='tg://user?id={admin_user.id}'>{html.escape(admin_user.first_name)}</a>"
        log_txt = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#NIGHTMODE\n"
            f"<b>Admin:</b> {admin_mention}\n"
            f"<b>Status:</b> Enabled ({close_time} to {open_time})"
        )
        try:
            await context.bot.send_message(log_channel, log_txt, parse_mode=ParseMode.HTML)
        except Exception as e:
            LOGGER.error(f"Failed to send nightmode on log: {e}")


async def check_nightmode_jobs():
    tz = pytz.timezone("Asia/Kolkata")
    now = datetime.datetime.now(tz)
    current_time_str = now.strftime("%H:%M")

    # Retrieve all active chats from Redis keys
    keys = REDIS.keys("nightmode_active:*")
    for key in keys:
        key_str = key.decode("utf-8")
        chat_id_str = key_str.split(":")[-1]
        
        status = REDIS.get(key_str)
        if status and status.decode("utf-8") == "true":
            hours = REDIS.get(f"nightmode_hours:{chat_id_str}")
            if hours:
                hours_str = hours.decode("utf-8")
                try:
                    close_time, open_time = hours_str.split()
                    if current_time_str == close_time:
                        await close_chat(int(chat_id_str))
                    elif current_time_str == open_time:
                        await open_chat(int(chat_id_str))
                except Exception as e:
                    LOGGER.error(f"Error checking nightmode for {chat_id_str}: {e}")


scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
scheduler.add_job(check_nightmode_jobs, trigger="cron", second=0)


def start_nightmode_scheduler():
    """Start the nightmode scheduler. Call this after the event loop is running."""
    try:
        if not scheduler.running:
            scheduler.start()
            LOGGER.info("[NIGHTMODE]: ✅ Scheduler started successfully")
    except Exception as e:
        LOGGER.error(f"[NIGHTMODE]: ❌ Failed to start scheduler: {e}")


__help__ = True

__mod_name__ = "NightMode"
