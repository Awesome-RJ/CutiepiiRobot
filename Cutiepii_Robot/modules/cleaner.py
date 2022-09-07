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

from Cutiepii_Robot import ALLOW_EXCL, CustomCommandHandler, CUTIEPII_PTB
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.helper_funcs.chat_status import (
    bot_can_delete,
    connection_status,
    dev_plus,
)
from Cutiepii_Robot.modules.helper_funcs.anonymous import user_admin
from Cutiepii_Robot.modules.sql import cleaner_sql as sql
from telegram import Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    filters,
    MessageHandler,
)
from telegram.constants import ParseMode

CMD_STARTERS = ("/", "!") if ALLOW_EXCL else "/"
BLUE_TEXT_CLEAN_GROUP = 13
CommandHandlerList = (CommandHandler, CustomCommandHandler,
                      DisableAbleCommandHandler)
command_list = [
    "cleanblue",
    "ignoreblue",
    "unignoreblue",
    "listblue",
    "ungignoreblue",
    "gignoreblue",
    "start",
    "help",
    "settings",
    "donate",
    "stalk",
    "aka",
    "leaderboard",
]

for handler_list in CUTIEPII_PTB.handlers:
    for handler in CUTIEPII_PTB.handlers[handler_list]:
        if any(
                isinstance(handler, cmd_handler)
                for cmd_handler in CommandHandlerList):
            command_list += handler.commands


async def clean_blue_text_must_click(update: Update,
                                     context: CallbackContext) -> None:
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    #    if (chat.get_member(1241223850)).can_delete_messages and sql.is_enabled(chat.id):
    if (chat.get_member(1241223850)).can_delete_messages and sql.is_enabled(
            chat.id):
        fst_word = await message.text.strip().split(None, 1)[0]

        if len(fst_word) > 1 and any(
                fst_word.startswith(start) for start in CMD_STARTERS):

            command = fst_word[1:].split("@")
            chat = update.effective_chat

            if sql.is_command_ignored(chat.id, command[0]):
                return

            if command[0] not in command_list:
                await message.delete()


@connection_status
@bot_can_delete
@user_admin
async def set_blue_text_must_click(update: Update,
                                   context: CallbackContext) -> None:
    chat = update.effective_chat
    message = update.effective_message
    bot, args = context.bot, context.args
    if len(args) >= 1:
        val = args[0].lower()
        if val in ("off", "no"):
            sql.set_cleanbt(chat.id, False)
            reply = f"Bluetext cleaning has been disabled for <b>{html.escape(chat.title)}</b>"

            await message.reply_text(reply, parse_mode=ParseMode.HTML)

        elif val in ("yes", "on"):
            sql.set_cleanbt(chat.id, True)
            reply = f"Bluetext cleaning has been enabled for <b>{html.escape(chat.title)}</b>"

            await message.reply_text(reply, parse_mode=ParseMode.HTML)

        else:
            reply = "Invalid argument.Accepted values are 'yes', 'on', 'no', 'off'"
            await message.reply_text(reply)
    else:
        clean_status = sql.is_enabled(chat.id)
        clean_status = "Enabled" if clean_status else "Disabled"
        reply = f"Bluetext cleaning for <b>{html.escape(chat.title)}</b> : <b>{clean_status}</b>"

        await message.reply_text(reply, parse_mode=ParseMode.HTML)


@user_admin
async def add_bluetext_ignore(update: Update,
                              context: CallbackContext) -> None:
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        if added := sql.chat_ignore_command(chat.id, val):
            reply = f"<b>{args[0]}</b> has been added to bluetext cleaner ignore list."
        else:
            reply = "Command is already ignored."
        await message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "No command supplied to be ignored."
        await message.reply_text(reply)


@user_admin
async def remove_bluetext_ignore(update: Update,
                                 context: CallbackContext) -> None:
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        if removed := sql.chat_unignore_command(chat.id, val):
            reply = f"<b>{args[0]}</b> has been removed from bluetext cleaner ignore list."
        else:
            reply = "Command isn't ignored currently."
        await message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "No command supplied to be unignored."
        await message.reply_text(reply)


@user_admin
async def add_bluetext_ignore_global(update: Update,
                                     context: CallbackContext) -> None:
    message = update.effective_message
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        if added := sql.global_ignore_command(val):
            reply = f"<b>{args[0]}</b> has been added to global bluetext cleaner ignore list."

        else:
            reply = "Command is already ignored."
        await message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "No command supplied to be ignored."
        await message.reply_text(reply)


@dev_plus
async def remove_bluetext_ignore_global(update: Update,
                                        context: CallbackContext) -> None:
    message = update.effective_message
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        if removed := sql.global_unignore_command(val):
            reply = f"<b>{args[0]}</b> has been removed from global bluetext cleaner ignore list."

        else:
            reply = "Command isn't ignored currently."
        await message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "No command supplied to be unignored."
        await message.reply_text(reply)


@dev_plus
async def bluetext_ignore_list(update: Update,
                               context: CallbackContext) -> None:

    message = update.effective_message
    chat = update.effective_chat

    global_ignored_list, local_ignore_list = sql.get_all_ignored(chat.id)
    text = ""

    if global_ignored_list:
        text = "The following commands are currently ignored globally from bluetext cleaning :\n"

        for x in global_ignored_list:
            text += f" - <code>{x}</code>\n"

    if local_ignore_list:
        text += "\nThe following commands are currently ignored locally from bluetext cleaning :\n"

        for x in local_ignore_list:
            text += f" - <code>{x}</code>\n"

    if not text:
        text = "No commands are currently ignored from bluetext cleaning."
        await message.reply_text(text)
        return

    await message.reply_text(text, parse_mode=ParseMode.HTML)
    return


CUTIEPII_PTB.add_handler(CommandHandler("cleanblue", set_blue_text_must_click))
CUTIEPII_PTB.add_handler(CommandHandler("ignoreblue", add_bluetext_ignore))
CUTIEPII_PTB.add_handler(CommandHandler("unignoreblue",
                                        remove_bluetext_ignore))
CUTIEPII_PTB.add_handler(
    CommandHandler("gignoreblue", add_bluetext_ignore_global))
CUTIEPII_PTB.add_handler(
    CommandHandler("ungignoreblue", remove_bluetext_ignore_global))
CUTIEPII_PTB.add_handler(CommandHandler("listblue", bluetext_ignore_list))
CUTIEPII_PTB.add_handler(
    MessageHandler(filters.COMMAND & filters.ChatType.GROUPS,
                   clean_blue_text_must_click))

__mod_name__ = "Cleaning"

__help__ = """
Blue text cleaner removed any made up commands that people send in your chat.
➛ /cleanblue <on/off/yes/no>*:* clean commands after sending
➛ /ignoreblue <word>*:* prevent auto cleaning of the command
➛ /unignoreblue <word>*:* remove prevent auto cleaning of the command
➛ /listblue*:* list currently whitelisted commands
 *Following are Disasters only commands, admins cannot use these:*
➛ /gignoreblue <word>*:* globally ignorea bluetext cleaning of saved word across Cutiepii Robot 愛.
➛ /ungignoreblue <word>*:* remove said command from global cleaning list
"""
