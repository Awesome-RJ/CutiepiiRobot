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

import os
import re
import requests

from datetime import datetime
from telethon import events

from Cutiepii_Robot.utils.pluginhelpers import is_admin
from Cutiepii_Robot import telethn, SUPPORT_CHAT, LOGGER


def main(url, filename):
    try:
        download_video("HD", url, filename)
    except (KeyboardInterrupt):
        download_video("SD", url, filename)


def download_video(quality, url, filename):
    html = requests.get(url).content.decode("utf-8")
    video_url = re.search(rf'{quality.lower()}_src:"(.+?)"', html)[1]
    file_size_request = requests.get(video_url, stream=True)
    int(file_size_request.headers["Content-Length"])
    block_size = 1024
    with open(f"{filename}.mp4", "wb") as f:
        for data in file_size_request.iter_content(block_size):
            f.write(data)
    LOGGER.debug("\nVideo downloaded successfully.")


@telethn.on(events.NewMessage(pattern="^/fbdl (.*)"))
async def _(event):
    if event.fwd_from:
        return
    if await is_admin(event, event.message.sender_id):
        url = event.pattern_match.group(1)
        if re.match(r"^(https:|)[/][/]www.([^/]+[.])*facebook.com", url):
            html = requests.get(url).content.decode("utf-8")
            await event.reply(
                "Starting Video download... \n Please note: FBDL is not for big files."
            )
        else:
            await event.reply(
                "This Video Is Either Private Or URL Is Invalid. Exiting... ")
            return

        _qualityhd = re.search('hd_src:"https', html)
        _qualitysd = re.search('sd_src:"https', html)
        _hd = re.search("hd_src:null", html)
        _sd = re.search("sd_src:null", html)

        _thelist = [_qualityhd, _qualitysd, _hd, _sd]
        filename = datetime.strftime(datetime.now(), "%Y-%m-%d-%H-%M-%S")

        main(url, filename)
        await event.reply("Video Downloaded Successfully. Starting To Upload.")

        kk = f"{filename}.mp4"

        await telethn.send_file(
            event.chat_id,
            kk,
            caption=
            f"Facebook Video downloaded Successfully by @Cutiepii_Robot.\nSay hi to devs @{SUPPORT_CHAT}.",
        )
        os.system(f"rm {kk}")
    else:
        await event.reply("`You Should Be Admin To Do This!`")
        return
