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
import re
import requests

from datetime import datetime
from telethon import events

from Cutiepii_Robot.utils.pluginhelpers import is_admin
from Cutiepii_Robot import telethn, BOT_USERNAME, SUPPORT_CHAT


def main(url, filename):
    try:
        download_video("HD", url, filename)
    except (KeyboardInterrupt):
        download_video("SD", url, filename)


def download_video(quality, url, filename):
    html = requests.get(url).content.decode("utf-8")
    video_url = re.search(rf'{quality.lower()}_src:"(.+?)"', html).group(1)
    file_size_request = requests.get(video_url, stream=True)
    int(file_size_request.headers["Content-Length"])
    block_size = 1024
    with open(filename + ".mp4", "wb") as f:
        for data in file_size_request.iter_content(block_size):
            f.write(data)
    print("\nVideo downloaded successfully.")


@telethn.on(events.NewMessage(pattern="^/fbdl (.*)"))
async def _(event):
    if event.fwd_from:
        return
    if await is_admin(event, event.message.sender_id):
        url = event.pattern_match.group(1)
        x = re.match(r"^(https:|)[/][/]www.([^/]+[.])*facebook.com", url)

        if x:
            html = requests.get(url).content.decode("utf-8")
            await event.reply(
                "Starting Video download... \n Please note: FBDL is not for big files."
            )
        else:
            await event.reply(
                "This Video Is Either Private Or URL Is Invalid. Exiting... "
            )
            return

        _qualityhd = re.search('hd_src:"https', html)
        _qualitysd = re.search('sd_src:"https', html)
        _hd = re.search("hd_src:null", html)
        _sd = re.search("sd_src:null", html)

        _thelist = [_qualityhd, _qualitysd, _hd, _sd]
        list = [id for id, val in enumerate(_thelist) if val is not None]
        filename = datetime.strftime(datetime.now(), "%Y-%m-%d-%H-%M-%S")

        main(url, filename)
        await event.reply("Video Downloaded Successfully. Starting To Upload.")

        kk = f"{filename}.mp4"
        caption = f"Facebook Video downloaded Successfully by @{BOT_USERNAME}.\nSay hi to devs @{SUPPORT_CHAT}."

        await telethn.send_file(
            event.chat_id,
            kk,
            caption = f"Facebook Video downloaded Successfully by @{BOT_USERNAME}.\nSay hi to devs @{SUPPORT_CHAT}.",
        )
        os.system(f"rm {kk}")
    else:
        await event.reply("`You Should Be Admin To Do This!`")
        return