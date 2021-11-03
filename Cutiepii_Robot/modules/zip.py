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
import zipfile

from datetime import datetime
from telethon import types
from telethon.tl import functions
from telethon.tl.types import DocumentAttributeVideo
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser


from Cutiepii_Robot import TEMP_DOWNLOAD_DIRECTORY, telethn
from Cutiepii_Robot.events import register


async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):

        return isinstance(
            (
                await telethn(functions.channels.GetParticipantRequest(chat, user))
            ).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerChat):

        ui = await telethn.get_peer_id(user)
        ps = (
            await telethn(functions.messages.GetFullChatRequest(chat.chat_id))
        ).full_chat.participants.participants
        return isinstance(
            next((p for p in ps if p.user_id == ui), None),
            (types.ChatParticipantAdmin, types.ChatParticipantCreator),
        )
    return None


@register(pattern="^/zip")
async def _(event):
    if event.fwd_from:
        return

    if not event.is_reply:
        await event.reply("Reply to a file to compress it.")
        return
    if (
        event.is_group
        and not (await is_register_admin(event.input_chat, event.message.sender_id))
    ):
        await event.reply(
            "Hey, You are not admin. You can't use this command, But you can use in my pm 🙂"
        )
        return
    mone = await event.reply("⏳️ Please wait...")
    if not os.path.isdir(TEMP_DOWNLOAD_DIRECTORY):
        os.makedirs(TEMP_DOWNLOAD_DIRECTORY)
    if event.reply_to_msg_id:
        reply_message = await event.get_reply_message()
        try:
            time.time()
            downloaded_file_name = await event.telethn.download_media(
                reply_message, TEMP_DOWNLOAD_DIRECTORY
            )
            directory_name = downloaded_file_name
        except Exception as e:  # pylint:disable=C0103,W0703
            await mone.reply(str(e))
    zipfile.ZipFile(directory_name + ".zip", "w", zipfile.ZIP_DEFLATED).write(
        directory_name
    )
    await event.telethn.send_file(
        event.chat_id,
        directory_name + ".zip",
        force_document=True,
        allow_cache=False,
        reply_to=event.message.id,
    )
    await mone.delete()


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))
            os.remove(os.path.join(root, file))

extracted = TEMP_DOWNLOAD_DIRECTORY + "extracted/"
thumb_image_path = TEMP_DOWNLOAD_DIRECTORY + "/thumb_image.jpg"
if not os.path.isdir(extracted):
    os.makedirs(extracted)


async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):

        return isinstance(
            (
                await telethn(functions.channels.GetParticipantRequest(chat, user))
            ).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerChat):

        ui = await telethn.get_peer_id(user)
        ps = (
            await telethn(functions.messages.GetFullChatRequest(chat.chat_id))
        ).full_chat.participants.participants
        return isinstance(
            next((p for p in ps if p.user_id == ui), None),
            (types.ChatParticipantAdmin, types.ChatParticipantCreator),
        )
    return None


@register(pattern="^/unzip")
async def _(event):
    if event.fwd_from:
        return

    if not event.is_reply:
        await event.reply("Reply to a zip file.")
        return
    if (
        event.is_group
        and not (await is_register_admin(event.input_chat, event.message.sender_id))
    ):
        await event.reply(
            "Hey, You are not admin. You can't use this command, But you can use in my pm 🙂"
        )
        return

    mone = await event.reply("Processing...")
    if not os.path.isdir(TEMP_DOWNLOAD_DIRECTORY):
        os.makedirs(TEMP_DOWNLOAD_DIRECTORY)
    if event.reply_to_msg_id:
        start = datetime.now()
        reply_message = await event.get_reply_message()
        try:
            time.time()
            downloaded_file_name = await telethn.download_media(
                reply_message, TEMP_DOWNLOAD_DIRECTORY
            )
        except Exception as e:
            await mone.reply(str(e))
        else:
            end = datetime.now()
            (end - start).seconds

        with zipfile.ZipFile(downloaded_file_name, "r") as zip_ref:
            zip_ref.extractall(extracted)
        filename = sorted(get_lst_of_files(extracted, []))
        await mone.edit("Unzipping now 😌")
        for single_file in filename:
            if os.path.exists(single_file):
                caption_rts = os.path.basename(single_file)
                force_document = True
                supports_streaming = False
                document_attributes = []
                if single_file.endswith((".mp4", ".mp3", ".flac", ".webm")):
                    metadata = extractMetadata(createParser(single_file))
                    width = 0
                    height = 0
                    duration = metadata.get("duration").seconds if metadata.has("duration") else 0
                    if os.path.exists(thumb_image_path):
                        metadata = extractMetadata(createParser(thumb_image_path))
                        if metadata.has("width"):
                            width = metadata.get("width")
                        if metadata.has("height"):
                            height = metadata.get("height")
                    document_attributes = [
                        DocumentAttributeVideo(
                            duration=duration,
                            w=width,
                            h=height,
                            round_message=False,
                            supports_streaming=True,
                        )
                    ]
                try:
                    await telethn.send_file(
                        event.chat_id,
                        single_file,
                        force_document=force_document,
                        supports_streaming=supports_streaming,
                        allow_cache=False,
                        reply_to=event.message.id,
                        attributes=document_attributes,
                    )
                except Exception as e:
                    await telethn.send_message(
                        event.chat_id,
                        "{} caused `{}`".format(caption_rts, str(e)),
                        reply_to=event.message.id,
                    )
                    continue
                await mone.delete()
                os.remove(single_file)
        os.remove(downloaded_file_name)


def get_lst_of_files(input_directory, output_lst):
    filesinfolder = os.listdir(input_directory)
    for file_name in filesinfolder:
        current_file_name = os.path.join(input_directory, file_name)
        if os.path.isdir(current_file_name):
            return get_lst_of_files(current_file_name, output_lst)
        output_lst.append(current_file_name)
    return output_lst


__mod_name__ = "Zipper"
