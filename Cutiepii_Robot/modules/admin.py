"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, [ https://github.com/Awesome-RJ ]
Copyright (c) 2021-2022, Yūki • Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot

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

import os
import html
import contextlib
import requests
import Cutiepii_Robot.modules.sql.pin_sql as sql

from html import escape
from io import BytesIO
from typing import Optional

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.constants import ParseMode, ChatType
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler, filters as PTB_Cutiepii_Filters
from telegram.helpers import mention_html
from telethon import events
from telethon.tl import functions, types
from telethon.errors import *
from telethon.tl import *
from telethon import *
from pyrogram import Client, filters
from pyrogram.types import Message

from Cutiepii_Robot import SUDO_USERS, TOKEN, CUTIEPII_PTB, LOGGER, pgram, telethn
from Cutiepii_Robot.modules.helper_funcs.msg_types import get_message_type
from Cutiepii_Robot.modules.helper_funcs.anonymous import user_admin
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.connection import connected
from Cutiepii_Robot.modules.users import build_keyboard_alternate
from Cutiepii_Robot.modules.helper_funcs.admin_status import user_admin_check, bot_admin_check, AdminPerms
from Cutiepii_Robot.modules.helper_funcs.chat_status import (
    ADMIN_CACHE,
    connection_status,
    is_user_admin,
    bot_admin,
    can_promote,
)

from Cutiepii_Robot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.events import register as CUTIEPII

ENUM_FUNC_MAP = {
    'Types.TEXT': CUTIEPII_PTB.bot.send_message,
    'Types.BUTTON_TEXT': CUTIEPII_PTB.bot.send_message,
    'Types.STICKER': CUTIEPII_PTB.bot.send_sticker,
    'Types.DOCUMENT': CUTIEPII_PTB.bot.send_document,
    'Types.PHOTO': CUTIEPII_PTB.bot.send_photo,
    'Types.AUDIO': CUTIEPII_PTB.bot.send_audio,
    'Types.VOICE': CUTIEPII_PTB.bot.send_voice,
    'Types.VIDEO': CUTIEPII_PTB.bot.send_video,
}


async def can_promote_users(message):
    result = await telethn(
        functions.channels.GetParticipantRequest(
            channel=message.chat_id,
            user_id=message.sender_id,
        ))
    p = result.participant
    return isinstance(p, types.ChannelParticipantCreator) or (isinstance(
        p, types.ChannelParticipantAdmin) and p.admin_rights.ban_users)


async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):
        return isinstance(
            (await
             telethn(functions.channels.GetParticipantRequest(chat, user)
                     )).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerUser):
        return True


async def can_promote_users(message):
    result = await telethn(
        functions.channels.GetParticipantRequest(
            channel=message.chat_id,
            user_id=message.sender_id,
        ))
    p = result.participant
    return isinstance(p, types.ChannelParticipantCreator) or (isinstance(
        p, types.ChannelParticipantAdmin) and p.admin_rights.ban_users)


async def can_ban_users(message):
    result = await telethn(
        functions.channels.GetParticipantRequest(
            channel=message.chat_id,
            user_id=message.sender_id,
        ))
    p = result.participant
    return isinstance(p, types.ChannelParticipantCreator) or (isinstance(
        p, types.ChannelParticipantAdmin) and p.admin_rights.ban_users)


@CUTIEPII(pattern=("/reload"))
async def reload(event):
    text = "✅ **bot restarted successfully**\n\n• Admin list has been **updated**"
    await telethn.send_message(event.chat_id, text)


@telethn.on(events.NewMessage(pattern="/users$"))
async def get_users(show):
    if not show.is_group:
        return
    if not await is_register_admin(show.input_chat, show.sender_id):
        return
    info = await telethn.get_entity(show.chat_id)
    title = info.title or "this chat"
    mentions = f"Users in {title}: \n"
    async for user in telethn.iter_participants(show.chat_id):
        mentions += (
            f"\nDeleted Account {user.id}" if user.deleted else
            f"\n[{user.first_name}](tg://user?id={user.id}) {user.id}")

    with open("userslist.txt", "w+") as file:
        file.write(mentions)
    await telethn.send_file(
        show.chat_id,
        "userslist.txt",
        caption=f"Users in {title}",
        reply_to=show.id,
    )
    os.remove("userslist.txt")


@loggable
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def set_sticker(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if not msg.reply_to_message:
        if not msg.reply_to_message.sticker:
            await msg.reply_text(
                "Reply to a sticker to set its pack as the group pack!")
            return ""
        await msg.reply_text(
            "Reply to a sticker to set its pack as the group pack!")
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
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}")
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


@loggable
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def setchatpic(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if (not msg.reply_to_message and not msg.reply_to_message.document
            and not msg.reply_to_message.photo):
        await msg.reply_text(
            "Please send a photo or a document to set it as the group photo!")
        return ""

    if msg.reply_to_message.photo:
        file_id = msg.reply_to_message.photo[-1].file_id
    elif msg.reply_to_message.document:
        file_id = msg.reply_to_message.document.file_id

    try:
        image_file = await context.bot.get_file(file_id
                                                )  # kanged from stickers
        image_data = image_file.download(out=BytesIO())
        image_data.seek(0)

        await bot.set_chat_photo(chat.id, image_data)
        await msg.reply_text(
            f"<b>{user.first_name}</b> changed the group photo."
            if not msg.sender_chat else "Group photo has been changed.",
            parse_mode=ParseMode.HTML)
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ADMIN\nChat photo changed\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}")
        return log_message

    except BadRequest as e:
        await msg.reply_text("An Error occurred:\n" + str(e))
        return ''


@loggable
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def rmchatpic(update: Update, context: CallbackContext) -> str:
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
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}")
        return log_message

    except BadRequest as e:
        await msg.reply_text("An Error occurred:\n" + str(e))
        return ''


@loggable
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def set_desc(update: Update, context: CallbackContext) -> str:
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
        if len(
                title
        ) > 255:  # telegram limits the title/description to 255 characters
            await msg.reply_text(
                "Description longer than 255 characters, Truncating it to 255 characters!"
            )
        await msg.reply_text(
            f"<b>{user.first_name}</b> changed the group description.to:\n<b>{title[:255]}</b>"
            if not msg.sender_chat else
            f"Group description has been changed.to:\n<b>{title[:255]}</b>",
            parse_mode=ParseMode.HTML)

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ADMIN\nChat description changed\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}")
        return log_message

    except BadRequest as e:
        await msg.reply_text("An Error occurred:\n" + str(e))
        return ''


@loggable
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def setchat_title(update: Update, context: CallbackContext) -> str:
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
        if len(
                title
        ) > 255:  # telegram limits the title/description to 255 characters
            await msg.reply_text(
                "Title longer than 255 characters, Truncating it to 255 characters!"
            )
        await msg.reply_text(
            f"<b>{user.first_name}</b> changed the group title.to:\n<b>{title[:255]}</b>"
            if not msg.sender_chat else
            f"Group title has been changed.to:\n<b>{title[:255]}</b>",
            parse_mode=ParseMode.HTML)

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ADMIN\nChat title changed\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}")
        return log_message

    except BadRequest as e:
        await msg.reply_text("An Error occurred:\n" + str(e))
        return ''


@loggable
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
async def promote_button(update: Update,
                         context: CallbackContext) -> Optional[str]:
    query = update.callback_query
    user = update.effective_user
    chat = update.effective_chat
    bot = context.bot

    mode = query.data.split("_")[1]
    try:
        if await is_user_admin(update, user.id):
            if mode == "demote":
                user_id = query.data.split("_")[2]
                user_member = await chat.get_member(user_id)
                await CUTIEPII_PTB.bot.promote_chat_member(
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
                with contextlib.suppress(KeyError):
                    ADMIN_CACHE.pop(update.effective_chat.id)
                await bot.answer_callback_query(query.id,
                                                "Admins cache refreshed!")
    except BadRequest as excp:
        if excp.message not in [
                "Message is not modified",
                "Query_id_invalid",
                "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in promote buttons. %s",
                             str(query.data))


@loggable
@user_admin
async def refresh_admin(update: Update, context: CallbackContext) -> None:
    with contextlib.suppress(KeyError):
        ADMIN_CACHE.pop(update.effective_chat.id)
    await update.effective_message.reply_text("Admins cache refreshed!")


@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
async def promoteanon(update: Update,
                      context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        await message.reply_text(
            "This command is meant to be used in groups not PM!")

    user_id, title = await extract_user_and_text(message, args)

    if not user_id:
        user_id = user.id
        title = " ".join(args)

    try:
        user_member = await chat.get_member(user_id)
    except Exception as e:
        await message.reply_text("Error:\n`{}`".format(e))
        return

    if user_member.status == "creator":
        await message.reply_text(
            "This user is the chat creator, he can manage his own stuff!")
        return

    if user_member.is_anonymous is True:
        await message.reply_text("This user is already anonymous!")
        return

    if user_id == bot.id:
        await message.reply_text("Yeah, I wish I could promote myself...")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = await chat.get_member(bot.id)
    # set same perms as user -  to keep the other perms untouched!
    u_member = await chat.get_member(user_id)
    # the perms may be not same as old ones if the bot doesn't have the rights to change them but can't do anything about it

    try:
        if title:
            await bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
        await CUTIEPII_PTB.bot.promote_chat_member(
            chat.id,
            user_id,
            is_anonymous=True,
            can_change_info=bool(bot_member.can_change_info
                                 and u_member.can_change_info),
            can_post_messages=bool(bot_member.can_post_messages
                                   and u_member.can_post_messages),
            can_edit_messages=bool(bot_member.can_edit_messages
                                   and u_member.can_edit_messages),
            can_delete_messages=bool(bot_member.can_delete_messages
                                     and u_member.can_delete_messages),
            can_invite_users=bool(bot_member.can_invite_users
                                  and u_member.can_invite_users),
            can_promote_members=bool(bot_member.can_promote_members
                                     and u_member.can_promote_members),
            can_restrict_members=bool(bot_member.can_restrict_members
                                      and u_member.can_restrict_members),
            can_pin_messages=bool(bot_member.can_pin_messages
                                  and u_member.can_pin_messages),
            can_manage_video_chats=bool(bot_member.can_manage_video_chats
                                        and u_member.can_manage_video_chats),
        )

        rmsg = f"<b>{user_member.user.first_name or user_id}</b> is now anonymous"
        if title:
            rmsg += f" with title <code>{html.escape(title)}</code>"
        await bot.sendMessage(
            chat.id,
            rmsg,
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            await message.reply_text(
                "How am I mean to promote someone who isn't in the group?")
        else:
            await message.reply_text("An error occurred while promoting.")
        return

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#PROMOTED\n"
        f"Anonymous\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message


@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
async def promote(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    user_id, title = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect..",
        )
        return

    try:
        user_member = await chat.get_member(user_id)
    except Exception as e:
        await message.reply_text(f"Error: {e}")
        return

    if user_member.status in ["administrator", "creator"]:
        await update.effective_message.reply_text(
            "How am I meant to promote someone that's already an admin?")
        return

    if user_id == bot.id:
        await update.effective_message.reply_text(
            "I can't promote myself! Get an admin to do it for me.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = await chat.get_member(bot.id)
    #can_promote_members = False
    #if "all" in permissions and bot_member.can_promote_members:
    #    can_promote_members = True

    try:
        await CUTIEPII_PTB.bot.promote_chat_member(
            chat.id,
            user_id,
            can_change_info=bot_member.can_change_info,
            can_post_messages=bot_member.can_post_messages,
            can_edit_messages=bot_member.can_edit_messages,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            #can_promote_members=False,
            can_restrict_members=bot_member.can_restrict_members,
            can_pin_messages=bot_member.can_pin_messages,
            #can_manage_video_chats=bot_member.can_manage_video_chats
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            await update.effective_message.reply_text(
                "I can't promote someone who isn't in the group.")
        else:
            await update.effective_message.reply_text(
                "An error occurred while promoting.")
        return

    await bot.sendMessage(
        chat.id,
        f"<b>╔━「 Promote in {chat.title}</b> \n"
        f"<b>➛ Admin:</b> {mention_html(user.id, user.first_name)} \n"
        f"<b>➛ User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
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
        ], ),
    )

    if len(title) > 16:
        await message.reply_text(
            "The title length is longer than 16 characters.\nTruncating it to 16 characters.",
        )

    with contextlib.suppress(BadRequest):
        await bot.setChatAdministratorCustomTitle(chat.id, user_id, title)

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#PROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    if title != "":
        log_message += f"<b>Admin Title:</b> {title}"

    return log_message


@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
async def midpromote(update: Update,
                     context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    user_id, title = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect..",
        )
        return

    try:
        user_member = await chat.get_member(user_id)
    except Exception as e:
        await message.reply_text(f"Error: {e}")
        return

    if user_member.status in ["administrator", "creator"]:
        await update.effective_message.reply_text(
            "How am I meant to midpromote someone that's already an admin?")
        return

    if user_id == bot.id:
        await update.effective_message.reply_text(
            "I can't midpromote myself! Get an admin to do it for me.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = await chat.get_member(bot.id)
    #can_promote_members = False
    #if "all" in permissions and bot_member.can_promote_members:
    #    can_promote_members = True

    try:
        await CUTIEPII_PTB.bot.promote_chat_member(
            chat.id,
            user_id,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
            can_pin_messages=bot_member.can_pin_messages,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            await update.effective_message.reply_text(
                "I can't midpromote someone who isn't in the group.")
        else:
            await update.effective_message.reply_text(
                "An error occured while midpromoting.")
        return

    await bot.sendMessage(
        chat.id,
        f"<b>╔━「 MidPromote in {chat.title}</b> \n"
        f"<b>➛ Admin:</b> {mention_html(user.id, user.first_name)} \n"
        f"<b>➛ User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
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
        ], ),
    )

    if len(title) > 16:
        await message.reply_text(
            "The title length is longer than 16 characters.\nTruncating it to 16 characters.",
        )

    with contextlib.suppress(BadRequest):
        await bot.setChatAdministratorCustomTitle(chat.id, user_id, title)

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#MIDPROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    if title != "":
        log_message += f"<b>Admin Title:</b> {title}"

    return log_message


@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
async def lowpromote(update: Update,
                     context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    user_id, title = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect..",
        )
        return

    try:
        user_member = await chat.get_member(user_id)
    except Exception as e:
        await message.reply_text(f"Error: {e}")
        return

    if user_member.status in ["administrator", "creator"]:
        await update.effective_message.reply_text(
            "How am I meant to lowpromote someone that's already an admin?")
        return

    if user_id == bot.id:
        await update.effective_message.reply_text(
            "I can't lowpromote myself! Get an admin to do it for me.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = await chat.get_member(bot.id)
    #can_promote_members = False
    #if "all" in permissions and bot_member.can_promote_members:
    #    can_promote_members = True

    try:
        await CUTIEPII_PTB.bot.promote_chat_member(
            chat.id,
            user_id,
            can_delete_messages=bot_member.can_delete_messages,
            can_invite_users=bot_member.can_invite_users,
        )
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            await update.effective_message.reply_text(
                "I can't lowpromote someone who isn't in the group.")
        else:
            await update.effective_message.reply_text(
                "An error occured while lowpromoting.")
        return

    await bot.sendMessage(
        chat.id,
        f"<b>╔━「 LowPromote in {chat.title}</b> \n"
        f"<b>➛ Admin:</b> {mention_html(user.id, user.first_name)} \n"
        f"<b>➛ User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
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
        ], ),
    )

    if len(title) > 16:
        await message.reply_text(
            "The title length is longer than 16 characters.\nTruncating it to 16 characters.",
        )

    with contextlib.suppress(BadRequest):
        await bot.setChatAdministratorCustomTitle(chat.id, user_id, title)

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#LOWPROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    if title != "":
        log_message += f"<b>Admin Title:</b> {title}"

    return log_message


@connection_status
@bot_admin
@can_promote
@user_admin
@loggable
async def fullpromote(update: Update,
                      context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    promoter = chat.get_member(user.id)

    user_id, title = await extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect..",
        )
        return

    try:
        user_member = await chat.get_member(user_id)
    except Exception as e:
        await message.reply_text(f"Error: {e}")
        return

    if user_member.status in ["administrator", "creator"]:
        await update.effective_message.reply_text(
            "How am I meant to promote someone that's already an admin?")
        return

    if user_id == bot.id:
        await update.effective_message.reply_text(
            "I can't promote myself! Get an admin to do it for me.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = await chat.get_member(bot.id)
    #can_promote_members = False
    #if "all" in permissions and bot_member.can_promote_members:
    #    can_promote_members = True

    result = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/promoteChatMember?chat_id={chat.id}&user_id={user_id}&can_change_info={bot_member.can_change_info}&can_post_messages={bot_member.can_post_messages}&can_edit_messages={bot_member.can_edit_messages}&can_delete_messages={bot_member.can_delete_messages}&can_invite_users={bot_member.can_invite_users}&can_promote_members={bot_member.can_promote_members}&can_restrict_members={bot_member.can_restrict_members}&can_pin_messages={bot_member.can_pin_messages}&can_manage_video_chats={can_manage_video_chats(chat.id, bot.id)}"
    )
    status = result.json()["ok"]
    if status is False:
        await update.effective_message.reply_text(
            "An error occurred while promoting.")
        return

    await bot.sendMessage(
        chat.id,
        f"<b>╔━「 FullPromote in {chat.title}</b> \n"
        f"<b>➛ Admin:</b> {mention_html(user.id, user.first_name)} \n"
        f"<b>➛ User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
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
        ], ),
    )

    if len(title) > 16:
        await message.reply_text(
            "The title length is longer than 16 characters.\nTruncating it to 16 characters.",
        )

    with contextlib.suppress(BadRequest):
        await bot.setChatAdministratorCustomTitle(chat.id, user_id, title)

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#FULLPROMOTED\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    if title != "":
        log_message += f"<b>Admin Title:</b> {title}"

    return log_message


@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
async def middemote(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = extract_user(message, args)
    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect..",
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if user_member.status == "creator":
        await update.effective_message.reply_text(
            "This person CREATED the chat, how would I middemote them?")
        return

    if not user_member.status == "administrator":
        await update.effective_message.reply_text(
            "Can't middemote what wasn't promoted!")
        return

    if user_id == bot.id:
        await update.effective_message.reply_text(
            "I can't demote myself! Get an admin to do it for me.")
        return

    try:
        await CUTIEPII_PTB.bot.promote_chat_member(
            chat.id,
            user_id,
            can_change_info=True,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=True,
            can_reict_members=False,
            can_pin_messages=True,
            can_promote_members=False,
            #can_manage_video_chats=False
        )

        await bot.sendMessage(
            chat.id,
            f"<b>╔═━「 ⏬ MidDemote Event Of {chat.title}  」</b> \n"
            f"<b>➛ Admin:</b>  {mention_html(user.id, user.first_name)}\n"
            f"<b>➛ User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}",
            parse_mode=ParseMode.HTML,
        )

        with contextlib.suppress(KeyError):
            ADMIN_CACHE.pop(update.effective_chat.id)

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#MIDDEMOTED\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message
    except BadRequest:
        await message.reply_text(
            "Could not demote. I might not be admin, or the admin status was appointed by another"
            " user, so I can't act upon them!", )
        return


@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
async def demote(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    user_id = extract_user(message, args)
    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return

    try:
        user_member = chat.get_member(user_id)
    except Exception as e:
        await message.reply_text(f"Error: {e}")
        return

    if user_member.status == "creator":
        await message.reply_text(
            "This person is the chat CREATOR, find someone else to play with.")
        return

    if user_member.status != "administrator":
        await message.reply_text("This user isn't an admin!")
        return

    if user_id == bot.id:
        await message.reply_text(
            "I can't demote myself! Get an admin to do it for me.")
        return

    try:
        await CUTIEPII_PTB.bot.promote_chat_member(
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
        await bot.sendMessage(
            chat.id,
            "<b>{}</b> was demoted{}.".format(
                user_member.user.first_name or user_id,
                f' by <b>{message.from_user.first_name}</b>'
                if not message.sender_chat else ''),
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
        await message.reply_text(f"Could not demote!\n{str(e)}")
        return


@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
async def demoteanon(update: Update,
                     context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.type == "private":
        await message.reply_text(
            "This command is meant to be used in groups not PM!")

    user_id = extract_user(message, args)

    if not user_id:
        user_id = user.id

    try:
        user_member = chat.get_member(user_id)
    except Exception as e:
        await message.reply_text("Error:\n`{}`".format(e))
        return

    if user_member.status == "creator" and user_id == user.id:
        await message.reply_text("meh")
        return

    if user_member.status == "creator":
        await message.reply_text(
            "This person is the chat CREATOR, find someone else to play with.")
        return

    if user_member.status != "administrator":
        await message.reply_text("This user isn't an admin!")
        return

    if user_member.is_anonymous is False:
        await message.reply_text("This user isn't anonymous!")
        return

    if user_id == bot.id:
        await message.reply_text(
            "I can't demote myself! Get an admin to do it for me.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = await chat.get_member(bot.id)
    # set same perms as user -  to keep the other perms untouched!
    u_member = await chat.get_member(user_id)
    # the perms may be not same as old ones if the bot doesn't have the rights to change them but can't do anything about it

    try:
        await CUTIEPII_PTB.bot.promote_chat_member(
            chat.id,
            user_id,
            is_anonymous=False,
            can_change_info=bool(bot_member.can_change_info
                                 and u_member.can_change_info),
            can_post_messages=bool(bot_member.can_post_messages
                                   and u_member.can_post_messages),
            can_edit_messages=bool(bot_member.can_edit_messages
                                   and u_member.can_edit_messages),
            can_delete_messages=bool(bot_member.can_delete_messages
                                     and u_member.can_delete_messages),
            can_invite_users=bool(bot_member.can_invite_users
                                  and u_member.can_invite_users),
            can_promote_members=bool(bot_member.can_promote_members
                                     and u_member.can_promote_members),
            can_restrict_members=bool(bot_member.can_restrict_members
                                      and u_member.can_restrict_members),
            can_pin_messages=bool(bot_member.can_pin_messages
                                  and u_member.can_pin_messages),
            can_manage_video_chats=bool(bot_member.can_manage_video_chats
                                        and u_member.can_manage_video_chats),
        )

        rmsg = f"<b>{user_member.user.first_name or user_id}</b> is no longer anonymous"
        await bot.sendMessage(
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
        await message.reply_text(f"Could not demote!\n{str(e)}")
        return


@user_admin
async def refresh_admin(update: Update, context: CallbackContext) -> None:
    with contextlib.suppress(KeyError):
        ADMIN_CACHE.pop(update.effective_chat.id)
    await update.effective_message.reply_text("Admins cache refreshed!")


@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
async def set_title(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message

    user_id, title = await extract_user_and_text(message, args)
    try:
        user_member = chat.get_member(user_id)
    except:
        return

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect..",
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
        await update.effective_message.reply_text(
            "Setting blank title doesn't do anything!")
        return

    if len(title) > 16:
        await message.reply_text(
            "The title length is longer than 16 characters.\nTruncating it to 16 characters.",
        )

    try:
        await bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
    except BadRequest:
        await message.reply_text(
            "Either they aren't promoted by me or you set a title text that is impossible to set."
        )
        return

    await bot.sendMessage(
        chat.id,
        f"Sucessfully set title for <code>{user_member.user.first_name or user_id}</code> "
        f"to <code>{html.escape(title[:16])}</code>!",
        parse_mode=ParseMode.HTML,
    )


@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@loggable
async def pin(update: Update, context: CallbackContext) -> str:
    bot, args = context.bot, context.args
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message
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
        is_silent = (args[0].lower() != "notify" or args[0].lower() == "loud"
                     or args[0].lower() == "violent")

    if prev_message and is_group:
        try:
            await bot.pinChatMessage(chat.id,
                                     prev_message.message_id,
                                     disable_notification=is_silent)
            await msg.reply_text(
                "Success! Pinned this message on this group",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(text="📝 View Messages",
                                         url=f"{message_link}"),
                    InlineKeyboardButton(text="❌ Delete",
                                         callback_data="close2"),
                ]]),
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


@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@loggable
async def unpin(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    bot = context.bot
    msg_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id
    unpinner = chat.get_member(user.id)

    if (not (unpinner.can_pin_messages or unpinner.status == "creator")
            and user.id not in SUDO_USERS):
        await update.effective_message.reply_text(
            "You don't have the necessary rights to do that!")
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
            context.bot.unpinChatMessage(chat.id, prev_message.message_id)
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
            await bot.unpinChatMessage(chat.id)
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
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}")

    return log_message


@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
async def pinned(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    msg = update.effective_message
    msg_id = (update.effective_message.reply_to_message.message_id
              if update.effective_message.reply_to_message else
              update.effective_message.message_id)

    chat = bot.getChat(chat_id=msg.chat.id)
    if chat.pinned_message:
        pinned_id = chat.pinned_message.message_id
        if msg.chat.username:
            link_chat_id = msg.chat.username
            message_link = f"https://t.me/{link_chat_id}/{pinned_id}"
        elif (str(msg.chat.id)).startswith("-100"):
            link_chat_id = (str(msg.chat.id)).replace("-100", "")
            message_link = f"https://t.me/c/{link_chat_id}/{pinned_id}"

        await msg.reply_text(
            f"📌 Pinned the message on {html.escape(chat.title)}.",
            reply_to_message_id=msg_id,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    text="Pinned Messages",
                    url=f"https://t.me/{link_chat_id}/{pinned_id}",
                )
            ]]),
        )

    else:
        await msg.reply_text(
            f"There is no pinned message on <b>{html.escape(chat.title)}!</b>",
            parse_mode=ParseMode.HTML,
        )


@bot_admin_check(AdminPerms.CAN_INVITE_USERS)
@user_admin_check(AdminPerms.CAN_INVITE_USERS)
@connection_status
async def invite(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    message = update.effective_message
    chat = update.effective_chat

    if chat.username:
        await message.reply_text(f"https://telegram.dog/{chat.username}")
    elif chat.type in [chat.SUPERGROUP, chat.CHANNEL]:
        bot_member = chat.get_member(bot.id)
        if bot_member.can_invite_users:
            invitelink = await bot.exportChatInviteLink(chat.id)
            await update.effective_message.reply_text(invitelink)
        else:
            await message.reply_text(
                "I don't have access to the invite link, try changing my permissions!",
            )
    else:
        await message.reply_text(
            "I can only give you invite links for supergroups and channels, sorry!",
        )


@pgram.on_message(
    filters.command(["staff", "admins", "adminlist"]) & filters.group)
def staff(client: Client, message: Message):
    creator = []
    co_founder = []
    admin = []
    admin_check = pgram.get_chat_members(message.chat.id,
                                         filter="administrators")
    for x in admin_check:
        # Ini buat nyari co-founder
        if x.status == "administrator" and x.can_promote_members and x.title:
            title = escape(x.title)
            co_founder.append(
                f" <b>├</b> <a href='tg://user?id={x.user.id}'>{x.user.first_name}</a> »<i> {title}</i>"
            )
        elif x.status == "administrator" and x.can_promote_members:
            co_founder.append(
                f" <b>├</b> <a href='tg://user?id={x.user.id}'>{x.user.first_name}</a>"
            )
        elif x.status == "administrator" and x.title:
            title = escape(x.title)
            admin.append(
                f" <b>├</b> <a href='tg://user?id={x.user.id}'>{x.user.first_name}</a> »<i> {title}</i>"
            )
        elif x.status == "administrator":
            admin.append(
                f" <b>├</b> <a href='tg://user?id={x.user.id}'>{x.user.first_name}</a>"
            )
        elif x.status == "creator" and x.title:
            title = escape(x.title)
            creator.append(
                f" <b>└</b> <a href='tg://user?id={x.user.id}'>{x.user.first_name}</a> »<i> {title}</i>"
            )
        elif x.status == "creator":
            creator.append(
                f" <b>└</b> <a href='tg://user?id={x.user.id}'>{x.user.first_name}</a>"
            )

    if not co_founder and not admin:
        result = f"<b>Staff {message.chat.title}</b>\n\n👑 <b>Founder</b>\n" + "\n".join(
            creator)
    elif not co_founder and len(admin) > 0:
        res_admin = admin[-1].replace("├", "└")
        admin.pop(-1)
        admin.append(res_admin)
        result = f"<b>Staff {message.chat.title}</b>\n\n👑 <b>Founder</b>\n" + "\n".join(
            creator) + "\n\n" "👮‍♂ <b>Admin</b>\n" + "\n".join(admin)
    elif len(co_founder) > 0 and not admin:
        resco_founder = co_founder[-1].replace("├", "└")
        co_founder.pop(-1)
        co_founder.append(resco_founder)
        result = f"<b>Staff {message.chat.title}</b>\n\n👑 <b>Founder</b>\n" + "\n".join(
            creator) + "\n\n" "🔱 <b>Co-Founder</b>\n" + "\n".join(co_founder)
    else:
        resco_founder = co_founder[-1].replace("├", "└")
        res_admin = admin[-1].replace("├", "└")
        co_founder.pop(-1)
        admin.pop(-1)
        co_founder.append(resco_founder)
        admin.append(res_admin)
        result = (f"<b>Staff {message.chat.title}</b>\n\n👑 <b>Founder</b>\n" +
                  "\n".join(creator) + "\n\n"
                  "🔱 <b>Co-Founder</b>\n" + "\n".join(co_founder) + "\n\n"
                  "👮‍♂ <b>Admin</b>\n" + "\n".join(admin))
    pgram.send_message(message.chat.id, result)


@connection_status
@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES)
async def permapin(update: Update, context: CallbackContext) -> None:

    message = update.effective_message  # type: Optional[Message]
    u = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user

    chat_id = update.effective_chat.id

    text, data_type, content, buttons = get_message_type(message)
    tombol = build_keyboard_alternate(buttons)
    with contextlib.suppress(BadRequest):
        await message.delete()
    if str(data_type) in {"Types.BUTTON_TEXT", "Types.TEXT"}:
        try:
            sendingmsg = await context.bot.send_message(
                chat_id,
                text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup(tombol))
        except BadRequest:
            await context.bot.send_message(
                chat_id,
                "Incorrect markdown text!\nIf you don't know what markdown is, please send `/markdownhelp` in PM.",
                parse_mode=ParseMode.MARKDOWN_V2)
            return
    else:
        sendingmsg = ENUM_FUNC_MAP[str(data_type)](
            chat_id,
            content,
            caption=text,
            parse_mode=ParseMode.MARKDOWN_V2,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(tombol))
    if sendingmsg is None:
        await context.bot.send_message(chat_id, "Specify what to pin!")

    try:
        await context.bot.pinChatMessage(chat_id, sendingmsg.message_id)
    except BadRequest:
        await context.bot.send_message(chat_id,
                                       "I don't have access to message pins!")


@connection_status
@bot_admin_check(AdminPerms.CAN_DELETE_MESSAGES)
@user_admin
async def permanent_pin_set(update: Update, context: CallbackContext) -> str:
    u = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    args = context.args
    msg = update.effective_message  # type: Optional[Message]
    user = update.effective_user

    conn = await connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = CUTIEPII_PTB.bot.getChat(conn)
        chat_id = conn
        chat_name = CUTIEPII_PTB.bot.getChat(conn).title
        if not args:
            get_permapin = sql.get_permapin(chat_id)
            text_maker = f"Cleanlinked is currently set to: `{bool(int(get_permapin))}`"
            if get_permapin:
                if chat.username:
                    old_pin = f"https://t.me/{chat.username}/{get_permapin}"
                else:
                    old_pin = f"https://t.me/c/{str(chat.id)[4:]}/{get_permapin}"
                text_maker += "\nTo disable cleanlinked send: `/cleanlinked off`"
                text_maker += "\n\n[The permanent pinned message is here]({})".format(
                    old_pin)
            await context.bot.send_message(chat_id,
                                           text_maker,
                                           parse_mode=ParseMode.MARKDOWN_V2)
            return ""
        prev_message = args[0]
        if prev_message == "off":
            sql.set_permapin(chat_id, 0)
            await context.bot.send_message(chat_id,
                                           "Cleanlinked has been disabled!")
            return
        if "/" in prev_message:
            prev_message = prev_message.split("/")[-1]
    else:
        if update.effective_message.chat.type == ChatType.PRIVATE:
            await context.bot.send_message(
                chat_id, "This command is meant to use in group not in PM")
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id
        chat_name = update.effective_message.chat.title
        if update.effective_update.effective_message.reply_to_message:
            prev_message = update.effective_message.reply_to_message.message_id
        elif len(args) >= 1 and args[0] in ["off", "false"]:
            sql.set_permapin(chat.id, 0)
            await context.bot.send_message(chat_id,
                                           "Cleanlinked has been disabled!")
            return
        elif len(args) >= 1 and args[0] in ["on", "true"]:
            sql.set_permapin(chat.id, 1)
            await context.bot.send_message(chat_id,
                                           "Cleanlinked has been enabled!")
            return
        else:
            get_permapin = sql.get_permapin(chat_id)
            text_maker = f"Cleanlinked is currently set to: `{bool(int(get_permapin))}`"
            if get_permapin:
                if chat.username:
                    old_pin = f"https://t.me/{chat.username}/{get_permapin}"
                else:
                    old_pin = f"https://t.me/c/{str(chat.id)[4:]}/{get_permapin}"
                text_maker += "\nTo disable cleanlinked send: `/cleanlinked off`"
                text_maker += "\n\n[The permanent pinned message is here]({})".format(
                    old_pin)
            await context.bot.send_message(chat_id,
                                           text_maker,
                                           parse_mode=ParseMode.MARKDOWN_V2)
            return ""

    is_group = chat.type not in ("private", "channel")

    if prev_message and is_group:
        sql.set_permapin(chat.id, prev_message)
        await context.bot.send_message(chat_id,
                                       "Cleanlinked successfully set!")
        return "<b>{}:</b>" \
               "\n#PERMANENT_PIN" \
               "\n<b>Admin:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name))

    return ""


@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES)
async def unpinall(update: Update, context: CallbackContext) -> None:
    member = await update.effective_chat.get_member(update.effective_user.id)
    if member.status != "creator" and member.user.id not in SUDO_USERS:
        return await update.effective_message.reply_text(
            "Only group owner can do this!")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Are you sure you want to unpin all messages?",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(text="Yes", callback_data="unpinallbtn_yes"),
            InlineKeyboardButton(text="No", callback_data="unpinallbtn_no"),
        ]]),
    )


async def permanent_pin(update: Update, context: CallbackContext) -> None:
    user = update.effective_user  # type: Optional[User]
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message
    args = context.args

    get_permapin = sql.get_permapin(chat.id)
    if get_permapin and user.id != context.bot.id:
        try:
            to_del = context.bot.pinChatMessage(chat.id,
                                                get_permapin,
                                                disable_notification=True)
        except BadRequest:
            sql.set_permapin(chat.id, 0)
            if chat.username:
                old_pin = f"https://t.me/{chat.username}/{get_permapin}"
            else:
                old_pin = f"https://t.me/c/{str(chat.id)[4:]}/{get_permapin}"
                LOGGER.debug(old_pin)
            await context.bot.send_message(
                chat.id,
                "*Cleanlinked error:*\nI can't pin messages here!\nMake sure I'm an admin and can pin messages.\n\nClean linked has been disabled, [The old permanent pinned message is here]({})"
                .format(old_pin),
                parse_mode=ParseMode.MARKDOWN_V2)
            return

        if to_del:
            try:
                LOGGER.debug(message.message_id)
                context.bot.deleteMessage(chat.id, message.message_id)
            except BadRequest:
                await context.bot.send_message(
                    chat.id, "Cleanlinked error: cannot delete pinned msg")
                LOGGER.debug("Cleanlinked error: cannot delete pin msg")


@bot_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@user_admin_check(AdminPerms.CAN_PIN_MESSAGES)
@loggable
async def unpinallbtn(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    query = update.callback_query
    user = update.effective_user
    reply = query.data.split("_")[1]
    if reply == "yes":
        if unpinall := requests.post(
                f"https://api.telegram.org/bot{TOKEN}/unpinAllChatMessages?chat_id={chat.id}"
        ):
            await query.message.edit_text(
                "All pinned messages have been unpinned.")
        else:
            await query.message.edit_text("Failed to unpin all messages")
            return
    else:
        await query.message.edit_text(
            "Unpin of all pinned messages has been cancelled.")
        return
    return ("<b>{}:</b>"
            "\n#UNPINNEDALL"
            "\n<b>Admin:</b> {}".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
            ))


CUTIEPII_PTB.add_handler(
    CommandHandler("setdesc",
                   set_desc,
                   filters=PTB_Cutiepii_Filters.ChatType.GROUPS))
CUTIEPII_PTB.add_handler(
    CommandHandler("setsticker",
                   set_sticker,
                   filters=PTB_Cutiepii_Filters.ChatType.GROUPS))
CUTIEPII_PTB.add_handler(
    CommandHandler("setgpic",
                   setchatpic,
                   filters=PTB_Cutiepii_Filters.ChatType.GROUPS))
CUTIEPII_PTB.add_handler(
    CommandHandler("delgpic",
                   rmchatpic,
                   filters=PTB_Cutiepii_Filters.ChatType.GROUPS))
CUTIEPII_PTB.add_handler(
    CommandHandler("setgtitle",
                   setchat_title,
                   filters=PTB_Cutiepii_Filters.ChatType.GROUPS))

CUTIEPII_PTB.add_handler(
    CommandHandler("pin", pin, filters=PTB_Cutiepii_Filters.ChatType.GROUPS))
CUTIEPII_PTB.add_handler(
    CommandHandler("unpin",
                   unpin,
                   filters=PTB_Cutiepii_Filters.ChatType.GROUPS))
CUTIEPII_PTB.add_handler(
    CommandHandler("unpinall",
                   unpinall,
                   filters=PTB_Cutiepii_Filters.ChatType.GROUPS))
CUTIEPII_PTB.add_handler(
    CommandHandler("permapin",
                   permapin,
                   filters=PTB_Cutiepii_Filters.ChatType.GROUPS))
CUTIEPII_PTB.add_handler(
    CommandHandler("cleanlinked",
                   permanent_pin_set,
                   filters=PTB_Cutiepii_Filters.ChatType.GROUPS))
CUTIEPII_PTB.add_handler(
    CallbackQueryHandler(unpinallbtn, pattern=r"unpinallbtn_"))
CUTIEPII_PTB.add_handler(
    CommandHandler("pinned",
                   pinned,
                   filters=PTB_Cutiepii_Filters.ChatType.GROUPS))

CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("invitelink", invite))

CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("promote", promote))
CUTIEPII_PTB.add_handler(
    CallbackQueryHandler(promote_button, pattern=r"admin_"))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("fullpromote", fullpromote))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("lowpromote", lowpromote))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("midpromote", midpromote))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("setanon", promoteanon))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("demote", demote))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("middemote", middemote))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("unsetanon", demoteanon))

CUTIEPII_PTB.add_handler(CommandHandler("title", set_title))
CUTIEPII_PTB.add_handler(
    CommandHandler("admincache",
                   refresh_admin,
                   filters=PTB_Cutiepii_Filters.ChatType.GROUPS))

__help__ = """
*User Commands*:
➛ /admins*:* list of admins in the chat
➛ /pinned*:* to get the current pinned message.
➛ /rules*:* get the rules for this chat.
➛ /modlist*:* moderation user list.
➛ /modcheck*:* moderation cheak of a user.
*Promote & Demote Commands are Admins only*:
➛ /promote (user) (?admin's title)*:* Promotes the user to admin.
➛ /demote (user)*:* Demotes the user from admin.
➛ /lowpromote*:* Promote a member with low rights
➛ /midpromote*:* Promote a member with mid rights
➛ /highpromote*:* Promote a member with max rights
➛ /lowdemote*:* Demote an admin to low permissions
➛ /middemote*:* Demote an admin to mid permissions
➛ /addmod*:* moderator of a user.
➛ /rmmod*:* Unmoderator of a user.

*Cleaner & Purge Commands are Admins only*:
➛ /del*:* deletes the message you replied to
➛ /purge*:* deletes all messages between this and the replied to message.
➛ /purge <integer X>*:* deletes the replied message, and X messages following it if replied to a message.
➛ /zombies*:* counts the number of deleted account in your group
➛ /kickthefools*:* Kick inactive members from group (one week)
*Pin & Unpin Commands are Admins only*:
➛ /pin*:* silently pins the message replied to - add 'loud' or 'notify' to give notifs to users.
➛ /unpin*:* unpins the currently pinned message - add 'all' to unpin all pinned messages.
➛ /permapin*:* Pin a custom message through the bot. This message can contain markdown, buttons, and all the other cool features.
➛ /unpinall*:* Unpins all pinned messages.
➛ /antichannelpin <yes/no/on/off>*:* Don't let telegram auto-pin linked channels. If no arguments are given, shows current setting.
➛ /cleanlinked <yes/no/on/off>*:* Delete messages sent by the linked channel.
*Log Channel are Admins only*:
➛ /logchannel*:* get log channel info
➛ /setlog*:* set the log channel.
➛ /unsetlog*:* unset the log channel.
*Setting the log channel is done by*:
 ➛ adding the bot to the desired channel (as an admin!)
 ➛ sending `/setlog` in the channel
 ➛ forwarding the `/setlog` to the group
*Rules*:
➛ /setrules <your rules here>*:* set the rules for this chat.
➛ /clearrules*:* clear the rules for this chat.

*Anti channel*
Tired of telegram's stupidity? well here you go
*Available commands:*
➛ /antichannel <on/off>*:* Bans and deletes anyone who tries to talk as channel and forces em to talk as themselves.
➛ /cleanlinked <on/off>*:* Automatically delete linked channel posts from chatroom
*The Others Commands are Admins only*:
➛ /invitelink*:* gets invitelink
➛ /title <title here>*:* sets a custom title for an admin that the bot promoted
➛ /admincache*:* force refresh the admins list
➛ /setgtitle <text>*:* set group title
➛ /setgpic*:* reply to an image to set as group photo
➛ /setdesc*:* Set group description
➛ /setsticker*:* Set group sticker
"""

__mod_name__ = "Admins"
__command_list__ = [
    "setdesc"
    "setsticker"
    "setgpic"
    "delgpic"
    "setgtitle"
    "invitelink", "promote", "fullpromote", "lowpromote", "midpromote",
    "demote", "admincache"
    "unpin"
    "pin"
    "permapin"
]
