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
import re

from typing import Optional, Union

from telegram import Message, Chat, Update, User, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.helpers import mention_html
from telegram.ext import ContextTypes, filters
from telegram.error import BadRequest

from Cutiepii_Robot import WHITELIST_USERS, LOGGER
from Cutiepii_Robot.modules.sql.approve_sql import is_approved
from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status
from Cutiepii_Robot.modules.helper_funcs.string_handling import extract_time
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.sql import antiflood_sql as sql
from Cutiepii_Robot.modules.helper_funcs.alternate import send_message
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    user_is_admin
)


FLOOD_GROUP = -5


async def mention_html_chat(chat_id: Union[int, str], name: str) -> str:
    return f'<a href="tg://t.me/{chat_id}">{html.escape(name)}</a>'


@cutiepii_msg(
        (filters.ALL
         & filters.ChatType.GROUPS
         & ~filters.StatusUpdate.ALL
         & ~filters.UpdateType.EDITED_MESSAGE
         & ~filters.ChatType.CHANNEL),
        group=FLOOD_GROUP)
@connection_status
@loggable
async def check_flood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    tag = "None"
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message
    if not user:  # ignore channels
        return ""

    if await user_is_admin(update, user.id, channels = True) or user.id in WHITELIST_USERS:
        sql.update_flood(chat.id, None)
        return ""

    if is_approved(chat.id, user.id):
        sql.update_flood(chat.id, None)
        return

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        getmode, getvalue = sql.get_flood_setting(chat.id)
        execstrings = ""
        if getmode == 1:
            await chat.ban_member(user.id)
            execstrings = "Banned"
            tag = "BANNED"
        elif getmode == 2:
            await chat.ban_member(user.id)
            await chat.unban_member(user.id)
            execstrings = "Kicked"
            tag = "KICKED"
        elif getmode == 3:
            await context.bot.restrict_chat_member(
                chat.id, user.id, permissions=ChatPermissions(can_send_messages=False)
            )
            execstrings = "Muted"
            tag = "MUTED"
        elif getmode == 4:
            bantime = await extract_time(msg, getvalue)
            await chat.ban_member(user.id, until_date=bantime)
            execstrings = "Banned for {}".format(getvalue)
            tag = "TBAN"
        elif getmode == 5:
            mutetime = await extract_time(msg, getvalue)
            await context.bot.restrict_chat_member(
                chat.id,
                user.id,
                until_date=mutetime,
                permissions=ChatPermissions(can_send_messages=False),
            )
            execstrings = "Muted for {}".format(getvalue)
            tag = "TMUTE"
        await send_message(
            update.effective_message, "*Anti Flood Triggered!\n{}!".format(execstrings)
        )

        return (
            "<b>{}:</b>"
            "\n#{}"
            "\n<b>User:</b> {}"
            "\nFlooded the group.".format(
                tag, html.escape(chat.title), mention_html(user.id, user.first_name)
            )
        )

    except BadRequest:
        await msg.reply_text(
            "I can't restrict people here, give me permissions first! Until then, I'll disable anti-flood."
        )
        sql.set_flood(chat.id, 0)
        return (
            "<b>{}:</b>"
            "\n#INFO"
            "\nDon't have enough permission to restrict users so automatically disabled anti-flood".format(
                chat.title
            )
        )


@cutiepii_msg(
        (filters.ALL
         & ~filters.StatusUpdate.ALL
         & filters.ChatType.GROUPS
         & ~filters.UpdateType.EDITED_MESSAGE
         & filters.ChatType.CHANNEL),
        group=-6)
@connection_status
@loggable
async def check_channel_flood(update: Update, _: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    msg = update.effective_message
    user = msg.sender_chat
    chat = update.effective_chat
    if not user:  # only for channels
        return ""

    if is_approved(chat.id, user.id):
        sql.update_flood(chat.id, None)
        return

    should_ban = sql.update_flood(chat.id, user.id)
    if not should_ban:
        return ""

    try:
        await chat.ban_sender_chat(user.id)
        execstrings = "Banned Channel: " + user.title
        tag = "BANNED"
        await send_message(
            update.effective_message, "*Anti Flood Triggered!\n{}!".format(execstrings)
        )

        return (
            "<b>{}:</b>"
            "\n#{}"
            "\n<b>User:</b> {}"
            "\nFlooded the group.".format(
                tag, html.escape(chat.title), mention_html_chat(user.id, user.title)
            )
        )

    except BadRequest:
        await msg.reply_text(
            "I can't restrict people here, give me permissions first! Until then, I'll disable anti-flood."
        )
        sql.set_flood(chat.id, 0)
        return (
            "<b>{}:</b>"
            "\n#INFO"
            "\nDon't have enough permission to restrict users so automatically disabled anti-flood".format(
                chat.title
            )
        )


@cutiepii_callback(pattern=r"unmute_flooder")
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True, noreply = True)
@loggable
async def flood_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    admeme = await chat.get_member(user.id)
    match = re.match(r"unmute_flooder\((.+?)\)", query.data)

    if match:
        user_id = match.group(1)
        try:
            await bot.restrict_chat_member(
                chat.id,
                int(user_id),
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_audios=True,
                    can_send_documents=True,
                    can_send_photos=True,
                    can_send_videos=True,
                    can_send_video_notes=True,
                    can_send_voice_notes=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            await update.effective_message.edit_text(
                f"Unmuted{f' by {mention_html(user.id, user.first_name)}' if not admeme.status == ChatMemberStatus.OWNER else ''}.",
                parse_mode="HTML",
            )
            logmsg = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#UNMUTE_FLOODER\n"
                    f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
                    f"<b>User:</b> {mention_html(user_id, html.escape((await chat.get_member(user_id)).user.first_name))}\n"
            )
            return logmsg
        except Exception as e:
            await update.effective_message.edit_text("An error occurred while unmuting!\n<code>{}</code>".format(e))


@cutiepii_cmd(command='setflood', rate_limit_calls=5, rate_limit_window=60, add_error_handler=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def set_flood(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:  # sourcery no-metrics
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    user = update.effective_user
    chat_name = chat.title

    if len(args) >= 1:
        val = args[0].lower()
        if val in ["off", "no", "0"]:
            sql.set_flood(chat.id, 0)
            await message.reply_text("<b>Flood Control Updated</b>\nAnti-flood limits have been disabled for this chat.")

        elif val.isdigit():
            amount = int(val)
            if amount <= 0:
                sql.set_flood(chat.id, 0)
                await message.reply_text("<b>Flood Control Updated</b>\nAnti-flood limits have been disabled for this chat.")
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin:</b> {}"
                    "\nDisable antiflood.".format(
                        html.escape(chat_name), mention_html(user.id, user.first_name)
                    )
                )

            elif amount <= 3:
                await send_message(
                    update.effective_message,
                    "<b>Invalid Limit</b>\nAnti-flood threshold must be 0 (disabled) or a number greater than 3.",
                )
                return ""

            else:
                sql.set_flood(chat.id, amount)
                await message.reply_text("<b>Flood Control Updated</b>\nSuccessfully updated anti-flood limit threshold to <code>{}</code> messages.".format(amount))
                return (
                    "<b>{}:</b>"
                    "\n#SETFLOOD"
                    "\n<b>Admin:</b> {}"
                    "\nSet antiflood to <code>{}</code>.".format(
                        html.escape(chat_name),
                        mention_html(user.id, user.first_name),
                        amount,
                    )
                )

        else:
            await message.reply_text("<b>Invalid Argument</b>\nPlease specify a numeric limit, <code>off</code>, or <code>no</code>.")
    else:
        await message.reply_text(
            "<b>Flood Control Configuration</b>\n"
            "Use <code>/setflood [number]</code> to configure anti-flood threshold.\n"
            "Use <code>/setflood off</code> to disable flood control.",
            parse_mode=ParseMode.HTML,
        )
    return ""


@cutiepii_cmd(command="flood", rate_limit_calls=10, rate_limit_window=60, add_error_handler=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check()
async def flood(update: Update, _: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message

    limit = sql.get_flood_limit(chat.id)
    flood_type = await get_flood_type(chat.id)
    
    if limit == 0:
        buttons = [
            [InlineKeyboardButton("🔢 Set Limit: 5", callback_data="antiflood_set_5"),
             InlineKeyboardButton("🔢 Set Limit: 10", callback_data="antiflood_set_10")],
            [InlineKeyboardButton("🔢 Set Limit: 15", callback_data="antiflood_set_15"),
             InlineKeyboardButton("🔢 Set Limit: 20", callback_data="antiflood_set_20")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="antiflood_help"),
             InlineKeyboardButton("❌ Close", callback_data="antiflood_close")]
        ]
        await msg.reply_text(
            "🔕 <b>Antiflood Disabled</b>\n\n"
            "I'm not currently enforcing any flood control here!\n\n"
            "<i>Use the buttons below to set a limit.</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        buttons = [
            [InlineKeyboardButton("➕ Increase", callback_data="antiflood_increase"),
             InlineKeyboardButton("➖ Decrease", callback_data="antiflood_decrease")],
            [InlineKeyboardButton("🔧 Change Mode", callback_data="antiflood_mode"),
             InlineKeyboardButton("🔕 Disable", callback_data="antiflood_disable")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="antiflood_help"),
             InlineKeyboardButton("❌ Close", callback_data="antiflood_close")]
        ]
        await msg.reply_text(
            f"🛡️ <b>Antiflood Settings</b>\n\n"
            f"<b>Current Limit:</b> {limit} messages\n"
            f"<b>Action Mode:</b> {flood_type}\n\n"
            f"<i>Members will be restricted after {limit} consecutive messages.</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )


@cutiepii_cmd(command=["setfloodmode", "floodmode"])
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@connection_status
@loggable
async def set_flood_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:  # sourcery no-metrics
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message

    if args := context.args:
        settypeflood = ""
        if args[0].lower() == "ban":
            settypeflood = "ban"
            sql.set_flood_strength(chat.id, 1, "0")
        elif args[0].lower() == "kick":
            settypeflood = "kick"
            sql.set_flood_strength(chat.id, 2, "0")
        elif args[0].lower() == "mute":
            settypeflood = "mute"
            sql.set_flood_strength(chat.id, 3, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                await send_message(update.effective_message, tflood_help_msg.format("tban"), parse_mode="markdown")
                return
            settypeflood = "tban for {}".format(args[1])
            sql.set_flood_strength(chat.id, 4, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                await send_message(update.effective_message, tflood_help_msg.format("tmute"), parse_mode="markdown")
                return
            settypeflood = "tmute for {}".format(args[1])
            sql.set_flood_strength(chat.id, 5, str(args[1]))
        else:
            await send_message(
                update.effective_message, "I only understand ban/kick/mute/tban/tmute!"
            )
            return
        await msg.reply_text(
                "Exceeding consecutive flood limit will result in {}!".format(settypeflood)
            )
        return (
            "<b>{}:</b>\n"
            "#FLOODMODE\n"
            "<b>Admin:</b> {}\n"
            "New Flood Mode: {}.".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                settypeflood,
            )
        )
    else:
        flood_type = await get_flood_type(chat.id)

        await msg.reply_text("Sending more message than flood limit will result in {}.".format(flood_type))

    return ""


async def get_flood_type(chat_id: int) -> str:
    global settypeflood
    getmode, getvalue = sql.get_flood_setting(chat_id)
    if getmode == 1:
        settypeflood = "ban"
    elif getmode == 2:
        settypeflood = "kick"
    elif getmode == 3:
        settypeflood = "mute"
    elif getmode == 4:
        settypeflood = "tban for {}".format(getvalue)
    elif getmode == 5:
        settypeflood = "tmute for {}".format(getvalue)
    return settypeflood


tflood_help_msg = ("It looks like you tried to set time value for antiflood but you didn't specified time; "
                   "Try, `/setfloodmode {} <timevalue>`."
                   "Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks.")


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


async def __chat_settings__(chat_id, user_id):
    limit = sql.get_flood_limit(chat_id)
    if limit == 0:
        return "Not enforcing to flood control."
    else:
        return "Antiflood has been set to`{}`.".format(limit)


__help__ = True


# Callback handler for antiflood module buttons
@cutiepii_callback(pattern=r"^antiflood_")
async def antiflood_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str = None):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    query = update.callback_query
    await query.answer()
    if data is None:
        data = query.data
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if user is admin
    from Cutiepii_Robot.modules.helper_funcs.admin_status import user_is_admin
    if not await user_is_admin(chat, user.id):
        await query.answer("⚠️ You need to be an admin to use this!", show_alert=True)
        return
    
    if data == "antiflood_close":
        await query.message.delete()
        return
    
    if data == "antiflood_help":
        help_text = """
<b>ℹ️ Antiflood System Help</b>

<b>What is antiflood?</b>
Prevents spam by restricting users who send too many consecutive messages.

<b>Available Actions:</b>
- Ban - Permanently ban the user
- Kick - Remove from group
- Mute - Silence the user
- Tban - Temporary ban (select time via buttons)
- Tmute - Temporary mute (select time via buttons)

<b>Time Formats:</b>
- m = minutes (e.g., 5m, 30m)
- h = hours (e.g., 1h, 6h)
- d = days (e.g., 1d, 3d)
- w = weeks (e.g., 1w, 2w)

<b>Quick Commands:</b>
❍ /flood - View current settings
❍ /setflood <number> - Set limit
❍ /setfloodmode <action> - Change action

<i>Admins are automatically ignored!</i>
        """
        buttons = [
            [InlineKeyboardButton("« Back", callback_data="antiflood_settings"),
             InlineKeyboardButton("❌ Close", callback_data="antiflood_close")]
        ]
        await query.message.edit_text(help_text, parse_mode=ParseMode.HTML,
                                     reply_markup=InlineKeyboardMarkup(buttons))
        return
    
    if data == "antiflood_settings" or data.startswith("antiflood_set_"):
        if data.startswith("antiflood_set_"):
            limit_val = int(data.split("_")[-1])
            sql.set_flood(chat.id, limit_val)
            await query.answer(f"✅ Set limit to {limit_val}", show_alert=True)
        
        limit = sql.get_flood_limit(chat.id)
        flood_type = await get_flood_type(chat.id)
        
        if limit == 0:
            buttons = [
                [InlineKeyboardButton("🔢 Set Limit: 5", callback_data="antiflood_set_5"),
                 InlineKeyboardButton("🔢 Set Limit: 10", callback_data="antiflood_set_10")],
                [InlineKeyboardButton("🔢 Set Limit: 15", callback_data="antiflood_set_15"),
                 InlineKeyboardButton("🔢 Set Limit: 20", callback_data="antiflood_set_20")],
                [InlineKeyboardButton("ℹ️ Help", callback_data="antiflood_help"),
                 InlineKeyboardButton("❌ Close", callback_data="antiflood_close")]
            ]
            await query.message.edit_text(
                "🔕 <b>Antiflood Disabled</b>\n\n"
                "I'm not currently enforcing any flood control here!\n\n"
                "<i>Use the buttons below to set a limit.</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            buttons = [
                [InlineKeyboardButton("➕ Increase", callback_data="antiflood_increase"),
                 InlineKeyboardButton("➖ Decrease", callback_data="antiflood_decrease")],
                [InlineKeyboardButton("🔧 Change Mode", callback_data="antiflood_mode"),
                 InlineKeyboardButton("🔕 Disable", callback_data="antiflood_disable")],
                [InlineKeyboardButton("ℹ️ Help", callback_data="antiflood_help"),
                 InlineKeyboardButton("❌ Close", callback_data="antiflood_close")]
            ]
            await query.message.edit_text(
                f"🛡️ <b>Antiflood Settings</b>\n\n"
                f"<b>Current Limit:</b> {limit} messages\n"
                f"<b>Action Mode:</b> {flood_type}\n\n"
                f"<i>Members will be restricted after {limit} consecutive messages.</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        return
    
    if data == "antiflood_increase":
        limit = sql.get_flood_limit(chat.id)
        new_limit = limit + 5
        sql.set_flood(chat.id, new_limit)
        await query.answer(f"✅ Increased to {new_limit}", show_alert=True)
        # Redirect to settings view
        await antiflood_callback(update, context, data="antiflood_settings")
        return
    
    if data == "antiflood_decrease":
        limit = sql.get_flood_limit(chat.id)
        new_limit = max(4, limit - 5)
        sql.set_flood(chat.id, new_limit)
        await query.answer(f"✅ Decreased to {new_limit}", show_alert=True)
        # Redirect to settings view
        await antiflood_callback(update, context, data="antiflood_settings")
        return
    
    if data == "antiflood_disable":
        sql.set_flood(chat.id, 0)
        await query.answer("✅ Antiflood disabled!", show_alert=True)
        # Redirect to settings view
        await antiflood_callback(update, context, data="antiflood_settings")
        return
    
    if data == "antiflood_mode":
        buttons = [
            [InlineKeyboardButton("🚫 Ban", callback_data="antiflood_mode_ban"),
             InlineKeyboardButton("👢 Kick", callback_data="antiflood_mode_kick")],
            [InlineKeyboardButton("🔇 Mute", callback_data="antiflood_mode_mute")],
            [InlineKeyboardButton("⏱️ Temp Ban", callback_data="antiflood_mode_tban"),
             InlineKeyboardButton("⏱️ Temp Mute", callback_data="antiflood_mode_tmute")],
            [InlineKeyboardButton("« Back", callback_data="antiflood_settings"),
             InlineKeyboardButton("❌ Close", callback_data="antiflood_close")]
        ]
        await query.message.edit_text(
            "<b>🔧 Select Flood Action Mode</b>\n\n"
            "Choose what action to take when a user floods:\n\n"
            "<b>Permanent Actions:</b>\n"
            "- 🚫 Ban - Permanently ban\n"
            "- 👢 Kick - Remove from group\n"
            "- 🔇 Mute - Silence permanently\n\n"
            "<b>Temporary Actions:</b>\n"
            "- ⏱️ Temp Ban - Ban for a time period\n"
            "- ⏱️ Temp Mute - Mute for a time period",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
    
    # Handle time selection for tban/tmute
    if data.startswith("antiflood_time_"):
        parts = data.split("_")
        if len(parts) >= 4:
            action_type = parts[2]  # tban or tmute
            time_value = "_".join(parts[3:])  # Handle time values like "1h" or "30m"
            
            mode_map = {"tban": 4, "tmute": 5}
            if action_type in mode_map:
                sql.set_flood_strength(chat.id, mode_map[action_type], time_value)
                action_name = "Temporary Ban" if action_type == "tban" else "Temporary Mute"
                await query.answer(f"✅ {action_name} set to {time_value}!", show_alert=True)
                # Redirect to settings view
                await antiflood_callback(update, context, data="antiflood_settings")
        return
    
    # Handle mode selection (ban, kick, mute, or show time selector for tban/tmute)
    if data.startswith("antiflood_mode_"):
        mode = data.split("_")[-1]
        mode_map = {"ban": 1, "kick": 2, "mute": 3}
        
        if mode in mode_map:
            # Permanent actions - set immediately
            sql.set_flood_strength(chat.id, mode_map[mode], "0")
            await query.answer(f"✅ Mode set to {mode.upper()}", show_alert=True)
            # Redirect to settings view
            await antiflood_callback(update, context, data="antiflood_settings")
        elif mode in ["tban", "tmute"]:
            # Temporary actions - show time selection
            action_name = "Temporary Ban" if mode == "tban" else "Temporary Mute"
            buttons = [
                [InlineKeyboardButton("⏱️ 5 Minutes", callback_data=f"antiflood_time_{mode}_5m"),
                 InlineKeyboardButton("⏱️ 15 Minutes", callback_data=f"antiflood_time_{mode}_15m")],
                [InlineKeyboardButton("⏱️ 30 Minutes", callback_data=f"antiflood_time_{mode}_30m"),
                 InlineKeyboardButton("⏱️ 1 Hour", callback_data=f"antiflood_time_{mode}_1h")],
                [InlineKeyboardButton("⏱️ 6 Hours", callback_data=f"antiflood_time_{mode}_6h"),
                 InlineKeyboardButton("⏱️ 12 Hours", callback_data=f"antiflood_time_{mode}_12h")],
                [InlineKeyboardButton("⏱️ 1 Day", callback_data=f"antiflood_time_{mode}_1d"),
                 InlineKeyboardButton("⏱️ 1 Week", callback_data=f"antiflood_time_{mode}_1w")],
                [InlineKeyboardButton("« Back to Modes", callback_data="antiflood_mode"),
                 InlineKeyboardButton("❌ Close", callback_data="antiflood_close")]
            ]
            await query.message.edit_text(
                f"<b>⏱️ Select Time for {action_name}</b>\n\n"
                f"Choose how long to {mode.replace('tban', 'ban').replace('tmute', 'mute')} users who flood:\n\n"
                f"<b>Quick Presets:</b>\n"
                f"- 5m, 15m, 30m - Short durations\n"
                f"- 1h, 6h, 12h - Medium durations\n"
                f"- 1d, 1w - Long durations\n\n"
                f"<i>For custom time, use command:</i>\n"
                f"<code>/setfloodmode {mode} &lt;time&gt;</code>\n"
                f"<i>Example: /setfloodmode {mode} 2h</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        return

__mod_name__ = "Anti-Flood"
