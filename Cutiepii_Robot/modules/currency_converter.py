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

from Cutiepii_Robot import CASH_API_KEY, CUTIEPII_PTB
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler


async def convert(update: Update):
    args = await update.effective_message.text.split(" ")
    message = update.effective_message

    if len(args) == 4:
        try:
            orig_cur_amount = float(args[1])

        except ValueError:
            await update.effective_message.reply_text(
                "Invalid Amount Of Currency")
            return

        orig_cur = args[2].upper()

        new_cur = args[3].upper()

        request_url = (f"https://www.alphavantage.co/query"
                       f"?function=CURRENCY_EXCHANGE_RATE"
                       f"&from_currency={orig_cur}"
                       f"&to_currency={new_cur}"
                       f"&apikey={CASH_API_KEY}")
        response = requests.get(request_url).json()
        try:
            current_rate = float(
                response["Realtime Currency Exchange Rate"]
                ["5. Exchange Rate"], )
        except (KeyError, IndexError):
            await update.effective_message.reply_text("Currency Not Supported."
                                                      )
            return
        new_cur_amount = round(orig_cur_amount * current_rate, 5)
        await message.reply_text(
            f"{orig_cur_amount} {orig_cur} = {new_cur_amount} {new_cur}", )

    elif len(args) == 1:
        await message.reply_text(_help_, parse_mode=ParseMode.MARKDOWN)

    else:
        await message.reply_text(
            f"*Invalid Args!!:* Required 3 But Passed {len(args) -1}",
            parse_mode=ParseMode.MARKDOWN,
        )


_help_ = """
💴 Currency converter:
➛ /cash`: currency converter.

Example:
 `/cash 1 USD INR`
      OR
 `/cash 1 usd inr`

Output: `1.0 USD = 75.505 INR`
"""

CUTIEPII_PTB.add_handler(CommandHandler("cash", convert))

__command_list__ = ["cash"]
