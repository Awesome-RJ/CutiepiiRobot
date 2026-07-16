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
DAMAGE (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import html

from Cutiepii_Robot import LOGGER, SUDO_USERS, WHITELIST_USERS
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.sql import reporting_sql as sql
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import BadRequest
from telegram.ext import (
    ContextTypes,
    filters,
)
from Cutiepii_Robot.modules.helper_funcs.admin_status_helpers import get_admin_item
import Cutiepii_Robot.modules.sql.log_channel_sql as logsql
from telegram.helpers import mention_html
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    user_not_admin_check,
    user_is_admin,
)

REPORT_GROUP = 12
REPORT_IMMUNE_USERS = SUDO_USERS + WHITELIST_USERS

@cutiepii_cmd(command='reports')
@bot_admin_check()
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
async def report_setting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    chat = update.effective_chat
    msg = update.effective_message

    if len(args) >= 1:
        if args[0] in ("yes", "on"):
            sql.set_chat_setting(chat.id, True)
            await msg.reply_text(
                "<b>Reporting Enabled</b>\nAdmin notifications for <code>/report</code> and <code>@admin</code> have been activated."
            )

        elif args[0] in ("no", "off"):
            sql.set_chat_setting(chat.id, False)
            await msg.reply_text(
                "<b>Reporting Disabled</b>\nAdmin notifications for <code>/report</code> and <code>@admin</code> have been deactivated."
            )
    else:
        await msg.reply_text(
            f"<b>Reporting Status</b>\nGroup reporting status: <code>{sql.chat_should_report(chat.id)}</code>",
            parse_mode=ParseMode.HTML,
        )


@cutiepii_cmd(command='report', filters=filters.ChatType.GROUPS, group=REPORT_GROUP)
@cutiepii_msg((filters.Regex(r"(?i)@admin(s)?")), group=REPORT_GROUP)
@user_not_admin_check
@loggable
async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not chat or not sql.chat_should_report(chat.id):
        return ""

    if not message.reply_to_message:
        await message.reply_text("<b>Invalid Command Usage</b>\nPlease reply to the message you want to report to administrators.", parse_mode=ParseMode.HTML)
        return ""

    log_setting = logsql.get_chat_setting(chat.id)
    if not log_setting:
        logsql.set_chat_setting(chat.id, True, True, True, True, True)
        log_setting = logsql.get_chat_setting(chat.id)

    reported_user = message.reply_to_message.from_user

    if user.id == reported_user.id:
        await message.reply_text("<b>Action Denied</b>\nYou cannot report yourself.", parse_mode=ParseMode.HTML)
        return ""

    if reported_user.id == bot.id:
        await message.reply_text("<b>Action Denied</b>\nI cannot process a report against myself.", parse_mode=ParseMode.HTML)
        return ""

    if reported_user.id in REPORT_IMMUNE_USERS:
        await message.reply_text("<b>Action Denied</b>\nSuper users cannot be reported.", parse_mode=ParseMode.HTML)
        return ""

    admin_list = []
    try:
        admins_data = get_admin_item(chat.id)
        for key, val in admins_data.items():
            if val['user']['is_bot'] or val['is_anonymous']:
                continue
            admin_list.append(int(key))
    except (KeyError, Exception):
        pass

    if not admin_list:
        try:
            admins = await bot.get_chat_administrators(chat.id)
            for admin in admins:
                if admin.user.is_bot or admin.is_anonymous:
                    continue
                admin_list.append(admin.user.id)
        except Exception as e:
            LOGGER.warning(f"Could not fetch chat administrators for report in {chat.id}: {e}")

    if reported_user.id in admin_list:
        await message.reply_text("<b>Action Denied</b>\nAdministrators cannot be reported.", parse_mode=ParseMode.HTML)
        return ""

    if message.sender_chat:
        reported = "Reported to administrators."
        for admin in admin_list:
            reported += f"<a href=\"tg://user?id={admin}\">\u2063</a>"
        await message.reply_text(reported, parse_mode = ParseMode.HTML)
        return ""

    msg_log = (
        f"<b>Report: </b>{html.escape(chat.title)}\n"
        f"<b>- Report by:</b> {mention_html(user.id, user.first_name)} (<code>{user.id}</code>)\n"
        f"<b>- Reported user:</b> {mention_html(reported_user.id, reported_user.first_name)} (<code>{reported_user.id}</code>)\n"
    )
    tmsg = ""
    for admin in admin_list:
        link = mention_html(admin, "​")
        tmsg += link

    keyboard2 = [
        [
            InlineKeyboardButton(
                "Kick",
                callback_data=f"reported_{chat.id}=kick={reported_user.id}",
            ),
            InlineKeyboardButton(
                "Ban",
                callback_data=f"reported_{chat.id}=banned={reported_user.id}",
            ),
        ],
        [
            InlineKeyboardButton(
                "Delete Message",
                callback_data=f"reported_{chat.id}=delete={reported_user.id}={message.reply_to_message.message_id}",
            ),
            InlineKeyboardButton(
                "Close Panel",
                callback_data=f"reported_{chat.id}=close={reported_user.id}",
            )
        ],
        [
            InlineKeyboardButton(
                    "Rules", url="t.me/{}?start={}".format(bot.username, chat.id)
                )
        ],
    ]
    reply_markup2 = InlineKeyboardMarkup(keyboard2)
    reportmsg = f"{mention_html(reported_user.id, reported_user.first_name)} has been reported to the administrators."
    reportmsg += tmsg
    await message.reply_text(
        reportmsg,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup2
    )
    if not log_setting.log_report:
        return ""
    return msg_log


@cutiepii_callback(pattern=r"reported_")
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods=True, noreply = True)
@loggable
async def report_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    query = update.callback_query
    splitter = query.data.replace("reported_", "").split("=")
    chat_id = int(splitter[0])
    action = splitter[1]
    user_id = int(splitter[2]) if len(splitter) > 2 else None

    if action == "kick":
        try:
            await bot.ban_chat_member(chat_id, user_id)
            await bot.unban_chat_member(chat_id, user_id)
            await query.answer("Successfully kicked")
            return ""
        except Exception as err:
            await query.answer(f"Failed to kick: {err}")
    elif action == "banned":
        try:
            await bot.ban_chat_member(chat_id, user_id)
            await query.answer("Successfully banned")
            return ""
        except Exception as err:
            await query.answer(f"Failed to ban: {err}", show_alert=True)
    elif action == "delete":
        try:
            msg_id = int(splitter[3])
            await bot.delete_message(chat_id, msg_id)
            await query.answer("Message deleted")

            kyb_no_del = [
                [
                    InlineKeyboardButton(
                        "Kick",
                        callback_data=f"reported_{chat_id}=kick={user_id}",
                    ),
                    InlineKeyboardButton(
                        "Ban",
                        callback_data=f"reported_{chat_id}=banned={user_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        "Close Panel",
                        callback_data=f"reported_{chat_id}=close={user_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "Rules", url="t.me/{}?start={}".format(bot.username, chat_id),
                    )
                ],
            ]

            await query.edit_message_reply_markup(
                InlineKeyboardMarkup(kyb_no_del)
            )
            return ""
        except Exception as err:
            await query.answer(
                text=f"Failed to delete message: {err}",
                show_alert=True
            )
    elif action == "close":
        try:
            await query.answer("Panel closed")

            kyb_no_del = [
                [
                    InlineKeyboardButton(
                        "Rules", url="t.me/{}?start={}".format(bot.username, chat_id),
                    )
                ],
            ]

            await query.edit_message_reply_markup(
                InlineKeyboardMarkup(kyb_no_del)
            )
            return ""
        except Exception as err:
            await query.answer(
                text=f"Failed to close panel: {err}",
                show_alert=True
            )


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


async def __chat_settings__(chat_id, _):
    return f"This chat is setup to send user reports to admins, via /report and @admin: <code>{sql.chat_should_report(chat_id)}</code>"


def __user_settings__(user_id):
    if sql.user_should_report(user_id) is True:
        return "You will receive reports from chats you're admin."
    else:
        return "You will not receive reports from chats you're admin."