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
from telethon import events
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import mention_html

from Cutiepii_Robot import telethn, dispatcher, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd

# In-memory dictionary to store user status updates
USER_STATUS_STORE = {}


@telethn.on(events.UserUpdate)
async def on_user_update(event):
    user_id = event.user_id
    now = datetime.datetime.now()
    
    status_type = "Offline"
    activity = None

    if event.online:
        status_type = "Online"
    elif event.typing:
        status_type = "Typing"
        activity = "choosing to type a message"
    elif event.recording:
        status_type = "Recording"
        activity = "recording a voice or video note"
    elif event.uploading:
        status_type = "Uploading"
        activity = "uploading a file"
    elif event.choosing:
        status_type = "Choosing"
        activity = "choosing media to send"
    elif event.last_seen:
        status_type = "Recently"
        
    USER_STATUS_STORE[user_id] = {
        "status": status_type,
        "timestamp": now,
        "activity": activity,
        "last_seen": event.last_seen
    }


@cutiepii_cmd(command="statuscheck", can_disable=False)
async def status_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args

    target_user = user
    if args:
        target_str = args[0]
        if target_str.startswith("@"):
            username = target_str[1:]
            try:
                entity = await telethn.get_entity(username)
                target_user = entity
            except Exception:
                await message.reply_text("Could not find the specified user.")
                return
        else:
            try:
                user_id = int(target_str)
                entity = await telethn.get_entity(user_id)
                target_user = entity
            except Exception:
                await message.reply_text("Could not find the specified user.")
                return
    elif message.reply_to_message:
        target_user = message.reply_to_message.from_user

    data = USER_STATUS_STORE.get(target_user.id)
    
    reply = (
        f"👤 <b>USER STATUS TRACKING</b> 👤\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"❍ <b>User:</b> {mention_html(target_user.id, target_user.first_name)}\n"
        f"❍ <b>ID:</b> <code>{target_user.id}</code>\n"
    )

    if data:
        status = data["status"]
        time_str = data["timestamp"].strftime("%H:%M:%S")
        reply += f"❍ <b>Current Presence:</b> <code>{status}</code> (at {time_str})\n"
        if data["activity"]:
            reply += f"❍ <b>Activity:</b> <code>{data['activity']}</code>\n"
    else:
        reply += "❍ <b>Current Presence:</b> <code>Offline/Recently</code>\n"
        
    reply += (
        f"\n⚙️ <i>Privacy-aware monitoring: respects 'Hide Status' user privacy configurations.</i>"
    )
    await message.reply_text(reply, parse_mode=ParseMode.HTML)


__help__ = True

__mod_name__ = "Status Tracking"
