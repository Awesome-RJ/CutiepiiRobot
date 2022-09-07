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

import requests
import json
import datetime

from telegram import Update
from telegram.ext import CallbackContext
from telegram.constants import ParseMode

from Cutiepii_Robot import CUTIEPII_PTB
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler


async def dot(number, thousand_separator="."):

    def reverse(string):
        string = "".join(reversed(string))
        return string

    s = reverse(str(number))
    count = 0
    result = ""
    for char in s:
        count = count + 1
        if count % 3 == 0:
            if len(s) == count:
                result = char + result
            else:
                result = thousand_separator + char + result
        else:
            result = char + result
    return result


async def covid(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    args = context.args
    query = " ".join(args)
    remove_space = query.split(" ")
    country = "%20".join(remove_space)
    if not country:
        url = "https://disease.sh/v3/covid-19/all?yesterday=false&twoDaysAgo=false&allowNull=true"
        country = "World"
    else:
        url = f"https://disease.sh/v3/covid-19/countries/{country}?yesterday=false&twoDaysAgo=false&strict=true&allowNull=true"
    request = requests.get(url).text
    case = json.loads(request)
    try:
        json_date = case["updated"]
    except (KeyError, IndexError):
        await message.reply_text("Make sure you have input correct country")
        return
    float_date = float(json_date) / 1000.0
    date = datetime.datetime.fromtimestamp(float_date).strftime(
        "%d %b %Y %I:%M:%S %p")
    try:
        flag = case["countryInfo"]["flag"]
    except (KeyError, IndexError):
        flag = []
    if flag:
        text = f"*COVID-19 Statistics in* [{query}]({flag})\n"
    else:
        text = f"*COVID-19 Statistics in {country} :*\n"
    text += f"Last Updated on `{date} GMT`\n\n🔼 Confirmed Cases : `{dot(case['cases'])}` | `+{dot(case['todayCases'])}`\n🔺 Active Cases : `{dot(case['active'])}`\n⚰️ Deaths : `{dot(case['deaths'])}` | `+{dot(case['todayDeaths'])}`\n💹 Recovered Cases: `{dot(case['recovered'])}` | `+{dot(case['todayRecovered'])}`\n💉 Total Tests : `{dot(case['tests'])}`\n👥 Populations : `{dot(case['population'])}`\n🌐 Source : worldometers"
    try:
        await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await message.reply_text(
            "Try again in few times, maybe API are go down")


CUTIEPII_PTB.add_handler(DisableAbleCommandHandler(["covid", "corona"], covid))
