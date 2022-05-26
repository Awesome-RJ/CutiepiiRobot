"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2022, Yūki • Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

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
import datetime
import os
import time
import traceback

import aiohttp
from telethon import events

from Cutiepii_Robot import telethn, TEMP_DOWNLOAD_DIRECTORY, SUPPORT_CHAT, CUTIEPII_PTB
from Cutiepii_Robot.modules.urluploader import download_file
from Cutiepii_Robot.utils.pluginhelpers import humanbytes, progress

def get_date_in_two_weeks():
    """
    get maximum date of storage for file
    :return: date in two weeks
    """
    today = datetime.datetime.now()
    date_in_two_weeks = today + datetime.timedelta(days=14)
    return date_in_two_weeks.date()


async def send_to_transfersh_async(file):

    size = os.path.getsize(file)
    size_of_file = humanbytes(size)
    final_date = get_date_in_two_weeks()
    file_name = os.path.basename(file)

    print("\nUploading file: {} (size of the file: {})".format(file_name, size_of_file))
    url = "https://transfer.sh/"

    with open(file, "rb") as f:
        async with aiohttp.ClientSession() as session, session.post(url, data={str(file): f}) as response:
            download_link = await response.text()

    print(
        "Link to download file(will be saved till {}):\n{}".format(
            final_date, download_link
        )
    )
    return download_link, final_date, size_of_file


async def send_to_tmp_async(file):
    url = "https://tmp.ninja/api.php?d=upload-tool"

    with open(file, "rb") as f:
        async with aiohttp.ClientSession() as session, session.post(url, data={"file": f}) as response:
            download_link = await response.text()

    return download_link


@telethn.on(events.NewMessage(pattern="/transfersh"))
async def tsh(event):
    if event.reply_to_msg_id:
        start = time.time()
        url = await event.get_reply_message()
        ilk = await event.respond("Downloading...")
        try:
            file_path = await url.download_media(
                progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                    progress(d, t, ilk, start, "Downloading...")
                )
            )
        except Exception as e:
            traceback.print_exc()
            print(e)
            await event.respond(f"Downloading Failed\n\n**Error:** {e}")

        await ilk.delete()

        try:
            orta = await event.respond("Uploading to TransferSh...")
            download_link, final_date, size = await send_to_transfersh_async(file_path)

            str(time.time() - start)
            await orta.edit(
                f"File Successfully Uploaded to TransferSh.\n\nLink 👉 {download_link}\nExpired Date 👉 {final_date}\n\nUploaded by *@{SUPPORT_CHAT}*"
            )
        except Exception as e:
            traceback.print_exc()
            print(e)
            await event.respond(f"Uploading Failed\n\n**Error:** {e}")

    raise events.StopPropagation


@telethn.on(events.NewMessage(pattern="/tmpninja"))
async def tmp(event):
    if event.reply_to_msg_id:
        start = time.time()
        url = await event.get_reply_message()
        ilk = await event.respond("Downloading...")
        try:
            file_path = await url.download_media(
                progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                    progress(d, t, ilk, start, "Downloading...")
                )
            )
        except Exception as e:
            traceback.print_exc()
            print(e)
            await event.respond(f"Downloading Failed\n\n**Error:** {e}")

        await ilk.delete()

        try:
            orta = await event.respond("Uploading to TmpNinja...")
            download_link = await send_to_tmp_async(file_path)

            str(time.time() - start)
            await orta.edit(
                f"File Successfully Uploaded to TmpNinja.\n\nLink 👉 {download_link}\n\nUploaded by *@{CUTIEPII_PTB.bot.username}*"
            )
        except Exception as e:
            traceback.print_exc()
            print(e)
            await event.respond(f"Uploading Failed\n\n**Error:** {e}")

    raise events.StopPropagation


@telethn.on(events.NewMessage(pattern="/up"))
async def up(event):
    if event.reply_to_msg_id:
        start = time.time()
        url = await event.get_reply_message()
        ilk = await event.respond("Downloading...")

        try:
            filename = os.path.join(TEMP_DOWNLOAD_DIRECTORY, os.path.basename(url.text))
            await download_file(url.text, filename, ilk, start, telethn)
        except Exception as e:
            print(e)
            await event.respond(f"Downloading Failed\n\n**Error:** {e}")

        await ilk.delete()

        try:
            orta = await event.respond("Uploading to Telegram...")

            dosya = await telethn.upload_file(
                filename,
                progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                    progress(d, t, orta, start, "Uploading to Telegram...")
                ),
            )

            str(time.time() - start)
            await telethn.send_file(
                event.chat.id,
                dosya,
                force_document=True,
                caption = f"Uploaded By *@{CUTIEPII_PTB.bot.username}*",
            )
        except Exception as e:
            traceback.print_exc()

            print(e)
            await event.respond(f"Uploading Failed\n\n**Error:** {e}")

        await orta.delete()

    raise events.StopPropagation


def main():
    if not os.path.isdir(TEMP_DOWNLOAD_DIRECTORY):
        os.mkdir(TEMP_DOWNLOAD_DIRECTORY)


if __name__ == "__main__":
    main()
