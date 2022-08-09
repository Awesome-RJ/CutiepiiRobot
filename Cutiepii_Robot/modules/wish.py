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
import random

from Cutiepii_Robot import OWNER_ID, telethn

from telethon import events, Button
from telegram.constants import ParseMode

BUTTON = [[
    Button.url("❓ What Is This", "https://t.me/Black_Knights_Union/195")
]]
COMET = "https://telegra.ph/file/713fbfbdde25cc1726866.mp4"
STAR = "https://telegra.ph/file/ad90b44c551cec31df76b.mp4"
WISH = """
**You can use** `/wish` **as a general Wishing Well of sorts**
**For example:**
`/wish I could date you 😍,` **or**
`/wish that sushi was 🍣 in /emojify, or
/wish I had someone to /cuddle at night...`
"""


@telethn.on(events.NewMessage(pattern="/wish ?(.*)"))
async def wish(e):
    quew = e.pattern_match.group(1)
    if e.sender_id != OWNER_ID and not quew:
        (await e.reply(WISH,
                       parse_mode=ParseMode.MARKDOWN,
                       buttons=BUTTON,
                       file=STAR), )
        return
    if not e.is_reply:
        mm = random.randint(1, 100)
        DREAM = f"**Your wish has been cast.✨**\n\n__chance of success {mm}%__"
        await e.reply(DREAM, buttons=BUTTON, file=COMET)
