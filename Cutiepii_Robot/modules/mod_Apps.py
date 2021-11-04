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
import time
import requests
import wget

from bs4 import BeautifulSoup
from pyrogram import filters

from Cutiepii_Robot.utils.pluginhelpers import admins_only
from Cutiepii_Robot.utils.progress import progress
from Cutiepii_Robot import pgram


@pgram.on_message(filters.command("mod") & ~filters.edited & ~filters.bot)
@admins_only
async def mudapk(client, message):
    pablo = await client.send_message(message.chat.id, "`Searching For Mod App.....`")
    sgname = message.text
    if not sgname:
        await pablo.edit("Invalid Command Syntax, Please Check Help Menu To Know More!")
        return
    PabloEscobar = (
        f"https://an1.com/tags/MOD/?story={sgname}&do=search&subaction=search"
    )
    r = requests.get(PabloEscobar)
    soup = BeautifulSoup(r.content, "html5lib")
    mydivs = soup.find_all("div", {"class": "search-results"})
    Pop = soup.find_all("div", {"class": "title"})
    sucker = mydivs[0]
    pH9 = sucker.find("a").contents[0]
    file_name = pH9

    pH = sucker.findAll("img")
    imme = wget.download(pH[0]["src"])
    Pablo = Pop[0].a["href"]

    ro = requests.get(Pablo)
    soup = BeautifulSoup(ro.content, "html5lib")

    mydis = soup.find_all("a", {"class": "get-product"})

    Lol = mydis[0]

    lemk = "https://an1.com" + Lol["href"]

    rr = requests.get(lemk)
    soup = BeautifulSoup(rr.content, "html5lib")

    script = soup.find("script", type="text/javascript")

    leek = re.search(r'href=[\'"]?([^\'" >]+)', script.text).group()
    dl_link = leek[5:]

    r = requests.get(dl_link)
    await pablo.edit("Downloading Mod App")
    open(f"{file_name}.apk", "wb").write(r.content)
    c_time = time.time()
    await pablo.edit(f"`Downloaded {file_name}! Now Uploading APK...`")
    await client.send_document(
        message.chat.id,
        document=open(f"{file_name}.apk", "rb"),
        thumb=imme,
        progress=progress,
        progress_args=(
            pablo,
            c_time,
            f"`Uploading {file_name} Mod App`",
            f"{file_name}.apk",
        ),
    )
    os.remove(f"{file_name}.apk")
    os.remove(imme)
    await pablo.delete()
