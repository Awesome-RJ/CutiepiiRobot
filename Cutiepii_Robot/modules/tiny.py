
"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

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
import cv2

from PIL import Image
from Cutiepii_Robot.modules.helper_funcs.decorators import register
from Cutiepii_Robot import telethn


@register(pattern="tiny")
async def tiny(event):
    reply = await event.get_reply_message()
    if not (reply and (reply.media)):
        await event.reply("`Please reply to a sticker`")
        return
    kontol = await event.reply("`Processing tiny...`")
    ik = await telethn.download_media(reply)
    if not ik:
        await kontol.edit("`Failed to download media.`")
        return

    im1 = Image.open("Cutiepii_Robot/resources/ken.png")
    fil_to_remove = []
    file = None
    try:
        if ik.endswith(".tgs"):
            await telethn.download_media(reply, "ken.tgs")
            fil_to_remove.append("ken.tgs")
            os.system("lottie_convert ken.tgs json.json")
            if os.path.exists("json.json"):
                fil_to_remove.append("json.json")
                with open("json.json", "r") as f:
                    jsn = f.read()
                jsn = jsn.replace("512", "2000")
                with open("json.json", "w") as f:
                    f.write(jsn)
                os.system("lottie_convert json.json ken.tgs")
                file = "ken.tgs"
            else:
                await event.reply("Failed to convert animated sticker.")
                return
        elif ik.endswith((".gif", ".mp4", ".webm")):
            iik = cv2.VideoCapture(ik)
            _, busy = iik.read()
            cv2.imwrite("i.png", busy)
            fil = "i.png"
            fil_to_remove.append(fil)
            im = Image.open(fil)
            z, d = im.size
            if z == d:
                xxx, yyy = 200, 200
            else:
                t = z + d
                a = z / t
                b = d / t
                aa = (a * 100) - 50
                bb = (b * 100) - 50
                xxx = 200 + 5 * aa
                yyy = 200 + 5 * bb
            k = im.resize((int(xxx), int(yyy)))
            k.save("k.png", format="PNG", optimize=True)
            fil_to_remove.append("k.png")
            im2 = Image.open("k.png")
            back_im = im1.copy()
            back_im.paste(im2, (150, 0))
            back_im.save("o.webp", "WEBP", quality=95)
            file = "o.webp"
        else:
            im = Image.open(ik)
            z, d = im.size
            if z == d:
                xxx, yyy = 200, 200
            else:
                t = z + d
                a = z / t
                b = d / t
                aa = (a * 100) - 50
                bb = (b * 100) - 50
                xxx = 200 + 5 * aa
                yyy = 200 + 5 * bb
            k = im.resize((int(xxx), int(yyy)))
            k.save("k.png", format="PNG", optimize=True)
            fil_to_remove.append("k.png")
            im2 = Image.open("k.png")
            back_im = im1.copy()
            back_im.paste(im2, (150, 0))
            back_im.save("o.webp", "WEBP", quality=95)
            file = "o.webp"

        if file:
            await telethn.send_file(event.chat_id, file, reply_to=event.reply_to_msg_id)
            if file not in fil_to_remove:
                fil_to_remove.append(file)
    except Exception as e:
        await event.reply(f"An error occurred: {e}")
    finally:
        await kontol.delete()
        for f in fil_to_remove:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass
        if os.path.exists(ik):
            try:
                os.remove(ik)
            except Exception:
                pass
