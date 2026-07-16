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
from datetime import datetime, timezone
from functools import wraps

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility
from telegram.error import Forbidden, BadRequest
from telegram.helpers import escape_markdown

from Cutiepii_Robot.modules.helper_funcs.misc import is_module_loaded

FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from Cutiepii_Robot import GBAN_LOGS, LOGGER, dispatcher, SUDO_USERS
    from Cutiepii_Robot.modules.helper_funcs.chat_status import user_admin
    from Cutiepii_Robot.modules.sql import log_channel_sql as sql

    def group_owner(func):
        @wraps(func)
        async def is_owner(update: Update, context: CallbackContext, *args, **kwargs):
            user = update.effective_user
            chat = update.effective_chat
            if chat.type == chat.PRIVATE:
                return await func(update, context, *args, **kwargs)
            if user:
                if user.id in SUDO_USERS:
                    return await func(update, context, *args, **kwargs)
                member = await chat.get_member(user.id)
                if member.status in ("creator", "owner"):
                    return await func(update, context, *args, **kwargs)
                await update.effective_message.reply_text(
                    "Only the group owner (creator) can change, set, or stop the log channel!"
                )
                return None
            return None
        return is_owner

    def loggable(func):
        @wraps(func)
        async def log_action(
            update: Update,
            context: CallbackContext,
            *args,
            **kwargs,
        ):
            result = func(update, context, *args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result

            chat = update.effective_chat
            message = update.effective_message

            if result and isinstance(result, str):
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += "\n<b>Event Stamp</b>: <code>{}</code>".format(
                    datetime.now(timezone.utc).strftime(datetime_fmt)
                )
                try:
                    if message and chat.type == chat.SUPERGROUP:
                        if chat.username:
                            result += f'\n<b>Link:</b> <a href="https://t.me/{chat.username}/{message.message_id}">click here</a>'
                        else:
                            cid = str(chat.id).replace("-100", '')
                            result += f'\n<b>Link:</b> <a href="https://t.me/c/{cid}/{message.message_id}">click here</a>'
                except AttributeError:
                    result += '\n<b>Link:</b> No link for manual actions.'

                log_chat = sql.get_chat_log_channel(chat.id)
                if log_chat:
                    await send_log(context, log_chat, chat.id, result)

            return result

        return log_action

    def gloggable(func):
        @wraps(func)
        async def glog_action(update: Update, context: CallbackContext, *args, **kwargs):
            result = func(update, context, *args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            chat = update.effective_chat
            message = update.effective_message

            if result:
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += "\n<b>Event Stamp</b>: <code>{}</code>".format(
                    datetime.now(timezone.utc).strftime(datetime_fmt),
                )

                try:
                    if message.chat.type == chat.SUPERGROUP:
                        if message.chat.username:
                            result += f'\n<b>Link:</b> <a href="https://t.me/{chat.username}/{message.message_id}">click here</a>'
                        else:
                            cid = str(chat.id).replace("-100", '')
                            result += f'\n<b>Link:</b> <a href="https://t.me/c/{cid}/{message.message_id}">click here</a>'
                except AttributeError:
                    result += '\n<b>Link:</b> No link for manual actions.' # or just without the whole line
                     
                log_chat = str(GBAN_LOGS)
                if log_chat:
                    await send_log(context, log_chat, chat.id, result)

            return result

        return glog_action

    async def send_log(
        context: CallbackContext, log_chat_id: str, orig_chat_id: str, result: str,
    ):
        bot = context.bot
        try:
            await bot.send_message(
                log_chat_id,
                result,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message == "Chat not found":
                await bot.send_message(
                    orig_chat_id, "This log channel has been deleted - unsetting.",
                )
                sql.stop_chat_logging(orig_chat_id)
            else:
                LOGGER.warning(excp.message)
                LOGGER.warning(result)
                LOGGER.exception("Could not parse")

                await bot.send_message(
                    log_chat_id,
                    result
                    + "\n\nFormatting has been disabled due to an unexpected error.",
                )
        except Forbidden as excp:
            if excp.message == "bot is not a member of the channel chat":
                await bot.send_message(
                    orig_chat_id, "I don't have access to the log channel - unsetting."
                )
                sql.stop_chat_logging(orig_chat_id)

    
    @group_owner
    @cutiepii_cmd(command="logchannel")
    async def logging(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        log_channel = sql.get_chat_log_channel(chat.id)
        if log_channel:
            try:
                log_channel_info = await bot.get_chat(log_channel)
                await message.reply_text(
                    f"This group has all it's logs sent to:"
                    f" {escape_markdown(log_channel_info.title)} (`{log_channel}`)",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Forbidden:
                sql.stop_chat_logging(chat.id)
                await message.reply_text("No log channel has been set for this group!")
        else:
            await update.effective_message.reply_text("No log channel has been set for this group!")

    
    @group_owner
    @cutiepii_cmd(command="setlog")
    async def setlog(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat
        from telegram import MessageOriginChannel, MessageOriginChat
        forward_chat = None
        if message.forward_origin:
            if isinstance(message.forward_origin, MessageOriginChannel):
                forward_chat = message.forward_origin.chat
            elif isinstance(message.forward_origin, MessageOriginChat):
                forward_chat = message.forward_origin.sender_chat
        elif getattr(message, "forward_from_chat", None):
            forward_chat = message.forward_from_chat

        if chat.type == chat.CHANNEL:
            await message.reply_text(
                "Now, forward the /setlog to the group you want to tie this channel to!",
            )

        elif forward_chat:
            sql.set_chat_log_channel(chat.id, forward_chat.id)
            try:
                await message.delete()
            except BadRequest as excp:
                if excp.message != "Message to delete not found":
                    pass
                else:
                    LOGGER.exception(
                        "Error deleting message in log channel. Should work anyway though.",
                    )

            try:
                await bot.send_message(
                    forward_chat.id,
                    f"This channel has been set as the log channel for {chat.title or chat.first_name}.",
                )
            except Forbidden as excp:
                if excp.message == "Forbidden: bot is not a member of the channel chat":
                    await bot.send_message(chat.id, "Successfully set log channel!")
                else:
                    LOGGER.exception("ERROR in setting the log channel.")

            await bot.send_message(chat.id, "Successfully set log channel!")

        else:
            await message.reply_text(
                "The steps to set a log channel are:\n"
                " - add bot to the desired channel\n"
                " - send /setlog to the channel\n"
                " - forward the /setlog to the group\n",
            )

    
    @group_owner
    @cutiepii_cmd(command="unsetlog")
    async def unsetlog(update: Update, context: CallbackContext):
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        log_channel = sql.stop_chat_logging(chat.id)
        if log_channel:
            await bot.send_message(
                log_channel, f"Channel has been unlinked from {chat.title}",
            )
            await update.effective_message.reply_text("Log channel has been un-set.")

        else:
            await update.effective_message.reply_text("No log channel has been set yet!")

    def __stats__():
        return f"- {sql.num_logchannels()} log channels set."

    async def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)

    async def __chat_settings__(chat_id, user_id):
        log_channel = sql.get_chat_log_channel(chat_id)
        if log_channel:
            log_channel_info = dispatcher.bot.get_chat(log_channel)
            return f"This group has all it's logs sent to: {escape_markdown(log_channel_info.title)} (`{log_channel}`)"
        return "No log channel is set for this group!"




else:
    # run anyway if module not loaded
    def loggable(func):
        return func

    def gloggable(func):
        return func
