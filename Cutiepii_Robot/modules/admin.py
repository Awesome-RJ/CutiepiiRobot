"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot

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

import time
import os
import html
import requests
import Cutiepii_Robot.modules.sql.pin_sql as sql
import Cutiepii_Robot.modules.sql.antilinkedchannel_sql as sql1

from io import BytesIO
from html import escape
from typing import Optional, Dict

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, Message
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import BadRequest
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.helpers import mention_html
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.tl.types import ChannelParticipantCreator
from telethon import events
from telethon.tl import functions, types
from telethon.errors import *
from telethon.tl import *
from telethon import *
# Pyrogram imports removed


from Cutiepii_Robot import SUDO_USERS, TOKEN, dispatcher, telethn, LOGGER, BOT_ID
from Cutiepii_Robot.modules.helper_funcs.parsing import build_keyboard_from_list, get_data, Types, VALID_FORMATTERS, ENUM_FUNC_MAP


from Cutiepii_Robot.modules.connection import connected
from Cutiepii_Robot.modules.helper_funcs.chat_status import (
    ADMIN_CACHE,
    connection_status,
)

from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    get_bot_member,
    bot_is_admin,
    user_is_admin,
    user_not_admin_check,
    update_admins_cache,
    ADMINS_CACHE, BOT_ADMIN_CACHE,
)
from Cutiepii_Robot.modules.helper_funcs.string_handling import (
    escape_invalid_curly_brackets
)

from Cutiepii_Robot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.helper_funcs.alternate import send_message
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd

async def can_promote_users(message):
    result = await telethn(
        functions.channels.GetParticipantRequest(
            channel=message.chat_id,
            user_id=message.sender_id,
        )
    )
    p = result.participant
    return isinstance(p, types.ChannelParticipantCreator) or (
        isinstance(p, types.ChannelParticipantAdmin) and p.admin_rights.ban_users
    )


async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):
        return isinstance(
            (
                await telethn(functions.channels.GetParticipantRequest(chat, user))
            ).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerUser):
        return True


async def can_ban_users(message: Message):
    result = await telethn(
        functions.channels.GetParticipantRequest(
            channel=message.chat_id,
            user_id=message.sender_id,
        )
    )
    p = result.participant
    return isinstance(p, types.ChannelParticipantCreator) or (
        isinstance(p, types.ChannelParticipantAdmin) and p.admin_rights.ban_users
    )




@cutiepii_cmd(command=['setgstickers', 'setgsticker'], can_disable=False)
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def set_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if not msg.reply_to_message:
        if not msg.reply_to_message.sticker:
            await msg.reply_text("Reply to a sticker to set its pack as the group pack!")
            return ""
        await msg.reply_text("Reply to a sticker to set its pack as the group pack!")
        return ""

    try:
        stk_set = msg.reply_to_message.sticker.set_name
        await bot.set_chat_sticker_set(chat.id, stk_set)
        await msg.reply_text(
                f"<b>{user.first_name}</b> changed the group stickers set."
                if not msg.sender_chat else "Group stickers set has been changed.",
                parse_mode=ParseMode.HTML)

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ADMIN\nChat sticker set changed\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message

    except BadRequest as e:
        # https://github.com/el0xren/tgbot/blob/773220202ea0b20137ccdd833dd97f10d0e54b83/tg_bot/modules/admin.py#L297
        if e.message == 'Participants_too_few':
             errmsg = "Sorry, due to telegram restrictions, the chat needs to have"\
                      " a minimum of 100 members before they can have group stickers!"
        else:
            errmsg = f"An Error occurred:\n{str(e)}"
        await msg.reply_text(errmsg)
        return ''

@cutiepii_cmd(command='setgpic', can_disable=False)
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def setchatpic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if (
        not msg.reply_to_message
        and not msg.reply_to_message.document
        and not msg.reply_to_message.photo
    ):
        await msg.reply_text("Please send a photo or a document to set it as the group photo!")
        return ""

    if msg.reply_to_message.photo:
        file_id = msg.reply_to_message.photo[-1].file_id
    elif msg.reply_to_message.document:
        file_id = msg.reply_to_message.document.file_id

    try:
        image_file = await context.bot.get_file(file_id)  # kanged from stickers
        image_data = await image_file.download_as_bytearray()
        image_bytes = BytesIO(image_data)

        await bot.set_chat_photo(chat.id, image_bytes)
        await msg.reply_text(
                f"<b>{user.first_name}</b> changed the group photo."
                if not msg.sender_chat else "Group photo has been changed.",
                parse_mode=ParseMode.HTML)
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ADMIN\nChat photo changed\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message

    except BadRequest as e:
        await msg.reply_text("An Error occurred:\n" + str(e))
        return ''


@cutiepii_cmd(command='delgpic', can_disable=False)
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def rmchatpic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    try:
        await bot.delete_chat_photo(chat.id)
        await msg.reply_text(
                f"<b>{user.first_name}</b> deleted the group photo."
                if not msg.sender_chat else "Group photo has been deleted.",
                parse_mode=ParseMode.HTML)
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ADMIN\nChat photo removed\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message

    except BadRequest as e:
        await msg.reply_text("An Error occurred:\n" + str(e))
        return ''


@cutiepii_cmd(command='setgdesc', can_disable=False)
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def set_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    args = context.args

    if args:
        title = "  ".join(args)

    if msg.reply_to_message:
        title = msg.reply_to_message.text

    if not title:
        await msg.reply_text("No title given!")
        return ""

    try:
        await bot.set_chat_description(chat.id, title)
        if len(title) > 255: # telegram limits the title/description to 255 characters
            await msg.reply_text("Description longer than 255 characters, Truncating it to 255 characters!")
        await msg.reply_text(
                f"<b>{user.first_name}</b> changed the group description.to:\n<b>{title[:255]}</b>"
                if not msg.sender_chat else f"Group description has been changed.to:\n<b>{title[:255]}</b>",
                parse_mode=ParseMode.HTML)

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ADMIN\nChat description changed\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message

    except BadRequest as e:
        await msg.reply_text("An Error occurred:\n" + str(e))
        return '' 

@cutiepii_cmd(command='setgtitle', can_disable=False)
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def setchat_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    args = context.args

    if args:
        title = "  ".join(args)

    if msg.reply_to_message:
        title = msg.reply_to_message.text

    if not title:
        await msg.reply_text("No title given!")
        return ""

    try:
        await bot.set_chat_title(chat.id, title)
        if len(title) > 255:  # telegram limits the title/description to 255 characters
            await msg.reply_text("Title longer than 255 characters, Truncating it to 255 characters!")
        await msg.reply_text(
                f"<b>{user.first_name}</b> changed the group title.to:\n<b>{title[:255]}</b>"
                if not msg.sender_chat else f"Group title has been changed.to:\n<b>{title[:255]}</b>",
                parse_mode=ParseMode.HTML)

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ADMIN\nChat title changed\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message

    except BadRequest as e:
        await msg.reply_text("An Error occurred:\n" + str(e))
        return ''


@cutiepii_callback(pattern=r"admin_")
@loggable
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
async def promote_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    bot = context.bot

    mode = query.data.split("_")[1]
    try:
        if await user_is_admin(chat, user.id):
            if mode == "demote":
                user_id = query.data.split("_")[2]
                user_member = await chat.get_member(user_id)
                await bot.promote_chat_member(
                    chat.id,
                    user_id,
                    can_change_info=False,
                    can_post_messages=False,
                    can_edit_messages=False,
                    can_delete_messages=False,
                    can_invite_users=False,
                    can_restrict_members=False,
                    can_pin_messages=False,
                    can_promote_members=False,
                    #can_manage_video_chats=False
                )
                await query.message.delete()
                await bot.answer_callback_query(
                    query.id,
                    f"Sucessfully demoted {user_member.user.first_name or user_id}",
                    show_alert=True,
                )
            elif mode == "refresh":
                try:
                    ADMIN_CACHE.pop(update.effective_chat.id)
                except KeyError:
                    pass
                await bot.answer_callback_query(query.id, "Admins cache refreshed!", show_alert=True)
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in promote buttons. %s", str(query.data))


@cutiepii_cmd(command=["setanon", "anonpromote"], can_disable=False)
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
async def promoteanon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        await message.reply_text("<b>Action Denied</b>\nThis command can only be used in group chats.")

    user_id, title = await extract_user_and_text(message, args)

    if not user_id:
        user_id = user.id
        title = " ".join(args)

    try:
        user_member = await chat.get_member(user_id)
    except Exception as e:
        await message.reply_text("<b>Error</b>\n<code>{}</code>".format(e))
        return

    if user_member.status == "creator":
        await message.reply_text("<b>Action Denied</b>\nThe target user is the chat owner.")
        return

    if user_member.is_anonymous is True:
        await message.reply_text("<b>Action Denied</b>\nThe target user is already posting anonymously.")
        return

    if user_id == bot.id:
        await message.reply_text("<b>Action Denied</b>\nI cannot promote myself.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = await get_bot_member(chat.id)
    # set same perms as user -  to keep the other perms untouched!
    u_member = await chat.get_member(user_id)
    # the perms may be not same as old ones if the bot doesn't have the rights to change them but can't do anything about it

    try:
        if title:
            await bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
        await bot.promote_chat_member(
            chat.id,
            user_id,
            is_anonymous=True,

            can_change_info=bool(bot_member.can_change_info and u_member.can_change_info),
            can_post_messages=bool(bot_member.can_post_messages and u_member.can_post_messages),
            can_edit_messages=bool(bot_member.can_edit_messages and u_member.can_edit_messages),
            can_delete_messages=bool(bot_member.can_delete_messages and u_member.can_delete_messages),
            can_invite_users=bool(bot_member.can_invite_users and u_member.can_invite_users),
            can_promote_members=bool(bot_member.can_promote_members and u_member.can_promote_members),
            can_restrict_members=bool(bot_member.can_restrict_members and u_member.can_restrict_members),
            can_pin_messages=bool(bot_member.can_pin_messages and u_member.can_pin_messages),
            can_manage_video_chats=bool(bot_member.can_manage_video_chats and u_member.can_manage_video_chats),

        )

        rmsg = f"<b>{user_member.user.first_name or user_id}</b> is now anonymous"
        if title:
            rmsg += f" with title <code>{html.escape(title)}</code>"
        await bot.send_message(
            chat.id,
            rmsg,
            parse_mode=ParseMode.HTML,
        ) 
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            await message.reply_text("<b>Action Denied</b>\nCannot promote a user who is not a member of this group.")
        else:
            await message.reply_text("<b>Error</b>\nAn unexpected error occurred while updating user permissions.")
        return

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#PROMOTED\n"
        f"Anonymous\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@cutiepii_cmd(command="promote", can_disable=False)
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
async def promote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = await chat.get_member(user.id)

    user_id, title = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(
            "<b>Invalid Command Usage</b>\nPlease specify a target user by replying to their message, mentioning their username, or providing their user ID.",
        )
        return

    try:
        user_member = await chat.get_member(user_id)
    except Exception as e:
        await message.reply_text(f"<b>Error</b>\n<code>{e}</code>")
        return

    if user_member.status in ["administrator", "creator"]:
        await update.effective_message.reply_text("<b>Action Denied</b>\nThe target user is already an administrator.")
        return

    if user_id == bot.id:
        await update.effective_message.reply_text("<b>Action Denied</b>\nI cannot promote myself.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = await get_bot_member(chat.id)
    #can_promote_members = False
    #if "all" in permissions and bot_member.can_promote_members:
    #    can_promote_members = True

    try:
        await bot.promote_chat_member(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
            can_manage_video_chats=bot_member.can_manage_video_chats,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            await update.effective_message.reply_text("I can't promote someone who isn't in the group.")
        else:
            await update.effective_message.reply_text("An error occurred while promoting.")
        return

    await bot.send_message(
        chat.id,
        f"<b>╔━「 Promote in {chat.title}</b> \n"
        f"<b>- Admin:</b> {mention_html(user.id, user.first_name)} \n"
        f"<b>- User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="⏬ Demote",
                        callback_data=f"admin_demote_{user_member.user.id}",
                    ),
                    InlineKeyboardButton(
                        text="🔄 Cache",
                        callback_data="admin_refresh",
                    ),
                ],
            ],
        ),
    )

    if len(title) > 16:
        await message.reply_text(
            "The title length is longer than 16 characters.\nTruncating it to 16 characters.",
        )

    try:
        await bot.set_chat_administrator_custom_title(chat.id, user_id, title)
    except:
        pass

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#PROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    if title != "":
        log_message += f"<b>Admin Title:</b> {title}"

    return log_message

@cutiepii_cmd(command=["midpromote", "halfpromote"], can_disable=False)
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
async def midpromote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = await chat.get_member(user.id)

    user_id, title = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(
            "⚠️ User not found\n\nI don't know who you're talking about, you're going to need to specify a user...",
        )
        return

    try:
        user_member = await chat.get_member(user_id)
    except Exception as e:
        await message.reply_text(f"Error: {e}")
        return

    if user_member.status in ["administrator", "creator"]:
        await update.effective_message.reply_text("How am I meant to midpromote someone that's already an admin?")
        return

    if user_id == bot.id:
        await update.effective_message.reply_text("I can't midpromote myself! Get an admin to do it for me.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = await get_bot_member(chat.id)
    #can_promote_members = False
    #if "all" in permissions and bot_member.can_promote_members:
    #    can_promote_members = True

    try:
        await bot.promote_chat_member(
            chat.id,
            user_id,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_pin_messages=bot_member.can_pin_messages,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            await update.effective_message.reply_text("I can't midpromote someone who isn't in the group.")
        else:
            await update.effective_message.reply_text("An error occured while midpromoting.")
        return


    await bot.send_message(
        chat.id,
        f"<b>╔━「 MidPromote in {chat.title}</b> \n"
        f"<b>- Admin:</b> {mention_html(user.id, user.first_name)} \n"
        f"<b>- User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="⏬ Demote",
                        callback_data=f"admin_demote_{user_member.user.id}",
                    ),
                    InlineKeyboardButton(
                        text="🔄 Cache",
                        callback_data="admin_refresh",
                    ),
                ],
            ],
        ),
    )

    if len(title) > 16:
        await message.reply_text(
            "The title length is longer than 16 characters.\nTruncating it to 16 characters.",
        )

    try:
        await bot.set_chat_administrator_custom_title(chat.id, user_id, title)
    except:
        pass

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#MIDPROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    if title != "":
        log_message += f"<b>Admin Title:</b> {title}"

    return log_message

@cutiepii_cmd(command="lowpromote", can_disable=False)
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
async def lowpromote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = await chat.get_member(user.id)

    user_id, title = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(
            "⚠️ User not found\n\nI don't know who you're talking about, you're going to need to specify a user...",
        )
        return

    try:
        user_member = await chat.get_member(user_id)
    except Exception as e:
        await message.reply_text(f"Error: {e}")
        return

    if user_member.status in ["administrator", "creator"]:
        await update.effective_message.reply_text("How am I meant to lowpromote someone that's already an admin?")
        return

    if user_id == bot.id:
        await update.effective_message.reply_text("I can't lowpromote myself! Get an admin to do it for me.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = await get_bot_member(chat.id)
    #can_promote_members = False
    #if "all" in permissions and bot_member.can_promote_members:
    #    can_promote_members = True

    try:
        await bot.promote_chat_member(
            chat.id,
            user_id,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            await update.effective_message.reply_text("I can't lowpromote someone who isn't in the group.")
        else:
            await update.effective_message.reply_text("An error occurred while low-promoting.")
        return

    await bot.send_message(
        chat.id,
        f"<b>╔━「 LowPromote in {chat.title}</b> \n"
        f"<b>- Admin:</b> {mention_html(user.id, user.first_name)} \n"
        f"<b>- User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="⏬ Demote",
                        callback_data=f"admin_demote_{user_member.user.id}",
                    ),
                    InlineKeyboardButton(
                        text="🔄 Cache",
                        callback_data="admin_refresh",
                    ),
                ],
            ],
        ),
    )

    if len(title) > 16:
        await message.reply_text(
            "The title length is longer than 16 characters.\nTruncating it to 16 characters.",
        )

    try:
        await bot.set_chat_administrator_custom_title(chat.id, user_id, title)
    except:
        pass

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#LOWPROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    if title != "":
        log_message += f"<b>Admin Title:</b> {title}"

    return log_message


@cutiepii_cmd(command="fullpromote", can_disable=False)
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
async def fullpromote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = await chat.get_member(user.id)

    user_id, title = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(
            "⚠️ User not found\n\nI don't know who you're talking about, you're going to need to specify a user...",
        )
        return

    try:
        user_member = await chat.get_member(user_id)
    except Exception as e:
        await message.reply_text(f"Error: {e}")
        return

    if user_member.status in ["administrator", "creator"]:
        await update.effective_message.reply_text("This user is already an admin!")
        return

    if user_id == bot.id:
        await update.effective_message.reply_text("I can't promote myself! Get an admin to do it for me.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = await get_bot_member(chat.id)
    #can_promote_members = False
    #if "all" in permissions and bot_member.can_promote_members:
    #    can_promote_members = True

    try:
        await bot.promote_chat_member(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_promote_members=bot_member.can_promote_members,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
            can_manage_video_chats=bot_member.can_manage_video_chats,
        )
    except BadRequest as err:
        await update.effective_message.reply_text(f"An error occurred while promoting: {err.message}")
        return

    await bot.send_message(
        chat.id,
        f"<b>╔━「 FullPromote in {chat.title}</b> \n"
        f"<b>- Admin:</b> {mention_html(user.id, user.first_name)} \n"
        f"<b>- User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="⏬ Demote",
                        callback_data=f"admin_demote_{user_member.user.id}",
                    ),
                    InlineKeyboardButton(
                        text="🔄 Cache",
                        callback_data="admin_refresh",
                    ),
                ],
            ],
        ),
    )

    if len(title) > 16:
        await message.reply_text(
            "The title length is longer than 16 characters.\nTruncating it to 16 characters.",
        )

    try:
        await bot.set_chat_administrator_custom_title(chat.id, user_id, title)
    except:
        pass

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#FULLPROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    if title != "":
        log_message += f"<b>Admin Title:</b> {title}"

    return log_message

@cutiepii_cmd(command="middemote", can_disable=False)
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
async def middemote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = await extract_user(message, args)
    if not user_id:
        await message.reply_text(
            "⚠️ User not found\n\nI don't know who you're talking about, you're going to need to specify a user...",
        )
        return

    try:
        user_member = await chat.get_member(user_id)
    except:
        return

    if user_member.status == "creator":
        await update.effective_message.reply_text("This person CREATED the chat, how would I middemote them?")
        return

    if not user_member.status == "administrator":
        await update.effective_message.reply_text("Can't middemote what wasn't promoted!")
        return

    if user_id == bot.id:
        await update.effective_message.reply_text("I can't demote myself! Get an admin to do it for me.")
        return

    try:
        await bot.promote_chat_member(
            chat.id,
            user_id,
            can_change_info=True,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=True,
            can_restrict_members=False,
            can_pin_messages=True,
            can_promote_members=False,
            #can_manage_video_chats=False
        )

        await bot.send_message(
            chat.id,
            f"<b>╔━「 ⏬ #MidDemote 」</b>\n"
            f"<b>╠ User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}\n"
            f"<b>╠━ User ID:</b> <code>{user_member.user.id}</code>\n"
            f"<b>╠ Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>╠━ Admin ID:</b> <code>{user.id}</code>\n"
            f"<b>╠ Chat Name:</b> {chat.title}\n"
            f"<b>╚━ Chat ID:</b> {chat.id}",
            parse_mode=ParseMode.HTML,
        )

        try:
            ADMIN_CACHE.pop(update.effective_chat.id)
        except KeyError:
            pass

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#MIDDEMOTED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message
    except BadRequest:
        await message.reply_text(
            "⚠️ Could not demote. I might not be admin, or the admin status was appointed by another"
            " user, so I can't act upon them!",
        )
        return

@cutiepii_cmd(command="demote", can_disable=False)
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
async def demote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = await extract_user(message, args)
    if not user_id:
        await message.reply_text(
            "⚠️ User not found\n\nI don't know who you're talking about, you're going to need to specify a user..."
        )
        return

    try:
        user_member = await chat.get_member(user_id)
    except Exception as e:
        await message.reply_text(f"Error: {e}")
        return

    if user_member.status == "creator":
        await message.reply_text("This person is the chat CREATOR, find someone else to play with.")
        return

    if user_member.status != "administrator":
        await message.reply_text("This user isn't an admin!")
        return

    if user_id == bot.id:
        await message.reply_text("I can't demote myself! Get an admin to do it for me.")
        return

    try:
        await bot.promote_chat_member(
            chat.id,
            user_id,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_video_chats=False,
            is_anonymous=False,
        )
        await bot.send_message(
            chat.id,
            "<b>{}</b> was demoted{}.".format(
                    user_member.user.first_name or user_id,
                    f' by <b>{message.from_user.first_name}</b>' if not message.sender_chat else ''
            ),
            parse_mode=ParseMode.HTML,
        )

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#DEMOTED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message

    except BadRequest as e:
        await message.reply_text(
            f"⚠️ Could not demote!\n{str(e)}"
        )
        return


@cutiepii_cmd(command="unsetanon", can_disable=False)
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
async def demoteanon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.type == "private":
        await message.reply_text("This command is meant to be used in groups not PM!")

    user_id = await extract_user(message, args)

    if not user_id:
        user_id = user.id

    try:
        user_member = await chat.get_member(user_id)
    except Exception as e:
        await message.reply_text("Error:\n`{}`".format(e))
        return

    if user_member.status == "creator" and user_id == user.id:
        await message.reply_text("meh")
        return

    if user_member.status == "creator":
        await message.reply_text("This person is the chat CREATOR, find someone else to play with.")
        return

    if user_member.status != "administrator":
        await message.reply_text("This user isn't an admin!")
        return

    if user_member.is_anonymous is False:
        await message.reply_text("This user isn't anonymous!")
        return

    if user_id == bot.id:
        await message.reply_text("I can't demote myself! Get an admin to do it for me.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = await get_bot_member(chat.id)
    # set same perms as user -  to keep the other perms untouched!
    u_member = await chat.get_member(user_id)
    # the perms may be not same as old ones if the bot doesn't have the rights to change them but can't do anything about it

    try:
        await bot.promote_chat_member(
            chat.id,
            user_id,
            is_anonymous=False,

            can_change_info=bool(bot_member.can_change_info and u_member.can_change_info),
            can_post_messages=bool(bot_member.can_post_messages and u_member.can_post_messages),
            can_edit_messages=bool(bot_member.can_edit_messages and u_member.can_edit_messages),
            can_delete_messages=bool(bot_member.can_delete_messages and u_member.can_delete_messages),
            can_invite_users=bool(bot_member.can_invite_users and u_member.can_invite_users),
            can_promote_members=bool(bot_member.can_promote_members and u_member.can_promote_members),
            can_restrict_members=bool(bot_member.can_restrict_members and u_member.can_restrict_members),
            can_pin_messages=bool(bot_member.can_pin_messages and u_member.can_pin_messages),
            can_manage_video_chats=bool(bot_member.can_manage_video_chats and u_member.can_manage_video_chats),
        )

        rmsg = f"<b>{user_member.user.first_name or user_id}</b> is no longer anonymous"
        await bot.send_message(
            chat.id,
            rmsg,
            parse_mode=ParseMode.HTML,
        )  

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#DEMOTED\n"
            f"Non anonymous\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message

    except BadRequest as e:
        await message.reply_text(
            f"⚠️ Could not demote!\n{str(e)}"
        )
        return




@cutiepii_cmd(command=["title", "set_admin_title"], can_disable=False)
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
async def set_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message

    user_id, title = await extract_user_and_text(message, args)
    try:
        user_member = await chat.get_member(user_id)
    except:
        return

    if not user_id:
        await message.reply_text(
            "⚠️ User not found\n\nI don't know who you're talking about, you're going to need to specify a user...",
        )
        return

    if user_member.status == "creator":
        await message.reply_text(
            "This person CREATED the chat, how can i set custom title for him?",
        )
        return

    if user_member.status != "administrator":
        await message.reply_text(
            "Can't set title for non-admins!\nPromote them first to set custom title!",
        )
        return

    if user_id == bot.id:
        await message.reply_text(
            "I can't set my own title myself! Get the one who made me admin to do it for me.",
        )
        return

    if not title:
        await update.effective_message.reply_text("Setting blank title doesn't do anything!")
        return

    if len(title) > 16:
        await message.reply_text(
            "The title length is longer than 16 characters.\nTruncating it to 16 characters.",
        )

    try:
        await bot.set_chat_administrator_custom_title(chat.id, user_id, title)
    except BadRequest:
        await message.reply_text(
            "Either they aren't promoted by me or you set a title text that is impossible to set."
        )
        return

    await bot.send_message(
        chat.id,
        f"Sucessfully set title for <code>{user_member.user.first_name or user_id}</code> "
        f"to <code>{html.escape(title[:16])}</code>!",
        parse_mode=ParseMode.HTML,
    )


@cutiepii_cmd(command="pin", can_disable=False)
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES, allow_mods = True)
@loggable
async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    bot, args = context.bot, context.args
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message

    if chat.type == "private":
        await msg.reply_text("This command is meant to be used in groups not PM!")
        return ""
    msg_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id

    if msg.chat.username:
        # If chat has a username, use this format
        link_chat_id = msg.chat.username
        message_link = f"https://t.me/{link_chat_id}/{msg_id}"
    elif (str(msg.chat.id)).startswith("-100"):
        # If chat does not have a username, use this
        link_chat_id = (str(msg.chat.id)).replace("-100", "")
        message_link = f"https://t.me/c/{link_chat_id}/{msg_id}"

    is_group = chat.type not in ("private", "channel")
    prev_message = update.effective_message.reply_to_message

    if prev_message is None:
        await msg.reply_text("Reply a message to pin it!")
        return

    is_silent = True
    if len(args) >= 1:
        is_silent = (
            args[0].lower() != "notify"
            or args[0].lower() == "loud"
            or args[0].lower() == "violent"
        )

    if prev_message and is_group:
        try:
            await bot.pin_chat_message(
                chat.id, prev_message.message_id, disable_notification=is_silent
            )
            await msg.reply_text(
                "Success! Pinned this message on this group",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="📝 View Message", url=f"{message_link}"
                            ),
                        ]
                    ]
                ),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message != "Chat_not_modified":
                raise

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#PINNED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
        )

        return log_message


@cutiepii_cmd(command="unpin", can_disable=False)
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES, allow_mods = True)
@loggable
async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if chat.type == "private":
        await msg.reply_text("This command is meant to be used in groups not PM!")
        return ""
    msg_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id
    unpinner = await chat.get_member(user.id)

    if (
        not (unpinner.can_pin_messages or unpinner.status == "creator")
        and user.id not in SUDO_USERS
    ):
        await update.effective_message.reply_text("You don't have the necessary rights to do that!")
        return

    if msg.chat.username:
        # If chat has a username, use this format
        link_chat_id = msg.chat.username
        message_link = f"https://t.me/{link_chat_id}/{msg_id}"
    elif (str(msg.chat.id)).startswith("-100"):
        # If chat does not have a username, use this
        link_chat_id = (str(msg.chat.id)).replace("-100", "")
        message_link = f"https://t.me/c/{link_chat_id}/{msg_id}"

    is_group = chat.type not in ("private", "channel")
    prev_message = update.effective_message.reply_to_message

    if prev_message and is_group:
        try:
            await context.bot.unpin_chat_message(chat.id, prev_message.message_id)
            await msg.reply_text(
                f"Unpinned <a href='{message_link}'>this message</a>.",
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as excp:
            if excp.message != "Chat_not_modified":
                raise

    if not prev_message and is_group:
        try:
            await context.bot.unpin_chat_message(chat.id)
            await msg.reply_text("🔽 Unpinned the last message on this group.")
        except BadRequest as excp:
            if excp.message == "Message to unpin not found":
                await msg.reply_text(
                    "I can't see pinned message, Maybe already unpined, or pin Message to old 🙂"
                )
            else:
                raise

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#MESSAGE-UNPINNED-SUCCESSFULLY\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
    )

    return log_message

@cutiepii_cmd(command="pinned", can_disable=False)
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
async def pinned(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    msg = update.effective_message
    chat = update.effective_chat

    if chat.type == "private":
        await msg.reply_text("This command is meant to be used in groups not PM!")
        return
    msg_id = (
        update.effective_message.reply_to_message.message_id
        if update.effective_message.reply_to_message
        else update.effective_message.message_id
    )

    chat = await bot.get_chat(chat_id=msg.chat.id)
    if chat.pinned_message:
        pinned_id = chat.pinned_message.message_id
        message_link = f"https://t.me/c/{str(chat.id)[4:]}/{pinned_id}"

        await msg.reply_text(
            f"Here is the pinned massage of {html.escape(chat.title)}.",
            reply_to_message_id=msg_id,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="📌 Pinned Message",
                            url=message_link,
                        )
                    ]
                ]
            ),
        )

    else:
        await msg.reply_text(
            f"There is no pinned message in <b>{html.escape(chat.title)}!</b>",
            parse_mode=ParseMode.HTML,
        )

@cutiepii_cmd(command=["invitelink", "link"], can_disable=False)
@bot_admin_check(AdminPerms.CAN_INVITE_USERS)
@user_admin_check(AdminPerms.CAN_INVITE_USERS, allow_mods = True)
@loggable
async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.username:
        await update.effective_message.reply_text(f"https://t.me/{chat.username}")
    elif chat.type in [chat.SUPERGROUP, chat.CHANNEL]:
        bot_member = await get_bot_member(chat.id)
        if bot_member.can_invite_users:
            invitelink = await bot.export_chat_invite_link(chat.id)
            await update.effective_message.reply_text(invitelink)

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#ADMIN\nInvite link exported\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"<b>Invite Link:</b> '<code>{invitelink}</code>'"

            )
            return log_message

        else:
            await update.effective_message.reply_text(
                "I don't have access to the invite link, try changing my permissions!"
            )
    else:
        await update.effective_message.reply_text(
            "I can only give you invite links for supergroups and channels, sorry!"
        )

# Pyrogram staff command removed

@cutiepii_cmd(command=["admin", "admins" , "staff", "adminlist"], can_disable=False)
async def adminlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat  
    user = update.effective_user  
    bot = context.bot

    if update.effective_message.chat.type == "private":
        await send_message(update.effective_message, "This command only works in Groups.")
        return

    chat_id = update.effective_chat.id

    try:
        msg = await update.effective_message.reply_text(
            "Fetching group admins...",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest:
        msg = await update.effective_message.reply_text(
            "Fetching group admins...",
            do_quote=False,
            parse_mode=ParseMode.HTML,
        )

    administrators = await bot.get_chat_administrators(chat_id)
    text = "Admins in <b>{}</b>:".format(html.escape(update.effective_chat.title))

    bot_admin_list = []
    for admin in administrators:
        user = admin.user
        if user.is_bot:
            if not user.first_name:
                name = "☠ Deleted Account"
            else:
                name = "{}".format(
                    mention_html(
                        user.id,
                        html.escape(user.first_name + " " + (user.last_name or "")),
                    ),
                )
            bot_admin_list.append(name)

    for admin in administrators:
        user = admin.user
        try:
            from Cutiepii_Robot.modules.sql import users_sql as sql
            sql.update_user(user.id, user.username, chat.id, chat.title)
        except Exception as e:
            LOGGER.error(f"Error saving admin {user.id} to database: {e}")
        status = admin.status
        custom_title = admin.custom_title

        if not user.first_name:
            name = "☠ Deleted Account"
        else:
            name = "{}".format(
                mention_html(
                    user.id,
                    html.escape(user.first_name + " " + (user.last_name or "")),
                ),
            )

        if user.is_bot:
            continue

        if status == ChatMemberStatus.OWNER:
            text += "\n 🌏 Creator:"
            text += "\n<code> - </code>{}\n".format(name)

            if custom_title:
                text += f"<code> ┗━ {html.escape(custom_title)}</code>\n"

    text += "\n🌟 Admins:"

    custom_admin_list = {}
    normal_admin_list = []

    for admin in administrators:
        user = admin.user
        status = admin.status
        custom_title = admin.custom_title

        if user.is_bot:
            continue

        if not user.first_name:
            name = "☠ Deleted Account"
        else:
            name = "{}".format(
                mention_html(
                    user.id,
                    html.escape(user.first_name + " " + (user.last_name or "")),
                ),
            )
        if status == ChatMemberStatus.ADMINISTRATOR:
            if custom_title:
                try:
                    custom_admin_list[custom_title].append(name)
                except KeyError:
                    custom_admin_list.update({custom_title: [name]})
            else:
                normal_admin_list.append(name)

    for admin in normal_admin_list:
        text += "\n<code> - </code>{}".format(admin)

    for admin_group in custom_admin_list.copy():
        if len(custom_admin_list[admin_group]) == 1:
            text += "\n<code> - </code>{} | <code>{}</code>".format(
                custom_admin_list[admin_group][0],
                html.escape(admin_group),
            )
            custom_admin_list.pop(admin_group)

    text += "\n"
    for admin_group, value in custom_admin_list.items():
        text += "\n🚨 <code>{}</code>".format(admin_group)
        for admin in value:
            text += "\n<code> - </code>{}".format(admin)
        text += "\n"

    if bot_admin_list:
        text += "\n🤖 Bots:"
        for bot_admin in bot_admin_list:
            text += "\n<code> - </code>{}".format(bot_admin)
        text += "\n"

    try:
        await msg.edit_text(text, parse_mode=ParseMode.HTML)
    except BadRequest:  # if original message is deleted
        return

@cutiepii_cmd(command="permapin")
@connection_status
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@loggable
async def permapin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
    msg = update.effective_message  # type: Optional[Message]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    bot = context.bot  # type: Optional[Bot]
    preview = True
    protect = False

    m = msg.text.split(' ', 1)
    if len(m) == 1 and not msg.reply_to_message:
        await msg.reply_text("Provide something to pin.")
        return
    _, text, data_type, content, buttons = get_data(msg, True)
    if not text:
        await msg.reply_text("Should I pin... nothing?")
        return
    await msg.delete()
    keyboard = InlineKeyboardMarkup(build_keyboard_from_list(buttons))

    if escape_invalid_curly_brackets(text, VALID_FORMATTERS):
        if "{admin}" in text and await user_is_admin(chat, user.id):
            return
        if "{user}" in text and not await user_is_admin(chat, user.id):
            return
        if "{preview}" in text:
            preview = False
        if "{protect}" in text:
            protect = True
        text = text.format(
                first = html.escape(msg.from_user.first_name),
                last = html.escape(
                        msg.from_user.last_name
                        or msg.from_user.first_name,
                ),
                fullname = html.escape(
                        " ".join(
                                [
                                    msg.from_user.first_name,
                                    msg.from_user.last_name or "",
                                ]
                        ),
                ),
                username = f'@{msg.from_user.username}'
                if msg.from_user.username
                else mention_html(
                        msg.from_user.id,
                        msg.from_user.first_name,
                ),
                mention = mention_html(
                        msg.from_user.id,
                        msg.from_user.first_name,
                ),
                chatname = html.escape(
                        msg.chat.title
                        if msg.chat.type != "private"
                        else msg.from_user.first_name,
                ),
                id = msg.from_user.id,
                user = "",
                admin = "",
                preview = "",
                protect = "",
        )

    else:
        text = ""

    try:
        if data_type in (Types.BUTTON_TEXT, Types.TEXT):
            pin_this = await bot.send_message(
                chat.id,
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=bool(preview),
                protect_content=bool(protect)
            )
        elif ENUM_FUNC_MAP[data_type] == dispatcher.bot.send_sticker:
            pin_this = await ENUM_FUNC_MAP[data_type](
                chat.id,
                content,
                reply_markup=keyboard,
            )
        else:
            pin_this = await ENUM_FUNC_MAP[data_type](
                chat.id,
                content,
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                protect_content=bool(protect)
            )

        await bot.pin_chat_message(chat.id, pin_this.message_id, disable_notification=False)

        sql1.enable_linked(chat.id)  # enable cleanlinked for this chat
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"PINNED\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
            f"\n<b>Message:</b> <a href='t.me/c/{str(chat.id)[4:]}''>Pinned Message</a>\n"
        )
        return log_message

    except BadRequest as excp:
        if excp.message == "Entity_mention_user_invalid":
            await msg.reply_text(
                "Looks like you tried to mention someone I've never seen before. If you really "
                "want to mention them, forward one of their messages to me, and I'll be able "
                "to tag them!"
            )
        else:
            await msg.reply_text(
                "Could not pin the message. Error: <code>{}</code>".format(
                    excp.message
                )
            )
        return


@connection_status
@bot_admin_check(AdminPerms.CAN_DELETE_MESSAGES)
@user_admin_check()
async def permanent_pin_set(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    u = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    args = context.args
    msg = update.effective_message  # type: Optional[Message]
    user = update.effective_user

    conn = await connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = await dispatcher.bot.get_chat(conn)
        chat_id = conn
        chat_name = chat.title
        if not args:
            get_permapin = sql.get_permapin(chat_id)
            text_maker = "Cleanlinked is currently set to: `{}`".format(bool(int(get_permapin)))
            if get_permapin:
                if chat.username:
                    old_pin = "https://t.me/{}/{}".format(chat.username, get_permapin)
                else:
                    old_pin = "https://t.me/c/{}/{}".format(str(chat.id)[4:], get_permapin)
                text_maker += "\nTo disable cleanlinked send: `/cleanlinked off`"
                text_maker += "\n\n[The permanent pinned message is here]({})".format(old_pin)
            await dispatcher.bot.send_message(chat_id, text_maker, parse_mode=ParseMode.MARKDOWN)
            return ""
        prev_message = args[0]
        if prev_message == "off":
            sql.set_permapin(chat_id, 0)
            await dispatcher.bot.send_message(chat_id, "Cleanlinked has been disabled!")
            return
        if "/" in prev_message:
            prev_message = prev_message.split("/")[-1]
    else:
        if update.effective_message.chat.type == "private":
            await dispatcher.bot.send_message(chat_id, "This command is meant to use in group not in PM")
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title
        if update.effective_update.effective_message.reply_to_message:
            prev_message = update.effective_message.reply_to_message.message_id
        elif len(args) >= 1 and args[0] in ["off", "false"]:
            sql.set_permapin(chat.id, 0)
            await dispatcher.bot.send_message(chat_id, "Cleanlinked has been disabled!")
            return
        elif len(args) >= 1 and args[0] in ["on", "true"]:
            sql.set_permapin(chat.id, 1)
            await dispatcher.bot.send_message(chat_id, "Cleanlinked has been enabled!")
            return
        else:
            get_permapin = sql.get_permapin(chat_id)
            text_maker = "Cleanlinked is currently set to: `{}`".format(bool(int(get_permapin)))
            if get_permapin:
                if chat.username:
                    old_pin = "https://t.me/{}/{}".format(chat.username, get_permapin)
                else:
                    old_pin = "https://t.me/c/{}/{}".format(str(chat.id)[4:], get_permapin)
                text_maker += "\nTo disable cleanlinked send: `/cleanlinked off`"
                text_maker += "\n\n[The permanent pinned message is here]({})".format(old_pin)
            await dispatcher.bot.send_message(chat_id, text_maker, parse_mode=ParseMode.MARKDOWN)
            return ""

    is_group = chat.type not in ("private", "channel")

    if prev_message and is_group:
        sql.set_permapin(chat.id, prev_message)
        await dispatcher.bot.send_message(chat_id, "Cleanlinked successfully set!")
        return "<b>{}:</b>" \
               "\n#PERMANENT_PIN" \
               "\n<b>Admin:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name))

    return ""

@cutiepii_cmd(command="unpinall", filters=filters.ChatType.GROUPS)
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES, allow_mods = True)
async def rmall_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    member = await chat.get_member(user.id)
    if member.status != ChatMemberStatus.OWNER and user.id not in SUDO_USERS:
        await update.effective_message.reply_text(
            "Only the chat owner can unpin all messages at once."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Unpin all messages", callback_data="pinned_rmall"
                    )
                ],
                [InlineKeyboardButton(text="Cancel", callback_data="pinned_cancel")],
            ]
        )
        await update.effective_message.reply_text(
            f"Are you sure you would like unpin all pinned messages in {chat.title}? This action cannot be undone.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )

@cutiepii_callback(pattern=r"pinned_.*")
@loggable
async def unpin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    chat = update.effective_chat
    msg = update.effective_message
    bot = context.bot
    member = await chat.get_member(query.from_user.id)
    user = query.from_user
    if query.data == "pinned_rmall":
        if member.status == ChatMemberStatus.OWNER or query.from_user.id in SUDO_USERS:

            try:
                await bot.unpin_all_chat_messages(chat.id)
            except BadRequest as excp:
                if excp.message == "Chat_not_modified":
                    pass
                else:
                    raise
            await msg.edit_text(f"Unpinned all messages in {chat.title}")

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNPINNED_ALL\n"
                f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
            )
            return log_message

        else:
            await query.answer("Only owner of the chat can do this.")
            return ""

    elif query.data == "pinned_cancel":
        if member.status == ChatMemberStatus.OWNER or query.from_user.id in SUDO_USERS:
            await msg.edit_text("Unpinning all pinned messages has been cancelled.")
            return ""
        else:
            await query.answer("Only owner of the chat can do this.")
            return ""

@cutiepii_cmd(command=["admincache", "cacheclear", "clearcache", "refresh", "reload"], can_disable=False)
async def admincache(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    try:
        last = _admincache[chat.id]
    except KeyError:
        last = None
    now = time.time()
    if last and last + 600 > now:
        return await msg.reply_text("this command can only be used once every 10 minutes")

    if chat.type in ["channel", "private"]:
        return await msg.reply_text("this command can only be used in groups")

    member = await chat.get_member(user.id)
    if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER] and user.id != 1087968824:
        return await msg.reply_text("this command can only be used by admins")

    ADMINS_CACHE[update.effective_chat.id] = await update.effective_chat.get_administrators()
    BOT_ADMIN_CACHE[update.effective_chat.id] = await update.effective_chat.get_member(BOT_ID)
    await msg.reply_text("I've refreshed my admin cache.")
    _admincache[chat.id] = time.time()


@cutiepii_cmd(command=['userlist', 'users'])
@bot_admin_check()
async def userlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message

    if chat.type == "private":
        await message.reply_text("This command can only be used in groups.")
        return

    # Check if the user is an admin
    if not await user_is_admin(update, update.effective_user.id):
        await message.reply_text("Only administrators can get the userlist.")
        return

    # Send a processing message
    progress_msg = await message.reply_text("Fetching user list, please wait...")

    try:
        members = []
        async for user in telethn.iter_participants(chat.id):
            if not user.deleted:
                first_name = user.first_name or "Unknown"
                members.append(f"{first_name} : {user.id}")

        total_members = len(members)

        file_name = f"{chat.title}_userlist.txt"
        with open(file_name, "w", encoding="utf-8") as file:
            file.write("\n".join(members))

        # Send document
        caption = f"Total Members: {total_members}\nHere is the list of users in this chat."
        with open(file_name, "rb") as document_file:
            await context.bot.send_document(
                chat_id=chat.id,
                document=document_file,
                caption=caption,
                filename=file_name,
                parse_mode=ParseMode.MARKDOWN
            )

        # Delete temp file and progress message
        os.remove(file_name)
        await progress_msg.delete()

    except Exception as e:
        LOGGER.exception(e)
        await progress_msg.edit_text("An error occurred while fetching the user list.")

# ========================================
# Command: /view_admins
# ========================================

@cutiepii_cmd(command="view_admins", filters=filters.ChatType.GROUPS, can_disable=False)
@connection_status
async def view_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    
    admins = await chat.get_administrators()
    
    reply = f"👮 <b>Administrators of {html.escape(chat.title)}:</b>\n\n"
    for admin in admins:
        user = admin.user
        status_tag = "👑 Creator" if admin.status == ChatMemberStatus.OWNER else "👮 Admin"
        reply += f"❍ {mention_html(user.id, user.first_name)} (<code>{user.id}</code>) - <b>{status_tag}</b>\n"
        if admin.status != ChatMemberStatus.OWNER:
            perms = []
            if admin.can_change_info: perms.append("Change Info")
            if admin.can_post_messages: perms.append("Post Messages")
            if admin.can_edit_messages: perms.append("Edit Messages")
            if admin.can_delete_messages: perms.append("Delete Messages")
            if admin.can_invite_users: perms.append("Invite Users")
            if admin.can_restrict_members: perms.append("Restrict Members")
            if admin.can_pin_messages: perms.append("Pin Messages")
            if admin.can_promote_members: perms.append("Promote Members")
            if admin.can_manage_video_chats: perms.append("Manage Video Chats")
            
            if perms:
                reply += f"  <i>Permissions:</i> {', '.join(perms)}\n"
            else:
                reply += f"  <i>Permissions:</i> None\n"
        else:
            reply += "  <i>Permissions:</i> Full Access\n"
        reply += "\n"
        
    await message.reply_text(reply, parse_mode=ParseMode.HTML)


# ========================================
# Command: /manage_admins /admin_perms
# ========================================

@cutiepii_cmd(command=["manage_admins", "admin_perms"], filters=filters.ChatType.GROUPS, can_disable=False)
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
async def manage_admins_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    
    admins = await chat.get_administrators()
    
    keyboard = []
    for admin in admins:
        user = admin.user
        if user.is_bot or admin.status == ChatMemberStatus.OWNER:
            continue
        keyboard.append([
            InlineKeyboardButton(text=f"👤 {user.first_name}", callback_data=f"m_adm_list:{user.id}")
        ])
        
    if not keyboard:
        await message.reply_text("There are no other administrators in this chat to manage.")
        return
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(
        "🛠️ <b>Interactive Admin Management:</b>\n\nSelect an administrator to view and manage their permissions:",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )


# Callback query handler for manage admins
@cutiepii_callback(pattern=r"^m_adm_")
async def manage_admins_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat = update.effective_chat
    user = update.effective_user
    
    user_member = await chat.get_member(user.id)
    if user_member.status != ChatMemberStatus.OWNER and not user_member.can_promote_members:
        await query.answer("You do not have permission to manage admin rights!", show_alert=True)
        return
        
    data = query.data.split(":")
    action = data[0]
    
    if action == "m_adm_list":
        target_user_id = int(data[1])
        try:
            target_member = await chat.get_member(target_user_id)
        except Exception:
            await query.answer("Could not fetch user details.", show_alert=True)
            return
            
        t_user = target_member.user
        
        def btn_txt(val, label):
            return f"✅ {label}" if val else f"❌ {label}"
            
        keyboard = [
            [
                InlineKeyboardButton(text=btn_txt(target_member.can_change_info, "Info"), callback_data=f"m_adm_toggle:{target_user_id}:info"),
                InlineKeyboardButton(text=btn_txt(target_member.can_delete_messages, "Delete"), callback_data=f"m_adm_toggle:{target_user_id}:delete")
            ],
            [
                InlineKeyboardButton(text=btn_txt(target_member.can_restrict_members, "Ban"), callback_data=f"m_adm_toggle:{target_user_id}:ban"),
                InlineKeyboardButton(text=btn_txt(target_member.can_pin_messages, "Pin"), callback_data=f"m_adm_toggle:{target_user_id}:pin")
            ],
            [
                InlineKeyboardButton(text=btn_txt(target_member.can_invite_users, "Invite"), callback_data=f"m_adm_toggle:{target_user_id}:invite"),
                InlineKeyboardButton(text=btn_txt(target_member.can_promote_members, "Promote"), callback_data=f"m_adm_toggle:{target_user_id}:promote")
            ],
            [
                InlineKeyboardButton(text="🗑️ Demote Admin", callback_data=f"m_adm_demote:{target_user_id}")
            ],
            [
                InlineKeyboardButton(text="🔙 Back to Admins", callback_data="m_adm_back")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🛠️ <b>Manage Permissions for {mention_html(t_user.id, t_user.first_name)}:</b>\n\n"
            f"Click on a permission button to toggle the right on/off.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
    elif action == "m_adm_toggle":
        target_user_id = int(data[1])
        perm_to_toggle = data[2]
        
        try:
            target_member = await chat.get_member(target_user_id)
        except Exception:
            await query.answer("Could not fetch user details.", show_alert=True)
            return
            
        can_change_info = target_member.can_change_info
        can_post_messages = target_member.can_post_messages
        can_edit_messages = target_member.can_edit_messages
        can_delete_messages = target_member.can_delete_messages
        can_invite_users = target_member.can_invite_users
        can_restrict_members = target_member.can_restrict_members
        can_pin_messages = target_member.can_pin_messages
        can_promote_members = target_member.can_promote_members
        can_manage_video_chats = target_member.can_manage_video_chats
        
        if perm_to_toggle == "info":
            can_change_info = not can_change_info
        elif perm_to_toggle == "delete":
            can_delete_messages = not can_delete_messages
        elif perm_to_toggle == "ban":
            can_restrict_members = not can_restrict_members
        elif perm_to_toggle == "pin":
            can_pin_messages = not can_pin_messages
        elif perm_to_toggle == "invite":
            can_invite_users = not can_invite_users
        elif perm_to_toggle == "promote":
            can_promote_members = not can_promote_members
            
        try:
            await context.bot.promote_chat_member(
                chat.id,
                target_user_id,
                can_change_info=can_change_info,
                can_post_messages=can_post_messages,
                can_edit_messages=can_edit_messages,
                can_delete_messages=can_delete_messages,
                can_invite_users=can_invite_users,
                can_restrict_members=can_restrict_members,
                can_pin_messages=can_pin_messages,
                can_promote_members=can_promote_members,
                can_manage_video_chats=can_manage_video_chats
            )
            await query.answer("Permission updated successfully!")
        except Exception as e:
            await query.answer(f"Failed to update permission: {e}", show_alert=True)
            return
            
        try:
            target_member = await chat.get_member(target_user_id)
        except Exception:
            return
            
        t_user = target_member.user
        
        def btn_txt(val, label):
            return f"✅ {label}" if val else f"❌ {label}"
            
        keyboard = [
            [
                InlineKeyboardButton(text=btn_txt(target_member.can_change_info, "Info"), callback_data=f"m_adm_toggle:{target_user_id}:info"),
                InlineKeyboardButton(text=btn_txt(target_member.can_delete_messages, "Delete"), callback_data=f"m_adm_toggle:{target_user_id}:delete")
            ],
            [
                InlineKeyboardButton(text=btn_txt(target_member.can_restrict_members, "Ban"), callback_data=f"m_adm_toggle:{target_user_id}:ban"),
                InlineKeyboardButton(text=btn_txt(target_member.can_pin_messages, "Pin"), callback_data=f"m_adm_toggle:{target_user_id}:pin")
            ],
            [
                InlineKeyboardButton(text=btn_txt(target_member.can_invite_users, "Invite"), callback_data=f"m_adm_toggle:{target_user_id}:invite"),
                InlineKeyboardButton(text=btn_txt(target_member.can_promote_members, "Promote"), callback_data=f"m_adm_toggle:{target_user_id}:promote")
            ],
            [
                InlineKeyboardButton(text="🗑️ Demote Admin", callback_data=f"m_adm_demote:{target_user_id}")
            ],
            [
                InlineKeyboardButton(text="🔙 Back to Admins", callback_data="m_adm_back")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🛠️ <b>Manage Permissions for {mention_html(t_user.id, t_user.first_name)}:</b>\n\n"
            f"Click on a permission button to toggle the right on/off.",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
    elif action == "m_adm_demote":
        target_user_id = int(data[1])
        try:
            await context.bot.promote_chat_member(
                chat.id,
                target_user_id,
                can_change_info=False,
                can_post_messages=False,
                can_edit_messages=False,
                can_delete_messages=False,
                can_invite_users=False,
                can_restrict_members=False,
                can_pin_messages=False,
                can_promote_members=False,
                can_manage_video_chats=False
            )
            await query.answer("Administrator successfully demoted!")
        except Exception as e:
            await query.answer(f"Failed to demote admin: {e}", show_alert=True)
            return
            
        admins = await chat.get_administrators()
        keyboard = []
        for admin in admins:
            user = admin.user
            if user.is_bot or admin.status == ChatMemberStatus.OWNER:
                continue
            keyboard.append([
                InlineKeyboardButton(text=f"👤 {user.first_name}", callback_data=f"m_adm_list:{user.id}")
            ])
            
        if not keyboard:
            await query.edit_message_text("There are no other administrators in this chat to manage.")
            return
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🛠️ <b>Interactive Admin Management:</b>\n\nSelect an administrator to view and manage their permissions:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
        
    elif action == "m_adm_back":
        admins = await chat.get_administrators()
        keyboard = []
        for admin in admins:
            user = admin.user
            if user.is_bot or admin.status == ChatMemberStatus.OWNER:
                continue
            keyboard.append([
                InlineKeyboardButton(text=f"👤 {user.first_name}", callback_data=f"m_adm_list:{user.id}")
            ])
            
        if not keyboard:
            await query.edit_message_text("There are no other administrators in this chat to manage.")
            return
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🛠️ <b>Interactive Admin Management:</b>\n\nSelect an administrator to view and manage their permissions:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )


@cutiepii_cmd(command="slowmode")
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
async def slow_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("Usage: `/slowmode [seconds|off]`")
        return

    val = args[0].lower()
    if val in ["off", "disable", "no", "0"]:
        delay = 0
    else:
        try:
            delay = int(val)
        except ValueError:
            await message.reply_text("Please specify a valid number of seconds or 'off'.")
            return

    try:
        await chat.set_slow_mode_delay(delay)
        if delay == 0:
            await message.reply_text("✅ Slow mode has been disabled in this chat.")
        else:
            await message.reply_text(f"✅ Slow mode has been enabled with a delay of <code>{delay}</code> seconds.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"Error setting slow mode: {e}")


@cutiepii_cmd(command="mute_all")
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
async def mute_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    sender = update.effective_user

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Confirm Mute 🔇", callback_data=f"muteall_confirm:{sender.id}"),
                InlineKeyboardButton("Cancel ❌", callback_data=f"muteall_cancel:{sender.id}")
            ]
        ]
    )
    await message.reply_text(
        f"⚠️ <b>Mute All Request</b>\n\n"
        f"Are you sure you want to mute all members in this group?",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


@cutiepii_cmd(command="unmute_all")
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
async def unmute_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    sender = update.effective_user

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Confirm Unmute 🔊", callback_data=f"unmuteall_confirm:{sender.id}"),
                InlineKeyboardButton("Cancel ❌", callback_data=f"unmuteall_cancel:{sender.id}")
            ]
        ]
    )
    await message.reply_text(
        f"⚠️ <b>Unmute All Request</b>\n\n"
        f"Are you sure you want to unmute all members in this group?",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


@cutiepii_callback(pattern=r"^(muteall|unmuteall)_(confirm|cancel):")
async def mute_unmute_all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat = update.effective_chat
    user = query.from_user
    
    data = query.data.split(":")
    action = data[0]
    expected_sender_id = int(data[1])
    
    if user.id != expected_sender_id:
        await query.answer("🔐 Only the admin who ran the command can use these buttons!", show_alert=True)
        return
        
    from telegram import ChatPermissions
    
    if action == "muteall_confirm":
        # First verify bot still has restrict admin perms
        bot_member = await chat.get_member(context.bot.id)
        if not bot_member.can_restrict_members:
            await query.answer("I need 'Restrict Members' permission to mute the group!", show_alert=True)
            return

        permissions = ChatPermissions(
            send_messages=False,
            send_audios=False,
            send_documents=False,
            send_photos=False,
            send_videos=False,
            send_video_notes=False,
            send_voice_notes=False,
            send_polls=False,
            send_other_messages=False,
            add_web_page_previews=False,
            change_info=False,
            invite_users=False,
            pin_messages=False,
        )
        try:
            await chat.set_permissions(permissions)
            await query.message.edit_text("🔇 Chat permissions updated: <b>The entire group has been muted!</b>", parse_mode=ParseMode.HTML)
        except Exception as e:
            await query.message.edit_text(f"Error: {e}")
            
    elif action == "unmuteall_confirm":
        # First verify bot still has restrict admin perms
        bot_member = await chat.get_member(context.bot.id)
        if not bot_member.can_restrict_members:
            await query.answer("I need 'Restrict Members' permission to unmute the group!", show_alert=True)
            return

        permissions = ChatPermissions(
            send_messages=True,
            send_audios=True,
            send_documents=True,
            send_photos=True,
            send_videos=True,
            send_video_notes=True,
            send_voice_notes=True,
            send_polls=True,
            send_other_messages=True,
            add_web_page_previews=True,
            invite_users=True,
        )
        try:
            await chat.set_permissions(permissions)
            await query.message.edit_text("🔊 Chat permissions updated: <b>The entire group has been unmuted!</b>", parse_mode=ParseMode.HTML)
        except Exception as e:
            await query.message.edit_text(f"Error: {e}")
            
    elif action in ["muteall_cancel", "unmuteall_cancel"]:
        try:
            await query.message.edit_text("❌ Action cancelled.")
        except Exception:
            pass


_admincache = dict()

__help__ = True

__mod_name__ = "Admins"