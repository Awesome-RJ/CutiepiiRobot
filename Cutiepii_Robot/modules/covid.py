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

import requests

from telegram import Update
from telegram.ext import CallbackContext
from telegram.constants import ParseMode

from Cutiepii_Robot import CUTIEPII_PTB
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler


async def covid(update: Update, context: CallbackContext):
    message = update.effective_message
    text = message.text.split(' ', 1)
    try:
       if len(text) == 1:
           r = requests.get("https://disease.sh/v3/covid-19/all").json()
           reply_text = f"**Global Totals** 🦠\nCases: {r['cases']:,}\nCases Today: {r['todayCases']:,}\nDeaths: {r['deaths']:,}\nDeaths Today: {r['todayDeaths']:,}\nRecovered: {r['recovered']:,}\nActive: {r['active']:,}\nCritical: {r['critical']:,}\nCases/Mil: {r['casesPerOneMillion']}\nDeaths/Mil: {r['deathsPerOneMillion']}"
       else:
           variabla = text[1]
           r = requests.get(
               f"https://disease.sh/v3/covid-19/countries/{variabla}").json()
           reply_text = f"**Cases for {r['country']} 🦠**\nCases: {r['cases']:,}\nCases Today: {r['todayCases']:,}\nDeaths: {r['deaths']:,}\nDeaths Today: {r['todayDeaths']:,}\nRecovered: {r['recovered']:,}\nActive: {r['active']:,}\nCritical: {r['critical']:,}\nCases/Mil: {r['casesPerOneMillion']}\nDeaths/Mil: {r['deathsPerOneMillion']}"
       await message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        return await update.effective_message.reply_text("There was a problem while importing the data!")


COVID_HANDLER = DisableAbleCommandHandler(["covid", "corona"], covid)
CUTIEPII_PTB.add_handler(COVID_HANDLER)
