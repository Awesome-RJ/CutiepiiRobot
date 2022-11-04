"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2022, Yūki • Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

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

from Cutiepii_Robot import LOGGER, SUDO_USERS, WHITELIST_USERS, CUTIEPII_PTB
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.sql import reporting_sql as sql
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    CallbackContext,
    filters,
    CallbackQueryHandler,
    CommandHandler,
)
import Cutiepii_Robot.modules.sql.log_channel_sql as logsql
from telegram.helpers import mention_html

from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check, bot_admin_check, AdminPerms, user_not_admin_check,
    A_CACHE)

REPORT_GROUP = 12
REPORT_IMMUNE_USERS = SUDO_USERS + WHITELIST_USERS


@bot_admin_check()
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def report_setting(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if len(args) >= 1:
        if args[0] in ("yes", "on"):
            sql.set_chat_setting(chat.id, True)
            await msg.reply_text(
                "Turned on reporting! Admins who have turned on reports will be notified when /report "
                "or @admin is called.")

        elif args[0] in ("no", "off"):
            sql.set_chat_setting(chat.id, False)
            await msg.reply_text(
                "Turned off reporting! No admins will be notified on /report or @admin."
            )
    else:
        await msg.reply_text(
            f"This group's current setting is: `{sql.chat_should_report(chat.id)}`",
            parse_mode=ParseMode.MARKDOWN,
        )


@user_not_admin_check
@loggable
async def report(update: Update, context: CallbackContext) -> str:
    # sourcery no-metrics
    global reply_markup
    bot = context.bot
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    log_setting = logsql.get_chat_setting(chat.id)
    if not log_setting:
        logsql.set_chat_setting(
            logsql.LogChannelSettings(chat.id, True, True, True, True, True))
        log_setting = logsql.get_chat_setting(chat.id)

    if chat and message.reply_to_message and sql.chat_should_report(chat.id):
        reported_user = message.reply_to_message.from_user

        if user.id == reported_user.id:
            await message.reply_text("Uh yeah, Sure sure...maso much?")
            return ""

        if reported_user.id == bot.id:
            await message.reply_text("Nice try.")
            return ""

        if reported_user.id in REPORT_IMMUNE_USERS:
            await message.reply_text("Uh? You reporting a Super user?")
            return ""

        admin_list = [
            i.user.id for i in A_CACHE[chat.id]
            if not (i.user.is_bot or i.is_anonymous)
        ]

        if reported_user.id in admin_list:
            await message.reply_text("Why are you reporting an admin?")
            return ""

        if message.sender_chat:
            reported = "Reported to admins."
            for admin in admin_list:
                try:
                    reported += f"<a href=\"tg://user?id={admin}\">\u2063</a>"
                except BadRequest:
                    LOGGER.exception(
                        f"Exception while reporting user: {user} in chat: {chat.id}"
                    )
            await message.reply_text(reported, parse_mode=ParseMode.HTML)

        message = update.effective_message
        msg = (
            f"<b>⚠️ Report: </b>{html.escape(chat.title)}\n"
            f"<b> • Report by:</b> {mention_html(user.id, user.first_name)}(<code>{user.id}</code>)\n"
            f"<b> • Reported user:</b> {mention_html(reported_user.id, reported_user.first_name)} (<code>{reported_user.id}</code>)\n"
        )
        tmsg = ""
        for admin in admin_list:
            link = mention_html(admin, "​")  # contains 0 width chatacters
            tmsg += link

        keyboard2 = [
            [
                InlineKeyboardButton(
                    "⚠ Kick",
                    callback_data=f"reported_{chat.id}=kick={reported_user.id}",
                ),
                InlineKeyboardButton(
                    "⛔️ Ban",
                    callback_data=
                    f"reported_{chat.id}=banned={reported_user.id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "❎ Delete Message",
                    callback_data=
                    f"reported_{chat.id}=delete={reported_user.id}={message.reply_to_message.message_id}",
                ),
                InlineKeyboardButton(
                    "❌ Close Panel",
                    callback_data=
                    f"reported_{chat.id}=close={reported_user.id}",
                )
            ],
            [
                InlineKeyboardButton("📝 Read the rules",
                                     url="t.me/{}?start={}".format(
                                         bot.username, chat.id))
            ],
        ]
        reply_markup2 = InlineKeyboardMarkup(keyboard2)
        reportmsg = f"{mention_html(reported_user.id, reported_user.first_name)} was reported to the admins."
        reportmsg += tmsg
        await message.reply_text(reportmsg,
                                 parse_mode=ParseMode.HTML,
                                 reply_markup=reply_markup2)
        if not log_setting.log_report:
            return ""
        return msg
    return ""


@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
async def buttons(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    splitter = query.data.replace("reported_", "").split("=")
    if splitter[1] == "kick":
        try:
            await bot.ban_chat_member(splitter[0], splitter[2])
            await bot.unban_chat_member(splitter[0], splitter[2])
            await query.answer("✅ Succesfully kicked")
            return ""
        except Exception as err:
            query.answer(f"🛑 Failed to kick\n{err}")
    elif splitter[1] == "banned":
        try:
            await bot.ban_chat_member(splitter[0], splitter[2])
            await query.answer("✅  Succesfully Banned")
            return ""
        except Exception as err:
            query.answer(f"🛑 Failed to Ban\n{err}", show_alert=True)
    elif splitter[1] == "delete":
        try:
            bot.deleteMessage(splitter[0], splitter[3])
            await query.answer("✅ Message Deleted")

            kyb_no_del = [
                [
                    InlineKeyboardButton(
                        "⚠ Kick",
                        callback_data=
                        f"reported_{splitter[0]}=kick={splitter[2]}",
                    ),
                    InlineKeyboardButton(
                        "⛔️ Ban",
                        callback_data=
                        f"reported_{splitter[0]}=banned={splitter[2]}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "❌ Close Panel",
                        callback_data=
                        f"reported_{splitter[0]}=close={splitter[2]}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📝 Read the rules",
                        url="t.me/{}?start={}".format(bot.username,
                                                      splitter[0]),
                    )
                ],
            ]

            query.edit_message_reply_markup(InlineKeyboardMarkup(kyb_no_del))
            return ""
        except Exception as err:
            query.answer(text=f"🛑 Failed to delete message!\n{err}",
                         show_alert=True)
    elif splitter[1] == "close":
        try:
            await query.answer("✅ Panel Closed!")

            kyb_no_del = [
                [
                    InlineKeyboardButton(
                        "📝 Read the rules",
                        url="t.me/{}?start={}".format(bot.username,
                                                      splitter[0]),
                    )
                ],
            ]

            query.edit_message_reply_markup(InlineKeyboardMarkup(kyb_no_del))
            return ""
        except Exception as err:
            query.answer(text=f"🛑 Failed to close panel!\n{err}",
                         show_alert=True)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, _):
    return f"This chat is setup to send user reports to admins, via /report and @admin: `{sql.chat_should_report(chat_id)}`"


def __user_settings__(user_id):
    if sql.user_should_report(user_id) is True:
        return "You will receive reports from chats you're admin."
    else:
        return "You will *not* receive reports from chats you're admin."


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, _):
    return f"This chat is setup to send user reports to admins, via /report and @admin: `{sql.chat_should_report(chat_id)}`"


def __user_settings__(user_id):
    if sql.user_should_report(user_id) is True:
        return "You will receive reports from chats you're admin."
    else:
        return "You will *not* receive reports from chats you're admin."


CUTIEPII_PTB.add_handler(CommandHandler("reports", report_setting))
CUTIEPII_PTB.add_handler(
    CommandHandler("report", report, filters=filters.ChatType.GROUPS))
#CUTIEPII_PTB.add_handler(MessageHandler(filters.Regex(r"(?i)@admins(s)?"), report))
CUTIEPII_PTB.add_handler(CallbackQueryHandler(buttons, pattern=r"report_"))

__mod_name__ = "Reporting"
