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

import requests

from pyrogram import filters
from pyrogram.types import (InlineKeyboardMarkup, InlineKeyboardButton)

from Cutiepii_Robot import pgram, telegraph
from Cutiepii_Robot.utils.errors import capture_err


@pgram.on_message(~filters.me & filters.command("nhentai", prefixes="/"),
                  group=8)
@capture_err
async def nhentai(message):
    query = message.text.split(" ")[1]
    title, tags, artist, total_pages, post_url, cover_image = nhentai_data(
        query)
    await message.reply_text(
        f"<code>{title}</code>\n\n<b>Tags:</b>\n{tags}\n<b>Artists:</b>\n{artist}\n<b>Pages:</b>\n{total_pages}",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Read Here", url=post_url)]]))


def nhentai_data(noombers):
    url = f"https://nhentai.net/api/gallery/{noombers}"
    res = requests.get(url).json()
    pages = res["images"]["pages"]
    info = res["tags"]
    title = res["title"]["english"]
    links = []
    tags = ""
    artist = ''
    total_pages = res["num_pages"]
    extensions = {"j": "jpg", "p": "png", "g": "gif"}
    for i, x in enumerate(pages):
        media_id = res["media_id"]
        temp = x["t"]
        file = f"{i+1}.{extensions[temp]}"
        link = f"https://i.nhentai.net/galleries/{media_id}/{file}"
        links.append(link)

    for i in info:
        if i["type"] == "tag":
            tag = i["name"]
            tag = tag.split(" ")
            tag = "_".join(tag)
            tags += f"#{tag} "
        if i["type"] == "artist":
            artist = f"{i['name']} "

    post_content = "".join(f"<img src={link}><br>" for link in links)

    post = telegraph.create_page(
        f"{title}",
        html_content=post_content,
        author_name="@Cutiepii_Robot",
        author_url="https://telegram.dog/Cutiepii_Robot")
    return title, tags, artist, total_pages, post["url"], links[0]
