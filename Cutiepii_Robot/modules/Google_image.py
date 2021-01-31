import os
import shutil
import glob
from re import findall
from bing_image_downloader import downloader
from telethon import *
from telethon.tl import functions
from telethon.tl import types
from telethon.tl.types import *

from Cutiepii_Robot import oko
from Cutiepii_Robot.event import register


async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):

        return isinstance(
            (await oko(functions.channels.GetParticipantRequest(chat, user))).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator)
        )
    elif isinstance(chat, types.InputPeerChat):

        ui = await client.get_peer_id(user)
        ps = (await client(functions.messages.GetFullChatRequest(chat.chat_id))) \
            .full_chat.participants.participants
        return isinstance(
            next((p for p in ps if p.user_id == ui), None),
            (types.ChatParticipantAdmin, types.ChatParticipantCreator)
        )
    else:
        return None


@register(pattern="^/img (.*)")
async def img_sampler(event):
     if event.fwd_from:
        return
     if event.is_group:
       if not (await is_register_admin(event.input_chat, event.message.sender_id)):
          await event.reply("😜 Hai.. You are not admin..🤭 You can't use this command.. But you can use in my pm🙈")
          return
     query = event.pattern_match.group(1)
     jit = f'"{query}"'
     downloader.download(jit, limit=5, output_dir='store', adult_filter_off=False, force_replace=False, timeout=60)
     os.chdir(f'./store/"{query}"')
     types = ('*.png', '*.jpeg', '*.jpg') # the tuple of file types
     filesgrabbed = []
     for files in types:
         filesgrabbed.extend(glob.glob(files))
     await event.client.send_file(event.chat_id, filesgrabbed, reply_to=event.id)
     os.remove(filesgrabbed)
     os.chdir('./')

    
