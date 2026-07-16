"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

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

from Cutiepii_Robot import ALLOW_EXCL, CustomCommandHandler, dispatcher, BOT_NAME, BOT_NAME
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.helper_funcs.chat_status import (
    connection_status,
    dev_plus,

)
from Cutiepii_Robot.modules.sql import cleaner_sql as sql
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    filters,
)
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility
Filters = filters  # Alias for backward compatibility
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    get_bot_member,
)

CMD_STARTERS = ("/", "!") if ALLOW_EXCL else "/"
BLUE_TEXT_CLEAN_GROUP = 13
CommandHandlerList = (CommandHandler, CustomCommandHandler, DisableAbleCommandHandler)
command_list = [
    "cleanblue",
    "ignoreblue",
    "unignoreblue",
    "listblue",
    "ungignoreblue",
    "gignoreblue" "start",
    "help",
    "settings",
    "donate",
    "stalk",
    "aka",
    "leaderboard",
]

for handler_list in dispatcher.handlers:
    for handler in dispatcher.handlers[handler_list]:
        if any(isinstance(handler, cmd_handler) for cmd_handler in CommandHandlerList):
            command_list.extend(handler.commands)

@cutiepii_msg((Filters.COMMAND & Filters.ChatType.GROUPS), group=BLUE_TEXT_CLEAN_GROUP)
async def clean_blue_text_must_click(update: Update, context: CallbackContext):
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    bot_member = await get_bot_member(chat.id)
    if getattr(bot_member, "can_delete_messages", False) and sql.is_enabled(chat.id):
        fst_word = message.text.strip().split(None, 1)[0]

        if len(fst_word) > 1 and any(
            fst_word.startswith(start) for start in CMD_STARTERS
        ):

            command = fst_word[1:].split("@")
            chat = update.effective_chat

            ignored = sql.is_command_ignored(chat.id, command[0])
            if ignored:
                return

            if command[0] not in command_list:
                message.delete()

@cutiepii_cmd(command='cleanbluetext', pass_args=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_DELETE_MESSAGES)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def set_blue_text_must_click(update: Update, context: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    bot, args = context.bot, context.args
    user = update.effective_user
    if len(args) >= 1:
        val = args[0].lower()
        if val in ("off", "no"):
            sql.set_cleanbt(chat.id, False)
            reply = "<b>Blue Text Cleaner Updated</b>\nBluetext cleaning has been disabled for <b>{}</b>.".format(
                html.escape(chat.title)
            )
            message.reply_text(reply, parse_mode=ParseMode.HTML)

        elif val in ("yes", "on"):
            sql.set_cleanbt(chat.id, True)
            reply = "<b>Blue Text Cleaner Updated</b>\nBluetext cleaning has been enabled for <b>{}</b>.".format(
                html.escape(chat.title)
            )
            message.reply_text(reply, parse_mode=ParseMode.HTML)

        else:
            reply = "<b>Invalid Argument</b>\nAccepted parameters are: <code>yes</code>, <code>on</code>, <code>no</code>, <code>off</code>."
            message.reply_text(reply, parse_mode=ParseMode.HTML)
    else:
        clean_status = sql.is_enabled(chat.id)
        clean_status = "Enabled" if clean_status else "Disabled"
        reply = "<b>Blue Text Cleaner Status</b>\nChat: <b>{}</b>\nStatus: <b>{}</b>".format(
            html.escape(chat.title), clean_status
        )
        message.reply_text(reply, parse_mode=ParseMode.HTML)

@cutiepii_cmd(command='ignorecleanbluetext', pass_args=True)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def add_bluetext_ignore(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        added = sql.chat_ignore_command(chat.id, val)
        if added:
            reply = "<b>Cleaner Settings Updated</b>\n<code>{}</code> has been added to the bluetext cleaner ignore list.".format(
                html.escape(args[0])
            )
        else:
            reply = "<b>Action Denied</b>\nThis command is already ignored."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "<b>Invalid Command Usage</b>\nPlease specify the command trigger to ignore."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

@cutiepii_cmd(command='unignorecleanbluetext', pass_args=True)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def remove_bluetext_ignore(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args

    if len(args) >= 1:
        val = args[0].lower()
        removed = sql.chat_unignore_command(chat.id, val)
        if removed:
            reply = (
                "<b>Cleaner Settings Updated</b>\n<code>{}</code> has been removed from the bluetext cleaner ignore list.".format(
                    html.escape(args[0])
                )
            )
        else:
            reply = "<b>Action Denied</b>\nThis command is not currently ignored."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "<b>Invalid Command Usage</b>\nPlease specify the command trigger to unignore."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

@cutiepii_cmd(command='ignoreglobalcleanbluetext', pass_args=True)
@dev_plus
async def add_bluetext_ignore_global(update: Update, context: CallbackContext):
    message = update.effective_message
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        added = sql.global_ignore_command(val)
        if added:
            reply = "<b>Cleaner Settings Updated</b>\n<code>{}</code> has been added to the global bluetext cleaner ignore list.".format(
                html.escape(args[0])
            )
        else:
            reply = "<b>Action Denied</b>\nThis command is already ignored."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "<b>Invalid Command Usage</b>\nPlease specify the command trigger to ignore."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

@cutiepii_cmd(command='unignoreglobalcleanbluetext', pass_args=True)
@dev_plus
async def remove_bluetext_ignore_global(update: Update, context: CallbackContext):
    message = update.effective_message
    args = context.args
    if len(args) >= 1:
        val = args[0].lower()
        removed = sql.global_unignore_command(val)
        if removed:
            reply = "<b>Cleaner Settings Updated</b>\n<code>{}</code> has been removed from the global bluetext cleaner ignore list.".format(
                html.escape(args[0])
            )
        else:
            reply = "<b>Action Denied</b>\nThis command is not currently ignored."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

    else:
        reply = "<b>Invalid Command Usage</b>\nPlease specify the command trigger to unignore."
        message.reply_text(reply, parse_mode=ParseMode.HTML)

@cutiepii_cmd(command='listcleanbluetext')
@dev_plus
async def bluetext_ignore_list(update: Update, context: CallbackContext):

    message = update.effective_message
    chat = update.effective_chat

    global_ignored_list, local_ignore_list = sql.get_all_ignored(chat.id)
    text = ""

    if global_ignored_list:
        text = "<b>Ignored Commands List</b>\n\n<b>Globally Ignored:</b>\n"

        for x in global_ignored_list:
            text += f" - <code>{x}</code>\n"

    if local_ignore_list:
        if not text:
            text = "<b>Ignored Commands List</b>\n"
        text += "\n<b>Locally Ignored:</b>\n"

        for x in local_ignore_list:
            text += f" - <code>{x}</code>\n"

    if not text:
        text = "<b>Cleaner Settings</b>\nNo commands are currently ignored from bluetext cleaning."
        message.reply_text(text, parse_mode=ParseMode.HTML)
        return

    message.reply_text(text, parse_mode=ParseMode.HTML)
    return
    return

__mod_name__ = "Cleaning"


__help__ = True
