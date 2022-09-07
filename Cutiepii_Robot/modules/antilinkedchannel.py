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
import html
from telegram.error import TelegramError
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import filters

from Cutiepii_Robot import CUTIEPII_PTB
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.helper_funcs.anonymous import user_admin
from Cutiepii_Robot.modules.helper_funcs.chat_status import bot_can_delete, bot_admin
import Cutiepii_Robot.modules.sql.antilinkedchannel_sql as sql


@bot_can_delete
@user_admin
async def set_antilinkedchannel(update: Update,
                                context: CallbackContext) -> None:
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    if len(args) > 0:
        s = args[0].lower()
        if s in ["yes", "on"]:
            sql.enable(chat.id)
            await message.reply_html(
                f"Enabled anti linked channel in {html.escape(chat.title)}")

        elif s in ["off", "no"]:
            sql.disable(chat.id)
            await message.reply_html(
                f"Disabled anti linked channel in {html.escape(chat.title)}")

        else:
            await update.effective_message.reply_text(
                f"Unrecognized arguments {s}")
        return
    message.reply_html(
        f"Linked channel deletion is currently {sql.status(chat.id)} in {html.escape(chat.title)}"
    )


async def eliminate_linked_channel_msg(update: Update):
    message = update.effective_message
    chat = update.effective_chat
    if not sql.status(chat.id):
        return
    try:
        await message.delete()
    except TelegramError:
        return


@bot_admin
@user_admin
async def set_antipinchannel(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    if len(args) > 0:
        s = args[0].lower()
        if s in ["yes", "on"]:
            if sql.status_linked(chat.id):
                sql.disable_linked(chat.id)
                sql.enable_pin(chat.id)
                await message.reply_html(
                    f"Disabled Linked channel deletion and Enabled anti channel pin in {html.escape(chat.title)}"
                )

            else:
                sql.enable_pin(chat.id)
                await message.reply_html(
                    f"Enabled anti channel pin in {html.escape(chat.title)}")

        elif s in ["off", "no"]:
            sql.disable_pin(chat.id)
            await message.reply_html(
                f"Disabled anti channel pin in {html.escape(chat.title)}")

        else:
            await update.effective_message.reply_text(
                f"Unrecognized arguments {s}")
        return
    message.reply_html(
        f"Linked channel message unpin is currently {sql.status_pin(chat.id)} in {html.escape(chat.title)}"
    )


def eliminate_linked_channel_msg(update: Update):
    message = update.effective_message
    chat = update.effective_chat
    if not sql.status_pin(chat.id):
        return
    try:
        message.unpin()
    except TelegramError:
        return


CUTIEPII_PTB.add_handler(
    DisableAbleCommandHandler("antilinkedchan",
                              set_antilinkedchannel,
                              filters=filters.ChatType.GROUPS))
CUTIEPII_PTB.add_handler(
    DisableAbleCommandHandler("antichannelpin",
                              set_antipinchannel,
                              filters=filters.ChatType.GROUPS))
