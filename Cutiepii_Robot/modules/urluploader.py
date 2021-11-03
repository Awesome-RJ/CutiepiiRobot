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
import time
import aiohttp

from Cutiepii_Robot.utils.pluginhelpers import humanbytes, time_formatter

from Cutiepii_Robot import BOT_USERNAME


async def download_file(url, file_name, message, start_time, bot):
    async with aiohttp.ClientSession() as session:
        time.time()
        await download_coroutine(session, url, file_name, message, start_time, bot)
    return file_name


async def download_coroutine(session, url, file_name, event, start, bot):

    CHUNK_SIZE = 1024 * 6  # 2341
    downloaded = 0
    display_message = ""
    async with session.get(url) as response:
        total_length = int(response.headers["Content-Length"])
        content_type = response.headers["Content-Type"]
        if "text" in content_type and total_length < 500:
            return await response.release()
        await event.edit(
            """**Initiating Download**
**URL:** {}
**File Name:** {}
**File Size:** {}
**© @Cutiepii_Robot**""".format(
                url,
                os.path.basename(file_name).replace("%20", " "),
                humanbytes(total_length),
            ),
            parse_mode="md",
        )
        with open(file_name, "wb") as f_handle:
            while True:
                chunk = await response.content.read(CHUNK_SIZE)
                if not chunk:
                    break
                f_handle.write(chunk)
                downloaded += CHUNK_SIZE
                now = time.time()
                diff = now - start
                if round(diff % 10.00) == 0:  # downloaded == total_length:
                    percentage = downloaded * 100 / total_length
                    speed = downloaded / diff
                    elapsed_time = round(diff) * 1000
                    time_to_completion = (
                        round((total_length - downloaded) / speed) * 1000
                    )
                    estimated_total_time = elapsed_time + time_to_completion
                    try:
                        total_length = max(total_length, downloaded)
                        current_message = """Downloading : {}%
URL: {}
File Name: {}
File Size: {}
Downloaded: {}
ETA: {}""".format(
                            "%.2f" % (percentage),
                            url,
                            file_name.split("/")[-1],
                            humanbytes(total_length),
                            humanbytes(downloaded),
                            time_formatter(estimated_total_time),
                        )
                        if current_message not in [display_message, "empty"]:
                            print(current_message)
                            await event.edit(current_message, parse_mode="html")

                            display_message = current_message
                    except Exception as e:
                        print("Error", e)
                        # logger.info(str(e))
        return await response.release()
