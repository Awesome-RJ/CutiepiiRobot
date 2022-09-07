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

import datetime
import pycountry
from typing import List

from requests import get
from Cutiepii_Robot import TIME_API_KEY, CUTIEPII_PTB
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext


def generate_time(to_find: str, findtype: List[str]) -> str:
    data = get(
        f"https://api.timezonedb.com/v2.1/list-time-zone"
        f"?key={TIME_API_KEY}"
        f"&format=json"
        f"&fields=countryCode,countryName,zoneName,gmtOffset,timestamp,dst",
    ).json()

    for zone in data["zones"]:
        for eachtype in findtype:
            if to_find in zone[eachtype].lower():
                country_name = zone["countryName"]
                country_zone = zone["zoneName"]
                country_code = zone["countryCode"]

                daylight_saving = "Yes" if zone["dst"] == 1 else "No"
                date_fmt = r"%d-%m-%Y"
                time_fmt = r"%H:%M:%S"
                day_fmt = r"%A"
                gmt_offset = zone["gmtOffset"]
                timestamp = datetime.datetime.now(
                    datetime.timezone.utc, ) + datetime.timedelta(
                        seconds=gmt_offset)
                current_date = timestamp.strftime(date_fmt)
                current_time = timestamp.strftime(time_fmt)
                current_day = timestamp.strftime(day_fmt)

                break

    try:
        result = (
            f"<b>Country:</b> <code>{country_name}</code>\n"
            f"<b>Zone Name:</b> <code>{country_zone}</code>\n"
            f"<b>Country Code:</b> <code>{country_code}</code>\n"
            f"<b>Daylight saving:</b> <code>{daylight_saving}</code>\n"
            f"<b>Day:</b> <code>{current_day}</code>\n"
            f"<b>Current Time:</b> <code>{current_time}</code>\n"
            f"<b>Current Date:</b> <code>{current_date}</code>\n"
            '<b>Timezones:</b> <a href="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones">List here</a>'
        )
    except Exception:
        result = None

    return result


async def gettime(update: Update, context: CallbackContext) -> None:
    message = update.effective_message

    try:
        query = message.text.strip().split(" ", 1)[1]
    except Exception:
        await update.effective_message.reply_text(
            "Provide a country name/abbreviation/timezone to find.")
        return
    send_message = await message.reply_text(
        f"Finding timezone info for <b>{query}</b>",
        parse_mode=ParseMode.HTML,
    )

    query_timezone = query.lower()
    py_country = pycountry.countries.search_fuzzy(query)
    if len(query_timezone) == 2:
        result = generate_time(query_timezone, ["countryCode"])
    elif py_country:
        result = generate_time(py_country[0].alpha_2.lower(), ["countryCode"])
    else:
        result = generate_time(query_timezone, ["zoneName", "countryName"])

    if not result:
        send_message.edit_text(
            f"Timezone info not available for <b>{query}</b>\n"
            "<b>All Timezones:</b> <a href='https://en.wikipedia.org/wiki/List_of_tz_database_time_zones'>List here</a>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    send_message.edit_text(
        result,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("time", gettime))

__mod_name__ = "Time"
__command_list__ = ["time"]
