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

from telethon.errors.rpcerrorlist import YouBlockedUserError
from telethon.tl import functions, types

from Cutiepii_Robot.events import register as Cutiepii
from Cutiepii_Robot import telethn, ubot


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


async def silently_send_message(conv, text):
    await conv.send_message(text)
    response = await conv.get_response()
    await conv.mark_read(message=response)
    return response


@Cutiepii(pattern="^/sg ?(.*)")
async def _(event):

    if event.fwd_from:

        return

    if event.is_group and not await is_register_admin(
        event.input_chat, event.message.sender_id
    ):
        return
    if not event.reply_to_msg_id:

        await event.reply("```Reply to any user message.```")

        return

    reply_message = await event.get_reply_message()

    if not reply_message.text:

        await event.reply("```reply to text message```")

        return

    chat = "Sangmatainfo_bot"
    uid = reply_message.sender_id

    if reply_message.sender.bot:

        await event.edit("```Reply to actual users message.```")

        return

    lol = await event.reply("```Processing```")

    async with ubot.conversation(chat) as conv:

        try:

            # response = conv.wait_event(
            #   events.NewMessage(incoming=True, from_users=1706537835)
            # )

            await silently_send_message(conv, f"/search_id {uid}")

            # response = await response
            responses = await silently_send_message(conv, f"/search_id {uid}")
        except YouBlockedUserError:

            await event.reply("```Please unblock @Sangmatainfo_bot and try again```")

            return
        await lol.edit(f"{responses.text}")
        # await lol.edit(f"{response.message.message}")
