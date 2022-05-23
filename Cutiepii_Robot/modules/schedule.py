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
import datetime

from requests import get
from pyrogram import filters
from pyrogram.types.bots_and_keyboards.inline_keyboard_button import InlineKeyboardButton
from pyrogram.types.bots_and_keyboards.inline_keyboard_markup import InlineKeyboardMarkup

from Cutiepii_Robot import pgram


def call_back_in_filter(data):
    return filters.create(lambda flt, _, query: flt.data in query.data,
                          data=data)


def latest():

    url = 'https://subsplease.org/api/?f=schedule&h=true&tz=Japan'
    res = get(url).json()

    k = None
    for x in res['schedule']:
        title = x['title']
        time = x['time']
        try:
            aired = bool(x['aired'])
            title = (
                f"**~~[{title}](https://subsplease.org/shows/{x['page']})~~**"
                if aired
                else f"**[{title}](https://subsplease.org/shows/{x['page']})**"
            )

        except KeyError:
            title = f"**[{title}](https://subsplease.org/shows/{x['page']})**"
        data = f"{title} - {time}"

        k = f"{k}\n{data}" if k else data
    return k


@pgram.on_message(filters.command('latest'))
def lates(_, message):
    mm = latest()
    message.reply_text(f"Today's Schedule:\nTZ: Japan\n{mm}",
                           reply_markup=InlineKeyboardMarkup([[
                           InlineKeyboardButton("Refresh", callback_data="fk")
                       ]]))


@pgram.on_callback_query(call_back_in_filter("fk"))
def callbackk(_, query):

    if query.data == "fk":
        mm = latest()
        time_ = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M")

        try:
            query.message.edit(f"Today\'s Schedule:\nTZ: Japan\n{mm}",
                               reply_markup=InlineKeyboardMarkup([[
                                   InlineKeyboardButton("Refresh",
                                                        callback_data="fk")
                               ]]))
            query.answer("Refreshed!")

        except:
            query.answer("Refreshed!")

