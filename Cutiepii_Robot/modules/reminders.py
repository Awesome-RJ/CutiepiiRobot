"""
MIT License

Copyright (C) 2021 @notRyuk

This file is part of @Cutiepii_Robot (Telegram Bot)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import re
import time

from telegram import Update
from telegram.ext import CommandHandler, run_async
from telegram.ext.callbackcontext import CallbackContext
from telegram.ext.filters import Filters
from telegram.parsemode import ParseMode

from Cutiepii_Robot import OWNER_ID, updater, dispatcher
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler


job_queue = updater.job_queue


def get_time(time: str) -> int:
    if time[-1] == "s":
        return int(time[:-1])
    if time[-1] == "m":
        return int(time[:-1])*60
    if time[-1] == "h":
        return int(time[:-1])*3600
    if time[-1] == "d":
        return int(time[:-1])*86400



reminder_message = """
Your reminder:
{reason}
<i>Which you timed {time} before in {title}</i>
"""

def reminders(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    jobs = list(job_queue.jobs())
    user_reminders = []
    for job in jobs:
        if job.name.endswith(str(user.id)):
            user_reminders.append(job.name[1:])
    if len(user_reminders) == 0:
        msg.reply_text(
            text = "You don't have any reminders set or all the reminders you have set have been completed",
            reply_to_message_id = msg.message_id
        )
        return
    reply_text = "Your reminders (<i>Mentioned below are the <b>Timstamps</b> of the reminders you have set</i>):\n"
    for i, u in enumerate(user_reminders):
        reply_text += f"\n{i+1}. <code>{u}</code>"
    msg.reply_text(
        text = reply_text,
        reply_to_message_id = msg.message_id,
        parse_mode = ParseMode.HTML
    )


def set_reminder(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    chat = update.effective_chat
    reason = msg.text.split()
    if len(reason) == 1:
        msg.reply_text(
            "No time and reminder to mention!",
            reply_to_message_id = msg.message_id
        )
        return
    if len(reason) == 2:
        msg.reply_text(
            "Nothing to reminder! Add a reminder",
            reply_to_message_id = msg.message_id
        )
        return
    t = reason[1].lower()
    if not re.match(r'[0-9]+(d|h|m|s)', t):
        msg.reply_text(
            "Use a correct format of time!",
            reply_to_message_id = msg.message_id
        )
        return
    def job(context: CallbackContext):
        title = ""
        if chat.type == "private": title += "this chat"
        if chat.type != "private": title += chat.title
        context.bot.send_message(
            chat_id = user.id,
            text = reminder_message.format(
                reason = " ".join(reason[2:]),
                time = t,
                title = title
            ),
            disable_notification = False,
            parse_mode = ParseMode.HTML
        )
    job_time = time.time()
    job_queue.run_once(
        callback = job, 
        when = get_time(t), 
        name = f"t{job_time}{user.id}".replace(".", "")
    )
    msg.reply_text(
        text = "Your reminder has been set after {time} from now!\nTimestamp: <code>{time_stamp}</code>".format(
            time = t,
            time_stamp = str(job_time).replace(".", "") + str(user.id)
        ), 
        reply_to_message_id = msg.message_id,
        parse_mode = ParseMode.HTML
    )
    
def clear_reminder(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    text = msg.text.split()
    if len(text) == 1 or not re.match(r'[0-9]+', text[1]):
        msg.reply_text(
            text = "No/Wrong timestamp mentioned",
            reply_to_message_id = msg.message_id
        )
        return
    if not text[1].endswith(str(user.id)):
        msg.reply_text(
            text = "The timestamp mentioned is not your reminder!",
            reply_to_message_id = msg.message_id
        )
        return
    jobs = list(job_queue.get_jobs_by_name("t" + text[1]))
    if len(jobs) == 0:
        msg.reply_text(
            text = "This reminder is already completed or either not set",
            reply_to_message_id = msg.message_id
        )
        return
    jobs[0].schedule_removal()
    msg.reply_text(
        text = "Done cleared the reminder!",
        reply_to_message_id = msg.message_id
    )

def clear_all_reminders(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    if user.id != OWNER_ID:
        msg.reply_text(
            text = "Who this guy not being the owner wants me clear all the reminders!!?",
            reply_to_message_id = msg.message_id
        )
        return
    jobs = list(job_queue.jobs())
    unremoved_reminders = []
    for job in jobs:
        try:
            job.schedule_removal()
        except Exception:
            unremoved_reminders.append(job.name[1:])
    reply_text = "Done cleared all the reminders!\n\n"
    if len(unremoved_reminders) > 0:
        reply_text += "Except (<i>Time stamps have been mentioned</i>):"
        for i, u in enumerate(unremoved_reminders):
            reply_text += f"\n{i+1}. <code>{u}</code>"
    msg.reply_text(
        text = reply_text,
        reply_to_message_id = msg.message_id,
        parse_mode = ParseMode.HTML
    )

def clear_all_my_reminders(update: Update, context: CallbackContext):
    user = update.effective_user
    msg = update.effective_message
    jobs = list(job_queue.jobs())
    if len(jobs) == 0:
        msg.reply_text(
            text = "You don't have any reminders!",
            reply_to_message_id = msg.message_id
        )
        return
    unremoved_reminders = []
    for job in jobs:
        if job.name.endswith(str(user.id)):
            try:
                job.schedule_removal()
            except Exception:
                unremoved_reminders.append(job.name[1:])
    reply_text = "Done cleared all your reminders!\n\n"
    if len(unremoved_reminders) > 0:
        reply_text += "Except (<i>Time stamps have been mentioned</i>):"
        for i, u in enumerate(unremoved_reminders):
            reply_text += f"\n{i+1}. <code>{u}</code>"
    msg.reply_text(
        text = reply_text,
        reply_to_message_id = msg.message_id,
        parse_mode = ParseMode.HTML
    )

__mod_name__ = "Reminders"
__help__ = """
  ➢ `/reminders`*:* get a list of *TimeStamps* of your reminders. 
  ➢ `/setreminder <time> <remind message>`*:* Set a reminder after the mentioned time.
  ➢ `/clearreminder <timestamp>`*:* clears the reminder with that timestamp if the time to remind is not yet completed.
  ➢ `/clearmyreminders`*:* clears all the reminders of the user.
  
*Owner Only:*
  ➢ `/warns <userhandle>`*:* get a user's number, and reason, of warns.
  
*Similar Commands:*
  ➢ `/reminders`, `/myreminders`
  ➢ `/clearmyreminders`, `/clearallmyreminders`
  
*Usage:*
  ➢ `/setreminder 30s reminder`*:* Here the time format is same as the time format in muting but with extra seconds(s)
  ➢ `/clearreminder 1234567890123456789`
"""

RemindersHandler = CommandHandler(['reminders', 'myreminders'], reminders, filters = Filters.chat_type.private, run_async=True)
SetReminderHandler = DisableAbleCommandHandler('setreminder', set_reminder, run_async=True)
ClearReminderHandler = DisableAbleCommandHandler('clearreminder', clear_reminder, run_async=True)
ClearAllRemindersHandler = CommandHandler(
    'clearallreminders', clear_all_reminders, filters = Filters.chat(OWNER_ID), run_async=True)
ClearALLMyRemindersHandler = CommandHandler(
    ['clearmyreminders', 'clearallmyreminders'], clear_all_my_reminders, filters = Filters.chat_type.private, run_async=True)

dispatcher.add_handler(RemindersHandler)
dispatcher.add_handler(SetReminderHandler)
dispatcher.add_handler(ClearReminderHandler)
dispatcher.add_handler(ClearAllRemindersHandler)
dispatcher.add_handler(ClearALLMyRemindersHandler)
