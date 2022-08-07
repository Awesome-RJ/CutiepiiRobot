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

import json
import requests

from telethon import types
from telethon.tl import functions

from Cutiepii_Robot.events import register, telethn


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


@register(pattern=r"^/phone (.*)")
async def phone(event):
    if (event.is_group and not await is_register_admin(
            event.input_chat, event.message.sender_id)):
        await event.reply("☎️ You are not admin 🚶‍♀️")
        return
    information = event.pattern_match.group(1)
    number = information
    key = "fe65b94e78fc2e3234c1c6ed1b771abd"
    api = ("http://apilayer.net/api/validate?access_key=" + key + "&number=" +
           number + "&country_code=&format=1")
    output = requests.get(api)
    content = output.text
    obj = json.loads(content)
    country_code = obj["country_code"]
    country_name = obj["country_name"]
    location = obj["location"]
    carrier = obj["carrier"]
    line_type = obj["line_type"]
    validornot = obj["valid"]
    aa = f"Valid: {str(validornot)}"
    a = f"Phone number: {str(number)}"
    b = f"Country: {str(country_code)}"
    c = f"Country Name: {str(country_name)}"
    d = f"Location: {str(location)}"
    e = f"Carrier: {str(carrier)}"
    f = f"Device: {str(line_type)}"
    g = f"{aa}\n{a}\n{b}\n{c}\n{d}\n{e}\n{f}"
    await event.reply(g)
