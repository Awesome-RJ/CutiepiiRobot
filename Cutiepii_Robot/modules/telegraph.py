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

from Cutiepii_Robot.events import register
from Cutiepii_Robot import telethn
from telethon import types
from PIL import Image
from datetime import datetime
from telegraph import Telegraph, upload_file, exceptions

TMP_DOWNLOAD_DIRECTORY = "tg-File/"
babe = "Cutiepii_Robot"
telegraph = Telegraph()
data = telegraph.create_account(short_name=babe)
auth_url = data["auth_url"]


@register(pattern="^/t(gm|gt) ?(.*)")
async def telegrap(event):
    optional_title = event.pattern_match.group(2)
    if event.reply_to_msg_id:
        start = datetime.now()
        reply_msg = await event.get_reply_message()
        input_str = event.pattern_match.group(1)
        if input_str == "gm":
            downloaded_file_name = await telethn.download_media(
                reply_msg, TMP_DOWNLOAD_DIRECTORY)
            end = datetime.now()
            if not downloaded_file_name:
                await telethn.send_message(event.chat_id,
                                           "Not Supported Format Media!")
                return
            if downloaded_file_name.endswith((".webp")):
                resize_image(downloaded_file_name)
            try:
                start = datetime.now()
                media_urls = upload_file(downloaded_file_name)
            except exceptions.TelegraphException as exc:
                await event.reply(f"ERROR: {str(exc)}")
                os.remove(downloaded_file_name)
            else:
                end = datetime.now()
                os.remove(downloaded_file_name)
                await telethn.send_message(
                    event.chat_id,
                    "Your telegraph is complete uploaded!",
                    buttons=[[
                        types.KeyboardButtonUrl(
                            "➡ View Telegraph",
                            f"https://telegra.ph{media_urls[0]}",
                        )
                    ]],
                )

        elif input_str == "gt":
            user_object = await telethn.get_entity(reply_msg.sender_id)
            title_of_page = user_object.first_name  # + " " + user_object.last_name
            # apparently, all Users do not have last_name field
            if optional_title:
                title_of_page = optional_title
            page_content = reply_msg.message
            if reply_msg.media:
                if page_content != "":
                    title_of_page = page_content
                else:
                    await telethn.send_message(event.chat_id,
                                               "Not Supported Format Text!")
                downloaded_file_name = await telethn.download_media(
                    reply_msg, TMP_DOWNLOAD_DIRECTORY)
                m_list = None
                with open(downloaded_file_name, "rb") as fd:
                    m_list = fd.readlines()
                for m in m_list:
                    page_content += m.decode("UTF-8") + "\n"
                os.remove(downloaded_file_name)
            page_content = page_content.replace("\n", "<br>")
            end = datetime.now()
            await telethn.send_message(
                event.chat_id,
                "Your telegraph is complete uploaded!",
                buttons=[[
                    types.KeyboardButtonUrl(
                        "➡ View Telegraph",
                        f"https://telegra.ph{media_urls[0]}",
                    )
                ]],
            )

    else:
        await event.reply(
            "Reply to a message to get a permanent telegra.ph link.")


def resize_image(image):
    im = Image.open(image)
    im.save(image, "PNG")


__mod_name__ = "Telegraph"
