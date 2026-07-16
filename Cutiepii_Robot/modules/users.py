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

import contextlib
import asyncio
import re
import time
from io import BytesIO

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import ContextTypes, filters
from telegram.helpers import escape_markdown

from Cutiepii_Robot import LOGGER, OWNER_ID, dispatcher, BOT_ID, REDIS
import Cutiepii_Robot.modules.sql.users_sql as sql
from Cutiepii_Robot.modules.helper_funcs.chat_status import sudo_plus
from Cutiepii_Robot.modules.sql.users_sql import get_all_users, update_user
from Cutiepii_Robot.modules.helper_funcs.admin_status import get_bot_member
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot.modules.helper_funcs.msg_types import Types


def _get_forward_user(message):
    """Get original sender from forwarded message (PTB v20+ uses forward_origin, not forward_from)."""
    try:
        origin = getattr(message, "forward_origin", None)
        if origin and getattr(origin, "sender_user", None):
            return origin.sender_user
        return getattr(message, "forward_from", None)
    except AttributeError:
        return None


USERS_GROUP = 4
CHAT_GROUP = 5


async def get_user_id(username):
    # ensure valid userid
    if len(username) <= 5:
        return None

    if username.startswith("@"):
        username = username[1:]

    users = sql.get_userid_by_name(username)

    if not users:
        return None

    elif len(users) == 1:
        return users[0].user_id

    else:
        for user_obj in users:
            try:
                userdat = await dispatcher.bot.get_chat(user_obj.user_id)
                if userdat.username == username:
                    return userdat.id

            except BadRequest as excp:
                if excp.message != "Chat not found":
                    LOGGER.exception("Error extracting user ID")

    return None


ENUM_FUNC_MAP = {
    Types.TEXT.value: "send_message",
    Types.BUTTON_TEXT.value: "send_message",
    Types.STICKER.value: "send_sticker",
    Types.DOCUMENT.value: "send_document",
    Types.PHOTO.value: "send_photo",
    Types.AUDIO.value: "send_audio",
    Types.VOICE.value: "send_voice",
    Types.VIDEO.value: "send_video",
}


def parse_markdown_buttons(text):
    buttons = []
    current_row = []
    pattern = r'\[([^\]]+)\]\(buttonurl:([^)]+?)(:same)?\)'
    for match in re.finditer(pattern, text):
        btn_text = match.group(1)
        url = match.group(2)
        same = match.group(3) is not None
        if same and current_row:
            current_row.append(InlineKeyboardButton(btn_text, url=url))
        else:
            if current_row:
                buttons.append(current_row)
                current_row = []
            current_row.append(InlineKeyboardButton(btn_text, url=url))
    if current_row:
        buttons.append(current_row)
    text = re.sub(pattern, '', text).strip()
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    return text, markup


async def send_broadcast_messages(context, queue_key, msg_text, meta_key, lock_key, target_type):
    failed = 0
    text, markup = parse_markdown_buttons(msg_text)
    data_type = int(REDIS.hget(meta_key, "data_type"))
    content = REDIS.hget(meta_key, "content") or None
    
    while True:
        status = REDIS.hget(meta_key, "status")
        if status != "running":
            break
        nxt = REDIS.lpop(queue_key)
        if not nxt:
            break
            
        try:
            if data_type in (Types.BUTTON_TEXT.value, Types.TEXT.value):
                await context.bot.send_message(
                    int(nxt),
                    text,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                    reply_markup=markup,
                )
            elif ENUM_FUNC_MAP[data_type] == "send_sticker":
                await context.bot.send_sticker(
                    int(nxt),
                    content,
                    reply_markup=markup,
                )
            else:
                func = getattr(context.bot, ENUM_FUNC_MAP[data_type])
                await func(
                    int(nxt),
                    content,
                    caption=text,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                    reply_markup=markup,
                )
            REDIS.hincrby(meta_key, f"sent_{target_type}", 1)
        except BadRequest:
            try:
                if data_type in (Types.BUTTON_TEXT.value, Types.TEXT.value):
                    await context.bot.send_message(
                        int(nxt),
                        text,
                        disable_web_page_preview=True,
                        reply_markup=markup,
                    )
                elif ENUM_FUNC_MAP[data_type] == "send_sticker":
                    await context.bot.send_sticker(
                        int(nxt),
                        content,
                        reply_markup=markup,
                    )
                else:
                    func = getattr(context.bot, ENUM_FUNC_MAP[data_type])
                    await func(
                        int(nxt),
                        content,
                        caption=text,
                        disable_web_page_preview=True,
                        reply_markup=markup,
                    )
                REDIS.hincrby(meta_key, f"sent_{target_type}", 1)
            except TelegramError:
                failed += 1
                REDIS.hincrby(meta_key, f"failed_{target_type}", 1)
        except TelegramError:
            failed += 1
            REDIS.hincrby(meta_key, f"failed_{target_type}", 1)
            
        REDIS.hset(meta_key, "updated_at", int(time.time()))
        REDIS.expire(lock_key, 3600)
        await asyncio.sleep(0.1)
        
    return failed


async def perform_broadcast(context, meta_key, lock_key, gq_key, uq_key, msg_text, to_group, to_user):
    REDIS.hset(meta_key, "status", "running")
    failed_g = 0
    failed_u = 0
    if to_group:
        failed_g = await send_broadcast_messages(context, gq_key, msg_text, meta_key, lock_key, "groups")
    if to_user:
        failed_u = await send_broadcast_messages(context, uq_key, msg_text, meta_key, lock_key, "users")
    
    status = REDIS.hget(meta_key, "status")
    if status == "running":
        REDIS.hset(meta_key, "status", "completed")
    REDIS.delete(lock_key)
    return failed_g, failed_u, status


@cutiepii_cmd(command=['broadcast', 'broadcastall', 'broadcastusers', 'broadcastgroups'], filters=filters.User(OWNER_ID), rate_limit_calls=1, rate_limit_window=10, add_error_handler=True)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    to_send = update.effective_message.text.split(None, 1)

    if len(to_send) >= 2 or update.effective_message.reply_to_message:
        cmd = to_send[0].lower()
        to_group = "groups" in cmd or "all" in cmd or "broadcast" == cmd or "/broadcast" == cmd
        to_user = "users" in cmd or "all" in cmd or "broadcast" == cmd or "/broadcast" == cmd

        if update.effective_message.reply_to_message:
            replied = update.effective_message.reply_to_message
            if replied.sticker:
                data_type = Types.STICKER.value
                content = replied.sticker.file_id
                text = ""
            elif replied.document:
                data_type = Types.DOCUMENT.value
                content = replied.document.file_id
                text = replied.caption or ""
            elif replied.photo:
                data_type = Types.PHOTO.value
                content = replied.photo[-1].file_id
                text = replied.caption or ""
            elif replied.audio:
                data_type = Types.AUDIO.value
                content = replied.audio.file_id
                text = replied.caption or ""
            elif replied.voice:
                data_type = Types.VOICE.value
                content = replied.voice.file_id
                text = replied.caption or ""
            elif replied.video:
                data_type = Types.VIDEO.value
                content = replied.video.file_id
                text = replied.caption or ""
            else:
                msg_text = replied.text or replied.caption or ""
                text, markup = parse_markdown_buttons(msg_text)
                data_type = Types.BUTTON_TEXT.value if markup else Types.TEXT.value
                content = None
        else:
            msg_text = to_send[1]
            text, markup = parse_markdown_buttons(msg_text)
            data_type = Types.BUTTON_TEXT.value if markup else Types.TEXT.value
            content = None

        meta_key = "broadcast:meta"
        lock_key = "broadcast:lock"
        gq_key = "broadcast:groups"
        uq_key = "broadcast:users"
        existing = REDIS.hgetall(meta_key)
        
        if existing and existing.get("status") in ["running", "paused", "pending_confirmation"]:
            await update.effective_message.reply_text("A broadcast is in progress. Use /broadcaststatus or /broadcastresume.")
            return

        if to_group:
            REDIS.delete(gq_key)
            for c in sql.get_all_chats() or []:
                REDIS.rpush(gq_key, int(c.chat_id))
        if to_user:
            REDIS.delete(uq_key)
            for u in sql.get_all_users() or []:
                REDIS.rpush(uq_key, int(u.user_id))

        total_groups = REDIS.llen(gq_key) if to_group else 0
        total_users = REDIS.llen(uq_key) if to_user else 0
        
        if update.effective_message.reply_to_message:
            replied = update.effective_message.reply_to_message
            if replied.sticker or replied.document or replied.photo or replied.audio or replied.voice or replied.video:
                message_text = text  # caption
            else:
                message_text = msg_text  # original text
        else:
            message_text = msg_text  # original text

        REDIS.hmset(
            meta_key,
            {
                "message": message_text,
                "to_group": int(to_group),
                "to_user": int(to_user),
                "total_groups": int(total_groups),
                "total_users": int(total_users),
                "sent_groups": 0,
                "sent_users": 0,
                "failed_groups": 0,
                "failed_users": 0,
                "status": "pending_confirmation",
                "admin_id": update.effective_user.id,
                "started_at": int(time.time()),
                "updated_at": int(time.time()),
                "data_type": int(data_type),
                "content": content or "",
            },
        )
        
        keyboard = [
            [InlineKeyboardButton("🟢 Confirm Broadcast", callback_data="broadcast_confirm")],
            [InlineKeyboardButton("🔴 Cancel", callback_data="broadcast_cancel")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        preview_text, _ = parse_markdown_buttons(text)
        preview_text = f"Broadcast Preview:\n\n{preview_text}\n\nTargets:\nGroups: {total_groups}\nUsers: {total_users}\n\nConfirm to start broadcasting?"
        await update.effective_message.reply_text(preview_text, reply_markup=reply_markup, parse_mode="MARKDOWN")


@cutiepii_cmd(command='broadcaststatus', filters=filters.User(OWNER_ID), add_error_handler=True)
async def broadcast_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    meta = REDIS.hgetall("broadcast:meta")
    if not meta:
        await update.effective_message.reply_text("No broadcast state.")
        return
        
    tg = int(meta.get("total_groups", 0) or 0)
    tu = int(meta.get("total_users", 0) or 0)
    sg = int(meta.get("sent_groups", 0) or 0)
    su = int(meta.get("sent_users", 0) or 0)
    fg = int(meta.get("failed_groups", 0) or 0)
    fu = int(meta.get("failed_users", 0) or 0)
    rg = REDIS.llen("broadcast:groups") if int(meta.get("to_group", 0)) else 0
    ru = REDIS.llen("broadcast:users") if int(meta.get("to_user", 0)) else 0
    status = meta.get("status", "unknown")
    
    await update.effective_message.reply_text(
        f"Status: {status}\nGroups: {sg}/{tg} (left {rg}), failed {fg}\nUsers: {su}/{tu} (left {ru}), failed {fu}"
    )


@cutiepii_cmd(command='broadcastresume', filters=filters.User(OWNER_ID), add_error_handler=True)
async def broadcast_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    meta_key = "broadcast:meta"
    lock_key = "broadcast:lock"
    gq_key = "broadcast:groups"
    uq_key = "broadcast:users"
    meta = REDIS.hgetall(meta_key)
    if not meta:
        await update.effective_message.reply_text("No broadcast to resume.")
        return
        
    if meta.get("status") == "completed" or (REDIS.llen(gq_key) == 0 and REDIS.llen(uq_key) == 0):
        await update.effective_message.reply_text("Broadcast already completed.")
        return
        
    if not REDIS.set(lock_key, str(int(time.time())), nx=True, ex=3600):
        await update.effective_message.reply_text("Another broadcast is running. Try again later.")
        return
        
    REDIS.hset(meta_key, "status", "running")
    msg_text = meta.get("message", "")
    to_group = bool(int(meta.get("to_group", 0)))
    to_user = bool(int(meta.get("to_user", 0)))
    
    async def run_bg_broadcast():
        try:
            failed_g, failed_u, final_status = await perform_broadcast(context, meta_key, lock_key, gq_key, uq_key, msg_text, to_group, to_user)
            try:
                await context.bot.send_message(
                    chat_id=int(meta.get("admin_id")),
                    text=f"📢 <b>Broadcast Status Update:</b>\nStatus: {final_status}\nGroups failed: {failed_g}\nUsers failed: {failed_u}",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass
        except Exception as e:
            LOGGER.error(f"Error in bg broadcast: {e}")
            REDIS.delete(lock_key)
            
    asyncio.create_task(run_bg_broadcast())
    await update.effective_message.reply_text("Broadcast resumed in background.")


@cutiepii_cmd(command='broadcastkill', filters=filters.User(OWNER_ID), add_error_handler=True)
async def broadcast_kill(update: Update, context: ContextTypes.DEFAULT_TYPE):
    meta_key = "broadcast:meta"
    meta = REDIS.hgetall(meta_key)
    if not meta:
        await update.effective_message.reply_text("No broadcast in progress.")
        return
        
    if meta.get("status") != "running":
        await update.effective_message.reply_text("Broadcast is not currently running.")
        return
        
    REDIS.hset(meta_key, "status", "killed")
    await update.effective_message.reply_text("Broadcast has been killed. It will stop shortly.")


@cutiepii_callback(pattern=r"broadcast_(confirm|cancel)")
async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    data = query.data
    meta_key = "broadcast:meta"
    lock_key = "broadcast:lock"
    gq_key = "broadcast:groups"
    uq_key = "broadcast:users"
    meta = REDIS.hgetall(meta_key)
    if not meta:
        await query.answer("No pending broadcast.")
        return
        
    if str(user.id) != meta.get("admin_id"):
        await query.answer("You are not authorized to confirm this broadcast.", show_alert=True)
        return
        
    if data == "broadcast_confirm":
        if meta.get("status") != "pending_confirmation":
            await query.answer("Broadcast already processed.")
            return
            
        if not REDIS.set(lock_key, str(int(time.time())), nx=True, ex=3600):
            await query.answer("Another broadcast is running.")
            return
            
        msg_text = meta.get("message", "")
        to_group = bool(int(meta.get("to_group", 0)))
        to_user = bool(int(meta.get("to_user", 0)))
        
        async def run_bg_broadcast():
            try:
                failed_g, failed_u, final_status = await perform_broadcast(context, meta_key, lock_key, gq_key, uq_key, msg_text, to_group, to_user)
                try:
                    await context.bot.send_message(
                        chat_id=int(meta.get("admin_id")),
                        text=f"📢 <b>Broadcast Status Update:</b>\nStatus: {final_status}\nGroups failed: {failed_g}\nUsers failed: {failed_u}",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
            except Exception as e:
                LOGGER.error(f"Error in bg broadcast: {e}")
                REDIS.delete(lock_key)
                
        asyncio.create_task(run_bg_broadcast())
        await query.edit_message_text("Broadcast started in background. You will receive a status update when it completes.")
        await query.answer()
    elif data == "broadcast_cancel":
        REDIS.delete(meta_key)
        REDIS.delete(gq_key)
        REDIS.delete(uq_key)
        await query.edit_message_text("Broadcast cancelled.")
        await query.answer()


@cutiepii_msg((filters.ALL & filters.ChatType.GROUPS), group=USERS_GROUP)
async def log_user(update: Update, _: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message

    update_user(msg.from_user.id, msg.from_user.username, chat.id, chat.title)

    if rep := msg.reply_to_message:
        update_user(
            rep.from_user.id,
            rep.from_user.username,
            chat.id,
            chat.title,
        )

        # PTB v20+ uses forward_origin; MessageOriginUser has sender_user
        _fwd_user = _get_forward_user(rep)
        if _fwd_user:
            update_user(_fwd_user.id, getattr(_fwd_user, "username", None))

        if rep.entities:
            for entity in rep.entities:
                if entity.type in ["text_mention", "mention"]:
                    with contextlib.suppress(AttributeError):
                        update_user(entity.user.id, entity.user.username)
        if rep.sender_chat and not rep.is_automatic_forward:
            update_user(
                rep.sender_chat.id,
                rep.sender_chat.username,
                chat.id,
                chat.title,
            )

    _fwd_user = _get_forward_user(msg)
    if _fwd_user:
        update_user(_fwd_user.id, getattr(_fwd_user, "username", None))

    if msg.entities:
        for entity in msg.entities:
            if entity.type in ["text_mention", "mention"]:
                with contextlib.suppress(AttributeError):
                    update_user(entity.user.id, entity.user.username)
    if msg.sender_chat and not msg.is_automatic_forward:
        update_user(msg.sender_chat.id, msg.sender_chat.username, chat.id, chat.title)

    if msg.new_chat_members:
        for user in msg.new_chat_members:
            if user.id == msg.from_user.id:  # we already added that in the first place
                continue
            update_user(user.id, user.username, chat.id, chat.title)

    if req := update.chat_join_request:
        update_user(req.from_user.id, req.from_user.username, chat.id, chat.title)


@cutiepii_cmd(command='chatlist', rate_limit_calls=3, rate_limit_window=60, add_error_handler=True)
@sudo_plus
async def chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    all_chats = sql.get_all_chats() or []
    chatfile = "List of chats.\n0. Chat name | Chat ID | Members count\n"
    P = 1
    for chat in all_chats:
        try:
            curr_chat = await context.bot.get_chat(chat.chat_id)
            chat_members = await curr_chat.get_member_count()
            chatfile += "{}. {} | {} | {}\n".format(
                P, chat.chat_name, chat.chat_id, chat_members
            )
            P = P + 1
        except:
            pass

    with BytesIO(str.encode(chatfile)) as output:
        output.name = "groups_list.txt"
        await update.effective_message.reply_document(
            document=output,
            filename="groups_list.txt",
            caption="Here be the list of groups in my database.",
        )
        
@cutiepii_msg((filters.ALL & filters.ChatType.GROUPS), group=USERS_GROUP)
async def chat_checker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    try:
        member = await get_bot_member(update.effective_chat.id)
        if getattr(member, "can_send_messages", None) is False:
            await bot.leave_chat(update.effective_message.chat.id)
    except:
        pass

        




def __user_info__(user_id):
    if user_id in [777000, 1087968824]:
        return """╘═━「 Groups count: <code>???</code> 」"""
    if user_id == dispatcher.bot.id:
        return """╘═━「 Groups count: <code>???</code> 」"""
    num_chats = sql.get_user_num_chats(user_id)
    return f"""╘═━「 Groups count: <code>{num_chats}</code> 」"""

def __stats__():
    return f"- {sql.num_users()} users, across {sql.num_chats()} chats"


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


__mod_name__ = "Users"
