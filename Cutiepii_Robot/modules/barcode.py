import os
import barcode
import urllib.request
from Cutiepii_Robot import *
from Cutiepii_Robot.events import register
from datetime import datetime
from barcode.writer import ImageWriter
from typing import List
from typing import Optional
from telethon import *
from telethon.tl import types, functions

db = mongodb["Cutiepii_Robot_Barcode"]
approved_users = db.approve


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
    return False


@register(pattern="^/barcode ?(.*)")
async def _(event):
    if event.fwd_from:
        return
    approved_userss = approved_users.find({})
    for ch in approved_userss:
        iid = ch["id"]
        userss = ch["user"]
    if event.is_group:
        if await is_register_admin(event.input_chat, event.message.sender_id):
            pass
        elif event.chat_id != iid or event.sender_id != userss:
            return
    start = datetime.now()
    input_str = event.pattern_match.group(1)
    message = "SYNTAX: `.barcode <long text to include>`"
    reply_msg_id = event.message.id
    if input_str:
        message = input_str
    elif event.reply_to_msg_id:
        previous_message = await event.get_reply_message()
        reply_msg_id = previous_message.id
        if previous_message.media:
            downloaded_file_name = await event.client.download_media(
                previous_message,
                Config.TEMP_DOWNLOAD_DIRECTORY,
            )
            m_list = None
            with open(downloaded_file_name, "rb") as fd:
                m_list = fd.readlines()
            message = "".join(m.decode("UTF-8") + "\r\n" for m in m_list)
            os.remove(downloaded_file_name)
        else:
            message = previous_message.message
    else:
        message = "SYNTAX: `.barcode <long text to include>`"
    bar_code_type = "code128"
    try:
        bar_code_mode_f = barcode.get(bar_code_type,
                                      message,
                                      writer=ImageWriter())
        filename = bar_code_mode_f.save(bar_code_type)
        await event.client.send_file(
            event.chat_id,
            filename,
            caption=message,
            reply_to=reply_msg_id,
        )
        os.remove(filename)
    except Exception as e:
        await event.reply(str(e))
        return
    end = datetime.now()
    ms = (end - start).seconds
    await event.reply(f"Created BarCode in {ms} seconds")


file_help = os.path.basename(__file__)
file_help = file_help.replace(".py", "")
file_helpo = file_help.replace("_", " ")

__help__ = """
 - /barcode <text>: makes a barcode out of the text, crop the barcode if you don't want to reveal the text
"""
__mod_name__ = "Barcode"
