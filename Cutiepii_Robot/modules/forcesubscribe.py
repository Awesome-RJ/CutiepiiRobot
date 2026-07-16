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
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import ContextTypes, MessageHandler, filters, CallbackQueryHandler
from telegram.error import BadRequest
from telegram.constants import ParseMode

from Cutiepii_Robot import dispatcher
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot.modules.sql import forceSubscribe_sql as sql


import re

@cutiepii_msg(pattern=filters.ChatType.GROUPS & ~filters.StatusUpdate.ALL, group=5)
async def check_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if new member has subscribed to all configured channels/groups"""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    # Get forcesubscribe settings
    fs_setting = sql.fs_settings(chat.id)
    if not fs_setting:
        return
    
    channel = fs_setting.channel
    channels = [c.strip() for c in re.split(r'[,\s;]+', channel) if c.strip()]
    
    not_joined_channels = []
    for chan in channels:
        try:
            member = await context.bot.get_chat_member(chan, user.id)
            if member.status not in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
                not_joined_channels.append(chan)
        except BadRequest:
            not_joined_channels.append(chan)
            
    if not_joined_channels:
        # User is not subscribed to all required chats
        button = []
        for chan in not_joined_channels:
            try:
                chat_info = await context.bot.get_chat(chan)
                title = chat_info.title
                invite_link = await context.bot.export_chat_invite_link(chan)
            except BadRequest:
                title = chan
                invite_link = f"https://t.me/{chan.replace('@', '')}" if str(chan).startswith("@") else None
            
            if invite_link:
                button.append([InlineKeyboardButton(f"Join {title}", url=invite_link)])
        
        button.append([InlineKeyboardButton("Unmute Me", callback_data=f"fs_unmute_{user.id}")])
        
        try:
            await message.delete()
        except BadRequest:
            pass
            
        await context.bot.send_message(
            chat.id,
            f"Hello {user.mention_html()},\n\n"
            f"You must join the following channels/groups to participate in this group:\n"
            + "\n".join([f"- <b>{c}</b>" for c in not_joined_channels]) + "\n\n"
            f"Please join them and click the 'Unmute Me' button below.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(button)
        )
        
        # Mute user
        await context.bot.restrict_chat_member(
            chat.id,
            user.id,
            permissions=None
        )


@cutiepii_callback(pattern=r"^fs_unmute_")
async def fs_unmute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle unmute button callback for multiple channels/groups"""
    query = update.callback_query
    chat = query.message.chat
    user = query.from_user
    
    # Extract user_id from callback data
    _, _, target_user_id = query.data.split("_")
    target_user_id = int(target_user_id)
    
    if user.id != target_user_id:
        await query.answer("This button is not configured for your user.", show_alert=True)
        return
    
    # Get forcesubscribe settings
    fs_setting = sql.fs_settings(chat.id)
    if not fs_setting:
        await query.answer("Force subscription requirements have been disabled for this chat.", show_alert=True)
        return
    
    channel = fs_setting.channel
    channels = [c.strip() for c in re.split(r'[,\s;]+', channel) if c.strip()]
    
    not_joined = []
    for chan in channels:
        try:
            member = await context.bot.get_chat_member(chan, user.id)
            if member.status not in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
                not_joined.append(chan)
        except BadRequest:
            not_joined.append(chan)
            
    if not not_joined:
        try:
            # User is subscribed, unmute them
            await context.bot.restrict_chat_member(
                chat.id,
                user.id,
                permissions=chat.permissions
            )
            await query.message.delete()
            await query.answer("Access Granted\nYou have been successfully unmuted. Welcome to the group.", show_alert=True)
        except BadRequest as e:
            await query.answer(f"Error\nFailed to unmute: {str(e)}", show_alert=True)
    else:
        await query.answer("Action Denied\nYou must join all the required channels or groups before you can be unmuted.", show_alert=True)


@cutiepii_cmd(command=["forcesubscribe", "fsub"], filters=filters.ChatType.GROUPS)
async def force_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable/disable force subscribe"""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    
    # Check if user is admin
    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        await message.reply_text("<b>Action Denied</b>\nYou do not have administrator privileges to run this command.", parse_mode=ParseMode.HTML)
        return
    
    # Check bot admin status
    bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
    if not bot_member.can_restrict_members:
        await message.reply_text("<b>Action Denied</b>\nI require the Restrict Members administrator permission to enable force subscription checks.", parse_mode=ParseMode.HTML)
        return
    
    if not args:
        # Show current settings
        fs_setting = sql.fs_settings(chat.id)
        if fs_setting:
            await message.reply_text(
                f"<b>Force Subscribe Status</b>\nForce subscribe is enabled.\nChannels/Groups: <code>{fs_setting.channel}</code>\n\n"
                f"Use <code>/forcesubscribe off</code> to disable.\n"
                f"Use <code>/forcesubscribe @channel1 @channel2</code> to set multiple targets.",
                parse_mode=ParseMode.HTML
            )
        else:
            await message.reply_text(
                "<b>Force Subscribe Status</b>\nForce subscribe is disabled.\n\n"
                "Use <code>/forcesubscribe @channel @group</code> to enable.",
                parse_mode=ParseMode.HTML
            )
        return
    
    if args[0].lower() in ["off", "disable", "no"]:
        sql.disapprove(chat.id)
        await message.reply_text("<b>Force Subscribe Updated</b>\nForce subscription requirements have been disabled for this chat.", parse_mode=ParseMode.HTML)
        # Log to log channel
        import Cutiepii_Robot.modules.sql.log_channel_sql as log_sql
        log_channel = log_sql.get_chat_log_channel(chat.id)
        if log_channel:
            admin_mention = f"<a href='tg://user?id={user.id}'>{html.escape(user.first_name)}</a>"
            log_txt = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#FORCESUBSCRIBE\n"
                f"<b>Admin:</b> {admin_mention}\n"
                f"<b>Status:</b> Disabled"
            )
            try:
                await context.bot.send_message(log_channel, log_txt, parse_mode=ParseMode.HTML)
            except Exception as e:
                LOGGER.error(f"Failed to send forcesubscribe disable log: {e}")
        return
    
    # Parse and validate multiple channels/groups
    channels_arg = " ".join(args)
    parsed_channels = [c.strip() for c in re.split(r'[,\s;]+', channels_arg) if c.strip()]
    
    if not parsed_channels:
        await message.reply_text("<b>Invalid Command Usage</b>\nPlease provide at least one channel or group username/ID.", parse_mode=ParseMode.HTML)
        return
        
    validated_channels = []
    validated_titles = []
    
    for chan in parsed_channels:
        try:
            chat_info = await context.bot.get_chat(chan)
            if chat_info.type not in ["channel", "supergroup", "group"]:
                await message.reply_text(f"<b>Invalid Target</b>\n<code>{chan}</code> is not a valid channel or group type.", parse_mode=ParseMode.HTML)
                return
            
            # Check if bot is admin in channel/group
            bot_channel_member = await context.bot.get_chat_member(chan, context.bot.id)
            if bot_channel_member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
                await message.reply_text(f"<b>Action Denied</b>\nI am not an administrator in <code>{chat_info.title}</code> ({chan}).", parse_mode=ParseMode.HTML)
                return
                
            validated_channels.append(chan)
            validated_titles.append(chat_info.title)
        except BadRequest as e:
            await message.reply_text(f"<b>Error</b>\nError validating <code>{chan}</code>: <code>{str(e)}</code>\n\nPlease verify that I am an administrator in that channel or group.", parse_mode=ParseMode.HTML)
            return
            
    saved_str = ",".join(validated_channels)
    sql.add_channel(chat.id, saved_str)
    
    titles_str = ", ".join(validated_titles)
    await message.reply_text(f"<b>Force Subscribe Updated</b>\nForce subscription has been enabled for: <b>{titles_str}</b>.", parse_mode=ParseMode.HTML)
    
    # Log to log channel
    import Cutiepii_Robot.modules.sql.log_channel_sql as log_sql
    log_channel = log_sql.get_chat_log_channel(chat.id)
    if log_channel:
        admin_mention = f"<a href='tg://user?id={user.id}'>{html.escape(user.first_name)}</a>"
        log_txt = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#FORCESUBSCRIBE\n"
            f"<b>Admin:</b> {admin_mention}\n"
            f"<b>Status:</b> Enabled forcesubscribe for {titles_str} (<code>{saved_str}</code>)"
        )
        try:
            await context.bot.send_message(log_channel, log_txt, parse_mode=ParseMode.HTML)
        except Exception as e:
            LOGGER.error(f"Failed to send forcesubscribe enable log: {e}")
 
 
@cutiepii_cmd(command="remfsub", filters=filters.ChatType.GROUPS)
async def remove_forcesubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if user is admin
    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        await message.reply_text("<b>Action Denied</b>\nYou do not have administrator privileges to run this command.", parse_mode=ParseMode.HTML)
        return
        
    sql.disapprove(chat.id)
    await message.reply_text("<b>Force Subscribe Updated</b>\nForce subscription requirements have been disabled and removed successfully.", parse_mode=ParseMode.HTML)
    
    # Log to log channel
    import Cutiepii_Robot.modules.sql.log_channel_sql as log_sql
    log_channel = log_sql.get_chat_log_channel(chat.id)
    if log_channel:
        admin_mention = f"<a href='tg://user?id={user.id}'>{html.escape(user.first_name)}</a>"
        log_txt = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#FORCESUBSCRIBE\n"
            f"<b>Admin:</b> {admin_mention}\n"
            f"<b>Status:</b> Disabled & Removed"
        )
        try:
            await context.bot.send_message(log_channel, log_txt, parse_mode=ParseMode.HTML)
        except Exception as e:
            LOGGER.error(f"Failed to send forcesubscribe remove log: {e}")


# Handler registration


__mod_name__ = "Force Subscribe"
__help__ = True
