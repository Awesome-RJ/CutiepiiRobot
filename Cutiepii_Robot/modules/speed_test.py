"""
MIT License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021 Awesome-RJ
Copyright (c) 2021, Yūki • Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

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

import datetime
import time
import requests
import speedtest

from Cutiepii_Robot import DEV_USERS, dispatcher, OWNER_ID
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.helper_funcs.chat_status import dev_plus
from Cutiepii_Robot.modules.helper_funcs.alternate import typing_action, send_action

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import CallbackContext, CallbackQueryHandler, run_async, Filters, CommandHandler


def convert(speed):
    return round(int(speed) / 1048576, 2)


@dev_plus
def speedtestxyz(update: Update, context: CallbackContext):
    buttons = [
        [
            InlineKeyboardButton("Image", callback_data="speedtest_image"),
            InlineKeyboardButton("Text", callback_data="speedtest_text"),
        ],
    ]
    update.effective_message.reply_text(
        "Select SpeedTest Mode", reply_markup=InlineKeyboardMarkup(buttons),
    )

        

def speedtestxyz_callback(update: Update, context: CallbackContext):
    query = update.callback_query

    if query.from_user.id in DEV_USERS:
        msg = update.effective_message.edit_text("Running a speedtest....")
        speed = speedtest.Speedtest()
        speed.get_best_server()
        speed.download()
        speed.upload()
        replymsg = "SpeedTest Results:"

        if query.data == "speedtest_image":
            speedtest_image = speed.results.share()
            update.effective_message.reply_photo(
                photo=speedtest_image, caption=replymsg,
            )
            msg.delete()

        elif query.data == "speedtest_text":
            result = speed.results.dict()
            replymsg += f"\nDownload: `{convert(result['download'])}Mb/s`\nUpload: `{convert(result['upload'])}Mb/s`\nPing: `{result['ping']}`"
            update.effective_message.edit_text(replymsg, parse_mode=ParseMode.MARKDOWN)
    else:
        query.answer("You are required to join Heroes Association to use this command.")
        
        
@typing_action
def get_bot_ip(update, _):
    """Sends the bot's IP address, so as to be able to ssh in if necessary.
    OWNER ONLY.
    """
    res = requests.get("http://ipinfo.io/ip")
    update.message.reply_text(res.text)


SPEED_TEST_HANDLER = DisableAbleCommandHandler("speedtest", speedtestxyz, run_async=True)
SPEED_TEST_CALLBACKHANDLER = CallbackQueryHandler(speedtestxyz_callback, pattern="speedtest_.*", run_async=True)
IP_HANDLER = CommandHandler("ip", get_bot_ip, filters=Filters.chat(OWNER_ID), run_async=True)

dispatcher.add_handler(SPEED_TEST_HANDLER)
dispatcher.add_handler(SPEED_TEST_CALLBACKHANDLER)
dispatcher.add_handler(IP_HANDLER)
                       
__mod_name__ = "SpeedTest"
__command_list__ = ["speedtest", "ip"]
__handlers__ = [SPEED_TEST_HANDLER, SPEED_TEST_CALLBACKHANDLER, IP_HANDLER]
