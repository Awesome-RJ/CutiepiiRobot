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
import requests
import os
import re
import urllib
import urllib.request

from datetime import datetime
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup
from random import randint
from typing import List
from telegram import ParseMode, InputMediaPhoto, Update, TelegramError, ChatAction
from telegram.ext import CommandHandler, run_async, CallbackContext

from Cutiepii_Robot import dispatcher
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler


def covid(update: Update, context: CallbackContext):
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
       message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        return msg.reply_text("There was a problem while importing the data!")


COVID_HANDLER = DisableAbleCommandHandler(["covid", "corona"], covid, run_async = True)
dispatcher.add_handler(COVID_HANDLER)
