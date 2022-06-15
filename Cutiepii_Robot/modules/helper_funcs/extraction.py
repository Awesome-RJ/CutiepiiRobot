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

from typing import List, Optional, Tuple

from telegram import Message, MessageEntity
from telegram.error import BadRequest

from Cutiepii_Robot import LOGGER
from Cutiepii_Robot.modules.users import get_user_id


def id_from_reply(message):
    prev_message = message.reply_to_message
    if not prev_message:
        return None, None
    user_id = prev_message.from_user.id
    res = message.text.split(None, 1)
    if prev_message.sender_chat:
        user_id = prev_message.sender_chat.id
    if len(res) < 2:
        return user_id, ""
    return user_id, res[1]


async def extract_user(message: Message, args: List[str]) -> Optional[int]:
    return asyncio.get_running_loop().run_until_complete(extract_user_and_text(message, args)[0])


async def extract_user_and_text(
    message: Message, args: List[str]
) -> Tuple[Optional[int], Optional[str]]:
    prev_message = message.reply_to_message
    split_text = message.text.split(None, 1)

    if len(split_text) < 2:
        return id_from_reply(message)  # only option possible

    text_to_parse = split_text[1]

    text = ""

    entities = list(message.parse_entities([MessageEntity.TEXT_MENTION]))
    ent = entities[0] if entities else None
    # if entity offset matches (command end/text start) then all good
    if entities and ent and ent.offset == len(message.text) - len(text_to_parse):
        ent = entities[0]
        user_id = ent.user.id
        text = message.text[ent.offset + ent.length:]

    elif len(args) >= 1 and args[0][0] == "@":
        user = args[0]
        user_id = await get_user_id(user)
        if not user_id:
            await message.reply_text(
                "No idea who this user is. You'll be able to interact with them if "
                "you reply to that person's message instead, or forward one of that user's messages."
            )
            return None, None
        res = await message.text.split(None, 2)
        if len(res) >= 3:
            text = res[2]

    elif len(args) >= 1 and args[0].lstrip("-").isdigit():
        user_id = int(args[0])
        res = await message.text.split(None, 2)
        if len(res) >= 3:
            text = res[2]

    elif prev_message:
        user_id, text = id_from_reply(message)

    else:
        return None, None

    try:
        await message.bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message in ("User_id_invalid", "Chat not found"):
            await message.reply_text(
                "I don't seem to have interacted with this user before - please forward a message from "
                "them to give me control! (like a voodoo doll, I need a piece of them to be able "
                "to execute certain commands...)"
            )
        else:
            LOGGER.exception("Exception %s on user %s", excp.message, user_id)

        return None, None

    return user_id, text


def extract_text(message) -> str:
    return (
        message.text
        or message.caption
        or (message.sticker.emoji if message.sticker else None)
    )


async def extract_unt_fedban(
    message: Message, args: List[str]
) -> Tuple[Optional[int], Optional[str]]:  # sourcery no-metrics
    prev_message = message.reply_to_message
    split_text = message.text.split(None, 1)

    if len(split_text) < 2:
        return id_from_reply(message)  # only option possible

    text_to_parse = split_text[1]

    text = ""

    entities = list(message.parse_entities([MessageEntity.TEXT_MENTION]))
    ent = entities[0] if entities else None
    # if entity offset matches (command end/text start) then all good
    if entities and ent and ent.offset == len(message.text) - len(text_to_parse):
        ent = entities[0]
        user_id = ent.user.id
        text = message.text[ent.offset + ent.length:]

    elif len(args) >= 1 and args[0][0] == "@":
        user = args[0]
        user_id = await get_user_id(user)
        if not user_id and not isinstance(user_id, int):
            await message.reply_text(
                "I don't have users on my DB.You will be able to interact with them if "
                "you reply to the person's message, or forward one of the user's message"
            )
            return None, None
        res = await message.text.split(None, 2)
        if len(res) >= 3:
            text = res[2]

    elif len(args) >= 1 and args[0].lstrip("-").isdigit():
        user_id = int(args[0])
        res = await message.text.split(None, 2)
        if len(res) >= 3:
            text = res[2]

    elif prev_message:
        user_id, text = id_from_reply(message)

    else:
        return None, None

    try:
        await message.bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message in ("User_id_invalid", "Chat not found") and not isinstance(
            user_id, int
        ):
            await message.reply_text(
                "I seem to have never interacted with this user "
                "Previously - please forward a message from them to give me control! "
                "(Like a voodoo doll, I need a piece to be able to "
                "run a certain command ...)"
            )
            return None, None
        if excp.message != "Chat not found":
            LOGGER.exception("Exception %s on user %s", excp.message, user_id)
            return None, None
        if not isinstance(user_id, int):
            return None, None

    return user_id, text


def extract_user_fban(message: Message, args: List[str]) -> Optional[int]:
    return extract_unt_fedban(message, args)[0]
