"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2022, Yūki • Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

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

import time
import requests
import datetime
import platform
import Cutiepii_Robot.modules.sql.users_sql as sql
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, __version__ as ptbver
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.helpers import escape_markdown


from Cutiepii_Robot import StartTime, CUTIEPII_PTB
from Cutiepii_Robot.__main__ import STATS
from Cutiepii_Robot.modules.sql import SESSION
from Cutiepii_Robot.modules.helper_funcs.chat_status import sudo_plus
from psutil import cpu_percent, virtual_memory, disk_usage, boot_time
from platform import python_version

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += f"{time_list.pop()}, "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time

@sudo_plus
async def stats(update: Update, context: CallbackContext):
    message = update.effective_message
    db_size = SESSION.execute(
        "SELECT pg_size_pretty(pg_database_size(current_database()))"
    ).scalar_one_or_none()
    uptime = datetime.datetime.fromtimestamp(boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    botuptime = get_readable_time((time.time() - StartTime))
    status = "*╔═━「 System statistics: 」*\n\n"
    status += f"*➛ System Start time:* {str(uptime)}" + "\n"
    uname = platform.uname()
    status += f"*➛ System:* {str(uname.system)}" + "\n"
    status += f"*➛ Node name:* {escape_markdown(str(uname.node))}" + "\n"
    status += f"*➛ Release:* {escape_markdown(str(uname.release))}" + "\n"
    status += f"*➛ Machine:* {escape_markdown(str(uname.machine))}" + "\n"

    mem = virtual_memory()
    cpu = cpu_percent()
    disk = disk_usage("/")
    status += f"*➛ CPU:* {str(cpu)}" + " %\n"
    status += f"*➛ RAM:* {str(mem[2])}" + " %\n"
    status += f"*➛ Storage:* {str(disk[3])}" + " %\n\n"
    status += f"*➛ Python version:* {python_version()}" + "\n"
    status += f"*➛ python-telegram-bot:* {str(ptbver)}" + "\n"
    status += f"*➛ Uptime:* {str(botuptime)}" + "\n"
    status += f"*➛ Database size:* {str(db_size)}" + "\n"
    kb = [
          [
           InlineKeyboardButton("Ping", callback_data="pingCB")
          ]
    ]
    try:
        await message.reply_text(status +
            "\n*Bot statistics*:\n"
            + "\n".join([mod.__stats__() for mod in STATS]) +
            "\n\n✦ [Support](https://telegram.dog/Black_Knights_Union_Support) | ✦ [Updates](https://telegram.dog/Black_Knights_Union)\n\n" +
            "╘═━「 by [Awesome-RJ](https://github.com/Awesome-RJ) 」\n",
        parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(kb), disable_web_page_preview=True, allow_sending_without_reply=True)
    except BaseException:
        await message.reply_text(
            (
                (
                    (
                        "\n*Bot statistics*:\n"
                        + "\n".join(mod.__stats__() for mod in STATS)
                    )
                    + "\n\n✦ [Support](https://telegram.dog/Black_Knights_Union_Support) | ✦ [Updates](https://telegram.dog/Black_Knights_Union)\n\n"
                )
                + "╘═━「 by [Awesome-RJ](https://github.com/Awesome-RJ) 」\n"
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(kb),
            disable_web_page_preview=True,
            allow_sending_without_reply=True,
        )


async def ping(update: Update, _):
    msg = update.effective_message
    start_time = time.time()
    message = await msg.reply_text("Pinging...")
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000, 3)
    await message.edit_text(
        "*Pong!!!*\n`{}ms`".format(ping_time), parse_mode=ParseMode.MARKDOWN
    )



async def pingCallback(update: Update, context: CallbackContext):
    query = update.callback_query
    start_time = time.time()
    requests.get("https://api.telegram.org")
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000, 3)
    await query.answer(f'Pong! {ping_time}ms')


STATS_HANDLER = CommandHandler(["stats", "statistics"], stats)
STATS_CALLBACK_HANDLER = CallbackQueryHandler(pingCallback, pattern=r"pingCB")

CUTIEPII_PTB.add_handler(STATS_HANDLER)
CUTIEPII_PTB.add_handler(STATS_CALLBACK_HANDLER)

__mod_name__ = "statistics"
