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
    if len(text) == 1:
        r = requests.get("https://corona.lmao.ninja/v2/all").json()
        reply_text = f"**Global Totals** 🦠\nCases: {r['cases']:,}\nCases Today: {r['todayCases']:,}\nDeaths: {r['deaths']:,}\nDeaths Today: {r['todayDeaths']:,}\nRecovered: {r['recovered']:,}\nActive: {r['active']:,}\nCritical: {r['critical']:,}\nCases/Mil: {r['casesPerOneMillion']}\nDeaths/Mil: {r['deathsPerOneMillion']}"
    else:
        variabla = text[1]
        r = requests.get(
            f"https://corona.lmao.ninja/v2/countries/{variabla}").json()
        reply_text = f"**Cases for {r['country']} 🦠**\nCases: {r['cases']:,}\nCases Today: {r['todayCases']:,}\nDeaths: {r['deaths']:,}\nDeaths Today: {r['todayDeaths']:,}\nRecovered: {r['recovered']:,}\nActive: {r['active']:,}\nCritical: {r['critical']:,}\nCases/Mil: {r['casesPerOneMillion']}\nDeaths/Mil: {r['deathsPerOneMillion']}"
    message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN)



COVID_HANDLER = DisableAbleCommandHandler(["covid", "corona"], covid, run_async = True)
dispatcher.add_handler(COVID_HANDLER)
