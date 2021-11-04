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
import secureme

from Cutiepii_Robot import telethn
from Cutiepii_Robot.events import register

@register(pattern="^/encrypt ?(.*)")
async def hmm(event):
    if event.reply_to_msg_id:
          lel = await event.get_reply_message()
          cmd = lel.text
    else:
          cmd = event.pattern_match.group(1)
    Text = cmd
    k = secureme.encrypt(Text)
    await event.reply(k)

@register(pattern="^/decrypt ?(.*)")
async def hmm(event):
    if event.reply_to_msg_id:
          lel = await event.get_reply_message()
          ok = lel.text
    else:
          ok = event.pattern_match.group(1)
    Text = ok
    k = secureme.decrypt(Text)
    await event.reply(k)