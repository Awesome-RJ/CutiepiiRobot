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

import asyncio

from telethon import events
from telethon.tl.types import ChannelParticipantsAdmins

from Cutiepii_Robot import telethn, BOT_NAME
from Cutiepii_Robot.events import register as cutiepii



@cutiepii(pattern="^/tagall ?(.*)")
async def _(event):
    if event.fwd_from:
        return
    mentions = f"Hi Friends I'm {BOT_NAME} I Call To All Of You"
    chat = await event.get_input_chat()
    async for x in telethn.iter_participants(chat, 100):
        mentions += f" \n [{x.first_name}](tg://user?id={x.id})"
    await event.reply(mentions)
    await event.delete()

__mod_name__ = "Tagger"
__help__ = """
  ➢ `/tagall` : Tag everyone in a chat.
  ➢ `/tagall` : Mention All Members
Exp:- /all <Text> or <reply>

Note:- This `/tagall` Command can mention members upto 10,000 in groups and can mention members upto 200 in channels !
"""
