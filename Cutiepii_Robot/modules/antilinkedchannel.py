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

from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes, filters as Filters
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility

from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    user_is_admin,
    u_na_errmsg
)
import Cutiepii_Robot.modules.sql.antilinkedchannel_sql as sql


@cutiepii_cmd(command="cleanlinked", group=112)
@connection_status
@bot_admin_check(AdminPerms.CAN_DELETE_MESSAGES)
@user_admin_check()
# @loggable
async def set_antilinkedchannel(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    if len(args) > 0:
        if not user_is_admin(update, user.id, perm = AdminPerms.CAN_CHANGE_INFO):
            await message.reply_text("<b>Action Denied</b>\nYou do not have the required administrator privileges in this chat.", parse_mode=ParseMode.HTML)
            return u_na_errmsg(message, AdminPerms.CAN_CHANGE_INFO)

        s = args[0].lower()
        if s in ["yes", "on"]:
            if sql.status_pin(chat.id):
                sql.disable_pin(chat.id)
                sql.enable_linked(chat.id)
                await message.reply_html("<b>CleanLinked Updated</b>\nEnabled CleanLinked and disabled anti-channel pinning in <b>{}</b>.".format(html.escape(chat.title)))
            else:
                sql.enable_linked(chat.id)
                await message.reply_html("<b>CleanLinked Updated</b>\nEnabled anti-linked channel protection in <b>{}</b>.".format(html.escape(chat.title)))
        elif s in ["off", "no"]:
            sql.disable_linked(chat.id)
            await message.reply_html("<b>CleanLinked Updated</b>\nDisabled anti-linked channel protection in <b>{}</b>.".format(html.escape(chat.title)))
        else:
            await message.reply_text("<b>Invalid Argument</b>\nUnrecognized argument: <code>{}</code>. Accepted values: <code>yes</code>, <code>on</code>, <code>no</code>, <code>off</code>.".format(html.escape(s)), parse_mode=ParseMode.HTML)
        return

    await message.reply_html(
        "<b>CleanLinked Status</b>\nChat: <b>{}</b>\nStatus: <code>{}</code>".format(html.escape(chat.title), "Enabled" if sql.status_linked(chat.id) else "Disabled"))


@cutiepii_msg(Filters.IS_AUTOMATIC_FORWARD, group=111)
async def eliminate_linked_channel_msg(update: Update, _: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    if not sql.status_linked(chat.id):
        return
    try:
        await message.delete()
    except TelegramError:
        sql.disable_linked(chat.id)
        await message.reply_text(
            "<b>Action Denied</b>\nI do not have message deletion permissions. CleanLinked has been disabled.",
            parse_mode=ParseMode.HTML
        )
        return


@cutiepii_cmd(command="antichannelpin", group=114)
@connection_status
@bot_admin_check(AdminPerms.CAN_DELETE_MESSAGES)
@user_admin_check()
# @loggable
async def set_antipinchannel(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user = update.effective_user

    if len(args) > 0:
        if not user_is_admin(update, user.id, perm = AdminPerms.CAN_CHANGE_INFO):
            await message.reply_text("<b>Action Denied</b>\nYou do not have the required administrator privileges in this chat.", parse_mode=ParseMode.HTML)
            return u_na_errmsg(message, AdminPerms.CAN_CHANGE_INFO)

        s = args[0].lower()
        if s in ["yes", "on"]:
            if sql.status_linked(chat.id):
                sql.disable_linked(chat.id)
                sql.enable_pin(chat.id)
                await message.reply_html("<b>Anti Channel Pin Updated</b>\nDisabled CleanLinked and enabled anti-channel pinning in <b>{}</b>.".format(html.escape(chat.title)))
            else:
                sql.enable_pin(chat.id)
                await message.reply_html("<b>Anti Channel Pin Updated</b>\nEnabled anti-channel pinning in <b>{}</b>.".format(html.escape(chat.title)))
        elif s in ["off", "no"]:
            sql.disable_pin(chat.id)
            await message.reply_html("<b>Anti Channel Pin Updated</b>\nDisabled anti-channel pinning in <b>{}</b>.".format(html.escape(chat.title)))
        else:
            await message.reply_text("<b>Invalid Argument</b>\nUnrecognized argument: <code>{}</code>. Accepted values: <code>yes</code>, <code>on</code>, <code>no</code>, <code>off</code>.".format(html.escape(s)), parse_mode=ParseMode.HTML)
        return

    await message.reply_html(
        "<b>Anti Channel Pin Status</b>\nChat: <b>{}</b>\nStatus: <code>{}</code>".format(html.escape(chat.title), "Enabled" if sql.status_pin(chat.id) else "Disabled"))


@cutiepii_msg(Filters.IS_AUTOMATIC_FORWARD | Filters.StatusUpdate.PINNED_MESSAGE, group=113)
async def eliminate_linked_channel_msg(update: Update, _: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    if not sql.status_pin(chat.id):
        return

    try:
        message.unpin()
    except TelegramError:
        sql.disable_pin(chat.id)
        await message.reply_text(
            "<b>Action Denied</b>\nI do not have pinned message unpinning permissions. Anti-channel pinning has been disabled.",
            parse_mode=ParseMode.HTML
        )
        return

__mod_name__ = "CleanLinked"

__help__ = True