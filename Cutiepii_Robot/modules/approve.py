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
import Cutiepii_Robot.modules.sql.approve_sql as sql

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import BadRequest
from telegram.ext import ContextTypes, filters
from telegram.helpers import mention_html

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot import SUDO_USERS
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    user_is_admin,
    AdminPerms,
)


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def _mention_from_member(member) -> str:
    """
    Build an HTML mention from a ChatMember object (has .user).
    """
    u = member.user
    return mention_html(u.id, u.first_name or u.username or str(u.id))


async def _mention_from_chat(chat) -> str:
    """
    Build a plain HTML link from a Chat object (channels / group chats used as users).
    """
    title = html.escape(chat.title or chat.username or str(chat.id))
    if chat.username:
        return f'<a href="https://t.me/{chat.username}">{title}</a>'
    return f'<code>{title}</code>'


async def _resolve_user(chat, bot, user_id: int):
    """
    Try to get a ChatMember, falling back to a raw Chat object.
    Returns (member_or_chat, mention_str) or (None, None) on failure.
    """
    try:
        member = await chat.get_member(user_id)
        return member, _mention_from_member(member)
    except BadRequest:
        pass
    try:
        chat_obj = await bot.get_chat(user_id)
        return chat_obj, _mention_from_chat(chat_obj)
    except BadRequest as e:
        if "Chat not found" in e.message:
            return None, None
        raise


# ─────────────────────────────────────────
# Commands
# ─────────────────────────────────────────

@cutiepii_cmd(command='approve', filters=filters.ChatType.GROUPS,
              rate_limit_calls=20, rate_limit_window=60, add_error_handler=True)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@loggable
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    bot = context.bot

    user_id = await extract_user(message, args)
    if not user_id:
        await message.reply_text(
            "<b>User Not Found</b>\n\nSpecify a user to approve — reply to their message or provide a username/ID.",
            parse_mode=ParseMode.HTML
        )
        return ""

    entity, mention = await _resolve_user(chat, bot, user_id)
    if entity is None:
        await message.reply_text("<b>User Not Found</b>\nCannot locate the specified user.", parse_mode=ParseMode.HTML)
        return ""

    # Don't approve admins — they already bypass everything
    status = getattr(getattr(entity, "status", None), "value", None) or getattr(entity, "status", None)
    if status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER,
                  "administrator", "creator"]:
        await message.reply_text(
            "<b>Action Denied</b>\nThe specified user is an administrator and already bypasses locks, blocklists, and antiflood restrictions.",
            parse_mode=ParseMode.HTML
        )
        return ""

    if sql.is_approved(message.chat_id, user_id):
        await message.reply_text(
            f"<b>User Approved Status</b>\n{mention} is already approved in <b>{html.escape(chat_title)}</b>.",
            parse_mode=ParseMode.HTML,
        )
        return ""

    sql.approve(message.chat_id, user_id)

    buttons = [
        [InlineKeyboardButton("Unapprove", callback_data=f"approve_unapprove_{user_id}"),
         InlineKeyboardButton("Approved List", callback_data="approve_list")],
        [InlineKeyboardButton("Close", callback_data="approve_close")]
    ]

    await message.reply_text(
        f"<b>User Approved</b>\n\n"
        f"{mention} has been approved in <b>{html.escape(chat_title)}</b>.\n\n"
        f"They will now bypass automated admin actions like locks, blocklists, and antiflood.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#APPROVED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention}"
    )


@cutiepii_cmd(command='unapprove', filters=filters.ChatType.GROUPS,
              rate_limit_calls=20, rate_limit_window=60, add_error_handler=True)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@loggable
async def disapprove(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    args = context.args
    user = update.effective_user
    bot = context.bot

    user_id = await extract_user(message, args)
    if not user_id:
        await message.reply_text(
            "<b>User Not Found</b>\n\nSpecify a user to unapprove.",
            parse_mode=ParseMode.HTML
        )
        return ""

    entity, mention = await _resolve_user(chat, bot, user_id)
    if entity is None:
        await message.reply_text("<b>User Not Found</b>\nCannot locate the specified user.", parse_mode=ParseMode.HTML)
        return ""

    status = getattr(getattr(entity, "status", None), "value", None) or getattr(entity, "status", None)
    if status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER,
                  "administrator", "creator"]:
        await message.reply_text(
            "<b>Action Denied</b>\nThe specified user is an administrator and already bypasses locks, blocklists, and antiflood restrictions.",
            parse_mode=ParseMode.HTML
        )
        return ""

    if not sql.is_approved(message.chat_id, user_id):
        await message.reply_text(
            f"<b>User Approved Status</b>\n{mention} is not approved yet.", parse_mode=ParseMode.HTML
        )
        return ""

    sql.disapprove(message.chat_id, user_id)

    buttons = [
        [InlineKeyboardButton("Re-approve", callback_data=f"approve_approve_{user_id}"),
         InlineKeyboardButton("Approved List", callback_data="approve_list")],
        [InlineKeyboardButton("Close", callback_data="approve_close")]
    ]

    await message.reply_text(
        f"<b>User Unapproved</b>\n\n"
        f"{mention} is no longer approved in <b>{html.escape(chat_title)}</b>.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#UNAPPROVED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention}"
    )


@cutiepii_cmd(command='approved', filters=filters.ChatType.GROUPS,
              rate_limit_calls=10, rate_limit_window=60, add_error_handler=True)
@user_admin_check()
async def approved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat_title = message.chat.title
    chat = update.effective_chat
    bot = context.bot

    approved_users = sql.list_approved(message.chat_id)
    buttons = [
        [InlineKeyboardButton("Refresh", callback_data="approve_list")],
        [InlineKeyboardButton("Help", callback_data="approve_help"),
         InlineKeyboardButton("Close", callback_data="approve_close")]
    ]

    if not approved_users:
        await message.reply_text(
            f"<b>Approved Users</b>\n\nNo users are currently approved in <b>{html.escape(chat_title)}</b>.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    msg = "<b>Approved Users</b>\n\n"
    for i in approved_users:
        try:
            member = await chat.get_member(int(i.user_id))
            name = html.escape(member.user.first_name or str(i.user_id))
            msg += f"- <a href='tg://user?id={i.user_id}'>{name}</a> (<code>{i.user_id}</code>)\n"
        except Exception:
            try:
                chat_obj = await bot.get_chat(int(i.user_id))
                name = html.escape(chat_obj.title or str(i.user_id))
                msg += f"- {name} (<code>{i.user_id}</code>)\n"
            except Exception:
                msg += f"- Unknown User (<code>{i.user_id}</code>)\n"

    msg += f"\n<i>Total: {len(approved_users)} approved user(s)</i>"
    await message.reply_text(msg, parse_mode=ParseMode.HTML,
                             reply_markup=InlineKeyboardMarkup(buttons))


@cutiepii_cmd(command='approval', filters=filters.ChatType.GROUPS)
@user_admin_check()
async def approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    bot = context.bot

    user_id = await extract_user(message, args)
    if not user_id:
        await message.reply_text(
            "<b>User Not Found</b>\n\nSpecify a user to check approval status.",
            parse_mode=ParseMode.HTML
        )
        return ""

    entity, mention = await _resolve_user(chat, bot, user_id)
    if entity is None:
        await message.reply_text("<b>User Not Found</b>\nCannot locate the specified user.", parse_mode=ParseMode.HTML)
        return ""

    status = getattr(getattr(entity, "status", None), "value", None) or getattr(entity, "status", None)
    if status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER,
                  "administrator", "creator"]:
        await message.reply_text(
            "<b>Action Denied</b>\nThe specified user is an administrator and already bypasses locks, blocklists, and antiflood restrictions.",
            parse_mode=ParseMode.HTML
        )
        return ""

    if sql.is_approved(message.chat_id, user_id):
        await message.reply_text(
            f"<b>User Approved Status</b>\n{mention} is an approved user and will bypass locks, antiflood, and blocklists.",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text(
            f"<b>User Approved Status</b>\n{mention} is not an approved user and remains subject to normal restrictions.",
            parse_mode=ParseMode.HTML
        )


@cutiepii_cmd(command='unapproveall', filters=filters.ChatType.GROUPS,
              rate_limit_calls=2, rate_limit_window=300, add_error_handler=True)
async def unapproveall(update: Update, _: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    member = await chat.get_member(user.id)

    if member.status not in [ChatMemberStatus.OWNER, "creator"] and user.id not in SUDO_USERS:
        await update.effective_message.reply_text(
            "<b>Action Denied</b>\nOnly the chat owner can unapprove all users at once.",
            parse_mode=ParseMode.HTML
        )
        return

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("Yes, unapprove all", callback_data="unapproveall_user")],
        [InlineKeyboardButton("Cancel", callback_data="unapproveall_cancel")],
    ])
    await update.effective_message.reply_text(
        f"<b>Unapprove All Users</b>\nAre you sure you want to unapprove all users in <b>{html.escape(chat.title)}</b>?\n\n"
        f"<i>This action cannot be undone.</i>",
        reply_markup=buttons,
        parse_mode=ParseMode.HTML,
    )


# ─────────────────────────────────────────
# Callbacks
# ─────────────────────────────────────────

@cutiepii_callback(pattern=r"^unapproveall_")
async def unapproveall_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat = update.effective_chat
    message = update.effective_message
    member = await chat.get_member(query.from_user.id)

    is_owner = member.status in [ChatMemberStatus.OWNER, "creator"]
    is_sudo = query.from_user.id in SUDO_USERS

    if query.data == "unapproveall_user":
        if is_owner or is_sudo:
            approved_users = sql.list_approved(chat.id)
            for entry in approved_users:
                sql.disapprove(chat.id, int(entry.user_id))
            await query.answer("Done")
            await message.edit_text("Successfully unapproved all users in this chat.")
        elif member.status == ChatMemberStatus.ADMINISTRATOR:
            await query.answer("Only the chat owner can do this.", show_alert=True)
        else:
            await query.answer("You must be an administrator to perform this action.", show_alert=True)

    elif query.data == "unapproveall_cancel":
        if is_owner or is_sudo:
            await query.answer("Cancelled")
            await message.edit_text("Unapprove-all has been cancelled.")
        elif member.status == ChatMemberStatus.ADMINISTRATOR:
            await query.answer("Only the chat owner can do this.", show_alert=True)
        else:
            await query.answer("You must be an administrator to perform this action.", show_alert=True)


@cutiepii_callback(pattern=r"^approve_")
async def approve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat = update.effective_chat
    user = query.from_user
    bot = context.bot

    # ── Admin gate ──────────────────────────────────────────────────────────
    if not await user_is_admin(update, user.id):
        await query.answer("Action Denied\nYou do not have administrator privileges in this chat.", show_alert=True)
        return

    # ── close ────────────────────────────────────────────────────────────────
    if data == "approve_close":
        try:
            await query.message.delete()
        except BadRequest:
            pass
        return

    # ── help ─────────────────────────────────────────────────────────────────
    if data == "approve_help":
        help_text = (
            "<b>Approval System Help</b>\n\n"
            "<b>What is approval?</b>\n"
            "Approved users bypass:\n"
            "- Locks (links, forwards, etc.)\n"
            "- Blacklist filters\n"
            "- Antiflood limits\n\n"
            "<b>Quick Commands:</b>\n"
            "- <code>/approve</code>: Approve a user\n"
            "- <code>/unapprove</code>: Unapprove a user\n"
            "- <code>/approved</code>: View approved list\n"
            "- <code>/approval</code>: Check a user's status\n\n"
            "<i>Admins are automatically exempt!</i>"
        )
        buttons = [
            [InlineKeyboardButton("Approved List", callback_data="approve_list")],
            [InlineKeyboardButton("Back", callback_data="approve_list"),
             InlineKeyboardButton("Close", callback_data="approve_close")]
        ]
        await query.message.edit_text(
            help_text, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # ── approved list ────────────────────────────────────────────────────────
    if data == "approve_list":
        approved_users = sql.list_approved(chat.id)
        buttons = [
            [InlineKeyboardButton("Refresh", callback_data="approve_list")],
            [InlineKeyboardButton("Help", callback_data="approve_help"),
             InlineKeyboardButton("Close", callback_data="approve_close")]
        ]

        if not approved_users:
            await query.message.edit_text(
                f"<b>Approved Users</b>\n\nNo users are currently approved in <b>{html.escape(chat.title)}</b>.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return

        msg = "<b>Approved Users List</b>\n\n"
        for i in approved_users:
            try:
                member = await chat.get_member(int(i.user_id))
                name = html.escape(member.user.first_name or str(i.user_id))
                msg += f"- <a href='tg://user?id={i.user_id}'>{name}</a> (<code>{i.user_id}</code>)\n"
            except Exception:
                try:
                    chat_obj = await bot.get_chat(int(i.user_id))
                    name = html.escape(chat_obj.title or str(i.user_id))
                    msg += f"- {name} (<code>{i.user_id}</code>)\n"
                except Exception:
                    msg += f"- Unknown User (<code>{i.user_id}</code>)\n"

        msg += f"\n<i>Total: {len(approved_users)} approved user(s)</i>"
        await query.message.edit_text(
            msg, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # ── inline unapprove button (from /approve result) ───────────────────────
    if data.startswith("approve_unapprove_"):
        try:
            target_id = int(data.split("approve_unapprove_")[1])
        except (ValueError, IndexError):
            await query.answer("Invalid user ID.", show_alert=True)
            return

        if not sql.is_approved(chat.id, target_id):
            await query.answer("This user is not approved.", show_alert=True)
            return

        sql.disapprove(chat.id, target_id)

        # Try to fetch name for confirmation
        try:
            member = await chat.get_member(target_id)
            name = member.user.first_name or str(target_id)
        except Exception:
            name = str(target_id)

        buttons = [
            [InlineKeyboardButton("Re-approve", callback_data=f"approve_approve_{target_id}"),
             InlineKeyboardButton("Approved List", callback_data="approve_list")],
            [InlineKeyboardButton("Close", callback_data="approve_close")]
        ]
        await query.message.edit_text(
            f"<b>User Unapproved</b>\n\n"
            f"<a href='tg://user?id={target_id}'>{html.escape(name)}</a> has been unapproved.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # ── inline re-approve button (from /unapprove result) ────────────────────
    if data.startswith("approve_approve_"):
        try:
            target_id = int(data.split("approve_approve_")[1])
        except (ValueError, IndexError):
            await query.answer("Invalid user ID.", show_alert=True)
            return

        if sql.is_approved(chat.id, target_id):
            await query.answer("This user is already approved.", show_alert=True)
            return

        sql.approve(chat.id, target_id)

        try:
            member = await chat.get_member(target_id)
            name = member.user.first_name or str(target_id)
        except Exception:
            name = str(target_id)

        buttons = [
            [InlineKeyboardButton("Unapprove", callback_data=f"approve_unapprove_{target_id}"),
             InlineKeyboardButton("Approved List", callback_data="approve_list")],
            [InlineKeyboardButton("Close", callback_data="approve_close")]
        ]
        await query.message.edit_text(
            f"<b>User Approved</b>\n\n"
            f"<a href='tg://user?id={target_id}'>{html.escape(name)}</a> has been approved.\n\n"
            f"They will now bypass locks, blocklists, and antiflood.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return


# ─────────────────────────────────────────
# Help & Module Name
# ─────────────────────────────────────────

__help__ = True

__mod_name__ = "Approvals"
