"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yuki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

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
import asyncio
import html
import contextlib

from time import perf_counter
from functools import wraps
from cachetools import TTLCache
from threading import RLock
from Cutiepii_Robot.modules.sql.moderators_sql import is_modd
from Cutiepii_Robot import (
    DEL_CMDS,
    DEV_USERS,
    SUDO_USERS,
    SUPPORT_CHAT,
    SUPPORT_USERS,
    TIGER_USERS,
    WHITELIST_USERS,
    dispatcher,
    OWNER_ID,
)
from Cutiepii_Robot.modules import connection
from Cutiepii_Robot.modules.helper_funcs.admin_status import get_bot_member

from telegram import Chat, ChatMember, Update, User
from telegram.constants import ParseMode, ChatMemberStatus
CHATMEMBER_ADMINISTRATOR = ChatMemberStatus.ADMINISTRATOR
CHATMEMBER_CREATOR = ChatMemberStatus.OWNER
from telegram.error import TelegramError, Forbidden, BadRequest
from telegram.ext import ContextTypes
CallbackContext = ContextTypes.DEFAULT_TYPE

from Cutiepii_Robot import LOGGER

# Stores admin list in memory for 10 minutes.
ADMIN_CACHE = TTLCache(maxsize=512, ttl=60 * 10, timer=perf_counter)
THREAD_LOCK = RLock()


def is_whitelist_plus(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    return any(user_id in user for user in [WHITELIST_USERS, TIGER_USERS, SUPPORT_USERS, SUDO_USERS, DEV_USERS])


def is_support_plus(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    return user_id in SUPPORT_USERS or user_id in SUDO_USERS or user_id in DEV_USERS


def is_sudo_plus(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    return user_id in SUDO_USERS or user_id in DEV_USERS


def is_stats_plus(chat: Chat, user_id: int, member: ChatMember = None) -> bool:
    return user_id in DEV_USERS


def user_can_changeinfo(chat: Chat, user: User, bot_id: int) -> bool:
    return chat.get_member(user.id).can_change_info


def bot_admin(func):
    """Decorator to check if bot is admin"""
    @wraps(func)
    async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            chat = update.effective_chat
            update_chat_title = chat.title
            message_chat_title = update.effective_message.chat.title

            if update_chat_title == message_chat_title:
                not_admin = "<b>Action Denied</b>\nI am not an administrator in this chat."
            else:
                not_admin = f"<b>Action Denied</b>\nI am not an administrator in <b>{html.escape(update_chat_title)}</b>."

            if await is_bot_admin(chat, context.bot.id):
                return await func(update, context, *args, **kwargs)
            else:
                await update.effective_message.reply_text(not_admin, parse_mode=ParseMode.HTML)
                return None
        except Exception as e:
            LOGGER.error(f"[ChatStatus] Error in bot_admin decorator: {e}")
            return None

    return is_admin


def owner_plus(func):
    """Decorator to restrict command to the bot owner only"""
    @wraps(func)
    async def is_owner_plus_func(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user

        if not user:
            return None

        if user.id == OWNER_ID:
            return await func(update, context, *args, **kwargs)

        if DEL_CMDS and " " not in update.effective_message.text:
            with contextlib.suppress(TelegramError):
                await update.effective_message.delete()
        else:
            await update.effective_message.reply_text(
                "<b>Action Denied</b>\nThis is a restricted command. You do not have the required permissions.",
                parse_mode=ParseMode.HTML
            )

    return is_owner_plus_func


def user_can_change(func):
    """Decorator to check if user has can_change_info permission"""
    @wraps(func)
    async def info_changer(update, context, *args, **kwargs):
        user = update.effective_user.id
        member = await update.effective_chat.get_member(user)

        if not (member.can_change_info or member.status == "creator") and user not in SUDO_USERS:
            await update.effective_message.reply_text(
                "<b>Action Denied</b>\nYou are missing the required permission: <code>can change info</code>.",
                parse_mode=ParseMode.HTML
            )
            return ""

        return await func(update, context, *args, **kwargs)

    return info_changer


def user_can_promote(func):
    """Decorator to check if user has can_promote_members permission"""
    @wraps(func)
    async def user_is_promoter(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        if not user:
            return
        user_id = user.id
        member = await update.effective_chat.get_member(user_id)
        no_rights = "<b>Action Denied</b>\nYou do not have the permission to add administrators."
        if (
            not (member.can_promote_members or member.status == "creator")
            and user_id not in SUDO_USERS
            and user_id not in [777000, 1087968824]
        ):
            if not update.callback_query:
                await update.effective_message.reply_text(no_rights, parse_mode=ParseMode.HTML)
            else:
                await update.callback_query.answer(
                    "Action Denied\nYou do not have the permission to add administrators.",
                    show_alert=True
                )
            return ""
        return await func(update, context, *args, **kwargs)

    return user_is_promoter


async def user_is_admin(update: Update, user_id: int, member: ChatMember = None) -> bool:
    """Check if user is admin in the chat"""
    try:
        chat = update.effective_chat

        if (
            chat.type == "private"
            or user_id in SUDO_USERS
            or user_id in DEV_USERS
            or (
                update.effective_message.reply_to_message
                and update.effective_message.reply_to_message.sender_chat is not None
                and update.effective_message.reply_to_message.sender_chat.type != "channel"
            )
        ):
            return True

        if not member:
            try:
                return user_id in ADMIN_CACHE[chat.id]
            except KeyError:
                try:
                    chat_admins = await dispatcher.bot.get_chat_administrators(chat.id)
                except Forbidden:
                    LOGGER.warning(f"[ChatStatus] Bot not authorized in chat {chat.id}")
                    return False

                admin_list = [x.user.id for x in chat_admins]
                ADMIN_CACHE[chat.id] = admin_list

                return user_id in admin_list

        return member.status in ("administrator", "creator")

    except Exception as e:
        LOGGER.error(f"[ChatStatus] Error checking user admin status: {e}")
        return False


async def is_bot_admin(chat: Chat, bot_id: int, bot_member: ChatMember = None) -> bool:
    if chat.type == "private":
        return True

    if not bot_member:
        try:
            bot_member = await get_bot_member(chat.id)
        except BadRequest:
            return False

    return bot_member.status in ("administrator", "creator")


async def can_delete(chat: Chat, bot_id: int) -> bool:
    return getattr(await get_bot_member(chat.id), "can_delete_messages", False)


async def is_user_in_chat(chat: Chat, user_id: int) -> bool:
    member = await chat.get_member(user_id)
    return member.status not in ("left", "kicked")


async def is_user_ban_protected(update: Update, user_id: int, member: ChatMember = None) -> bool:
    chat = update.effective_chat if hasattr(update, "effective_chat") else update
    msg = getattr(update, "effective_message", None)
    if (
        chat.type == "private"
        or user_id in SUDO_USERS
        or user_id in DEV_USERS
        or user_id in WHITELIST_USERS
        or user_id in TIGER_USERS
        or is_modd(chat.id, user_id)
        or (msg and msg.reply_to_message and msg.reply_to_message.sender_chat is not None and
            msg.reply_to_message.sender_chat.type != "channel")
    ):
        return True

    if not member:
        member = await chat.get_member(user_id)

    return member.status in ("administrator", "creator")


def dev_plus(func):
    """Decorator for developer-only commands"""
    @wraps(func)
    async def is_dev_plus_func(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            user = update.effective_user

            if user and user.id in DEV_USERS:
                return await func(update, context, *args, **kwargs)

            if not user:
                return None

            if DEL_CMDS and " " not in update.effective_message.text:
                with contextlib.suppress(TelegramError):
                    await update.effective_message.delete()
            else:
                await update.effective_message.reply_text(
                    "<b>Action Denied</b>\nThis command is restricted to bot developers.",
                    parse_mode=ParseMode.HTML
                )
            return None
        except Exception as e:
            LOGGER.error(f"[ChatStatus] Error in dev_plus decorator: {e}")
            return None

    return is_dev_plus_func


def sudo_plus(func):
    """Decorator for sudo+ level commands"""
    @wraps(func)
    async def is_sudo_plus_func(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            user = update.effective_user
            chat = update.effective_chat

            if user and is_sudo_plus(chat, user.id):
                return await func(update, context, *args, **kwargs)

            if not user:
                return None

            if DEL_CMDS and " " not in update.effective_message.text:
                with contextlib.suppress(TelegramError):
                    await update.effective_message.delete()
            else:
                await update.effective_message.reply_text(
                    "<b>Action Denied</b>\nThis command is restricted to bot administrators.",
                    parse_mode=ParseMode.HTML
                )
            return None
        except Exception as e:
            LOGGER.error(f"[ChatStatus] Error in sudo_plus decorator: {e}")
            return None

    return is_sudo_plus_func


def stats_plus(func):
    """Decorator for stats/dev+ level commands"""
    @wraps(func)
    async def is_stats_plus_func(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        chat = update.effective_chat

        if user and is_stats_plus(chat, user.id):
            return await func(update, context, *args, **kwargs)

        if not user:
            return None

        if DEL_CMDS and " " not in update.effective_message.text:
            with contextlib.suppress(TelegramError):
                await update.effective_message.delete()
        else:
            await update.effective_message.reply_text(
                "<b>Action Denied</b>\nThis command is restricted to bot developers.",
                parse_mode=ParseMode.HTML
            )

    return is_stats_plus_func


def support_plus(func):
    """Decorator for support+ level commands"""
    @wraps(func)
    async def is_support_plus_func(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user
        chat = update.effective_chat

        if user and is_support_plus(chat, user.id):
            return await func(update, context, *args, **kwargs)

        if not user:
            return None

        if DEL_CMDS and " " not in update.effective_message.text:
            with contextlib.suppress(TelegramError):
                await update.effective_message.delete()

    return is_support_plus_func


def whitelist_plus(func):
    """Decorator for whitelist+ level commands"""
    @wraps(func)
    async def is_whitelist_plus_func(
        update: Update, context: CallbackContext, *args, **kwargs,
    ):
        user = update.effective_user
        chat = update.effective_chat

        if user and is_whitelist_plus(chat, user.id):
            return await func(update, context, *args, **kwargs)

        await update.effective_message.reply_text(
            f"<b>Action Denied</b>\nYou do not have permission to use this command. For assistance, contact @{SUPPORT_CHAT}.",
            parse_mode=ParseMode.HTML
        )

    return is_whitelist_plus_func


def user_admin(func):
    """Decorator to check if user is admin"""
    @wraps(func)
    async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            user = update.effective_user

            if user and await user_is_admin(update, user.id):
                return await func(update, context, *args, **kwargs)

            if not user:
                return None

            if DEL_CMDS and " " not in update.effective_message.text:
                with contextlib.suppress(TelegramError):
                    await update.effective_message.delete()
            else:
                if update.callback_query:
                    await update.callback_query.answer(
                        "Action Denied\nYou must be an administrator to perform this action.",
                        show_alert=True
                    )
                    return ""
                await update.effective_message.reply_text(
                    "<b>Action Denied</b>\nYou must be an administrator to perform this action.",
                    parse_mode=ParseMode.HTML
                )
            return None
        except Exception as e:
            import traceback
            LOGGER.error(f"[ChatStatus] Error in user_admin decorator: {e}\n{traceback.format_exc()}")
            return None

    return is_admin


def is_user_admin_callback_query(func):
    """Decorator to check if user is admin for callback queries"""
    @wraps(func)
    async def is_admin(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.callback_query.from_user
        chat = update.effective_chat

        member = await chat.get_member(user.id)
        if member.status in (CHATMEMBER_ADMINISTRATOR, CHATMEMBER_CREATOR) or user.id in DEV_USERS:
            return await func(update, context, *args, **kwargs)

        if not user:
            return None

        await update.callback_query.answer(
            "Action Denied\nYou do not have access to use this.",
            show_alert=True
        )

    return is_admin


def user_admin_no_reply(func):
    """Decorator to check if user is admin, silently ignoring non-admins"""
    @wraps(func)
    async def is_not_admin_no_reply(
                update: Update, context: CallbackContext, *args, **kwargs
        ):
        user = update.effective_user

        if user and await user_is_admin(update, user.id):
            return await func(update, context, *args, **kwargs)

        if not user:
            return None

        if DEL_CMDS and " " not in update.effective_message.text:
            with contextlib.suppress(TelegramError):
                await update.effective_message.delete()

    return is_not_admin_no_reply


def user_not_admin(func):
    """Decorator that runs handler only if user is NOT an admin"""
    @wraps(func)
    async def is_not_admin(update: Update, context: CallbackContext, *args, **kwargs):
        user = update.effective_user

        if user and not await user_is_admin(update, user.id):
            return await func(update, context, *args, **kwargs)

        return None

    return is_not_admin


def bot_can_delete(func):
    """Decorator to check if bot has delete messages permission"""
    @wraps(func)
    async def delete_rights(update: Update, context: CallbackContext, *args, **kwargs):
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_delete = "<b>Action Denied</b>\nI do not have the permission to delete messages."
        else:
            cant_delete = f"<b>Action Denied</b>\nI do not have the permission to delete messages in <b>{html.escape(update_chat_title)}</b>."

        if await can_delete(chat, context.bot.id):
            return await func(update, context, *args, **kwargs)
        await update.effective_message.reply_text(cant_delete, parse_mode=ParseMode.HTML)

    return delete_rights


def can_pin(func):
    """Decorator to check if bot has pin messages permission"""
    @wraps(func)
    async def pin_rights(update: Update, context: CallbackContext, *args, **kwargs):
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_pin = "<b>Action Denied</b>\nI do not have the permission to pin messages."
        else:
            cant_pin = f"<b>Action Denied</b>\nI do not have the permission to pin messages in <b>{html.escape(update_chat_title)}</b>."

        bot_member = await get_bot_member(chat.id)
        if getattr(bot_member, "can_pin_messages", False):
            return await func(update, context, *args, **kwargs)
        await update.effective_message.reply_text(cant_pin, parse_mode=ParseMode.HTML)

    return pin_rights


def can_promote(func):
    """Decorator to check if bot has promote members permission"""
    @wraps(func)
    async def promote_rights(update: Update, context: CallbackContext, *args, **kwargs):
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_promote = "<b>Action Denied</b>\nI do not have the permission to promote or demote members."
        else:
            cant_promote = f"<b>Action Denied</b>\nI do not have the permission to promote or demote members in <b>{html.escape(update_chat_title)}</b>."

        bot_member = await get_bot_member(chat.id)
        if getattr(bot_member, "can_promote_members", False):
            return await func(update, context, *args, **kwargs)
        await update.effective_message.reply_text(cant_promote, parse_mode=ParseMode.HTML)

    return promote_rights


def can_restrict(func):
    """Decorator to check if bot has restrict members permission"""
    @wraps(func)
    async def restrict_rights(update: Update, context: CallbackContext, *args, **kwargs):
        chat = update.effective_chat
        update_chat_title = chat.title
        message_chat_title = update.effective_message.chat.title

        if update_chat_title == message_chat_title:
            cant_restrict = "<b>Action Denied</b>\nI do not have the permission to restrict members."
        else:
            cant_restrict = f"<b>Action Denied</b>\nI do not have the permission to restrict members in <b>{html.escape(update_chat_title)}</b>."

        bot_member = await get_bot_member(chat.id)
        if getattr(bot_member, "can_restrict_members", False):
            return await func(update, context, *args, **kwargs)
        await update.effective_message.reply_text(cant_restrict, parse_mode=ParseMode.HTML)

    return restrict_rights


def user_can_ban(func):
    """Decorator to check if user has ban/restrict permissions"""
    @wraps(func)
    async def user_is_banhammer(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        chat = update.effective_chat
        member = await chat.get_member(user_id)
        if (
            not member.can_restrict_members
            and member.status != "creator"
            and user_id not in SUDO_USERS
        ):
            await update.effective_message.reply_text(
                "<b>Action Denied</b>\nYou do not have the required ban/restrict permissions.",
                parse_mode=ParseMode.HTML
            )
            return ""
        return await func(update, context, *args, **kwargs)

    return user_is_banhammer


def connection_status(func):
    """Decorator to handle connection status"""
    @wraps(func)
    async def connected_status(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        try:
            if not update.effective_user:
                return None

            conn = await connected(
                context.bot,
                update,
                update.effective_chat,
                update.effective_user.id,
                need_admin=False,
            )

            if conn:
                chat = await dispatcher.bot.get_chat(conn)
                # Store connected chat in context data for downstream use
                context.chat_data["_connected_chat"] = chat
                try:
                    # Best-effort override for backward compat (may silently fail on PTB v20+)
                    object.__setattr__(update, "_effective_chat", chat)
                except Exception:
                    pass
            else:
                if update.effective_message.chat.type == "private":
                    await update.effective_message.reply_text(
                        "<b>Connection Error</b>\nPlease initiate <code>/connect</code> in a group chat first.",
                        parse_mode=ParseMode.HTML
                    )
                    return None

            return await func(update, context, *args, **kwargs)
        except Exception as e:
            LOGGER.error(f"[ChatStatus] Error in connection_status decorator: {e}")
            return None

    return connected_status


connected = connection.connected
