import re
import os
import subprocess
import sys

from contextlib import suppress
from time import sleep

import Cutiepii_Robot

from Cutiepii_Robot import dispatcher, DEV_USERS
from Cutiepii_Robot.modules.helper_funcs.chat_status import dev_plus
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram import TelegramError, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Unauthorized
from telegram.ext import CallbackContext, CommandHandler, run_async

def leave_cb(update: Update, context: CallbackContext):
    bot = context.bot
    callback = update.callback_query
    if callback.from_user.id not in DEV_USERS:
        callback.answer(text="This isn't for you", show_alert=True)
        return

    match = re.match(r"leavechat_cb_\((.+?)\)", callback.data)
    chat = int(match.group(1))
    bot.leave_chat(chat_id=chat)
    callback.answer(text="Left chat")

@dev_plus
def allow_groups(update: Update, context: CallbackContext):
    args = context.args
    if not args:
        state = "Lockdown is " + "on" if not Cutiepii_Robot.ALLOW_CHATS else "off"
        update.effective_message.reply_text(f"Current state: {state}")
        return
    if args[0].lower() in ["off", "no"]:
        Cutiepii_Robot.ALLOW_CHATS = True
    elif args[0].lower() in ["yes", "on"]:
        Cutiepii_Robot.ALLOW_CHATS = False
    else:
        update.effective_message.reply_text("Format: /lockdown Yes/No or Off/On")
        return
    update.effective_message.reply_text("Done! Lockdown value toggled.")
	
@dev_plus
def leave(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    if args:
        chat_id = str(args[0])
        leave_msg = " ".join(args[1:])
        try:
            context.bot.send_message(chat_id, leave_msg)
            bot.leave_chat(int(chat_id))
            update.effective_message.reply_text("Left chat.")
        except TelegramError:
            update.effective_message.reply_text("Failed to leave chat for some reason.")
    else:
        chat = update.effective_chat
        # user = update.effective_user
        cutiepii_leave_bt = [[
            InlineKeyboardButton(text="I am sure of this action.", callback_data="leavechat_cb_({})".format(chat.id))
        ]]
        update.effective_message.reply_text("I'm going to leave {}, press the button below to confirm".format(chat.title), reply_markup=InlineKeyboardMarkup(cutiepii_leave_bt))

	
@dev_plus
def gitpull(update: Update, context: CallbackContext):
    sent_msg = update.effective_message.reply_text(
        "Pulling all changes from remote and then attempting to restart.",
    )
    subprocess.Popen("git pull", stdout=subprocess.PIPE, shell=True)

    sent_msg_text = sent_msg.text + "\n\nChanges pulled...I guess.. Restarting in "

    for i in reversed(range(5)):
        sent_msg.edit_text(sent_msg_text + str(i + 1))
        sleep(1)

    sent_msg.edit_text("Restarted.")

    os.system("restart.bat")
    os.execv("start.bat", sys.argv)


@dev_plus
def restart(update: Update, context: CallbackContext):
    update.effective_message.reply_text(
	"Exiting all Processes and starting a new Instance!"
    )
    process = subprocess.run("pkill python3 && python3 -m Cutiepii_Robot", shell=True, check=True)
    process.communicate()

LEAVE_HANDLER = CommandHandler("leave", leave, run_async=True)
GITPULL_HANDLER = CommandHandler("gitpull", gitpull, run_async=True)
RESTART_HANDLER = CommandHandler("reboot", restart, run_async=True)
ALLOWGROUPS_HANDLER = CommandHandler("lockdown", allow_groups, run_async=True)
LEAVE_CALLBACK_HANDLER = CallbackQueryHandler(leave_cb, pattern=r"leavechat_cb_", run_async=True)

dispatcher.add_handler(ALLOWGROUPS_HANDLER)
dispatcher.add_handler(LEAVE_HANDLER)
dispatcher.add_handler(GITPULL_HANDLER)
dispatcher.add_handler(RESTART_HANDLER)
dispatcher.add_handler(LEAVE_CALLBACK_HANDLER)

__mod_name__ = "Dev"
__handlers__ = [LEAVE_HANDLER, GITPULL_HANDLER, RESTART_HANDLER, ALLOWGROUPS_HANDLER, LEAVE_CALLBACK_HANDLER]
