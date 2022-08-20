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
import shutil
import cv2

from Cutiepii_Robot import LOGGER
from PIL import Image, ImageEnhance, ImageFilter


async def bright(client: Client, message: Message):
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
            brightness = ImageEnhance.Brightness(image)
            edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "brightness.jpg"
            brightness.enhance(1.5).save(edit_img_loc)
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
        LOGGER.debug("bright-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def mix(client: Client, message: Message):
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
            red, green, blue = image.split()
            new_image = Image.merge("RGB", (green, red, blue))
            edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "mix.jpg"
            new_image.save(edit_img_loc)
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
        LOGGER.debug("mix-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def black_white(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "black_white.jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            a = await client.download_media(message=message.reply_to_message,
                                            file_name=download_location)
            await msg.edit("Processing Image...")
            image_file = cv2.imread(a)
            grayImage = cv2.cvtColor(image_file, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(edit_img_loc, grayImage)
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
        LOGGER.debug("black_white-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def normal_blur(client: Client, message: Message):
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
            OriImage = Image.open(a)
            blurImage = OriImage.filter(ImageFilter.BLUR)
            edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "BlurImage.jpg"
            blurImage.save(edit_img_loc)
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
        LOGGER.debug("normal_blur-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def g_blur(client: Client, message: Message):
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
            im1 = Image.open(a)
            im2 = im1.filter(ImageFilter.GaussianBlur(radius=5))
            edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "gaussian_blur.jpg"
            im2.save(edit_img_loc)
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
        LOGGER.debug("g_blur-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def box_blur(client: Client, message: Message):
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
            im1 = Image.open(a)
            im2 = im1.filter(ImageFilter.BoxBlur(0))
            edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "box_blur.jpg"
            im2.save(edit_img_loc)
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
        LOGGER.debug("box_blur-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return
