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

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd
import Cutiepii_Robot.modules.sql.global_bans_sql as gban_sql
import Cutiepii_Robot.modules.sql.users_sql as user_sql
import contextlib
import asyncio
import html

from Cutiepii_Robot import DEV_USERS, OWNER_ID, dispatcher
from Cutiepii_Robot.modules.helper_funcs.chat_status import dev_plus
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler,
)
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility
from telegram import Bot

async def get_muted_chats(bot: Bot, update: Update, leave: bool = False):
    chat_id = update.effective_chat.id
    chats = user_sql.get_all_chats()
    muted_chats, progress = 0, 0
    chat_list = []
    progress_message = None

    for chat in chats:

        if ((100 * chats.index(chat)) / len(chats)) > progress:
            progress_bar = f"{progress}% completed in getting muted chats."
            if progress_message:
                try:
                    await bot.edit_message_text(
                        progress_bar, chat_id, progress_message.message_id
                    )
                except:
                    pass
            else:
                progress_message = await bot.send_message(chat_id, progress_bar)
            progress += 5

        cid = chat.chat_id
        await asyncio.sleep(0.1)

        try:
            await bot.send_chat_action(cid, "typing")
        except (BadRequest, Forbidden):
            muted_chats += 1
            chat_list.append(cid)
        except:
            pass

    try:
        await progress_message.delete()
    except:
        pass

    if not leave:
        return muted_chats
    for muted_chat in chat_list:
        await asyncio.sleep(0.1)
        with contextlib.suppress(BaseException):
            await bot.leave_chat(muted_chat, timeout=120)
        user_sql.rem_chat(muted_chat)
    return muted_chats


async def get_invalid_chats(update: Update, context: CallbackContext, remove: bool = False):
    bot = context.bot
    chat_id = update.effective_chat.id
    chats = user_sql.get_all_chats()
    kicked_chats, progress = 0, 0
    chat_list = []
    progress_message = None

    for chat in chats:

        if ((100 * chats.index(chat)) / len(chats)) > progress:
            progress_bar = f"{progress}% completed in getting invalid chats."
            if progress_message:
                try:
                    await bot.edit_message_text(
                        progress_bar, chat_id, progress_message.message_id,
                    )
                except:
                    pass
            else:
                progress_message = await bot.send_message(chat_id, progress_bar)
            progress += 5

        cid = chat.chat_id
        await asyncio.sleep(0.1)
        try:
            await bot.get_chat(cid, timeout=60)
        except (BadRequest, Forbidden):
            kicked_chats += 1
            chat_list.append(cid)
        except:
            pass

    try:
        await progress_message.delete()
    except:
        pass

    if not remove:
        return kicked_chats
    for muted_chat in chat_list:
        await asyncio.sleep(0.1)
        user_sql.rem_chat(muted_chat)
    return kicked_chats


async def get_invalid_gban(update: Update, context: CallbackContext, remove: bool = False):
    bot = context.bot
    banned = gban_sql.get_gban_list()
    ungbanned_users = 0
    ungban_list = []

    for user in banned:
        user_id = user["user_id"]
        await asyncio.sleep(0.1)
        try:
            await bot.get_chat(user_id)
        except BadRequest:
            ungbanned_users += 1
            ungban_list.append(user_id)
        except:
            pass

    if not remove:
        return ungbanned_users
    for user_id in ungban_list:
        await asyncio.sleep(0.1)
        gban_sql.ungban_user(user_id)
    return ungbanned_users


@dev_plus
@cutiepii_cmd(command="dbcleanup")
async def dbcleanup(update: Update, context: CallbackContext):
    msg = update.effective_message

    await msg.reply_text("<b>Database Cleanup</b>\nRetrieving invalid chat count...", parse_mode=ParseMode.HTML)
    invalid_chat_count = await get_invalid_chats(update, context)

    await msg.reply_text("<b>Database Cleanup</b>\nRetrieving invalid global ban count...", parse_mode=ParseMode.HTML)
    invalid_gban_count = await get_invalid_gban(update, context)

    reply = (
        "<b>Database Cleanup Report</b>\n\n"
        f"- <b>Total Invalid Chats:</b> <code>{invalid_chat_count}</code>\n"
        f"- <b>Total Invalid Global Bans:</b> <code>{invalid_gban_count}</code>"
    )

    buttons = [[InlineKeyboardButton("Cleanup DB", callback_data="db_cleanup")]]

    await msg.reply_text(
        reply,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.HTML
    )


@cutiepii_callback(pattern="db_.*")
async def callback_button(update: Update, context: CallbackContext):
    bot = context.bot
    query = update.callback_query
    message = query.message
    chat_id = update.effective_chat.id
    query_type = query.data

    admin_list = [OWNER_ID] + DEV_USERS

    await query.answer()

    if query_type == "db_leave_chat" and query.from_user.id in admin_list:
        await bot.edit_message_text("<b>Database Cleanup</b>\nLeaving chats...", chat_id, message.message_id, parse_mode=ParseMode.HTML)
        chat_count = await get_muted_chats(update, context, True)
        await bot.send_message(chat_id, f"<b>Database Cleanup</b>\nLeft <code>{chat_count}</code> chats.", parse_mode=ParseMode.HTML)
    elif (
        query_type == "db_leave_chat"
        or query_type == "db_cleanup"
        and query.from_user.id not in admin_list
    ):
        await query.answer("You are not authorized to use this option.", show_alert=True)
    elif query_type == "db_cleanup":
        await bot.edit_message_text("<b>Database Cleanup</b>\nCleaning database...", chat_id, message.message_id, parse_mode=ParseMode.HTML)
        invalid_chat_count = await get_invalid_chats(update, context, True)
        invalid_gban_count = await get_invalid_gban(update, context, True)
        reply = (
            "<b>Database Cleanup Complete</b>\n\n"
            f"Successfully cleaned up <code>{invalid_chat_count}</code> chats and <code>{invalid_gban_count}</code> globally banned users from the database."
        )
        await bot.send_message(chat_id, reply, parse_mode=ParseMode.HTML)




__mod_name__ = "DB Cleanup"
__handlers__ = [
]
