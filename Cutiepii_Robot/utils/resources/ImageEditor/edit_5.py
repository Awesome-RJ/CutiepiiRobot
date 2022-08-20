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

import asyncio
import os
import shutil

from Cutiepii_Robot import LOGGER

async def normalglitch_1(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "normalglitch_1.jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            await client.download_media(message=message.reply_to_message,
                                        file_name=download_location)
            await msg.edit("Processing Image...")
            cd = [
                "glitch_this", "-c", "-o", edit_img_loc, download_location, "1"
            ]
            process = await asyncio.create_subprocess_exec(
                *cd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            await process.communicate()
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
        LOGGER.debug("normalglitch_1-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def normalglitch_2(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "normalglitch_2.jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            await client.download_media(message=message.reply_to_message,
                                        file_name=download_location)
            await msg.edit("Processing Image...")
            cd = [
                "glitch_this", "-c", "-o", edit_img_loc, download_location, "2"
            ]
            process = await asyncio.create_subprocess_exec(
                *cd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            await process.communicate()
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
        LOGGER.debug("normalglitch_2-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def normalglitch_3(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "normalglitch_3.jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            await client.download_media(message=message.reply_to_message,
                                        file_name=download_location)
            await msg.edit("Processing Image...")
            cd = [
                "glitch_this", "-c", "-o", edit_img_loc, download_location, "3"
            ]
            process = await asyncio.create_subprocess_exec(
                *cd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            await process.communicate()
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
        LOGGER.debug("normalglitch_3-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def normalglitch_4(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "normalglitch_4.jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            await client.download_media(message=message.reply_to_message,
                                        file_name=download_location)
            await msg.edit("Processing Image...")
            cd = [
                "glitch_this", "-c", "-o", edit_img_loc, download_location, "4"
            ]
            process = await asyncio.create_subprocess_exec(
                *cd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            await process.communicate()
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
        LOGGER.debug("normalglitch_4-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def normalglitch_5(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "normalglitch_5.jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            await client.download_media(message=message.reply_to_message,
                                        file_name=download_location)
            await msg.edit("Processing Image...")
            cd = [
                "glitch_this", "-c", "-o", edit_img_loc, download_location, "5"
            ]
            process = await asyncio.create_subprocess_exec(
                *cd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            await process.communicate()
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
        LOGGER.debug("normalglitch_5-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def scanlineglitch_1(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "scanlineglitch_1.jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            await client.download_media(message=message.reply_to_message,
                                        file_name=download_location)
            await msg.edit("Processing Image...")
            cd = [
                "glitch_this", "-c", "-s", "-o", edit_img_loc,
                download_location, "1"
            ]
            process = await asyncio.create_subprocess_exec(
                *cd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            await process.communicate()
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
        LOGGER.debug("scanlineglitch_1-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def scanlineglitch_2(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "scanlineglitch_2.jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            await client.download_media(message=message.reply_to_message,
                                        file_name=download_location)
            await msg.edit("Processing Image...")
            cd = [
                "glitch_this", "-c", "-s", "-o", edit_img_loc,
                download_location, "2"
            ]
            process = await asyncio.create_subprocess_exec(
                *cd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            await process.communicate()
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
        LOGGER.debug("scanlineglitch_2-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def scanlineglitch_3(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "scanlineglitch_3.jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            await client.download_media(message=message.reply_to_message,
                                        file_name=download_location)
            await msg.edit("Processing Image...")
            cd = [
                "glitch_this", "-c", "-s", "-o", edit_img_loc,
                download_location, "3"
            ]
            process = await asyncio.create_subprocess_exec(
                *cd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            await process.communicate()
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
        LOGGER.debug("scanlineglitch_3-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def scanlineglitch_4(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "scanlineglitch_4.jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            await client.download_media(message=message.reply_to_message,
                                        file_name=download_location)
            await msg.edit("Processing Image...")
            cd = [
                "glitch_this", "-c", "-s", "-o", edit_img_loc,
                download_location, "4"
            ]
            process = await asyncio.create_subprocess_exec(
                *cd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            await process.communicate()
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
        LOGGER.debug("scanlineglitch_4-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return


async def scanlineglitch_5(client: Client, message: Message):
    try:
        userid = str(chat_id)
        if not os.path.isdir(f"./DOWNLOADS/{userid}"):
            os.makedirs(f"./DOWNLOADS/{userid}")
        download_location = "./DOWNLOADS" + "/" + userid + "/" + userid + ".jpg"
        edit_img_loc = "./DOWNLOADS" + "/" + userid + "/" + "scanlineglitch_5.jpg"
        if not message.reply_to_message.empty:
            msg = await message.reply_to_message.reply_text(
                "Downloading image", quote=True)
            await client.download_media(message=message.reply_to_message,
                                        file_name=download_location)
            await msg.edit("Processing Image...")
            cd = [
                "glitch_this", "-c", "-s", "-o", edit_img_loc,
                download_location, "5"
            ]
            process = await asyncio.create_subprocess_exec(
                *cd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            await process.communicate()
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
        LOGGER.debug("scanlineglitch_5-error - " + str(e))
        if "USER_IS_BLOCKED" in str(e):
            return
        try:
            await message.reply_to_message.reply_text("Something went wrong!",
                                                      quote=True)
        except Exception:
            return
