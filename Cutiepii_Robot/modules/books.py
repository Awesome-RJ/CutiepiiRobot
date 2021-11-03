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

from bs4 import BeautifulSoup
from telethon import events

from Cutiepii_Robot import telethn, SUPPORT_CHAT, BOT_USERNAME


@telethn.on(events.NewMessage(pattern="^/book (.*)"))
async def _(event):
    if event.fwd_from:
        return
    input_str = event.pattern_match.group(1)
    KkK = await event.reply("searching for the book...")
    lin = "https://b-ok.cc/s/"
    text = input_str
    link = lin + text

    headers = [
        "User-Agent",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:74.0) Gecko/20100101 Firefox/74.0",
    ]
    page = requests.get(link)
    soup = BeautifulSoup(page.content, "html.parser")
    f = open("book.txt", "w")
    total = soup.find(class_="totalCounter")
    for nb in total.descendants:
        nbx = nb.replace("(", "").replace(")", "")
    if nbx == "0":
        await event.reply("No Books Found with that name.")
    else:

        lool = 0
        for tr in soup.find_all("td"):
            for td in tr.find_all("h3"):
                for ts in td.find_all("a"):
                    title = ts.get_text()
                    lool += 1
                for ts in td.find_all("a", attrs={"href": re.compile("^/book/")}):
                    ref = ts.get("href")
                    link = "https://b-ok.cc" + ref

                f.write("\n" + title)
                f.write("\nBook link:- " + link + "\n\n")

        f.write(f"By @{BOT_USERNAME}.")
        f.close()
        caption = f"A collabration with Friday.\n Join Support @{SUPPORT_CHAT}"

        await telethn.send_file(
            event.chat_id,
            "book.txt",
            caption=f"**BOOKS GATHERED SUCCESSFULLY!\n\nBY DAISYX. JOIN THE SUPPORT @{SUPPORT_CHAT}.**",
        )
        os.remove("book.txt")
        await KkK.delete()
