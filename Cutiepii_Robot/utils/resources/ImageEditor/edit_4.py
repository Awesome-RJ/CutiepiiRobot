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

import io
import os
import shutil

import cv2
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageOps

from Cutiepii_Robot import REM_BG_API_KEY, LOGGER


async def rotate_90(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "rotate_90.jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            a = await client.download_media(message=message.reply_to_message,
                                            file_name=download_location)
            await msg.edit("Processing Image...")
            src = cv2.imread(a)
            image = cv2.rotate(src, cv2.cv2.ROTATE_90_CLOCKWISE)
            cv2.imwrite(edit_img_loc, image)
            await message.reply_chat_action("upload_photo")
            await message.reply_to_message.reply_photo(edit_img_loc,
                                                       quote=True)
            await msg.delete()
        else:
            await message.reply_text("Why did you delete that??")
        try:
            shutil.rmtree(f"./DOWNLOADS/{userid}")
        except Exception:
            pass
    except Exception as e:
        LOGGER.debug("rotate_90-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def rotate_180(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "rotate_180.jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            a = await client.download_media(message=message.reply_to_message,
                                            file_name=download_location)
            await msg.edit("Processing Image...")
            src = cv2.imread(a)
            image = cv2.rotate(src, cv2.ROTATE_180)
            cv2.imwrite(edit_img_loc, image)
            await message.reply_chat_action("upload_photo")
            await message.reply_to_message.reply_photo(edit_img_loc,
                                                       quote=True)
            await msg.delete()
        else:
            await message.reply_text("Why did you delete that??")
        try:
            shutil.rmtree(f"./DOWNLOADS/{userid}")
        except Exception:
            pass
    except Exception as e:
        LOGGER.debug("rotate_180-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def rotate_270(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "rotate_270.jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            a = await client.download_media(message=message.reply_to_message,
                                            file_name=download_location)
            await msg.edit("Processing Image...")
            src = cv2.imread(a)
            image = cv2.rotate(src, cv2.ROTATE_90_COUNTERCLOCKWISE)
            cv2.imwrite(edit_img_loc, image)
            await message.reply_chat_action("upload_photo")
            await message.reply_to_message.reply_photo(edit_img_loc,
                                                       quote=True)
            await msg.delete()
        else:
            await message.reply_text("Why did you delete that??")
        try:
            shutil.rmtree(f"./DOWNLOADS/{userid}")
        except Exception:
            pass
    except Exception as e:
        LOGGER.debug("rotate_270-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


def resize_photo(photo: str, userid: str) -> io.BytesIO:
    image = Image.open(photo)
    maxsize = 512
    scale = maxsize / max(image.width, image.height)
    new_size = (int(image.width * scale), int(image.height * scale))
    image = image.resize(new_size, Image.LANCZOS)
    resized_photo = io.BytesIO()
    resized_photo.name = "./DOWNLOADS" + "/" + userid + "resized.png"
    image.save(resized_photo, "PNG")
    return resized_photo


async def round_sticker(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            a = await client.download_media(message=message.reply_to_message,
                                            file_name=download_location)
            await msg.edit("Processing Image...")
            resized = resize_photo(a, userid)
            img = Image.open(resized).convert("RGB")
            npImage = np.array(img)
            h, w = img.size
            alpha = Image.new("L", img.size, 0)
            draw = ImageDraw.Draw(alpha)
            draw.pieslice([0, 0, h, w], 0, 360, fill=255)
            npAlpha = np.array(alpha)
            npImage = np.dstack((npImage, npAlpha))
            edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "rounded.webp"
            Image.fromarray(npImage).save(edit_img_loc)
            await message.reply_chat_action("upload_photo")
            await message.reply_to_message.reply_sticker(edit_img_loc,
                                                         quote=True)
            await msg.delete()
        else:
            await message.reply_text("Why did you delete that??")
        try:
            shutil.rmtree(f"./DOWNLOADS/{userid}")
        except Exception:
            pass
    except Exception as e:
        LOGGER.debug("round_sticker-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def inverted(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            a = await client.download_media(message=message.reply_to_message,
                                            file_name=download_location)
            await msg.edit("Processing Image...")
            image = Image.open(a)
            inverted_image = ImageOps.invert(image)
            edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "inverted.png"
            inverted_image.save(edit_img_loc)
            await message.reply_chat_action("upload_photo")
            await message.reply_to_message.reply_photo(edit_img_loc,
                                                       quote=True)
            await msg.delete()
        else:
            await message.reply_text("Why did you delete that??")
        try:
            shutil.rmtree(f"./DOWNLOADS/{userid}")
        except Exception:
            pass
    except Exception as e:
        LOGGER.debug("inverted-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def removebg_plain(client: Client, message: Message):
    try:
        if REM_BG_API_KEY != "":
            userid = str(chat_id)
            if not os.path.isdir(f"./DOWNLOADS/{userid}"):
                os.makedirs(f"./DOWNLOADS/{userid}")
            download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
            edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "nobgplain.png"
            if not message.reply_to_message.empty:
                msg = await message.reply_to_message.reply_text(
                    "Downloading image", quote=True)
                await client.download_media(message=message.reply_to_message,
                                            file_name=download_location)
                await msg.edit("Processing Image...")

                response = requests.post(
                    "https://api.remove.bg/v1.0/removebg",
                    files={"image_file": open(download_location, "rb")},
                    data={"size": "auto"},
                    headers={"X-Api-Key": REM_BG_API_KEY},
                )
                if response.status_code == 200:
                    with open(f"{edit_img_loc}", "wb") as out:
                        out.write(response.content)
                else:
                    await message.reply_to_message.reply_text(
                        "Check if your api is correct", quote=True)
                    return

                await message.reply_chat_action("upload_document")
                await message.reply_to_message.reply_document(edit_img_loc,
                                                              quote=True)
                await msg.delete()
            else:
                await message.reply_text("Why did you delete that??")
            try:
                shutil.rmtree(f"./DOWNLOADS/{userid}")
            except Exception:
                pass
        else:
            await message.reply_to_message.reply_text(
                "Get the api from https://www.remove.bg/b/background-removal-api and add in Config Var",
                quote=True,
                disable_web_page_preview=True,
            )
    except Exception as e:
        LOGGER.debug("removebg_plain-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def removebg_white(client: Client, message: Message):
    try:
        if REM_BG_API_KEY != "":
            userid = str(chat_id)
            if not os.path.isdir(f"./DOWNLOADS/{userid}"):
                os.makedirs(f"./DOWNLOADS/{userid}")
            download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
            edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "nobgwhite.png"
            if not message.reply_to_message.empty:
                msg = await message.reply_to_message.reply_text(
                    "Downloading image", quote=True)
                await client.download_media(message=message.reply_to_message,
                                            file_name=download_location)
                await msg.edit("Processing Image...")

                response = requests.post(
                    "https://api.remove.bg/v1.0/removebg",
                    files={"image_file": open(download_location, "rb")},
                    data={"size": "auto"},
                    headers={"X-Api-Key": REM_BG_API_KEY},
                )
                if response.status_code == 200:
                    with open(f"{edit_img_loc}", "wb") as out:
                        out.write(response.content)
                else:
                    await message.reply_to_message.reply_text(
                        "Check if your api is correct", quote=True)
                    return

                await message.reply_chat_action("upload_photo")
                await message.reply_to_message.reply_photo(edit_img_loc,
                                                           quote=True)
                await msg.delete()
            else:
                await message.reply_text("Why did you delete that??")
            try:
                shutil.rmtree(f"./DOWNLOADS/{userid}")
            except Exception:
                pass
        else:
            await message.reply_to_message.reply_text(
                "Get the api from https://www.remove.bg/b/background-removal-api and add in Config Var",
                quote=True,
                disable_web_page_preview=True,
            )
    except Exception as e:
        LOGGER.debug("removebg_white-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def removebg_sticker(client: Client, message: Message):
    try:
        if REM_BG_API_KEY != "":
            userid = str(chat_id)
            if not os.path.isdir(f"./DOWNLOADS/{userid}"):
                os.makedirs(f"./DOWNLOADS/{userid}")
            download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
            edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "nobgsticker.webp"
            if not message.reply_to_message.empty:
                msg = await message.reply_to_message.reply_text(
                    "Downloading image", quote=True)
                await client.download_media(message=message.reply_to_message,
                                            file_name=download_location)
                await msg.edit("Processing Image...")

                response = requests.post(
                    "https://api.remove.bg/v1.0/removebg",
                    files={"image_file": open(download_location, "rb")},
                    data={"size": "auto"},
                    headers={"X-Api-Key": REM_BG_API_KEY},
                )
                if response.status_code == 200:
                    with open(f"{edit_img_loc}", "wb") as out:
                        out.write(response.content)
                else:
                    await message.reply_to_message.reply_text(
                        "Check if your api is correct", quote=True)
                    return

                await message.reply_chat_action("upload_photo")
                await message.reply_to_message.reply_sticker(edit_img_loc,
                                                             quote=True)
                await msg.delete()
            else:
                await message.reply_text("Why did you delete that??")
            try:
                shutil.rmtree(f"./DOWNLOADS/{userid}")
            except Exception:
                pass
        else:
            await message.reply_to_message.reply_text(
                "Get the api from https://www.remove.bg/b/background-removal-api and add in Config Var",
                quote=True,
                disable_web_page_preview=True,
            )
    except Exception as e:
        LOGGER.debug("removebg_sticker-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return
