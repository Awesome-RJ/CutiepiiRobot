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

import io
import contextlib
import aiohttp

from telethon.tl import functions
from telethon.tl import types

from Cutiepii_Robot.events import register
from Cutiepii_Robot import OPENWEATHERMAP_ID, CUTIEPII_PTB, telethn as tbot
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler


async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):
        return isinstance(
            (await
             tbot(functions.channels.GetParticipantRequest(chat,
                                                           user))).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerUser):
        return True


import json
from datetime import datetime

from pytz import country_timezones as c_tz, timezone as tz, country_names as c_n
from requests import get
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext
from .sql.clear_cmd_sql import get_clearcmd


def get_tz(con):
    for c_code in c_n:
        if con == c_n[c_code]:
            return tz(c_tz[c_code][0])
    with contextlib.suppress(KeyError):
        if c_n[con]:
            return tz(c_tz[con][0])


async def weather(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    city = message.text[len("/weather "):]

    if city:
        APPID = OPENWEATHERMAP_ID
        result = None
        timezone_countries = {
            timezone: country
            for country, timezones in c_tz.items() for timezone in timezones
        }

        if "," in city:
            newcity = city.split(",")
            if len(newcity[1]) == 2:
                city = newcity[0].strip() + "," + newcity[1].strip()
            else:
                country = get_tz((newcity[1].strip()).title())
                try:
                    countrycode = timezone_countries[f"{country}"]
                except (KeyError, IndexError):
                    weather.edit("`Invalid country.`")
                    return
                city = newcity[0].strip() + "," + countrycode.strip()
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={APPID}"
        try:
            request = get(url)
            result = json.loads(request.text)
        except ConnectionError:
            return message.reply_text(
                "Connection timed out! please try again later.")

        if request.status_code != 200:
            msg = "No weather information for this location!"

        else:

            cityname = result["name"]
            longitude = result["coord"]["lon"]
            latitude = result["coord"]["lat"]
            curtemp = result["main"]["temp"]
            feels_like = result["main"]["feels_like"]
            humidity = result["main"]["humidity"]
            min_temp = result["main"]["temp_min"]
            max_temp = result["main"]["temp_max"]
            country = result["sys"]["country"]
            sunrise = result["sys"]["sunrise"]
            sunset = result["sys"]["sunset"]
            wind = result["wind"]["speed"]
            weath = result["weather"][0]
            desc = weath["main"]
            icon = weath["id"]
            condmain = weath["main"]
            conddet = weath["description"]

            if icon <= 232:  # Rain storm
                icon = "⛈"
            elif icon <= 321:  # Drizzle
                icon = "🌧"
            elif icon <= 504:  # Light rain
                icon = "🌦"
            elif icon <= 531:  # Cloudy rain
                icon = "⛈"
            elif icon <= 622:  # Snow
                icon = "❄️"
            elif icon <= 781:  # Atmosphere
                icon = "🌪"
            elif icon <= 800:  # Bright
                icon = "☀️"
            elif icon <= 801:  # A little cloudy
                icon = "⛅️"
            elif icon <= 804:  # Cloudy
                icon = "☁️"

            ctimezone = tz(c_tz[country][0])
            time = (datetime.now(ctimezone).strftime("%A %d %b, %H:%M").lstrip(
                "0").replace(" 0", " "))
            fullc_n = c_n[f"{country}"]
            dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

            kmph = str(wind * 3.6).split(".")
            mph = str(wind * 2.237).split(".")

            def fahrenheit(f):
                temp = str(((f - 273.15) * 9 / 5 + 32)).split(".")
                return temp[0]

            def celsius(c):
                temp = str((c - 273.15)).split(".")
                return temp[0]

            def sun(unix):
                return (datetime.fromtimestamp(
                    unix, tz=ctimezone).strftime("%H:%M").lstrip("0").replace(
                        " 0", " "))

            ## AirQuality
            air_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={latitude}&lon={longitude}&appid={APPID}"
            air_data = json.loads(get(air_url).text)

            into_dicts = air_data['list'][0]
            air_qi = into_dicts['main']
            aqi = int(air_qi['aqi'])

            ## Pollutant concentration
            # airinfo = into_dicts['components']
            # components_co   = airinfo["co"]
            # components_no   = airinfo["no"]

            def air_qual(aqin):
                if aqin == 1:
                    return "Good"
                if aqin == 2:
                    return "Fair"
                if aqin == 3:
                    return 'Moderate'
                if aqin == 4:
                    return 'Poor'
                if aqin == 5:
                    return "Very Poor"

            msg = f"*{cityname}, {fullc_n}*\n"
            msg += f"`Longitude: {longitude}`\n"
            msg += f"`Latitude: {latitude}`\n\n"
            msg += f"➛ **Time:** `{time}`\n"
            msg += f"➛ **Temperature:** `{celsius(curtemp)}°C\n`"
            msg += f"➛ **Feels like:** `{celsius(feels_like)}°C\n`"
            msg += f"➛ **Condition:** `{condmain}, {conddet}` " + f"{icon}\n"
            msg += f"➛ **Humidity:** `{humidity}%`\n"
            msg += f"➛ **Wind:** `{kmph[0]} km/h`\n"
            msg += f"➛ **Sunrise**: `{sun(sunrise)}`\n"
            msg += f"➛ **Sunset**: `{sun(sunset)}`\n"
            msg += f"➛ **Air Quality**: `{air_qual(aqi)}`"

    else:
        msg = "Please specify a city or country"

    delmsg = await message.reply_text(
        text=msg,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )

    cleartime = get_clearcmd(chat.id, "weather")


"""
    if cleartime:
        context.bot.run_async(delete, delmsg, cleartime.time)
"""


@register(pattern="^/wttr (.*)")
async def _(event):
    if event.fwd_from:
        return

    sample_url = "https://wttr.in/{}.png"
    # logger.info(sample_url)
    input_str = event.pattern_match.group(1)
    async with aiohttp.ClientSession() as session:
        response_api_zero = await session.get(sample_url.format(input_str))
        # logger.info(response_api_zero)
        response_api = await response_api_zero.read()
        with io.BytesIO(response_api) as out_file:
            await event.reply(file=out_file)


CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("weather", weather))
