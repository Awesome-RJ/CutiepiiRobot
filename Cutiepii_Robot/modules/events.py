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
import random
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, filters
from telegram.constants import ParseMode
from telegram.helpers import mention_html

from Cutiepii_Robot import dispatcher, LOGGER, DEV_USERS, SUDO_USERS
from Cutiepii_Robot.modules.sql import events_sql as sql
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd


@cutiepii_cmd(command="eventcreate", filters=filters.User(DEV_USERS + SUDO_USERS))
async def event_create(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args

    if not args:
        await message.reply_text("Usage: `/eventcreate [event_key]`")
        return

    event_key = args[0].lower().strip()
    sql.create_event(event_key, user.id)
    
    reply = (
        f"🎪 <b>NEW EVENT CREATED!</b> 🎪\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 <b>Event Key:</b> <code>{html.escape(event_key)}</code>\n"
        f"👮 <b>Organizer:</b> {mention_html(user.id, user.first_name)}\n\n"
        f"To join this event, users can send: `/join {html.escape(event_key)}`"
    )
    await message.reply_text(reply, parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="eventend", filters=filters.User(DEV_USERS + SUDO_USERS))
async def event_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("Usage: `/eventend [event_key]`")
        return

    event_key = args[0].lower().strip()
    participants = sql.get_event_participants(event_key)

    if not sql.end_event(event_key):
        await message.reply_text("This event was not found or is already finished.")
        return

    reply = (
        f"🏁 <b>EVENT CONCLUDED!</b> 🏁\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 <b>Event Key:</b> <code>{html.escape(event_key)}</code>\n"
        f"👥 <b>Total Participants:</b> <code>{len(participants)}</code>\n\n"
    )

    if participants:
        # Choose a random winner as a reward mechanism
        winner_entry = random.choice(participants)
        try:
            winner_user = await context.bot.get_chat(winner_entry.user_id)
            winner_mention = mention_html(winner_user.id, winner_user.first_name)
        except Exception:
            winner_mention = f"User (ID: <code>{winner_entry.user_id}</code>)"

        reply += (
            f"🎁 <b>Lucky Winner:</b> {winner_mention}\n\n"
            f"<i>Rewards have been distributed to the participants! Thank you all for joining!</i>"
        )
    else:
        reply += "No participants joined this event."

    await message.reply_text(reply, parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="join", can_disable=False)
async def event_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args

    if not args:
        active_events = sql.get_active_events()
        if active_events:
            reply = "🎪 <b>Active Events:</b>\n\n"
            for e in active_events:
                reply += f"❍ <code>{html.escape(e.event_key)}</code> (Created by ID: {e.creator_id})\n"
            reply += "\nUse `/join [event_key]` to join one!"
        else:
            reply = "There are no active events at the moment."
        await message.reply_text(reply, parse_mode=ParseMode.HTML)
        return

    event_key = args[0].lower().strip()
    success, msg = sql.join_event(event_key, user.id)

    if success:
        await message.reply_text(f"✅ Success! You have joined the event <code>{html.escape(event_key)}</code>.", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(f"❌ Failed to join: {msg}")


@cutiepii_cmd(command="events", can_disable=False)
async def events_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    active = sql.get_active_events()
    recent = sql.get_recent_history()

    reply = "🎪 <b>EVENTS & COMPETITIONS</b> 🎪\n"
    reply += "━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    reply += "🟢 <b>Active Events:</b>\n"
    if active:
        for e in active:
            reply += f"❍ <code>{html.escape(e.event_key)}</code>\n"
    else:
        reply += "❍ No active events.\n"

    reply += "\n📜 <b>Recent History (Ended):</b>\n"
    if recent:
        for r in recent:
            reply += f"❍ <code>{html.escape(r.event_key)}</code> (Ended)\n"
    else:
        reply += "❍ No recent event history."

    await message.reply_text(reply, parse_mode=ParseMode.HTML)




__mod_name__ = "Events"
__help__ = True

__handlers__ = [
]
