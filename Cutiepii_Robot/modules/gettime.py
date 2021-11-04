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
from typing import List

import requests
from Cutiepii_Robot import TIME_API_KEY, dispatcher
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from telegram import ParseMode, Update
from telegram.ext import CallbackContext, run_async


def generate_time(to_find: str, findtype: List[str]) -> str:
    data = requests.get(
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
                    datetime.timezone.utc,
                ) + datetime.timedelta(seconds=gmt_offset)
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
    except:
        result = None

    return result


def gettime(update: Update, context: CallbackContext):
    message = update.effective_message

    try:
        query = message.text.strip().split(" ", 1)[1]
    except:
        message.reply_text("Provide a country name/abbreviation/timezone to find.")
        return
    send_message = message.reply_text(
        f"Finding timezone info for <b>{query}</b>", parse_mode=ParseMode.HTML,
    )

    query_timezone = query.lower()
    if len(query_timezone) == 2:
        result = generate_time(query_timezone, ["countryCode"])
    else:
        result = generate_time(query_timezone, ["zoneName", "countryName"])

    if not result:
        send_message.edit_text(
            f"Timezone info not available for <b>{query}</b>\n"
            '<b>All Timezones:</b> <a href="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones">List here</a>',
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        return

    send_message.edit_text(
        result, parse_mode=ParseMode.HTML, disable_web_page_preview=True,
    )


TIME_HANDLER = DisableAbleCommandHandler("time", gettime, run_async=True)

dispatcher.add_handler(TIME_HANDLER)

__mod_name__ = "Time"
__command_list__ = ["time"]
__handlers__ = [TIME_HANDLER]
