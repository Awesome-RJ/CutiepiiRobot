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

import time
import requests

from typing import List
from telegram import Update
from telegram.constants import ParseMode

from Cutiepii_Robot import StartTime, CUTIEPII_PTB
from Cutiepii_Robot.modules.helper_funcs.chat_status import sudo_plus
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler

sites_list = {
    "Telegram": "https://api.telegram.org",
    "Kaizoku": "https://animekaizoku.com",
    "Kayo": "https://animekayo.com",
    "Jikan": "https://api.jikan.moe/v3",
    "Kuki Chatbot": "https://www.kukiapi.xyz/",
}


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(
            seconds, 24)
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


def ping_func(to_ping: List[str]) -> List[str]:
    ping_result = []

    for each_ping in to_ping:

        start_time = time.time()
        site_to_ping = sites_list[each_ping]
        r = requests.get(site_to_ping)
        end_time = time.time()
        ping_time = f"{str(round((end_time - start_time), 2))}s"

        pinged_site = f"<b>{each_ping}</b>"

        if each_ping in ("Kaizoku", "Kayo"):
            pinged_site = f"<a href='{sites_list[each_ping]}'>{each_ping}</a>"
            ping_time = f"<code>{ping_time} (Status: {r.status_code})</code>"

        ping_text = f"{pinged_site}: <code>{ping_time}</code>"
        ping_result.append(ping_text)

    return ping_result


@sudo_plus
async def ping(update: Update):
    msg = update.effective_message

    start_time = time.time()
    message = await msg.reply_text("Pinging...")
    end_time = time.time()
    telegram_ping = f"{str(round((end_time - start_time) * 1000, 3))} ms"
    uptime = get_readable_time((time.time() - StartTime))

    await message.edit_text(
        f"PONG!!\n<b>Time Taken:</b> <code>{telegram_ping}</code>\n<b>Service uptime:</b> <code>{uptime}</code>",
        parse_mode=ParseMode.HTML,
    )


@sudo_plus
async def pingall(update: Update):
    to_ping = ["Kaizoku", "Kayo", "Telegram", "Jikan", "Kuki Chatbot"]
    pinged_list = ping_func(to_ping)
    pinged_list.insert(2, "")
    uptime = get_readable_time((time.time() - StartTime))

    reply_msg = "⏱Ping results are:\n" + "\n".join(pinged_list)
    reply_msg += f"\n<b>Service uptime:</b> <code>{uptime}</code>"

    await update.effective_message.reply_text(
        reply_msg,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("ping", ping))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("pingall", pingall))

__command_list__ = ["ping", "pingall"]
