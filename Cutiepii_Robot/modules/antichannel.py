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
from typing import Optional

from telegram import Update
from telegram.error import TelegramError
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, filters
from telegram.helpers import mention_html
from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.sql.approve_sql import is_approved
from Cutiepii_Robot.modules.helper_funcs.admin_status import user_admin_check, bot_admin_check, AdminPerms, bot_is_admin
from Cutiepii_Robot.modules.sql.antichannel_sql import antichannel_status, disable_antichannel, enable_antichannel

@cutiepii_cmd(command="antichannel", group=100)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def set_antichannel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user = update.effective_user

    if len(args) > 0:
        s = args[0].lower()

        if s in ["yes", "on", "true"]:
            enable_antichannel(chat.id)
            await message.reply_html("<b>Anti Channel Updated</b>\nAnti-channel protection has been enabled for <b>{}</b>.".format(html.escape(chat.title)))
            log_message = (
                f"#ANTICHANNEL\n"
                f"Enabled\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
            )
            return log_message

        elif s in ["off", "no", "false"]:
            disable_antichannel(chat.id)
            await message.reply_html("<b>Anti Channel Updated</b>\nAnti-channel protection has been disabled for <b>{}</b>.".format(html.escape(chat.title)))
            log_message = (
                f"#ANTICHANNEL\n"
                f"Disabled\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
            )
            return log_message

        else:
            await message.reply_text("<b>Invalid Argument</b>\nUnrecognized argument: <code>{}</code>. Accepted values: <code>yes</code>, <code>on</code>, <code>no</code>, <code>off</code>.".format(html.escape(s)), parse_mode=ParseMode.HTML)
            return

    await message.reply_html(
        "<b>Anti Channel Status</b>\nChat: <b>{}</b>\nStatus: <code>{}</code>".format(html.escape(chat.title), "Enabled" if antichannel_status(chat.id) else "Disabled"))
    return


@cutiepii_msg(filters.ChatType.GROUPS & filters.ChatType.CHANNEL & ~filters.IS_AUTOMATIC_FORWARD, group=110)
async def eliminate_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    bot = context.bot
    if not antichannel_status(chat.id):
        return

    # ignore approved users
    if is_approved(chat.id, message.sender_chat.id):
        return

    await message.delete()
    sender_chat = message.sender_chat
    try:
        await bot.ban_chat_sender_chat(sender_chat_id=sender_chat.id, chat_id=chat.id)
    except TelegramError:
        if not await bot_is_admin(chat, AdminPerms.CAN_RESTRICT_MEMBERS):
            disable_antichannel(chat.id)
            await message.reply_text("<b>Action Denied</b>\nI do not have member restriction permissions. Anti-channel protection has been disabled.", parse_mode=ParseMode.HTML)
