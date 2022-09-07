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

from datetime import datetime
from functools import wraps
import asyncio
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler
from Cutiepii_Robot.modules.helper_funcs.misc import is_module_loaded
from Cutiepii_Robot import LOGGER, CUTIEPII_PTB
from Cutiepii_Robot.modules.helper_funcs.anonymous import user_admin, AdminPerms

FILENAME = __name__.rsplit(".", 1)[-1]

if is_module_loaded(FILENAME):
    from telegram.constants import ParseMode
    from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
    from telegram.error import BadRequest, Forbidden
    from telegram.helpers import escape_markdown

    from Cutiepii_Robot import GBAN_LOGS
    from Cutiepii_Robot.modules.helper_funcs.chat_status import (
        user_admin as u_admin,
        is_user_admin,
    )
    from Cutiepii_Robot.modules.sql import log_channel_sql as sql

    def loggable(func):

        @wraps(func)
        def log_action(update, context, *args, **kwargs):
            result = func(update, context, *args, **kwargs)
            chat = update.effective_chat
            message = update.effective_message
            if result:
                if chat.type == chat.SUPERGROUP and chat.username:
                    result += f"\n<b>Link:</b> <a href=https://t.me/{chat.username}/{message.message_id}'>click here</a>"
                if log_chat := sql.get_chat_log_channel(chat.id):
                    try:
                        send_log(context.bot, log_chat, chat.id, result)
                    except AttributeError:
                        sql.stop_chat_logging(chat.id)

            elif result != "":
                LOGGER.warning(
                    "%s was set as loggable, but had no return statement.",
                    func,
                )

            return result

        return log_action

    def gloggable(func):

        @wraps(func)
        def glog_action(update, context, *args, **kwargs):
            result = func(update, context, *args, **kwargs)
            chat = update.effective_chat  # type: Optional[Chat]
            message = update.effective_message  # type: Optional[Message]

            if result:
                datetime_fmt = "%H:%M - %d-%m-%Y"
                result += f"\n<b>Event Stamp</b>: <code>{datetime.utcnow().strftime(datetime_fmt)}</code>"

                if message.chat.type == chat.SUPERGROUP and message.chat.username:
                    result += f"\n<b>Link:</b> <a href='https://t.me/{chat.username}/{message.message_id}'>click here</a>"
                if log_chat := str(GBAN_LOGS):
                    send_log(context, log_chat, chat.id, result)

            return result

        return glog_action

    async def send_log(context: CallbackContext, log_chat_id: str,
                       orig_chat_id: str, result: str):
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
                    orig_chat_id,
                    "This log channel has been deleted - unsetting.")
                sql.stop_chat_logging(orig_chat_id)
            else:
                LOGGER.warning(excp.message)
                LOGGER.warning(result)
                LOGGER.exception("Could not parse")

                await bot.send_message(
                    log_chat_id,
                    result +
                    "\n\nFormatting has been disabled due to an unexpected error.",
                )

    @u_admin
    async def logging(update: Update, context: CallbackContext) -> None:
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        if log_channel := sql.get_chat_log_channel(chat.id):
            log_channel_info = await bot.get_chat(log_channel)
            await message.reply_text(
                f"This group has all it's logs sent to:"
                f" {escape_markdown(log_channel_info.title)} (`{log_channel}`)",
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            await message.reply_text(
                "No log channel has been set for this group!")

    @user_admin(AdminPerms.CAN_CHANGE_INFO)
    async def setlog(update: Update, context: CallbackContext) -> None:
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat
        if chat.type == chat.CHANNEL:
            await message.reply_text(
                "Now, forward the /setlog to the group you want to tie this channel to!"
            )

        elif message.forward_from_chat:
            sql.set_chat_log_channel(chat.id, message.forward_from_chat.id)
            try:
                await message.delete()
            except BadRequest as excp:
                if excp.message != "Message to delete not found":
                    LOGGER.exception(
                        "Error deleting message in log channel. Should work anyway though."
                    )

            try:
                await bot.send_message(
                    message.forward_from_chat.id,
                    f"This channel has been set as the log channel for {chat.title or chat.first_name}.",
                )
            except Forbidden as excp:
                if excp.message == "Forbidden: bot is not a member of the channel chat":
                    await bot.send_message(chat.id,
                                           "Successfully set log channel!")
                else:
                    LOGGER.exception("ERROR in setting the log channel.")

            await bot.send_message(chat.id, "Successfully set log channel!")

        else:
            await message.reply_text("The steps to set a log channel are:\n"
                                     " - add bot to the desired channel\n"
                                     " - send /setlog to the channel\n"
                                     " - forward the /setlog to the group\n")

    @user_admin(AdminPerms.CAN_CHANGE_INFO)
    async def unsetlog(update: Update, context: CallbackContext) -> None:
        bot = context.bot
        message = update.effective_message
        chat = update.effective_chat

        if log_channel := sql.stop_chat_logging(chat.id):
            await bot.send_message(
                log_channel, f"Channel has been unlinked from {chat.title}")
            await message.reply_text("Log channel has been un-set.")

        else:
            await message.reply_text("No log channel has been set yet!")

    def __stats__():
        return f"➛ {sql.num_logchannels()} log channels set."

    def __migrate__(old_chat_id, new_chat_id):
        sql.migrate_chat(old_chat_id, new_chat_id)

    def __chat_settings__(chat_id, user_id):
        if log_channel := sql.get_chat_log_channel(chat_id):
            log_channel_info = asyncio.get_running_loop().run_until_complete(
                CUTIEPII_PTB.bot.get_chat(log_channel))
            return f"This group has all it's logs sent to: {escape_markdown(log_channel_info.title)} (`{log_channel}`)"
        return "No log channel is set for this group!"

    __help__ = """
*Admins only:*
• `/logchannel`*:* get log channel info
• `/setlog`*:* set the log channel.
• `/unsetlog`*:* unset the log channel.
Setting the log channel is done by:
• adding the bot to the desired channel (as an admin!)
• sending `/setlog` in the channel
• forwarding the `/setlog` to the group
"""

    __mod_name__ = "Logger"

else:
    # run anyway if module not loaded
    def loggable(func):
        return func

    def gloggable(func):
        return func


@user_admin(AdminPerms.CAN_CHANGE_INFO)
async def log_settings(update: Update):
    chat = update.effective_chat
    chat_set = sql.get_chat_setting(chat_id=chat.id)
    if not chat_set:
        sql.set_chat_setting(setting=sql.LogChannelSettings(
            chat.id, True, True, True, True, True))
    btn = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="Warn", callback_data="log_tog_warn"),
            InlineKeyboardButton(text="Action", callback_data="log_tog_act"),
        ],
        [
            InlineKeyboardButton(text="Join", callback_data="log_tog_join"),
            InlineKeyboardButton(text="Leave", callback_data="log_tog_leave"),
        ],
        [InlineKeyboardButton(text="Report", callback_data="log_tog_rep")],
    ])
    msg = update.effective_message
    await msg.reply_text("Toggle channel log settings", reply_markup=btn)


from Cutiepii_Robot.modules.sql import log_channel_sql as sql


async def log_setting_callback(update: Update,
                               context: CallbackContext) -> None:
    cb = update.callback_query
    user = cb.from_user
    chat = cb.message.chat
    if not await is_user_admin(update, user.id):
        cb.answer("You aren't admin", show_alert=True)
        return
    setting = cb.data.replace("log_tog_", "")
    chat_set = sql.get_chat_setting(chat_id=chat.id)
    if not chat_set:
        sql.set_chat_setting(setting=sql.LogChannelSettings(
            chat.id, True, True, True, True, True))

    t = sql.get_chat_setting(chat.id)
    if setting == "warn":
        r = t.toggle_warn()
        cb.answer(f"Warning log set to {r}")
        return
    if setting == "act":
        r = t.toggle_action()
        cb.answer(f"Action log set to {r}")
        return
    if setting == "join":
        r = t.toggle_joins()
        cb.answer(f"Join log set to {r}")
        return
    if setting == "leave":
        r = t.toggle_leave()
        cb.answer(f"Leave log set to {r}")
        return
    if setting == "rep":
        r = t.toggle_report()
        cb.answer(f"Report log set to {r}")
        return

    cb.answer("Idk what to do")

    CUTIEPII_PTB.add_handler(CommandHandler("logchannel", logging))
    CUTIEPII_PTB.add_handler(
        CallbackQueryHandler(unbanb_btn, pattern=r"unbanb_"))
    CUTIEPII_PTB.add_handler(CommandHandler("unsetlog", unsetlog))
    CUTIEPII_PTB.add_handler(CommandHandler("logsettings", unsetlog))
    CUTIEPII_PTB.add_handler(
        CallbackQueryHandler(log_setting_callback, pattern=r"log_tog_.*"))
