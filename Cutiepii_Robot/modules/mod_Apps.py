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
import time
import requests
import wget

from bs4 import BeautifulSoup
from pyrogram import filters, Client
from pyrogram.types import Message

from Cutiepii_Robot.utils.pluginhelpers import admins_only
from Cutiepii_Robot.utils.progress import progress
from Cutiepii_Robot import pgram

Cutiepii_PYRO_Mod = filters.command("mod")


@pgram.on_message(Cutiepii_PYRO_Mod & ~filters.bot)
@pgram.on_edited_message(Cutiepii_PYRO_Mod)
@admins_only
async def mudapk(client: Client, message: Message):
    pablo = await client.send_message(message.chat.id,
                                      "`Searching For Mod App.....`")
    sgname = message.text
    if not sgname:
        await pablo.edit(
            "Invalid Command Syntax, Please Check Help Menu To Know More!")
        return
    PabloEscobar = (
        f"https://an1.com/tags/MOD/?story={sgname}&do=search&subaction=search")
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
