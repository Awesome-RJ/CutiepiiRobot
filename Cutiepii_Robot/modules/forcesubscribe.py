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

import logging
import time

from pyrogram import filters
from pyrogram.errors import RPCError
from pyrogram.errors.exceptions.bad_request_400 import (
    ChannelPrivate,
    ChatAdminRequired,
    PeerIdInvalid,
    UsernameNotOccupied,
    UserNotParticipant,
)
from pyrogram.types import ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup

from Cutiepii_Robot import BOT_ID, OWNER_ID as SUDO_USERS, pgram, CUTIEPII_PTB
from Cutiepii_Robot.modules.sql import forceSubscribe_sql as sql

logging.basicConfig(level=logging.INFO)

static_data_filter = filters.create(
    lambda _, __, query: query.data == "onUnMuteRequest")


@pgram.on_callback_query(static_data_filter)
def _onUnMuteRequest(client, cb):
    try:
        user_id = cb.from_user.id
        chat_id = cb.message.chat.id
    except:
        return
    if chat_db := sql.fs_settings(chat_id):
        channel = chat_db.channel
        try:
            chat_member = client.get_chat_member(chat_id, user_id)
        except:
            return
        if chat_member.restricted_by:
            if chat_member.restricted_by.id == BOT_ID:
                try:
                    client.get_chat_member(channel, user_id)
                    client.unban_chat_member(chat_id, user_id)
                    cb.message.delete()
                    # if cb.message.reply_to_message.from_user.id == user_id:
                    # cb.message.delete()
                except UserNotParticipant:
                    client.answer_callback_query(
                        cb.id,
                        text=
                        f"❗ Join our @{channel} channel and press 'UnMute Me' button.",
                        show_alert=True,
                    )
                except ChannelPrivate:
                    client.unban_chat_member(chat_id, user_id)
                    cb.message.delete()

            else:
                client.answer_callback_query(
                    cb.id,
                    text=
                    "❗ You have been muted by admins due to some other reason.",
                    show_alert=True,
                )
        elif client.get_chat_member(chat_id, BOT_ID).status != "administrator":
            client.send_message(
                chat_id,
                f"❗ **{cb.from_user.mention} is trying to UnMute himself but i can't unmute him because i am not an admin in this chat add me as admin again.**\n__#Leaving this chat...__",
            )

        else:
            client.answer_callback_query(
                cb.id,
                text="❗ Warning! Don't press the button when you can talk.",
                show_alert=True,
            )


@pgram.on_edited_message(filters.text & ~filters.private, group=1)
def _check_member(client, message):
    chat_id = message.chat.id
    if chat_db := sql.fs_settings(chat_id):
        try:
            user_id = message.from_user.id
        except:
            return
        try:
            if client.get_chat_member(chat_id, user_id).status not in (
                    "administrator",
                    "creator",
            ):
                channel = chat_db.channel
                try:
                    client.get_chat_member(channel, user_id)
                except UserNotParticipant:
                    try:
                        sent_message = message.reply_text(
                            f"Welcome {message.from_user.mention} 🙏 \n **You havent joined our @{channel} Channel yet** 😭 \n \nPlease Join [Our Channel](https://telegram.dog/{channel}) and hit the **UNMUTE ME** Button. \n \n ",
                            disable_web_page_preview=True,
                            reply_markup=InlineKeyboardMarkup([
                                [
                                    InlineKeyboardButton(
                                        "Join Channel",
                                        url=f"https://telegram.dog/{channel}",
                                    )
                                ],
                                [
                                    InlineKeyboardButton(
                                        "UnMute Me",
                                        callback_data="onUnMuteRequest",
                                    )
                                ],
                            ]),
                        )

                        client.restrict_chat_member(
                            chat_id, user_id,
                            ChatPermissions(can_send_messages=False))
                    except ChatAdminRequired:
                        sent_message.edit(
                            f"❗ **Cutiepii Robot 愛 is not an admin here..**\n__Give me ban permissions and retry.. \n#Ending FSub...__"
                        )
                    except RPCError:
                        return

                except ChatAdminRequired:
                    client.send_message(
                        chat_id,
                        text=
                        f"❗ **I not an admin of @{channel} channel.**\n__Give me admin of that channel and retry.\n#Ending FSub...__",
                    )
                except ChannelPrivate:
                    return
        except:
            return


@pgram.on_message(
    filters.command([
        "forcesubscribe", "forcesub", "forcesub@Cutiepii_Robot",
        "forcesubscribe@Cutiepii_Robot"
    ]) & ~filters.private)
def config(client, message):
    user = client.get_chat_member(message.chat.id, message.from_user.id)
    if user.status == "creator" or user.user.id in SUDO_USERS:
        chat_id = message.chat.id
        if len(message.command) > 1:
            input_str = message.command[1]
            input_str = input_str.replace("@", "")
            if input_str.lower() in ("off", "no", "disable"):
                sql.disapprove(chat_id)
                message.reply_text(
                    "❌ **Force Subscribe is Disabled Successfully.**")
            elif input_str.lower() in ("clear"):
                sent_message = message.reply_text(
                    "**Unmuting all members who are muted by me...**")
                try:
                    for chat_member in client.get_chat_members(
                            message.chat.id, filter="restricted"):
                        if chat_member.restricted_by.id == BOT_ID:
                            client.unban_chat_member(chat_id,
                                                     chat_member.user.id)
                            time.sleep(1)
                    sent_message.edit(
                        "✅ **UnMuted all members who are muted by me.**")
                except ChatAdminRequired:
                    sent_message.edit(
                        "❗ **I am not an admin in this chat.**\n__I can't unmute members because i am not an admin in this chat make me admin with ban user permission.__"
                    )
            else:
                try:
                    client.get_chat_member(input_str, "me")
                    sql.add_channel(chat_id, input_str)
                    message.reply_text(
                        f"✅ **Force Subscribe is Enabled**\n__Force Subscribe is enabled, all the group members have to subscribe this [channel](https://telegram.dog/{input_str}) in order to send messages in this group.__",
                        disable_web_page_preview=True,
                    )
                except UserNotParticipant:
                    message.reply_text(
                        f"❗ **Not an Admin in the Channel**\n__I am not an admin in the [channel](https://telegram.dog/{input_str}). Add me as a admin in order to enable ForceSubscribe.__",
                        disable_web_page_preview=True,
                    )
                except (UsernameNotOccupied, PeerIdInvalid):
                    message.reply_text("❗ **Invalid Channel Username.**")
                except Exception as err:
                    message.reply_text(f"❗ **ERROR:** ```{err}```")
        elif sql.fs_settings(chat_id):
            message.reply_text(
                f"✅ **Force Subscribe is enabled in this chat.**\n__For this [Channel](https://telegram.dog/{sql.fs_settings(chat_id).channel})__",
                disable_web_page_preview=True,
            )
        else:
            message.reply_text(
                "❌ **Force Subscribe is disabled in this chat.**")
    else:
        message.reply_text(
            "❗ **Group Creator Required**\n__You have to be the group creator to do that.__"
        )


__help__ = f"""
*Force Subscribe*:
- Cutiepii Robot 愛 can mute members who are not subscribed your channel until they subscribe
- When enabled I will mute unsubscribed members and show them a unmute button. When they pressed the button I will unmute them

*Setup*
1) First of all add me in the group as admin with ban users permission and in the channel as admin.
Note: Only creator of the group can setup me and i will not allow force subscribe again if not done so.
 
*Commmands*:
➛ /forcesubscribe*:* To get the current settings.
➛ /forcesubscribe <no/off/disable>*:* To turn of ForceSubscribe.
➛ /forcesubscribe <channel username>*:* To turn on and setup the channel.
➛ /forcesubscribe clear*:* To unmute all members who muted by me.
Note: /forcesub is an alias of /forcesubscribe
 
"""
__mod_name__ = "F-Sub"
