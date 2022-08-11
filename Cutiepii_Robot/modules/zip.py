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
            (await
             telethn(functions.channels.GetParticipantRequest(chat, user)
                     )).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerChat):

        ui = await telethn.get_peer_id(user)
        ps = (await telethn(functions.messages.GetFullChatRequest(chat.chat_id)
                            )).full_chat.participants.participants
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
    if (event.is_group and not (await is_register_admin(
            event.input_chat, event.message.sender_id))):
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
                reply_message, TEMP_DOWNLOAD_DIRECTORY)
            directory_name = downloaded_file_name
        except Exception as e:  # pylint:disable=C0103,W0703
            await mone.reply(str(e))
    zipfile.ZipFile(f"{directory_name}.zip", "w",
                    zipfile.ZIP_DEFLATED).write(directory_name)

    await event.telethn.send_file(
        event.chat_id,
        f"{directory_name}.zip",
        force_document=True,
        allow_cache=False,
        reply_to=event.message.id,
    )

    await mone.delete()


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))
            os.remove(os.path.join(root, file))


extracted = f"{TEMP_DOWNLOAD_DIRECTORY}extracted/"
thumb_image_path = f"{TEMP_DOWNLOAD_DIRECTORY}/thumb_image.jpg"
if not os.path.isdir(extracted):
    os.makedirs(extracted)


async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):

        return isinstance(
            (await
             telethn(functions.channels.GetParticipantRequest(chat, user)
                     )).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerChat):

        ui = await telethn.get_peer_id(user)
        ps = (await telethn(functions.messages.GetFullChatRequest(chat.chat_id)
                            )).full_chat.participants.participants
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
    if (event.is_group and not (await is_register_admin(
            event.input_chat, event.message.sender_id))):
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
                reply_message, TEMP_DOWNLOAD_DIRECTORY)
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
                    duration = metadata.get(
                        "duration").seconds if metadata.has("duration") else 0
                    if os.path.exists(thumb_image_path):
                        metadata = extractMetadata(
                            createParser(thumb_image_path))
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
                        f"{caption_rts} caused `{str(e)}`",
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
