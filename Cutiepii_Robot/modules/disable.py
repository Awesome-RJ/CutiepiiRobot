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

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
import asyncio
from typing import Union

from future.utils import string_types
from telegram import Update, Chat
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, MessageHandler, filters
from telegram.helpers import escape_markdown

from Cutiepii_Robot import dispatcher, REDIS, OWNER_ID
import html
from telegram.ext import ContextTypes
 
from Cutiepii_Robot.modules.helper_funcs.handlers import CMD_STARTERS, SpamChecker
from Cutiepii_Robot.modules.helper_funcs.misc import is_module_loaded
from Cutiepii_Robot.modules.helper_funcs.alternate import send_message, typing_action
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    AdminPerms,
    user_is_admin,
)

from Cutiepii_Robot.modules.connection import connected


CMD_STARTERS = tuple(CMD_STARTERS)


FILENAME = __name__.rsplit(".", 1)[-1]

# If module is due to be loaded, then setup all the magical handlers
if is_module_loaded(FILENAME):
    from .sql import disable_sql as sql

    DISABLE_CMDS = []
    DISABLE_OTHER = []
    ADMIN_CMDS = []

    class DisableAbleCommandHandler(CommandHandler):
        def __init__(self, command, callback, admin_ok=False, **kwargs):
            if "run_async" in kwargs:
                del kwargs["run_async"]
            if "pass_args" in kwargs:
                del kwargs["pass_args"]  # Removed in v20+ - args are automatically available via context.args
            super().__init__(command, callback, **kwargs)
            self.admin_ok = admin_ok
            if isinstance(command, str):
                DISABLE_CMDS.append(command)
                if admin_ok:
                    ADMIN_CMDS.append(command)
            else:
                DISABLE_CMDS.extend(command)
                if admin_ok:
                    ADMIN_CMDS.extend(command)
        async def check_update(self, update):
            if not isinstance(update, Update) or not update.effective_message:
                return
            message = update.effective_message

            try:
                user_id = update.effective_user.id
            except Exception:
                user_id = None

            raw_text = message.text or message.caption
            if raw_text and len(raw_text) > 1:
                fst_word = raw_text.split(None, 1)[0]
                if len(fst_word) > 1 and any(
                    fst_word.startswith(start) for start in CMD_STARTERS
                ):
                    args = raw_text.split()[1:]
                    command = fst_word[1:].split("@")
                    command.append(update.get_bot().username)

                    if not (
                        command[0].lower() in self.commands
                        and (len(command) <= 1 or command[1].lower() == update.get_bot().username.lower())
                    ):
                        return None

                    if SpamChecker.check_user(user_id):
                        return None

                    filter_result = self.filters.check_update(update) if self.filters else True
                    if asyncio.iscoroutine(filter_result):
                        filter_result = await filter_result
                    if filter_result:
                        chat = update.effective_chat
                        user = update.effective_user
                        # disabled, admincmd, user admin
                        if sql.is_command_disabled(chat.id, command[0].lower()):
                            # check if command was disabled
                            is_disabled = command[
                                0
                            ] in ADMIN_CMDS and user_is_admin(chat, user.id)
                            if not is_disabled:
                                disabledel = REDIS.get(f"disabledel:{chat.id}")
                                if disabledel and disabledel.decode("utf-8") == "true":
                                    try:
                                        await message.delete()
                                    except Exception:
                                        pass
                                return None
                            return args, filter_result

                        return args, filter_result
            return False

    class DisableAbleMessageHandler(MessageHandler):
        def __init__(self, pattern, callback, friendly="", **kwargs):
            if "run_async" in kwargs:
                del kwargs["run_async"]
            if "pass_args" in kwargs:
                del kwargs["pass_args"]  # Removed in v20+ - args are automatically available via context.args
            if "pass_chat_data" in kwargs:
                del kwargs["pass_chat_data"]  # Removed in v20+
            if "pass_user_data" in kwargs:
                del kwargs["pass_user_data"]  # Removed in v20+
            super().__init__(pattern, callback, **kwargs)
            DISABLE_OTHER.append(friendly or str(pattern))
            self.friendly = friendly or str(pattern)
        async def check_update(self, update):
            if isinstance(update, Update) and update.effective_message:
                chat = update.effective_chat

                try:
                    user_id = update.effective_user.id
                except Exception:
                    user_id = None

                filter_result = self.filters.check_update(update)
                if asyncio.iscoroutine(filter_result):
                    filter_result = await filter_result
                if filter_result:
                    if SpamChecker.check_user(user_id):
                        return None
                    if sql.is_command_disabled(chat.id, self.friendly):
                        return False
                    return True
            return False



    # @user_admin_check(AdminPerms.CAN_CHANGE_INFO)
    @user_admin_check(AdminPerms.CAN_CHANGE_INFO)
    @typing_action
    @cutiepii_cmd(command="disable")
    async def disable(update, context):
        chat = update.effective_chat  # type: Optional[Chat]
        user = update.effective_user
        args = context.args

        conn = await connected(context.bot, update, chat, user.id, need_admin=True)
        if conn:
            chat = await dispatcher.bot.get_chat(conn)
            chat_name = chat.title
        else:
            if update.effective_message.chat.type == "private":
                await send_message(
                    update.effective_message,
                    "<b>Action Denied</b>\nThis command can only be used in group chats.",
                    parse_mode=ParseMode.HTML
                )
                return ""
            chat = update.effective_chat
            chat_name = update.effective_message.chat.title

        if len(args) >= 1:
            disable_cmd = args[0]
            if disable_cmd.startswith(CMD_STARTERS):
                disable_cmd = disable_cmd[1:]

            if disable_cmd in set(DISABLE_CMDS + DISABLE_OTHER):
                sql.disable_command(chat.id, disable_cmd)
                if conn:
                    text = "<b>Command Disabled</b>\nDisabled the use of <code>{}</code> command in <b>{}</b>.".format(
                        disable_cmd, html.escape(chat_name)
                    )
                else:
                    text = "<b>Command Disabled</b>\nDisabled the use of <code>{}</code> command.".format(disable_cmd)
                await send_message(
                    update.effective_message,
                    text,
                    parse_mode=ParseMode.HTML,
                )
            else:
                await send_message(update.effective_message, "<b>Error</b>\nThis command cannot be disabled.", parse_mode=ParseMode.HTML)

        else:
            await send_message(update.effective_message, "<b>Invalid Command Usage</b>\nPlease specify the command you wish to disable.", parse_mode=ParseMode.HTML)
    # @user_admin_check(AdminPerms.CAN_CHANGE_INFO)
    @user_admin_check(AdminPerms.CAN_CHANGE_INFO)
    @typing_action
    @cutiepii_cmd(command="enable")
    async def enable(update, context):
        chat = update.effective_chat  # type: Optional[Chat]
        user = update.effective_user
        args = context.args

        conn = await connected(context.bot, update, chat, user.id, need_admin=True)
        if conn:
            chat = await dispatcher.bot.get_chat(conn)
            chat_id = conn
            chat_name = chat.title
        else:
            if update.effective_message.chat.type == "private":
                await send_message(
                    update.effective_message,
                    "<b>Action Denied</b>\nThis command can only be used in group chats.",
                    parse_mode=ParseMode.HTML
                )
                return ""
            chat = update.effective_chat
            chat_id = update.effective_chat.id
            chat_name = update.effective_message.chat.title

        if len(args) >= 1:
            enable_cmd = args[0]
            if enable_cmd.startswith(CMD_STARTERS):
                enable_cmd = enable_cmd[1:]

            if sql.enable_command(chat.id, enable_cmd):
                if conn:
                    text = "<b>Command Enabled</b>\nEnabled the use of <code>{}</code> command in <b>{}</b>.".format(
                        enable_cmd, html.escape(chat_name)
                    )
                else:
                    text = "<b>Command Enabled</b>\nEnabled the use of <code>{}</code> command.".format(enable_cmd)
                await send_message(
                    update.effective_message,
                    text,
                    parse_mode=ParseMode.HTML,
                )
            else:
                await send_message(update.effective_message, "<b>Information</b>\nThis command is not currently disabled.", parse_mode=ParseMode.HTML)

        else:
            await send_message(update.effective_message, "<b>Invalid Command Usage</b>\nPlease specify the command you wish to enable.", parse_mode=ParseMode.HTML)
    @user_admin_check(AdminPerms.CAN_CHANGE_INFO)
    @typing_action
    @cutiepii_cmd(command="listcmds")
    async def list_cmds(update, context):
        if DISABLE_CMDS:
            result = "".join(
                " - <code>{}</code>\n".format(html.escape(str(cmd)))
                for cmd in set(DISABLE_CMDS)
            )

            text = "<b>Toggleable Commands</b>\nThe following commands can be disabled:\n{}".format(result)
            def paginate(text):
                lines = text.split("\n")
                previous_text = ""
                for line in lines:
                    if len(previous_text) + 1 + len(line) > 4096: # char limit
                        yield previous_text
                        # stop before limit, if adding line makes msg too long
                        previous_text = line
                    else:
                        previous_text = (previous_text + "\n" + line).strip("\n")
                yield previous_text
 
            for page in paginate(text):
                await update.effective_message.reply_text(
                    page,
                    parse_mode=ParseMode.HTML,
                )
        else:
            await update.effective_message.reply_text("<b>Information</b>\nNo commands are toggleable.", parse_mode=ParseMode.HTML)

    # do not async
    async def build_curr_disabled(chat_id: Union[str, int]) -> str:
        disabled = sql.get_all_disabled(chat_id)
        if not disabled:
            return "<b>Information</b>\nNo commands are currently disabled."

        result = "".join(" - <code>{}</code>\n".format(html.escape(cmd)) for cmd in disabled)
        return "<b>Disabled Commands</b>\nThe following commands are currently restricted in this chat:\n{}".format(result)
    @typing_action
    @cutiepii_cmd(command=["cmds", "disabled"])
    async def commands(update, context):
        chat = update.effective_chat
        user = update.effective_user
        conn = await connected(context.bot, update, chat, user.id, need_admin=True)
        if conn:
            chat = await dispatcher.bot.get_chat(conn)
            chat_id = conn
        else:
            if update.effective_message.chat.type == "private":
                await send_message(
                    update.effective_message,
                    "<b>Action Denied</b>\nThis command can only be used in group chats.",
                    parse_mode=ParseMode.HTML
                )
                return ""
            chat = update.effective_chat
            chat_id = update.effective_chat.id

        text = await build_curr_disabled(chat.id)
        await send_message(update.effective_message, text, parse_mode=ParseMode.HTML)

    async def __import_data__(chat_id, data):
        disabled = data.get("disabled", {})
        for disable_cmd in disabled:
            sql.disable_command(chat_id, disable_cmd)

    def __stats__():
        return "- {} disabled items, across {} chats.".format(
            sql.num_disabled(), sql.num_chats()
        )

    async def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)

    async def __chat_settings__(chat_id, user_id):
        return await build_curr_disabled(chat_id)

    @user_admin_check(AdminPerms.CAN_CHANGE_INFO)
    @cutiepii_cmd(command="disabledel")
    async def disabledel_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        message = update.effective_message
        args = context.args

        if not args:
            pref = REDIS.get(f"disabledel:{chat.id}")
            pref = pref.decode("utf-8") if pref else "false"
            status = "ON" if pref == "true" else "OFF"
            await message.reply_text(f"<b>Delete Triggers Status</b>\nDelete triggers for disabled commands is currently: <code>{status}</code>", parse_mode=ParseMode.HTML)
            return

        action = args[0].lower().strip()
        if action in ["on", "yes", "enable"]:
            REDIS.set(f"disabledel:{chat.id}", "true")
            await message.reply_text("<b>Delete Triggers Enabled</b>\nTrigger messages for disabled commands will now be deleted.", parse_mode=ParseMode.HTML)
        elif action in ["off", "no", "disable"]:
            REDIS.set(f"disabledel:{chat.id}", "false")
            await message.reply_text("<b>Delete Triggers Disabled</b>\nTrigger messages for disabled commands will not be deleted.", parse_mode=ParseMode.HTML)
        else:
            await message.reply_text("<b>Usage</b>\nUse <code>/disabledel [on|off]</code> to toggle trigger deletion.", parse_mode=ParseMode.HTML)

    @cutiepii_cmd(command="enableall")
    async def enable_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        message = update.effective_message
        user = update.effective_user
        
        if user.id != OWNER_ID:
            await message.reply_text("<b>Action Denied</b>\nThis command is restricted to the bot owner.", parse_mode=ParseMode.HTML)
            return

        disabled = sql.get_all_disabled(chat.id)
        if not disabled:
            await message.reply_text("<b>Information</b>\nNo commands are currently disabled in this chat.", parse_mode=ParseMode.HTML)
            return

        for cmd in disabled:
            sql.enable_command(chat.id, cmd)

        await message.reply_text("<b>Commands Restored</b>\nAll disabled commands have been successfully enabled for this chat.", parse_mode=ParseMode.HTML)

    __mod_name__ = "Disabling"
    __help__ = True



else:
    DisableAbleCommandHandler = CommandHandler
    DisableAbleMessageHandler = MessageHandler
