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

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, cutiepii_message_reaction, cutiepii_msg
import asyncio
import html
import ast
import contextlib
import Cutiepii_Robot.modules.sql.locks_sql as sql
from telegram import Message, Chat, MessageEntity, Update, ChatPermissions
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import BadRequest, TelegramError
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, MessageReactionHandler, filters
from telegram.helpers import mention_html
from alphabet_detector import AlphabetDetector

from Cutiepii_Robot.modules.helper_funcs.filters import CustomFilters
from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status, can_delete
from Cutiepii_Robot.modules.sql.approve_sql import is_approved
from Cutiepii_Robot import dispatcher, SUDO_USERS, LOGGER, BOT_ID
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.connection import connected
from Cutiepii_Robot.modules.helper_funcs.alternate import send_message, typing_action
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    bot_is_admin,
    user_is_admin,
    user_not_admin_check,
)

PERM_GROUP = -8
REST_GROUP = -12
ad = AlphabetDetector()

#Thanks to AstrakoBot for anonchannel code - https://github.com/Astrako/AstrakoBot/commit/2c076173d48ad4d65b5301cacf6cc8486ff14d96

class CustomCommandHandler(CommandHandler):
    def __init__(self, command, callback, **kwargs):
        if "run_async" in kwargs:
            del kwargs["run_async"]
        super().__init__(command, callback, **kwargs)

    async def check_update(self, update: Update):
        parent_result = super().check_update(update)
        if asyncio.iscoroutine(parent_result):
            parent_result = await parent_result
        if parent_result and not (
                sql.is_restr_locked(update.effective_chat.id, 'messages') and not user_is_admin(update,
                                                                                                update.effective_user.id)):
            args = update.effective_message.text.split()[1:]
            filter_result = self.filters.check_update(update) if self.filters else True
            if asyncio.iscoroutine(filter_result):
                filter_result = await filter_result
            if filter_result:
                return args, filter_result
        return False


CommandHandler = CustomCommandHandler

LOCK_TYPES = {
    "audio": filters.AUDIO,
    "voice": filters.VOICE,
    "document": filters.Document.ALL,
    "video": filters.VIDEO,
   "videonote": filters.VIDEO_NOTE,
    "contact": filters.CONTACT,
    "photo": filters.PHOTO,
    "url": filters.Entity(MessageEntity.URL)
    | filters.CaptionEntity(MessageEntity.URL),
    "bots": filters.StatusUpdate.NEW_CHAT_MEMBERS,
    "forward": filters.FORWARDED & ~ filters.IS_AUTOMATIC_FORWARD,
    "game": filters.GAME,
    "location": filters.LOCATION,
    "egame": filters.Dice.ALL,
    "rtl": "rtl",
    "button": "button",
    "inline": "inline",
    "phone": filters.Entity(MessageEntity.PHONE_NUMBER) | filters.CaptionEntity(MessageEntity.PHONE_NUMBER),
    "command": filters.COMMAND,
    "email": filters.Entity(MessageEntity.EMAIL) | filters.CaptionEntity(MessageEntity.EMAIL),
    "anonchannel": CustomFilters.anonchannel,
    "forwardchannel": "forwardchannel",
    "forwardbot": "forwardbot",
    "apk" : filters.Document.MimeType("application/vnd.android.package-archive"),
    "doc" : filters.Document.MimeType("application/msword"),
    "exe" : filters.Document.MimeType("application/x-ms-dos-executable"),
    "gif" : filters.Document.MimeType("video/mp4"),
    "jpg" : filters.Document.MimeType("image/jpeg"),
    "mp3" : filters.Document.MimeType("audio/mpeg"),
    "pdf" : filters.Document.MimeType("application/pdf"),
    "txt" : filters.Document.MimeType("text/plain"),
    "xml" : filters.Document.MimeType("application/xml"),
    "zip" : filters.Document.MimeType("application/zip"),
    "spoiler": filters.Entity(MessageEntity.SPOILER) | filters.CaptionEntity(MessageEntity.SPOILER),
    "blockquote": filters.Entity(MessageEntity.BLOCKQUOTE) | filters.CaptionEntity(MessageEntity.BLOCKQUOTE) | filters.Entity("expandable_blockquote") | filters.CaptionEntity("expandable_blockquote"),
    "code": filters.Entity(MessageEntity.CODE) | filters.CaptionEntity(MessageEntity.CODE) | filters.Entity(MessageEntity.PRE) | filters.CaptionEntity(MessageEntity.PRE),
    "album": "album",
    "cashtag": "cashtag",
    "checklist": "checklist",
    "comment": "comment",
    "emojionly": "emojionly",
    "forwardstory": "forwardstory",
    "forwarduser": "forwarduser",
    "guestbot": "guestbot",
    "outsidereaction": "outsidereaction",
    "reaction": "reaction",
    "zalgo": "zalgo",
    "emoji": "emoji",
    "emojicustom": "emojicustom",
}

LOCK_CHAT_RESTRICTION = {
    "all": {
        "can_send_messages": False,
        "can_send_audios": False,
        "can_send_documents": False,
        "can_send_photos": False,
        "can_send_videos": False,
        "can_send_video_notes": False,
        "can_send_voice_notes": False,
        "can_send_polls": False,
        "can_send_other_messages": False,
        "can_add_web_page_previews": False,
        "can_change_info": False,
        "can_invite_users": False,
        "can_pin_messages": False,
    },
    "messages": {"can_send_messages": False},
    "media": {
        "can_send_audios": False,
        "can_send_documents": False,
        "can_send_photos": False,
        "can_send_videos": False,
        "can_send_video_notes": False,
        "can_send_voice_notes": False,
    },
    "sticker": {"can_send_other_messages": False},
    "gif": {"can_send_other_messages": False},
    "poll": {"can_send_polls": False},
    "other": {"can_send_other_messages": False},
    "previews": {"can_add_web_page_previews": False},
    "info": {"can_change_info": False},
    "invite": {"can_invite_users": False},
    "pin": {"can_pin_messages": False},
}

UNLOCK_CHAT_RESTRICTION = {
    "all": {
        "can_send_messages": True,
        "can_send_audios": True,
        "can_send_documents": True,
        "can_send_photos": True,
        "can_send_videos": True,
        "can_send_video_notes": True,
        "can_send_voice_notes": True,
        "can_send_polls": True,
        "can_send_other_messages": True,
        "can_add_web_page_previews": True,
        "can_invite_users": True,
    },
    "messages": {"can_send_messages": True},
    "media": {
        "can_send_audios": True,
        "can_send_documents": True,
        "can_send_photos": True,
        "can_send_videos": True,
        "can_send_video_notes": True,
        "can_send_voice_notes": True,
    },
    "sticker": {"can_send_other_messages": True},
    "gif": {"can_send_other_messages": True},
    "poll": {"can_send_polls": True},
    "other": {"can_send_other_messages": True},
    "previews": {"can_add_web_page_previews": True},
    "info": {"can_change_info": True},
    "invite": {"can_invite_users": True},
    "pin": {"can_pin_messages": True},
}

PERM_GROUP = -8
REST_GROUP = -12


# NOT ASYNC
async def restr_members(
    bot, chat_id, members, messages=False, media=False, other=False, previews=False
):

    for mem in members:
        with contextlib.suppress(TelegramError):
            await bot.restrict_chat_member(
                chat_id,
                mem.user.id,
                permissions=ChatPermissions(
                    can_send_messages=messages,
                    can_send_audios=media,
                    can_send_documents=media,
                    can_send_photos=media,
                    can_send_videos=media,
                    can_send_video_notes=media,
                    can_send_voice_notes=media,
                    can_send_other_messages=other,
                    can_add_web_page_previews=previews,
            ))


async def unrestr_members(
    bot, chat_id, members, messages=True, media=True, other=True, previews=True
):
    for mem in members:
        with contextlib.suppress(TelegramError):
            await bot.restrict_chat_member(
                chat_id,
                mem.user.id,
                permissions=ChatPermissions(
                    can_send_messages=messages,
                    can_send_audios=media,
                    can_send_documents=media,
                    can_send_photos=media,
                    can_send_videos=media,
                    can_send_video_notes=media,
                    can_send_voice_notes=media,
                    can_send_other_messages=other,
                    can_add_web_page_previews=previews,
            ))


LOCKABLES = {
    "all": "Restricts everything (all messages and permissions).",
    "messages": "Restricts sending any messages.",
    "media": "Restricts sending all media types.",
    "sticker": "Restricts sending stickers.",
    "gif": "Restricts sending Gifs/Animations.",
    "poll": "Restricts sending polls.",
    "other": "Restricts other message types.",
    "previews": "Restricts adding web page previews.",
    "info": "Restricts changing group info.",
    "invite": "Restricts inviting users.",
    "pin": "Restricts pinning messages.",
    "audio": "Restricts audio media messages.",
    "voice": "Restricts voice messages.",
    "document": "Restricts document media messages.",
    "video": "Restricts video messages.",
    "videonote": "Restricts video notes.",
    "contact": "Restricts contact media messages.",
    "photo": "Restricts photo messages.",
    "url": "Messages containing URLs.",
    "bots": "Restricts adding bots to the group.",
    "forward": "Restricts forwarded messages.",
    "game": "Restricts game messages.",
    "location": "Restricts location media messages.",
    "egame": "Restricts dice animations / games.",
    "rtl": "Messages with right-to-left characters (e.g., Arabic, Hebrew).",
    "button": "Messages containing inline buttons.",
    "inline": "Restricts inline bot results.",
    "phone": "Messages containing phone numbers.",
    "command": "Messages starting with '/'.",
    "email": "Messages containing emails.",
    "anonchannel": "Restricts messages sent through anonymous channels.",
    "forwardchannel": "Restricts forwarded messages from channels.",
    "forwardbot": "Restricts forwarded messages from bots.",
    "apk": "Restricts APK file documents.",
    "doc": "Restricts Word document files.",
    "exe": "Restricts executable files.",
    "jpg": "Restricts JPG/JPEG image documents.",
    "mp3": "Restricts MP3 audio documents.",
    "pdf": "Restricts PDF documents.",
    "txt": "Restricts plain text documents.",
    "xml": "Restricts XML document files.",
    "zip": "Restricts ZIP archive files.",
    "spoiler": "Messages containing spoilers.",
    "blockquote": "Messages containing blockquotes/quotes.",
    "code": "Messages containing code blocks or preformatted text.",
    "album": "Restricts photos or videos sent as an album/media group.",
    "cashtag": "Restricts cashtags (e.g. $BTC).",
    "checklist": "Restricts native Telegram checklists.",
    "comment": "Restricts comment messages (replies in channel discussion groups).",
    "emoji": "Restricts standard emojis.",
    "emojicustom": "Restricts custom (premium) emojis.",
    "emojigame": "Restricts dice animations / games.",
    "emojionly": "Restricts messages containing only emojis.",
    "externalreply": "Restricts replies to messages outside the chat/thread.",
    "forwardstory": "Restricts messages forwarded from Telegram Stories.",
    "forwarduser": "Restricts messages forwarded from users.",
    "guestbot": "Restricts guest bots (bots that are not members of your group).",
    "outsidereaction": "Restricts reactions from users who are not members of the group.",
    "reaction": "Restricts message reactions.",
    "zalgo": "Restricts zalgo text (glitched text).",
}

@cutiepii_cmd(command="locktypes")
async def locktypes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /locktypes to list all lockable types with inline buttons."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    lockables_list = sorted(list(LOCKABLES.items()))

    # Create rows of 3 buttons each
    keyboard = [
        [
            InlineKeyboardButton(
                text=lock_type.capitalize(),
                callback_data=f"locktype_{lock_type}"
            )
            for lock_type, _ in lockables_list[i:i + 3]
        ]
        for i in range(0, len(lockables_list), 3)
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text(
        "<b>Available Lock Types</b>\nSelect a button below to view the detailed description for that lock type.",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

@cutiepii_callback(pattern=r"^locktype_")
async def locktype_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show lock type description when an inline button is clicked."""
    query = update.callback_query
    lock_type = query.data.split("_", 1)[1]
    description = LOCKABLES.get(lock_type, "No description available.")    

    await query.answer(
        text=f"{lock_type.capitalize()} Lock:\n{description}",
        show_alert=True        
    )

@cutiepii_cmd(command="lock")
@connection_status
@typing_action
@bot_admin_check()
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
@loggable
async def lock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user

    if not await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
        await send_message(
            update.effective_message,
            "<b>Action Denied</b>\nI do not have the required administrator permissions in this chat.",
        )
        return ""

    if not args:
        await send_message(
            update.effective_message,
            "<b>Invalid Command Usage</b>\nPlease specify the feature to lock. Use <code>/locktypes</code> to see all options.",
        )
        return ""

    locked_list = []
    perm_locked_list = []
    
    for ltype in args:
        ltype = ltype.lower()
        if ltype == "bot":
            ltype = "bots"
        elif ltype == "emojigame":
            ltype = "egame"
        if ltype == "anonchannel":
            await send_message(
                update.effective_message,
                "<b>Action Denied</b>\n<code>anonchannel</code> is not a valid lock type. Please use <code>/antichannel on</code> to restrict anonymous channels."
            )
            continue
            
        if ltype in LOCK_TYPES:
            sql.update_lock(chat.id, ltype, locked=True)
            locked_list.append(ltype)
        elif ltype in LOCK_CHAT_RESTRICTION:
            curr_chat = await context.bot.get_chat(chat.id)
            current_permission = curr_chat.permissions
            await context.bot.set_chat_permissions(
                chat_id=chat.id,
                permissions=get_permission_list(
                    ast.literal_eval(str(current_permission)),
                    LOCK_CHAT_RESTRICTION[ltype],
                ),
            )
            perm_locked_list.append(ltype)
        else:
            await send_message(
                update.effective_message,
                f"<b>Invalid Lock Type</b>\n<code>{ltype}</code> is not a recognized lock type. Use <code>/locktypes</code> for a full list of lockable features.",
                parse_mode=ParseMode.HTML
            )

    log_msg = ""
    response_msg = ""
    
    if locked_list:
        response_msg += f"<b>Lock Settings Updated</b>\nLocked <code>{', '.join(locked_list)}</code> for non-admin members.\n"
        log_msg += f"\nLocked <code>{', '.join(locked_list)}</code>."
    if perm_locked_list:
        response_msg += f"<b>Lock Settings Updated</b>\nLocked chat permissions: <code>{', '.join(perm_locked_list)}</code> for all non-admin members.\n"
        log_msg += f"\nLocked permissions <code>{', '.join(perm_locked_list)}</code>."

    if response_msg:
        await send_message(update.effective_message, response_msg.strip(), parse_mode=ParseMode.MARKDOWN)
        return (
            "<b>{}:</b>"
            "\n#LOCK"
            "\n<b>Admin:</b> {}"
            "{}"
        ).format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            log_msg,
        )
        
    return ""


@cutiepii_cmd(command="unlock")
@bot_admin_check()
@typing_action
@user_admin_check()
@loggable
async def unlock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user

    if not args:
        await send_message(update.effective_message, "What are you trying to unlock...? Try `/locktypes` for a list of lockables.")
        return ""

    unlocked_list = []
    perm_unlocked_list = []

    for ltype in args:
        ltype = ltype.lower()
        if ltype == "bot":
            ltype = "bots"
        elif ltype == "emojigame":
            ltype = "egame"
        if ltype == "anonchannel":
            await send_message(update.effective_message, "`anonchannel` is not a lock, please use `/antichannel off` to disable restricting channels")
            continue

        if ltype in LOCK_TYPES:
            sql.update_lock(chat.id, ltype, locked=False)
            unlocked_list.append(ltype)
        elif ltype in UNLOCK_CHAT_RESTRICTION:
            curr_chat = await context.bot.get_chat(chat.id)
            current_permission = curr_chat.permissions
            await context.bot.set_chat_permissions(
                chat_id=chat.id,
                permissions=get_permission_list(
                    ast.literal_eval(str(current_permission)),
                    UNLOCK_CHAT_RESTRICTION[ltype],
                ),
            )
            perm_unlocked_list.append(ltype)
        else:
            await send_message(
                update.effective_message,
                f"Unknown lock type: `{ltype}`. Try `/locktypes` for the list of lockables.",
                parse_mode=ParseMode.MARKDOWN
            )

    log_msg = ""
    response_msg = ""

    if unlocked_list:
        response_msg += f"Unlocked {', '.join([f'`{x}`' for x in unlocked_list])} for everyone!\n"
        log_msg += f"\nUnlocked <code>{', '.join(unlocked_list)}</code>."
    if perm_unlocked_list:
        response_msg += f"Unlocked chat permissions: {', '.join([f'`{x}`' for x in perm_unlocked_list])} for everyone!\n"
        log_msg += f"\nUnlocked permissions <code>{', '.join(perm_unlocked_list)}</code>."

    if response_msg:
        await send_message(update.effective_message, response_msg.strip(), parse_mode=ParseMode.MARKDOWN)
        return (
            "<b>{}:</b>"
            "\n#UNLOCK"
            "\n<b>Admin:</b> {}"
            "{}"
        ).format(
            html.escape(chat.title),
            mention_html(user.id, user.first_name),
            log_msg,
        )

    return ""


@cutiepii_msg((filters.ALL & filters.ChatType.GROUPS), group=PERM_GROUP)
@user_not_admin_check
async def del_lockables(update: Update, context: ContextTypes.DEFAULT_TYPE):  # sourcery no-metrics
    chat = update.effective_chat
    message = update.effective_message
    user = message.sender_chat or update.effective_user
    if is_approved(chat.id, user.id):
        return
    for lockable, filter in LOCK_TYPES.items():
        if lockable == "rtl":
            if sql.is_locked(chat.id, lockable) and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES):
                if message.caption:
                    check = ad.detect_alphabet(u"{}".format(message.caption))
                    if "ARABIC" in check:
                        try:
                            await message.delete()
                        except BadRequest as excp:
                            if excp.message != "Message to delete not found":
                                LOGGER.exception("ERROR in lockables - rtl:caption")
                        break
                if message.text:
                    check = ad.detect_alphabet(u"{}".format(message.text))
                    if "ARABIC" in check:
                        try:
                            await message.delete()
                        except BadRequest as excp:
                            if excp.message != "Message to delete not found":
                                LOGGER.exception("ERROR in lockables - rtl:text")
                        break
            continue
        if lockable == "button":
            if (
                sql.is_locked(chat.id, lockable)
                and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
                and message.reply_markup
                and message.reply_markup.inline_keyboard
            ):
                try:
                    await message.delete()
                except BadRequest as excp:
                    if excp.message != "Message to delete not found":
                        LOGGER.exception("ERROR in lockables - button")
                break
            continue
        if lockable == "inline":
            if (
                sql.is_locked(chat.id, lockable)
                and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
                and message
                and message.via_bot
            ):
                try:
                    await message.delete()
                except BadRequest as excp:
                    if excp.message != "Message to delete not found":
                        LOGGER.exception("ERROR in lockables - inline")
                break
            continue
        if lockable == "forwardchannel":
            if sql.is_locked(chat.id, lockable) and await can_delete(chat, BOT_ID):
                from telegram import MessageOriginChannel, MessageOriginChat
                is_channel_forward = False
                if message.forward_origin:
                    if isinstance(message.forward_origin, MessageOriginChannel):
                        is_channel_forward = True
                    elif isinstance(message.forward_origin, MessageOriginChat):
                        if getattr(message.forward_origin.sender_chat, "type", None) == "channel":
                            is_channel_forward = True
                elif getattr(message, "forward_from_chat", None) and getattr(message.forward_from_chat, "type", None) == "channel":
                    is_channel_forward = True

                if is_channel_forward:
                    try:
                        await message.delete()
                    except BadRequest as excp:
                        if excp.message != "Message to delete not found":
                            LOGGER.exception("ERROR in lockables - forwardchannel")
                    break
                continue
            continue
        if lockable == "forwardbot":
            if sql.is_locked(chat.id, lockable) and await can_delete(chat, BOT_ID):
                from telegram import MessageOriginUser
                is_bot_forward = False
                if message.forward_origin:
                    if isinstance(message.forward_origin, MessageOriginUser) and message.forward_origin.sender_user:
                        if message.forward_origin.sender_user.is_bot:
                            is_bot_forward = True
                elif getattr(message, "forward_from", None) and getattr(message.forward_from, "is_bot", False):
                    is_bot_forward = True

                if is_bot_forward:
                    try:
                        await message.delete()
                    except BadRequest as excp:
                        if excp.message != "Message to delete not found":
                            LOGGER.exception("ERROR in lockables - forwardbot")
                    break
                continue
            continue

        if lockable == "album":
            if (
                sql.is_locked(chat.id, lockable)
                and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
                and message.media_group_id is not None
            ):
                try:
                    await message.delete()
                except BadRequest as excp:
                    if excp.message != "Message to delete not found":
                        LOGGER.exception("ERROR in lockables - album")
                break
            continue

        if lockable == "cashtag":
            if (
                sql.is_locked(chat.id, lockable)
                and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
                and any(ent.type == MessageEntity.CASHTAG for ent in (message.entities or []))
            ):
                try:
                    await message.delete()
                except BadRequest as excp:
                    if excp.message != "Message to delete not found":
                        LOGGER.exception("ERROR in lockables - cashtag")
                break
            continue

        if lockable == "checklist":
            if (
                sql.is_locked(chat.id, lockable)
                and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
                and getattr(message, "checklist", None) is not None
            ):
                try:
                    await message.delete()
                except BadRequest as excp:
                    if excp.message != "Message to delete not found":
                        LOGGER.exception("ERROR in lockables - checklist")
                break
            continue

        if lockable == "comment":
            if (
                sql.is_locked(chat.id, lockable)
                and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
                and message.reply_to_message
                and message.reply_to_message.is_automatic_forward
            ):
                try:
                    await message.delete()
                except BadRequest as excp:
                    if excp.message != "Message to delete not found":
                        LOGGER.exception("ERROR in lockables - comment")
                break
            continue

        if lockable == "emojionly":
            if (
                sql.is_locked(chat.id, lockable)
                and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
            ):
                text_to_check = message.text or message.caption
                if text_to_check:
                    import emoji
                    stripped = "".join(text_to_check.split())
                    if stripped and all(emoji.is_emoji(c) for c in stripped):
                        try:
                            await message.delete()
                        except BadRequest as excp:
                            if excp.message != "Message to delete not found":
                                LOGGER.exception("ERROR in lockables - emojionly")
                        break
            continue

        if lockable == "emoji":
            if (
                sql.is_locked(chat.id, lockable)
                and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
            ):
                text_to_check = message.text or message.caption
                if text_to_check:
                    import emoji
                    if emoji.emoji_count(text_to_check) > 0:
                        try:
                            await message.delete()
                        except BadRequest as excp:
                            if excp.message != "Message to delete not found":
                                LOGGER.exception("ERROR in lockables - emoji")
                        break
            continue

        if lockable == "emojicustom":
            if (
                sql.is_locked(chat.id, lockable)
                and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
            ):
                ents = (message.entities or []) + (message.caption_entities or [])
                if any(ent.type == MessageEntity.CUSTOM_EMOJI for ent in ents):
                    try:
                        await message.delete()
                    except BadRequest as excp:
                        if excp.message != "Message to delete not found":
                            LOGGER.exception("ERROR in lockables - emojicustom")
                    break
            continue

        if lockable == "externalreply":
            if (
                sql.is_locked(chat.id, lockable)
                and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
                and getattr(message, "external_reply", None) is not None
            ):
                try:
                    await message.delete()
                except BadRequest as excp:
                    if excp.message != "Message to delete not found":
                        LOGGER.exception("ERROR in lockables - externalreply")
                break
            continue

        if lockable == "forwardstory":
            if (
                sql.is_locked(chat.id, lockable)
                and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
                and message.forward_origin
                and getattr(message.forward_origin, "type", None) == "story"
            ):
                try:
                    await message.delete()
                except BadRequest as excp:
                    if excp.message != "Message to delete not found":
                        LOGGER.exception("ERROR in lockables - forwardstory")
                break
            continue

        if lockable == "forwarduser":
            if (
                sql.is_locked(chat.id, lockable)
                and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
                and message.forward_origin
                and getattr(message.forward_origin, "type", None) in ("user", "hidden_user")
            ):
                try:
                    await message.delete()
                except BadRequest as excp:
                    if excp.message != "Message to delete not found":
                        LOGGER.exception("ERROR in lockables - forwarduser")
                break
            continue

        if lockable == "guestbot":
            if (
                sql.is_locked(chat.id, lockable)
                and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
                and message.via_bot
            ):
                try:
                    chat_member = await chat.get_member(message.via_bot.id)
                    is_member = chat_member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER, ChatMemberStatus.RESTRICTED)
                except Exception:
                    is_member = False
                if not is_member:
                    try:
                        await message.delete()
                    except BadRequest as excp:
                        if excp.message != "Message to delete not found":
                            LOGGER.exception("ERROR in lockables - guestbot")
                    break
            continue

        if lockable == "zalgo":
            if (
                sql.is_locked(chat.id, lockable)
                and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
            ):
                text_to_check = message.text or message.caption
                if text_to_check:
                    import re
                    combining_range = re.compile(r"[\u0300-\u036F\u1AB0-\u1AFF\u1DC0-\u1DFF\u20D0-\u20FF\uFE20-\uFE2F]")
                    matches = combining_range.findall(text_to_check)
                    if len(matches) > 10 and len(matches) / len(text_to_check) > 0.3:
                        try:
                            await message.delete()
                        except BadRequest as excp:
                            if excp.message != "Message to delete not found":
                                LOGGER.exception("ERROR in lockables - zalgo")
                        break
            continue
        if (
            callable(filter) and filter(update.effective_message)
            and sql.is_locked(chat.id, lockable)
            and await bot_is_admin(chat, AdminPerms.CAN_DELETE_MESSAGES)
        ):
            if lockable == "bots":
                new_members = update.effective_message.new_chat_members
                for new_mem in new_members:
                    if new_mem.is_bot:
                        if not await bot_is_admin(chat, AdminPerms.CAN_RESTRICT_MEMBERS):
                            await send_message(
                                update.effective_message,
                                "I see a bot and I've been told to stop them from joining..."
                                "but I'm not admin!",
                            )
                            return

                        await chat.ban_member(new_mem.id)
                        await send_message(
                            update.effective_message,
                            "Only admins are allowed to add bots in this chat! Get outta here.",
                        )
                        break
            else:
                try:
                    await message.delete()
                except BadRequest as excp:
                    if excp.message != "Message to delete not found":
                        LOGGER.exception("ERROR in lockables")

                break


async def build_lock_message(chat_id):
    locks = sql.get_locks(chat_id)
    res = ""
    locklist = []
    permslist = []
    if locks:
        res += "*" + "These are the current locks in this Chat:" + "*"
        locklist.append("sticker = `{}`".format(locks.sticker))
        locklist.append("audio = `{}`".format(locks.audio))
        locklist.append("voice = `{}`".format(locks.voice))
        locklist.append("document = `{}`".format(locks.document))
        locklist.append("video = `{}`".format(locks.video))
        locklist.append("videonote = `{}`".format(locks.videonote))
        locklist.append("contact = `{}`".format(locks.contact))
        locklist.append("photo = `{}`".format(locks.photo))
        locklist.append("gif = `{}`".format(locks.gif))
        locklist.append("url = `{}`".format(locks.url))
        locklist.append("bots = `{}`".format(locks.bots))
        locklist.append("forward = `{}`".format(locks.forward))
        locklist.append("game = `{}`".format(locks.game))
        locklist.append("location = `{}`".format(locks.location))
        locklist.append("rtl = `{}`".format(locks.rtl))
        locklist.append("button = `{}`".format(locks.button))
        locklist.append("egame = `{}`".format(locks.egame))
        locklist.append("inline = `{}`".format(locks.inline))
        locklist.append("apk = `{}`".format(locks.apk))
        locklist.append("doc = `{}`".format(locks.doc))
        locklist.append("exe = `{}`".format(locks.exe))
        locklist.append("jpg = `{}`".format(locks.jpg))
        locklist.append("mp3 = `{}`".format(locks.mp3))
        locklist.append("pdf = `{}`".format(locks.pdf))
        locklist.append("txt = `{}`".format(locks.txt))
        locklist.append("xml = `{}`".format(locks.xml))
        locklist.append("zip = `{}`".format(locks.zip))
        locklist.append("phone = `{}`".format(locks.phone))
        locklist.append("command = `{}`".format(locks.command))
        locklist.append("email = `{}`".format(locks.email))
        locklist.append("anonchannel = `{}`".format(locks.anonchannel))
        locklist.append("forwardchannel = `{}`".format(locks.forwardchannel))
        locklist.append("forwardbot = `{}`".format(locks.forwardbot))
        locklist.append("videonote = `{}`".format(locks.videonote))
    
    curr_chat = await dispatcher.bot.get_chat(chat_id)
    permissions = curr_chat.permissions
    permslist.append("messages = `{}`".format(permissions.can_send_messages))
    # Check if any media permissions are enabled
    media_enabled = any([
        permissions.can_send_audios,
        permissions.can_send_documents,
        permissions.can_send_photos,
        permissions.can_send_videos,
        permissions.can_send_video_notes,
        permissions.can_send_voice_notes,
    ])
    permslist.append("media = `{}`".format(media_enabled))
    permslist.append("poll = `{}`".format(permissions.can_send_polls))
    permslist.append("other = `{}`".format(permissions.can_send_other_messages))
    permslist.append("previews = `{}`".format(permissions.can_add_web_page_previews))
    permslist.append("info = `{}`".format(permissions.can_change_info))
    permslist.append("invite = `{}`".format(permissions.can_invite_users))
    permslist.append("pin = `{}`".format(permissions.can_pin_messages))

    if locklist:
        # Ordering lock list
        locklist.sort()
        # Building lock list string
        for x in locklist:
            res += "\n - {}".format(x)
    res += "\n\n*" + "These are the current chat permissions:" + "*"
    for x in permslist:
        res += "\n - {}".format(x)
    return res


@cutiepii_cmd(command="locks")
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
@typing_action
async def list_locks(update: Update, _: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    res = await build_lock_message(chat.id)
    await send_message(update.effective_message, res, parse_mode=ParseMode.MARKDOWN)

@cutiepii_cmd(command="lockwarns")
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
@typing_action
async def lock_warns(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
	args = context.args
	chat = update.effective_chat
	user = update.effective_user

	conn = await connected(context.bot, update, chat, user.id, need_admin=True)
	if conn:
		chat = await dispatcher.bot.get_chat(conn)
		chat_id = conn
	else:
		if update.effective_message.chat.type == 'private':
			await send_message(update.effective_message, "You can do this command in groups, not PM")
			return ""
		chat_id = update.effective_chat.id

	if args:
		if args[0] in ("on", "yes"):
			sql.set_lockconf(chat_id, True)
			try:
				await send_message(update.effective_message, "I *will warn* user if send any message/media which currently locked", parse_mode="markdown")
			except BadRequest:
				await send_message(update.effective_message, "I *will warn* user if send any message/media which currently locked", parse_mode="markdown", do_quote=False)
		elif args[0] in ("off", "no"):
			sql.set_lockconf(chat_id, False)
			try:
				await send_message(update.effective_message, "I *will not warn* user if send any message/media which currently locked", parse_mode="markdown")
			except BadRequest:
				await send_message(update.effective_message, "I *will not warn* user if send any message/media which currently locked", parse_mode="markdown", do_quote=False)
		else:
			try:
				await send_message(update.effective_message, "I only understand 'on/yes' or 'off/no' only!", parse_mode="markdown")
			except BadRequest:
				await send_message(update.effective_message, "I only understand 'on/yes' or 'off/no' only!", parse_mode="markdown", do_quote=False)
	else:
		getconf = sql.get_lockconf(chat_id)
		if getconf:
			try:
				await send_message(update.effective_message, "Currently I *will warn* user if send any message/media which currently locked", parse_mode="markdown")
			except BadRequest:
				await send_message(update.effective_message, "Currently I *will warn* user if send any message/media which currently locked", parse_mode="markdown", do_quote=False)
		else:
			try:
				await send_message(update.effective_message, "Currently I *will not warn* user if send any message/media which currently locked", parse_mode="markdown")
			except BadRequest:
				await send_message(update.effective_message, "Currently I *will not warn* user if send any message/media which currently locked", parse_mode="markdown", do_quote=False)


def get_permission_list(current, new):
    permissions = {
        "can_send_messages": None,
        "can_send_audios": None,
        "can_send_documents": None,
        "can_send_photos": None,
        "can_send_videos": None,
        "can_send_video_notes": None,
        "can_send_voice_notes": None,
        "can_send_polls": None,
        "can_send_other_messages": None,
        "can_add_web_page_previews": None,
        "can_change_info": None,
        "can_invite_users": None,
        "can_pin_messages": None,
    }
    permissions.update(current)
    permissions.update(new)
    return ChatPermissions(**permissions)


async def __import_data__(chat_id, data):
    # set chat locks
    locks = data.get("locks", {})
    for itemlock in locks:
        if itemlock in LOCK_TYPES:
            sql.update_lock(chat_id, itemlock, locked=True)
        elif itemlock in LOCK_CHAT_RESTRICTION:
            sql.update_restriction(chat_id, itemlock, locked=True)


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


async def __chat_settings__(chat_id, user_id):
    return build_lock_message(chat_id)



__help__ = True

@cutiepii_message_reaction()
async def reaction_lock_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reaction_update = update.message_reaction
    if not reaction_update:
        return

    chat = reaction_update.chat
    user = reaction_update.user

    if not user:
        return

    if not reaction_update.new_reaction:
        return

    is_reaction_locked = sql.is_locked(chat.id, "reaction")
    is_outside_reaction_locked = sql.is_locked(chat.id, "outsidereaction")

    if not (is_reaction_locked or is_outside_reaction_locked):
        return

    if await user_is_admin(update, user.id, allow_moderators=True):
        return

    take_action = False
    reason = ""

    if is_reaction_locked:
        take_action = True
        reason = "Reactions are locked in this chat!"
    elif is_outside_reaction_locked:
        try:
            member = await chat.get_member(user.id)
            is_member = member.status in (ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER, ChatMemberStatus.RESTRICTED)
        except Exception:
            is_member = False

        if not is_member:
            take_action = True
            reason = "Reactions from non-members are locked in this chat!"

    if take_action:
        try:
            await context.bot.send_message(
                chat_id=chat.id,
                text=f"⚠️ {mention_html(user.id, user.first_name)}, {reason}",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass

__mod_name__ = "Locks"

