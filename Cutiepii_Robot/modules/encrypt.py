"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

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
from Cutiepii_Robot.modules.helper_funcs.decorators import register


import os
import secureme

from Cutiepii_Robot import telethn
from Cutiepii_Robot.events import register

@register(pattern="^/encrypt ?(.*)")
async def encrypt_text(event):
    if event.reply_to_msg_id:
        lel = await event.get_reply_message()
        cmd = lel.text
    else:
        cmd = event.pattern_match.group(1)

    if not cmd:
        await event.reply("<b>Invalid Command Usage</b>\nUsage: <code>/encrypt [text]</code> or reply to a message containing text.", parse_mode="html")
        return

    try:
        k = secureme.encrypt(cmd)
        await event.reply(f"<b>Encrypted Text</b>:\n<code>{k}</code>", parse_mode="html")
    except Exception as e:
        await event.reply(f"<b>Error</b>\nAn error occurred during encryption: <code>{str(e)}</code>", parse_mode="html")

@register(pattern="^/decrypt ?(.*)")
async def decrypt_text(event):
    if event.reply_to_msg_id:
        lel = await event.get_reply_message()
        ok = lel.text
    else:
        ok = event.pattern_match.group(1)

    if not ok:
        await event.reply("<b>Invalid Command Usage</b>\nUsage: <code>/decrypt [text]</code> or reply to a message containing text.", parse_mode="html")
        return

    try:
        k = secureme.decrypt(ok)
        await event.reply(f"<b>Decrypted Text</b>:\n<code>{k}</code>", parse_mode="html")
    except Exception as e:
        await event.reply(f"<b>Error</b>\nAn error occurred during decryption: <code>{str(e)}</code>", parse_mode="html")
