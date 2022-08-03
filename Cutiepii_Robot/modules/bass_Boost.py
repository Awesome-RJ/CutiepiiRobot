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

import asyncio
import io
import math
import os
import numpy as np

from pydub import AudioSegment
from telethon import events

from Cutiepii_Robot.utils.pluginhelpers import is_admin
from Cutiepii_Robot import telethn, BOT_ID, OWNER_ID, SUPPORT_CHAT

TMP_DOWNLOAD_DIRECTORY = "./"


@telethn.on(events.NewMessage(pattern="/bassboost (.*)"))
async def __(event):
    if not event.is_group:

        return
    if not await is_admin(event, BOT_ID):

        return
    if await event.message.sender_id != OWNER_ID:
        return

    v = False
    accentuate_db = 40
    reply = await event.get_reply_message()
    if not reply:
        await event.reply("Can You Reply To A MSG :?")
        return
    if event.pattern_match.group(1):
        ar = event.pattern_match.group(1)
        try:
            int(ar)
            if int(ar) >= 2 and int(ar) <= 100:
                accentuate_db = int(ar)
            else:
                await event.reply(
                    "`BassBost Level Should Be From 2 to 100 Only.`")
                return
        except Exception as exx:
            await event.reply("`SomeThing Went Wrong..` \n**Error:** " +
                              str(exx))
            return
    else:
        accentuate_db = 2
    lel = await event.reply("`Downloading This File...`")
    # fname = await telethn.download_media(message=reply.media)
    r_message = reply.media
    fname = await telethn.download_media(r_message, TMP_DOWNLOAD_DIRECTORY)
    await lel.edit("`BassBoosting In Progress..`")
    if fname.endswith(".oga") or fname.endswith(".ogg"):
        v = True
        audio = AudioSegment.from_file(fname)
    elif fname.endswith(".mp3") or fname.endswith(".m4a") or fname.endswith(
            ".wav"):
        audio = AudioSegment.from_file(fname)
    else:
        await lel.edit(
            "`This Format is Not Supported Yet` \n**Currently Supported :** `mp3, m4a and wav.`"
        )
        os.remove(fname)
        return
    sample_track = list(audio.get_array_of_samples())
    await asyncio.sleep(0.3)
    est_mean = np.mean(sample_track)
    await asyncio.sleep(0.3)
    est_std = 3 * np.std(sample_track) / (math.sqrt(2))
    await asyncio.sleep(0.3)
    bass_factor = int(round((est_std - est_mean) * 0.005))
    await asyncio.sleep(5)
    attenuate_db = 0
    filtered = audio.low_pass_filter(bass_factor)
    await asyncio.sleep(5)
    out = (audio - attenuate_db).overlay(filtered + accentuate_db)
    await asyncio.sleep(6)
    m = io.BytesIO()
    if v:
        m.name = "voice.ogg"
        out.split_to_mono()
        await lel.edit("`Now Exporting...`")
        await asyncio.sleep(0.3)
        out.export(m, format="ogg", bitrate="64k", codec="libopus")
        await lel.edit("`Process Completed. Uploading Now Here..`")
        await telethn.send_file(
            event.chat_id,
            m,
            voice_note=True,
            caption=f"Bass Boosted, \nDone By @{SUPPORT_CHAT}",
        )

    else:
        m.name = "BassBoosted.mp3"
        await lel.edit("`Now Exporting...`")
        await asyncio.sleep(0.3)
        out.export(m, format="mp3")
        await lel.edit("`Process Completed. Uploading Now Here..`")
        await telethn.send_file(
            event.chat_id,
            m,
            caption=f"Bass Boosted, \nDone By @{SUPPORT_CHAT}",
        )

    os.remove(m)
    await event.delete()

    os.remove(fname)
