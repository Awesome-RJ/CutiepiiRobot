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

import asyncio
import html
import io
import re
import time


from Cutiepii_Robot import SUDO_USERS, dispatcher

from Cutiepii_Robot.modules.helper_funcs.string_handling import (
    extract_time_seconds, markdown_to_html,
)
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.helper_funcs.readable_time import get_readable_time
from Cutiepii_Robot.modules.sql import remind_sql as sql
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    get_bot_member,
    bot_is_admin,
    user_is_admin,
    user_not_admin_check,
    update_admins_cache,
    ADMINS_CACHE, BOT_ADMIN_CACHE,
)
from telegram import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes, CallbackQueryHandler,
    CommandHandler,
)
from telegram.helpers import mention_html

html_tags = re.compile("<.*?>")

REMINDER_LIMIT = int(20)

@cutiepii_cmd(command=["remind", "reminder"], can_disable=False, rate_limit_calls=5, rate_limit_window=60, add_error_handler=True)
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = msg.text.split(None, 2)

    if len(args) != 3:
        await msg.reply_text(
            "Incorrect format\nFormat: `/remind 20m message here`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    duration, text = args[1:]

    when = extract_time_seconds(msg, duration)
    if not when or when == "":
        return
    if int(when) > 63072000:
        await msg.reply_text("Max remind time is limtied to 2 years!")
        return
    if int(when) < 30:
        await msg.reply_text("Your reminder needs to be more than 30 seconds!")
        return

    t = (round(time.time()) + when)
    chat_limit = sql.num_reminds_in_chat(chat.id)
    if chat_limit >= REMINDER_LIMIT:
        await msg.reply_text(f"You can set {REMINDER_LIMIT} reminders in a chat.")
        return

    sql.set_remind(chat.id, t, text[:512], user.id)

    confirmation = f"Noted! I'll remind you after {args[1]}.\nThis reminder's timestamp is <code>{t}</code>."
    if len(text) > 512:
        confirmation += "\n<b>Note</b>: Reminder was over 512 characters and was truncated."

    await msg.reply_text(confirmation, parse_mode=ParseMode.HTML)

    return (
        f"<b>{chat.title}:</b>\n"
        f"#REMINDER\n"
        f"<b>Admin</b>: {mention_html(user.id, user.first_name)}\n"
        f"<b>Time left</b>: {duration}\n"
        "<b>Message</b>: {}{}".format(re.sub(html_tags, "", text[:20]), "...." if len(text) > 20 else "")
    )


@cutiepii_cmd(command=["reminds", "reminders"], can_disable=False, rate_limit_calls=30, rate_limit_window=60, add_error_handler=True)
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
async def reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message
    chat.title = "your private chat" if chat.type == "private" else chat.title
    reminders = sql.get_reminds_in_chat(chat.id)
    if len(reminders) < 1:
        return await msg.reply_text(f"There are no reminders in {chat.title} yet.")
    text = f"Reminders in {chat.title} are:\n"
    for reminder in reminders:
        try:
            user = await context.bot.get_chat(reminder.user_id)
            user_mention = mention_html(user.id, user.first_name) if not user.username else "@"+user.username
        except Exception:
            user_mention = f"User (<code>{reminder.user_id}</code>)"
        text += ("\n- {}\n  <b>By</b>: {}\n  <b>Time left</b>: {}\n  <b>Time stamp</b>: <code>{}</code>").format(reminder.remind_message, user_mention, get_readable_time(reminder.time_seconds-round(time.time())), reminder.time_seconds)
    text += "\n\n<b>Note</b>: You can clear a particular reminder with its time stamp."
    if len(text) > 4096:
        text = re.sub(html_tags, "", text)
        with io.BytesIO(str.encode(text)) as file:
            file.name = f"reminders_{chat.id}.txt"
            await context.bot.send_document(chat_id=update.effective_chat.id, document=file, caption="Click to get the list of all reminders in this chat.", reply_to_message_id=msg.message_id)
        return
    await msg.reply_text(text, parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="clearreminder", can_disable=False, rate_limit_calls=10, rate_limit_window=60, add_error_handler=True)
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
async def clearreminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    args = context.args
    if len(args) >= 1:
        timestamp = args[0]
        try:
            timestamp = int(timestamp)
        except:
            timestamp = 0

        remind = sql.get_remind_in_chat(chat.id, timestamp)
        if not remind:
            await msg.reply_text("This time stamp doesn't seem to be valid.")
            return

        sql.rem_remind(chat.id, timestamp, remind.remind_message, remind.user_id)
        await msg.reply_text("I've deleted this reminder.")
        user = update.effective_user
        return (
            f"<b>{chat.title}:</b>\n"
            f"#REMINDER_DELETED\n"
            f"<b>Admin</b>: {mention_html(user.id, user.first_name)}\n"
            f"<b>Reminder by</b>: <code>{remind.user_id}</code>\n"
            f"<b>Time stamp</b>: <code>{timestamp}</code>\n"
            "<b>Message</b>: {}{}".format(re.sub(html_tags, "", remind.remind_message[:20]), "...." if len(remind.remind_message) > 20 else "")
        )
    else:
        await msg.reply_text("You need to provide me the timestamp of the reminder.\n<b>Note</b>: You can see timestamps via /reminders command.", parse_mode=ParseMode.HTML)
        return


@cutiepii_cmd(command="clearallreminders", can_disable=False, rate_limit_calls=2, rate_limit_window=300, add_error_handler=True)
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
async def clearallreminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = await update.effective_chat.get_member(update.effective_user.id)
    if update.effective_chat.type != "private" and member.status != "creator" and member.user.id not in SUDO_USERS:
        return await update.effective_message.reply_text("Only group owner can do this!")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Are you sure you want to delete all reminders?",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(text="Yes", callback_data="clearremind_yes"),
            InlineKeyboardButton(text="No", callback_data="clearremind_no"),
        ]]),
    )


@cutiepii_callback(pattern=r"clearremind_")
@loggable
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
async def clearallremindersbtn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat = update.effective_chat
    option = query.data.split("_")[1]
    member = await chat.get_member(update.effective_user.id)
    if update.effective_chat.type != "private" and member.status != "creator" and member.user.id not in SUDO_USERS:
        return await query.answer("Only group owner can do this!")
    if option == "no":
        await query.message.edit_text("No reminders were deleted!")
    elif option == "yes":
        reminders = sql.get_reminds_in_chat(chat.id)
        for r in reminders:
            try:
                sql.rem_remind(r.chat_id, r.time_seconds, r.remind_message, r.user_id)
            except:
                pass
        await query.message.edit_text("I have deleted all reminders.")
    await context.bot.answer_callback_query(query.id)
    return (
            f"<b>{chat.title}:</b>\n"
            f"#ALL_REMINDERS_DELETED"
    )


async def check_reminds():
    while True:
        t = round(time.time())
        if t in sql.REMINDERS:
            r = sql.REMINDERS[t]
            for a in r:
                try:
                    try:
                        user = await dispatcher.bot.get_chat(a["user_id"])
                        user_mention = mention_html(user.id, user.first_name) if not user.username else "@" + user.username
                    except Exception:
                        user_mention = f"User (<code>{a['user_id']}</code>)"
                    
                    text = "{}'s reminder:\n{}".format(user_mention, markdown_to_html(a["message"]))
                    await dispatcher.bot.send_message(a["chat_id"], text, parse_mode=ParseMode.HTML)
                    sql.rem_remind(a["chat_id"], t, a["message"], a["user_id"])
                except Exception as e:
                    LOGGER.warning(f"Failed to process reminder: {e}")
                    continue
        await asyncio.sleep(1)

#starts the reminder
try:
    loop = asyncio.get_running_loop()
    loop.create_task(check_reminds())
except RuntimeError:
    try:
        asyncio.get_event_loop().create_task(check_reminds())
    except Exception as e:
        LOGGER.warning(f"Could not start reminders loop: {e}")


__mod_name__ = "Reminders"

__help__ = True
