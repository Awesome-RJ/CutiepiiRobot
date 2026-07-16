# BSD 2-Clause License
# 
# Copyright (C) 2017-2019, Paul Larsen
# Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
# Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>
# 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, cutiepii_join_request
import html
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ChatJoinRequestHandler, CallbackQueryHandler, CommandHandler
from telegram.error import BadRequest

from Cutiepii_Robot import dispatcher, LOGGER, REDIS
from Cutiepii_Robot.modules.helper_funcs.admin_status import user_is_admin
import Cutiepii_Robot.modules.sql.log_channel_sql as log_sql

async def safe_query_answer(query, text, show_alert=False):
    try:
        await query.answer(text, show_alert=show_alert)
    except BadRequest as e:
        if "Query is too old" in str(e) or "query id is invalid" in str(e):
            LOGGER.warning(f"Failed to answer callback query: {e}")
        else:
            raise

@cutiepii_join_request()
async def join_request_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.chat_join_request
    if not request:
        return

    chat = request.chat
    user = request.from_user

    LOGGER.info(f"[JOINREQ]: join_request_handler triggered for user {user.id} ({user.first_name}) in chat {chat.id} ({chat.title})")

    import Cutiepii_Robot.modules.sql.welcome_sql as welcome_sql
    from multicolorcaptcha import CaptchaGenerator
    import random
    import string
    from io import BytesIO

    # Check if captcha is enabled for join requests (Pre-Entry Verification)
    if welcome_sql.welcome_mutes(chat.id) == "captcha":
        # Generate Captcha
        generator = CaptchaGenerator(4)
        captcha = generator.gen_captcha_image(difficult_level=2, multicolor=True)
        image = captcha["image"]
        correct_ans = str(captcha["characters"])

        fileobj = BytesIO()
        fileobj.name = f"captcha_{user.id}.png"
        image.save(fp=fileobj)
        fileobj.seek(0)

        # Generate distractors
        def gen_dist():
            return "".join(random.choices(string.ascii_uppercase + string.digits, k=4))

        options = [correct_ans]
        while len(options) < 4:
            dist = gen_dist()
            if dist not in options:
                options.append(dist)
        random.shuffle(options)

        # Store correct answer in Redis (5 minutes expiry)
        REDIS.set(f"joinreq_ans:{chat.id}:{user.id}", correct_ans, ex=300)

        # Build buttons for the options
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text=opt, callback_data=f"jrcaptcha_{chat.id}_{user.id}_{opt}")
                    for opt in options[:2]
                ],
                [
                    InlineKeyboardButton(text=opt, callback_data=f"jrcaptcha_{chat.id}_{user.id}_{opt}")
                    for opt in options[2:]
                ]
            ]
        )

        try:
            await context.bot.send_photo(
                chat_id=user.id,
                photo=fileobj,
                caption=f"<b>Pre-Entry Verification for {html.escape(chat.title)}</b>\n\nPlease solve the captcha below to join the group. Select the correct characters:",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            # Log pre-entry captcha sent
            LOGGER.info(f"[JOINREQ CAPTCHA]: Sent captcha to {user.id} for chat {chat.id}")
            return
        except Exception as e:
            LOGGER.warning(f"Could not initiate PM with {user.id} for captcha: {e}")

    # Get joinreq setting from Redis
    setting = REDIS.get(f"joinreq:{chat.id}")
    if not setting:
        setting = REDIS.get(f"autoapprove:{chat.id}")
    if isinstance(setting, bytes):
        setting = setting.decode("utf-8")
    if not setting:
        setting = "on" # Default is to show buttons
    elif setting == "true":
        setting = "auto"
    elif setting == "false":
        setting = "off"

    if setting == "auto":
        try:
            await context.bot.approve_chat_join_request(chat_id=chat.id, user_id=user.id)
            LOGGER.info(f"[AUTOAPPROVED]: Automatically approved {user.id} in chat {chat.id}")
            
            # Log auto-approve
            log_channel = log_sql.get_chat_log_channel(chat.id)
            if log_channel:
                log_txt = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#JOIN_REQUEST #AUTO_APPROVED\n\n"
                    f"👤 <b>USER INFO:</b>\n"
                    f"❍ <b>Name:</b> {html.escape(user.full_name) or 'N/A'}\n"
                    f"❍ <b>ID:</b> <code>{user.id}</code>\n"
                    f"❍ <b>Mention:</b> <a href='tg://user?id={user.id}'>{html.escape(user.first_name)}</a>\n"
                    f"❍ <b>Username:</b> @{user.username if user.username else 'N/A'}\n\n"
                    f"<b>Status:</b> Automatically Approved"
                )
                try:
                    await context.bot.send_message(log_channel, log_txt, parse_mode=ParseMode.HTML)
                except Exception as e:
                    LOGGER.error(f"Failed to send autoapprove log: {e}")
            return
        except Exception as e:
            LOGGER.error(f"[AUTOAPPROVED ERROR]: Failed to auto-approve {user.id} in {chat.id}: {e}")
            return

    elif setting == "on":
        # Format user info and send notification
        username_str = f"@{user.username}" if user.username else "None"
        user_mention = f"<a href='tg://user?id={user.id}'>{html.escape(user.first_name)}</a>"
        
        try:
            admins = await chat.get_administrators()
            admin_tags = "".join([f"<a href='tg://user?id={admin.user.id}'>\u2063</a>" for admin in admins if not admin.user.is_bot])
        except Exception:
            admin_tags = ""

        txt = (
            f"<b>New join request is available</b>{admin_tags}\n"
            f"👤 <b>USER's INFO</b>\n"
            f"❍ <b>Name:</b> {html.escape(user.full_name)}\n"
            f"❍ <b>Mention:</b> {user_mention}\n"
            f"❍ <b>ID:</b> <code>{user.id}</code>\n"
            f"❍ <b>Username:</b> {username_str}\n"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Accept", callback_data=f"accept_joinreq_{user.id}"),
                    InlineKeyboardButton("Decline", callback_data=f"decline_joinreq_{user.id}")
                ]
            ]
        )

        try:
            await context.bot.send_message(
                chat_id=chat.id,
                text=txt,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        except BadRequest as e:
            LOGGER.error(f"Failed to send join request message: {e}")
        return

    else: # "off"
        # Silent (not showing any alert or notification)
        return

@cutiepii_callback(pattern=r"^(accept|decline)_joinreq_")
async def accept_decline_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    admin_user = query.from_user
    chat = update.effective_chat
    message = query.message

    # Check if the user interacting is admin or owner
    if not await user_is_admin(update, admin_user.id):
        await safe_query_answer(query, "Action Denied\nYou do not have administrator privileges to run this command.", show_alert=True)
        return

    split = query.data.split("_")
    action = split[0]  # "accept" or "decline"
    target_user_id = int(split[2])

    try:
        target_user = await context.bot.get_chat(target_user_id)
        target_mention = f"<a href='tg://user?id={target_user.id}'>{html.escape(target_user.first_name)}</a>"
    except Exception:
        target_mention = f"User {target_user_id}"

    admin_mention = f"<a href='tg://user?id={admin_user.id}'>{html.escape(admin_user.first_name)}</a>"

    if action == "accept":
        try:
            await context.bot.approve_chat_join_request(chat_id=chat.id, user_id=target_user_id)
            await safe_query_answer(query, "Request Approved")
            await message.edit_text(
                f"{admin_mention} approved the join request of {target_mention}.",
                parse_mode=ParseMode.HTML
            )
            
            # Log approval
            log_channel = log_sql.get_chat_log_channel(chat.id)
            if log_channel:
                log_txt = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#JOIN_REQUEST #APPROVED\n\n"
                    f"👤 <b>USER INFO:</b>\n"
                    f"❍ <b>Name:</b> {html.escape(target_user.full_name if hasattr(target_user, 'full_name') else '') or 'N/A'}\n"
                    f"❍ <b>ID:</b> <code>{target_user_id}</code>\n"
                    f"❍ <b>Mention:</b> {target_mention}\n"
                    f"❍ <b>Username:</b> @{target_user.username if hasattr(target_user, 'username') and target_user.username else 'N/A'}\n\n"
                    f"👮 <b>ADMIN INFO:</b>\n"
                    f"❍ <b>Admin:</b> {admin_mention}\n"
                    f"❍ <b>Admin ID:</b> <code>{admin_user.id}</code>\n\n"
                    f"<b>Status:</b> Approved"
                )
                try:
                    await context.bot.send_message(log_channel, log_txt, parse_mode=ParseMode.HTML)
                except Exception as e:
                    LOGGER.error(f"Failed to send join request approval log: {e}")
        except Exception as e:
            await safe_query_answer(query, f"Failed to approve request: {e}", show_alert=True)
    elif action == "decline":
        try:
            await context.bot.decline_chat_join_request(chat_id=chat.id, user_id=target_user_id)
            await safe_query_answer(query, "Request Declined")
            await message.edit_text(
                f"{admin_mention} declined the join request of {target_mention}.",
                parse_mode=ParseMode.HTML
            )
            
            # Log decline
            log_channel = log_sql.get_chat_log_channel(chat.id)
            if log_channel:
                log_txt = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#JOIN_REQUEST #DECLINED\n\n"
                    f"👤 <b>USER INFO:</b>\n"
                    f"❍ <b>Name:</b> {html.escape(target_user.full_name if hasattr(target_user, 'full_name') else '') or 'N/A'}\n"
                    f"❍ <b>ID:</b> <code>{target_user_id}</code>\n"
                    f"❍ <b>Mention:</b> {target_mention}\n"
                    f"❍ <b>Username:</b> @{target_user.username if hasattr(target_user, 'username') and target_user.username else 'N/A'}\n\n"
                    f"👮 <b>ADMIN INFO:</b>\n"
                    f"❍ <b>Admin:</b> {admin_mention}\n"
                    f"❍ <b>Admin ID:</b> <code>{admin_user.id}</code>\n\n"
                    f"<b>Status:</b> Declined"
                )
                try:
                    await context.bot.send_message(log_channel, log_txt, parse_mode=ParseMode.HTML)
                except Exception as e:
                    LOGGER.error(f"Failed to send join request decline log: {e}")
        except Exception as e:
            await safe_query_answer(query, f"Failed to decline request: {e}", show_alert=True)

@cutiepii_cmd(command=["joinreq", "autoapprove"])
async def joinreq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if chat.type == "private":
        await message.reply_text("<b>Action Denied</b>\nThis command can only be used in group chats.", parse_mode=ParseMode.HTML)
        return

    # Check if user is admin
    if not await user_is_admin(update, user.id):
        await message.reply_text("<b>Action Denied</b>\nYou do not have administrator privileges to run this command.", parse_mode=ParseMode.HTML)
        return

    args = context.args
    if args:
        val = args[0].lower()
        if val in ["on", "off", "auto"]:
            REDIS.set(f"joinreq:{chat.id}", val)
            await message.reply_text(f"<b>Join Request Settings Updated</b>\nJoin request setting has been set to: <code>{val.upper()}</code>", parse_mode=ParseMode.HTML)
            return
        else:
            await message.reply_text("<b>Invalid Argument</b>\nPlease specify either <code>on</code>, <code>off</code>, or <code>auto</code>.", parse_mode=ParseMode.HTML)
            return

    # Check current status
    setting = REDIS.get(f"joinreq:{chat.id}")
    if not setting:
        setting = REDIS.get(f"autoapprove:{chat.id}")
    if isinstance(setting, bytes):
        setting = setting.decode("utf-8")
    if not setting:
        setting = "on"
    elif setting == "true":
        setting = "auto"
    elif setting == "false":
        setting = "off"
    
    buttons = [
        [
            InlineKeyboardButton("ON" if setting == "on" else "ON (Select)", callback_data="joinreq_set_on"),
            InlineKeyboardButton("AUTO" if setting == "auto" else "AUTO (Select)", callback_data="joinreq_set_auto"),
            InlineKeyboardButton("OFF" if setting == "off" else "OFF (Select)", callback_data="joinreq_set_off")
        ]
    ]
    
    keyboard = InlineKeyboardMarkup(buttons)
    
    await message.reply_text(
        f"<b>Join Request Settings</b>\n\n"
        f"<b>Current Setting:</b> <code>{setting.upper()}</code>\n\n"
        f"<b>Modes:</b>\n"
        f"- <b>ON</b> - Shows Accept/Decline approval notification buttons in the group\n"
        f"- <b>AUTO</b> - Automatically approves all join requests immediately\n"
        f"- <b>OFF</b> - No notification/alerts shown (silently keeps requests pending)\n\n"
        f"<i>Select a button below or use command <code>/joinreq [on/off/auto]</code> to change settings.</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard
    )

@cutiepii_callback(pattern=r"^joinreq_set_(on|off|auto)$")
async def joinreq_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    chat = update.effective_chat
    message = query.message

    if not await user_is_admin(update, user.id):
        await safe_query_answer(query, "Action Denied\nYou do not have administrator privileges to run this command.", show_alert=True)
        return

    cb_data = query.data
    val = cb_data.split("_")[2]
    
    REDIS.set(f"joinreq:{chat.id}", val)
    await safe_query_answer(query, f"Join request setting set to {val.upper()}")
    
    buttons = [
        [
            InlineKeyboardButton("ON" if val == "on" else "ON (Select)", callback_data="joinreq_set_on"),
            InlineKeyboardButton("AUTO" if val == "auto" else "AUTO (Select)", callback_data="joinreq_set_auto"),
            InlineKeyboardButton("OFF" if val == "off" else "OFF (Select)", callback_data="joinreq_set_off")
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    
    try:
        await message.edit_text(
            f"<b>Join Request Settings</b>\n\n"
            f"<b>Current Setting:</b> <code>{val.upper()}</code>\n\n"
            f"<b>Modes:</b>\n"
            f"- <b>ON</b> - Shows Accept/Decline approval notification buttons in the group\n"
            f"- <b>AUTO</b> - Automatically approves all join requests immediately\n"
            f"- <b>OFF</b> - No notification/alerts shown (silently keeps requests pending)\n\n"
            f"<i>Select a button below or use command <code>/joinreq [on/off/auto]</code> to change settings.</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )
    except BadRequest as excp:
        if "Message is not modified" not in excp.message:
            raise

from telethon.tl.functions.messages import GetChatInviteImportersRequest
from Cutiepii_Robot import telethn

@cutiepii_cmd(command="clear_pending")
async def clear_pending_req(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    bot = context.bot
    user = update.effective_user

    if chat.type == "private":
        await message.reply_text("<b>Action Denied</b>\nThis command can only be used in group chats.", parse_mode=ParseMode.HTML)
        return

    # Check user permissions
    if not await user_is_admin(update, user.id):
        await message.reply_text("<b>Action Denied</b>\nYou do not have administrator privileges to run this command.", parse_mode=ParseMode.HTML)
        return

    status_msg = await message.reply_text("<b>Clear Pending Requests</b>\nDeclining all pending join requests in this group...", parse_mode=ParseMode.HTML)
    
    try:
        peer = await telethn.get_input_entity(chat.id)
        
        res = await telethn(GetChatInviteImportersRequest(
            peer=peer,
            requested=True,
            limit=100
        ))
        
        importers = res.users
        if not importers:
            await status_msg.edit_text("<b>Clear Pending Requests</b>\nThere are no pending join requests to clear in this chat.", parse_mode=ParseMode.HTML)
            return
            
        cleared_count = 0
        for u in importers:
            try:
                await bot.decline_chat_join_request(chat_id=chat.id, user_id=u.id)
                cleared_count += 1
            except Exception as e:
                LOGGER.warning(f"Failed to decline join request for {u.id}: {e}")
                
        await status_msg.edit_text(f"<b>Clear Pending Requests</b>\nSuccessfully cleared <code>{cleared_count}</code> pending join request(s).", parse_mode=ParseMode.HTML)
    except Exception as e:
        await status_msg.edit_text(f"<b>Error</b>\nAn error occurred while clearing requests: <code>{e}</code>", parse_mode=ParseMode.HTML)


@cutiepii_callback(pattern=r"^jrcaptcha_")
async def joinreq_captcha_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    chat_id = int(data[1])
    user_id = int(data[2])
    choice = data[3]

    correct_ans = REDIS.get(f"joinreq_ans:{chat_id}:{user_id}")
    if not correct_ans:
        await query.message.edit_caption(
            caption="<b>Captcha Expired</b>\nPlease request to join the group again to verify.",
            parse_mode=ParseMode.HTML
        )
        return

    correct_ans = correct_ans.decode("utf-8")

    if choice == correct_ans:
        try:
            await context.bot.approve_chat_join_request(chat_id=chat_id, user_id=user_id)
            await query.message.edit_caption(
                caption="<b>Captcha Solved Successfully</b>\nYour join request has been approved. You can now enter the group.",
                parse_mode=ParseMode.HTML
            )
            
            chat = await context.bot.get_chat(chat_id)
            log_channel = log_sql.get_chat_log_channel(chat_id)
            if log_channel:
                log_txt = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#JOIN_REQUEST #CAPTCHA_SOLVED\n\n"
                    f"👤 <b>USER:</b> <a href='tg://user?id={user_id}'>User {user_id}</a>\n"
                    f"<b>Status:</b> Approved via PM Captcha Solver"
                )
                try:
                    await context.bot.send_message(log_channel, log_txt, parse_mode=ParseMode.HTML)
                except Exception:
                    pass
        except Exception as e:
            await query.message.edit_caption(
                caption=f"<b>Error</b>\nCould not approve request: <code>{e}</code>",
                parse_mode=ParseMode.HTML
            )
    else:
        try:
            await context.bot.decline_chat_join_request(chat_id=chat_id, user_id=user_id)
            await query.message.edit_caption(
                caption="<b>Verification Failed</b>\nYour request to join has been declined.",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            await query.message.edit_caption(
                caption=f"<b>Error</b>\nCould not decline request: <code>{e}</code>",
                parse_mode=ParseMode.HTML
            )

    REDIS.delete(f"joinreq_ans:{chat_id}:{user_id}")




__mod_name__ = "Join Request"

__help__ = True

__handlers__ = [
]
