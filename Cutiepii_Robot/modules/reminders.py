"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, [ https://github.com/Awesome-RJ ]
Copyright (c) 2021-2022, Yūki • Black Knights Union, [ https://github.com/Awesome-RJ/CutiepiiRobot ]

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
import io
import re
import time

from Cutiepii_Robot import SUDO_USERS, CUTIEPII_PTB
from Cutiepii_Robot.modules.helper_funcs.anonymous import user_admin
from Cutiepii_Robot.modules.helper_funcs.string_handling import (
    extract_time_seconds,
    markdown_to_html,
)
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.ping import get_readable_time
from Cutiepii_Robot.modules.sql import remind_sql as sql
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
)
from telegram.helpers import mention_html

html_tags = re.compile("<.*?>")

REMINDER_LIMIT = 20


@user_admin
@loggable
async def remind(update: Update, context: CallbackContext) -> None:
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
        await msg.reply_text(
            f"You can set {REMINDER_LIMIT} reminders in a chat.")
        return

    sql.set_remind(chat.id, t, text[:512], user.id)

    confirmation = f"Noted! I'll remind you after {args[1]}.\nThis reminder's timestamp is <code>{t}</code>."
    if len(text) > 512:
        confirmation += "\n<b>Note</b>: Reminder was over 512 characters and was truncated."

    await msg.reply_text(confirmation, parse_mode=ParseMode.HTML)

    return (f"<b>{chat.title}:</b>\n"
            f"#REMINDER\n"
            f"<b>Admin</b>: {mention_html(user.id, user.first_name)}\n"
            f"<b>Time left</b>: {duration}\n"
            "<b>Message</b>: {}{}".format(re.sub(html_tags, "", text[:20]),
                                          "...." if len(text) > 20 else ""))


@user_admin
async def reminders(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message
    chat.title = "your private chat" if chat.type == "private" else chat.title
    reminders = sql.get_reminds_in_chat(chat.id)
    if len(reminders) < 1:
        return await msg.reply_text(
            f"There are no reminders in {chat.title} yet.")
    text = f"Reminders in {chat.title} are:\n"
    for reminder in reminders:
        user = await context.bot.get_chat(reminder.user_id)
        text += (
            "\n➛ {}\n  <b>By</b>: {}\n  <b>Time left</b>: {}\n  <b>Time stamp</b>: <code>{}</code>"
        ).format(
            reminder.remind_message,
            f"@{user.username}" if user.username else mention_html(
                user.id, user.first_name),
            get_readable_time(reminder.time_seconds - round(time.time())),
            reminder.time_seconds,
        )

    text += "\n\n<b>Note</b>: You can clear a particular reminder with its time stamp."
    if len(text) > 4096:
        text = re.sub(html_tags, "", text)
        with io.BytesIO(str.encode(text)) as file:
            file.name = f"reminders_{chat.id}.txt"
            await CUTIEPII_PTB.bot.send_document(
                chat_id=update.effective_chat.id,
                document=file,
                caption="Click to get the list of all reminders in this chat.",
                reply_to_message_id=msg.message_id)
        return
    await msg.reply_text(text, parse_mode=ParseMode.HTML)


@user_admin
@loggable
async def clearreminder(update: Update, context: CallbackContext) -> None:
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

        sql.rem_remind(chat.id, timestamp, remind.remind_message,
                       remind.user_id)
        await msg.reply_text("I've deleted this reminder.")
        user = update.effective_user
        return (f"<b>{chat.title}:</b>\n"
                f"#REMINDER_DELETED\n"
                f"<b>Admin</b>: {mention_html(user.id, user.first_name)}\n"
                f"<b>Reminder by</b>: <code>{remind.user_id}</code>\n"
                f"<b>Time stamp</b>: <code>{timestamp}</code>\n"
                "<b>Message</b>: {}{}".format(
                    re.sub(html_tags, "", remind.remind_message[:20]),
                    "...." if len(remind.remind_message) > 20 else ""))
    await msg.reply_text(
        "You need to provide me the timestamp of the reminder.\n<b>Note</b>: You can see timestamps via /reminders command.",
        parse_mode=ParseMode.HTML)
    return


@user_admin
async def clearallreminders(update: Update, context: CallbackContext) -> None:
    member = await update.effective_chat.get_member(update.effective_user.id)
    if update.effective_chat.type != "private" and member.status != "creator" and member.user.id not in SUDO_USERS:
        return await update.effective_message.reply_text(
            "Only group owner can do this!")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Are you sure you want to delete all reminders?",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(text="Yes", callback_data="clearremind_yes"),
            InlineKeyboardButton(text="No", callback_data="clearremind_no"),
        ]]),
    )


@user_admin
@loggable
async def clearallremindersbtn(update: Update,
                               context: CallbackContext) -> None:
    query = update.callback_query
    chat = update.effective_chat
    option = query.data.split("_")[1]
    member = chat.get_member(update.effective_user.id)
    if update.effective_chat.type != "private" and member.status != "creator" and member.user.id not in SUDO_USERS:
        return await query.answer("Only group owner can do this!")
    if option == "no":
        await query.message.edit_text("No reminders were deleted!")
    elif option == "yes":
        reminders = sql.get_reminds_in_chat(chat.id)
        for r in reminders:
            try:
                sql.rem_remind(r.chat_id, r.time_seconds, r.remind_message,
                               r.user_id)
            except:
                pass
        await query.message.edit_text("I have deleted all reminders.")
    await context.bot.answer_callback_query(query.id)
    return (f"<b>{chat.title}:</b>\n"
            f"#ALL_REMINDERS_DELETED")


async def check_reminds(update: Update, context: CallbackContext) -> None:
    while True:
        t = round(time.time())
        if t in sql.REMINDERS:
            r = sql.REMINDERS[t]
            for a in r:
                try:
                    user = await CUTIEPII_PTB.bot.get_chat(a["user_id"])
                    text = f"""{mention_html(user.id, user.first_name)}'s reminder:\n{markdown_to_html(a["message"])}"""

                    await context.bot.send_message(a["chat_id"],
                                                   text,
                                                   parse_mode=ParseMode.HTML)
                    sql.rem_remind(a["chat_id"], t, a["message"], a["user_id"])
                except:
                    continue
        await asyncio.sleep(1)


"""
#starts the reminder
asyncio.get_event_loop().create_task(check_reminds())
"""

__mod_name__ = "Reminders"

__help__ = """
This module lets you setup upto 20 reminders per group/pm.
The usage is as follows

*Commands*:
➛ /remind <time> <text>*:* Sets a reminder for given time, usage is same like a mute command
➛ /reminders*:* Lists all the reminders for current chat
➛ /clearreminder <timestampID>*:* Removes the reminder of the given timestamp ID from the list
➛ /clearallreminders*:* Cleans all saved reminders (owner only)

*TimestampID:* An ID number listed under each reminder, used to remove a reminder
*Time:* 1d or 1h or 1m or 30s

*Notes:*
 • You can only supply one time variable, be it day(s), hour(s), minute(s) or seconds
 • The shortest reminder can be 30 seconds
 • Reminders are limited to 512 chracters per reminder
 • Only group admins can setup reminders

*Example:*
`/remind 2h You need to sleep!`
This will print a reminder with the text after 2 hours

`/clearreminder 1631378953`
Removes the reminder of the said timestamp ID
"""

CUTIEPII_PTB.add_handler(CommandHandler(["remind", "reminder"], remind))
CUTIEPII_PTB.add_handler(CommandHandler(["reminds", "reminders"], reminders))
CUTIEPII_PTB.add_handler(CommandHandler("clearreminder", clearreminder))
CUTIEPII_PTB.add_handler(CommandHandler("clearallreminders",
                                        clearallreminders))
CUTIEPII_PTB.add_handler(
    CallbackQueryHandler(clearallremindersbtn, pattern=r"clearremind_"))
