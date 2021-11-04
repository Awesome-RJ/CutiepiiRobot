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

import os
import logging
import asyncio

from telethon import Button
from telethon import events
from telethon.tl.types import ChannelParticipantsAdmins

from Cutiepii_Robot import telethn

@telethn.on(events.NewMessage(pattern="^/tagall|/call|/tall|/all|/mentionall|#all|@all?(.*)"))
async def mentionall(event):
  if event.is_private:
    return await event.respond("Use This In Channel or Group!")

  admins = []
  async for admin in telethn.iter_participants(event.chat_id, filter=ChannelParticipantsAdmins):
    admins.append(admin.id)
  if event.sender_id not in admins:
    return await event.respond("Only admins can mention all!")

  if event.pattern_match.group(1):
    mode = "text_on_cmd"
    msg = event.pattern_match.group(1)
  elif event.reply_to_msg_id:
    mode = "text_on_reply"
    msg = event.reply_to_msg_id
    if msg is None:
        return await event.respond("__I can't mention members for older messages! (messages which sended before i added to group)__")
  elif event.pattern_match.group(1) and event.reply_to_msg_id:
    return await event.respond("__Give me one argument!__")
  else:
    return await event.respond("__Reply to a message or give me some text to mention others!__")

  if mode == "text_on_cmd":
    usrnum = 0
    usrtxt = ""
    async for usr in telethn.iter_participants(event.chat_id):
      usrnum += 1
      usrtxt += f"[{usr.first_name}](tg://user?id={usr.id}) "
      if usrnum == 5:
        await telethn.send_message(event.chat_id, f"{usrtxt}\n\n{msg}")
        await asyncio.sleep(2)
        usrnum = 0
        usrtxt = ""

  elif mode == "text_on_reply":
    usrnum = 0
    usrtxt = ""
    async for usr in telethn.iter_participants(event.chat_id):
      usrnum += 1
      usrtxt += f"[{usr.first_name}](tg://user?id={usr.id}) "
      if usrnum == 5:
        await telethn.send_message(event.chat_id, usrtxt, reply_to=msg)
        await asyncio.sleep(2)
        usrnum = 0
        usrtxt = ""
        
__mod_name__ = "Mention All"
