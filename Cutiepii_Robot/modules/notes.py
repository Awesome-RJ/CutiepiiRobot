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
import re
import ast
import random
import html

from io import BytesIO
from typing import Optional

from telegram import (
    InlineKeyboardMarkup,
    Update,
    InlineKeyboardButton,
)
from telegram.constants import ParseMode, MessageLimit
MAX_MESSAGE_LENGTH = MessageLimit.MAX_TEXT_LENGTH
from telegram.error import BadRequest
from telegram.ext import (
    ContextTypes,
    filters,
)
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility
from telegram.helpers import mention_html, mention_markdown

from Cutiepii_Robot import LOGGER, dispatcher, SUDO_USERS, SUPPORT_CHAT, JOIN_LOGGER
from Cutiepii_Robot.modules.helper_funcs.alternate import send_message, typing_action
from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status
from Cutiepii_Robot.modules.helper_funcs.misc import build_keyboard, delete
from Cutiepii_Robot.modules.private_notes import getprivatenotes
from Cutiepii_Robot.modules.sql.clear_cmd_sql import get_clearcmd
from Cutiepii_Robot.modules.helper_funcs.parsing import get_data, ENUM_FUNC_MAP, Types, parse_filler, revertMd2HTML
from Cutiepii_Robot.modules.helper_funcs.handlers import MessageHandlerChecker
from Cutiepii_Robot.modules.helper_funcs.string_handling import escape_invalid_curly_brackets, escape_markdown

from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    AdminPerms,
)

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot.modules.log_channel import loggable
import Cutiepii_Robot.modules.sql.notes_sql as sql

FILE_MATCHER = re.compile(r"^###file_id(!photo)?###:(.*?)(?:\s|$)")
STICKER_MATCHER = re.compile(r"^###sticker(!photo)?###:")
BUTTON_MATCHER = re.compile(r"^###button(!photo)?###:(.*?)(?:\s|$)")
MYFILE_MATCHER = re.compile(r"^###file(!photo)?###:")
MYPHOTO_MATCHER = re.compile(r"^###photo(!photo)?###:")
MYAUDIO_MATCHER = re.compile(r"^###audio(!photo)?###:")
MYVOICE_MATCHER = re.compile(r"^###voice(!photo)?###:")
MYVIDEO_MATCHER = re.compile(r"^###video(!photo)?###:")
MYVIDEONOTE_MATCHER = re.compile(r"^###video_note(!photo)?###:")


async def get(update: Update, context: ContextTypes.DEFAULT_TYPE, notename: str, show_none: bool = True, no_format: bool = False, note_chat_id: int = None):
    bot = context.bot
    user = update.effective_user
    chat_id = update.effective_message.chat.id
    note_chat_id = note_chat_id or update.effective_chat.id
    note = sql.get_note(note_chat_id, notename)
    message = update.effective_message
    preview = True
    protect = False

    if note:
        if MessageHandlerChecker.check_user(update.effective_user.id):
            return
        if message.reply_to_message:
            reply_id = message.reply_to_message.message_id
        else:
            reply_id = message.message_id
        if note.is_reply:
            if JOIN_LOGGER:
                try:
                    await bot.forward_message(
                        chat_id=chat_id, from_chat_id=JOIN_LOGGER, message_id=note.value
                    )
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        raise
                    await message.reply_text(
                        "This message seems to have been lost - I'll remove it "
                        "from your notes list."
                    )
                    sql.rm_note(note_chat_id, notename)
            else:
                try:
                    await bot.forward_message(
                        chat_id=chat_id, from_chat_id=chat_id, message_id=note.value
                    )
                except BadRequest as excp:
                    if excp.message == "Message to forward not found":
                        raise
                    await message.reply_text(
                        "Looks like the original sender of this note has deleted "
                        "their message - sorry! Get your bot admin to start using a "
                        "message dump to avoid this. I'll remove this note from "
                        "your saved notes."
                    )
                    sql.rm_note(note_chat_id, notename)
        else:
            VALID_NOTE_FORMATTERS = [
                "first",
                "last",
                "fullname",
                "username",
                "id",
                "chatname",
                "mention",
                "user",
                "admin",
                "preview",
                "protect",
            ]
            valid_format = escape_invalid_curly_brackets(
                note.value, VALID_NOTE_FORMATTERS
            )
            if valid_format:
                if not no_format:
                    if "%%%" in valid_format:
                        split = valid_format.split("%%%")
                        if all(split):
                            text = random.choice(split)
                        else:
                            text = valid_format
                    else:
                        text = valid_format
                else:
                    text = valid_format
                text = text.format(
                    first=html.escape(message.from_user.first_name),
                    last=html.escape(
                        message.from_user.last_name or message.from_user.first_name
                    ),
                    fullname=html.escape(
                        " ".join(
                            [message.from_user.first_name, message.from_user.last_name]
                            if message.from_user.last_name
                            else [message.from_user.first_name]
                        )
                    ),
                    username="@" + html.escape(message.from_user.username)
                    if message.from_user.username
                    else mention_html(
                        message.from_user.id, message.from_user.first_name
                    ),
                    mention=mention_html(
                        message.from_user.id, message.from_user.first_name
                    ),
                    chatname=html.escape(
                        message.chat.title
                        if message.chat.type != "private"
                        else message.from_user.first_name
                    ),
                    id=message.from_user.id,
                )
            else:
                text = ""

            keyb = []
            parseMode = ParseMode.HTML
            buttons = sql.get_buttons(note_chat_id, notename)
            if no_format:
                parseMode = None
                text = await revertMd2HTML(text, buttons)
            else:
                keyb = build_keyboard(buttons)

            keyboard = InlineKeyboardMarkup(keyb)

            try:
                setting = await getprivatenotes(chat_id)
                if note.msgtype in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    text = re.sub(r'\n{3,}', '\n\n', text)

                    if setting:
                        try:
                            await bot.send_message(
                                user.id,
                                text,
                                parse_mode=parseMode,
                                disable_web_page_preview=True,
                                reply_markup=keyboard,
                            )
                        except Forbidden:
                            await bot.send_message(
                                chat_id,
                                "Please start me in PM to receive the note.",
                                reply_to_message_id=reply_id,
                            )
                    else:
                        delmsg = await bot.send_message(
                            chat_id,
                            text,
                            reply_to_message_id=reply_id,
                            parse_mode=parseMode,
                            reply_markup=keyboard,
                            disable_web_page_preview=bool(preview),
                            protect_content=bool(protect)
                        )

                        cleartime = get_clearcmd(chat_id, "notes")

                        if cleartime:
                            context.application.create_task(delete(delmsg, cleartime.time))

                elif note.msgtype == sql.Types.STICKER:
                    if setting:
                        try:
                            await bot.send_sticker(
                                user.id,
                                note.file,
                                reply_markup=keyboard,
                            )
                        except Forbidden:
                            await bot.send_message(
                                chat_id,
                                "Please start me in PM to receive the note.",
                                reply_to_message_id=reply_id,
                            )
                    else:
                        delmsg = await bot.send_sticker(
                            chat_id,
                            note.file,
                            reply_to_message_id=reply_id,
                            reply_markup=keyboard,
                        )

                        cleartime = get_clearcmd(chat_id, "notes")

                        if cleartime:
                            context.application.create_task(delete(delmsg, cleartime.time))
                else:
                    func = ENUM_FUNC_MAP[note.msgtype]
                    if setting:
                        try:
                            await func(
                                user.id,
                                note.file,
                                caption=text,
                                parse_mode=parseMode,
                                reply_markup=keyboard,
                            )
                        except Forbidden:
                            await bot.send_message(
                                chat_id,
                                "Please start me in PM to receive the note.",
                                reply_to_message_id=reply_id,
                            )
                    else:
                        delmsg = await func(
                            chat_id,
                            note.file,
                            caption=text,
                            reply_to_message_id=reply_id,
                            parse_mode=parseMode,
                            reply_markup=keyboard,
                            protect_content=bool(protect)
                        )

                        cleartime = get_clearcmd(chat_id, "notes")

                        if cleartime:
                            context.application.create_task(delete(delmsg, cleartime.time))

            except BadRequest as excp:
                if excp.message == "Entity_mention_user_invalid":
                    await message.reply_text(
                        "Looks like you tried to mention someone I've never seen before. If you really "
                        "want to mention them, forward one of their messages to me, and I'll be able "
                        "to tag them!"
                    )
                elif FILE_MATCHER.match(note.value):
                    await message.reply_text(
                        "This note was an incorrectly imported file from another bot - I can't use "
                        "it. If you really need it, you'll have to save it again. In "
                        "the meantime, I'll remove it from your notes list."
                    )
                    sql.rm_note(note_chat_id, notename)
                else:
                    await message.reply_text(
                        "This note could not be sent, as it is incorrectly formatted. Ask in "
                        f"@{SUPPORT_CHAT} if you can't figure out why!"
                    )
                    LOGGER.exception(
                        "Could not parse message #%s in chat %s",
                        notename,
                        str(note_chat_id),
                    )
                    LOGGER.warning("Message was: %s", str(note.value))
        return
    elif show_none:
        await message.reply_text("This note doesn't exist")


@cutiepii_cmd(command='get', can_disable=True)
@connection_status
async def cmd_get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) >= 2 and args[1].lower() in ["raw", "noformat"]:
        await get(update, context, args[0].lower(), show_none=True, no_format=True)
    elif len(args) >= 1:
        await get(update, context, args[0].lower(), show_none=True)
    else:
        await update.effective_message.reply_text("Specify a note name!")


@cutiepii_msg((filters.Regex(r"^#[^\s]+")), group=-14, friendly='get')
@connection_status
async def hash_get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message.text
    fst_word = message.split()[0]
    no_hash = fst_word[1:].lower()
    split_msg = message.split()
    if len(split_msg) >= 2:
        return await get(update, context, no_hash, show_none=False, no_format=split_msg[1].lower() in ["raw", "noformat"])

    await get(update, context, no_hash, show_none=False)


@cutiepii_msg((filters.Regex(r"^[/!>]\d+$")), group=-16, friendly='get')
@connection_status
async def slash_get(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message, chat_id = update.effective_message.text, update.effective_chat.id
    no_slash = message[1:]
    note_list = sql.get_all_chat_notes(chat_id)

    try:
        noteid = note_list[int(no_slash) - 1]
        note_name = str(noteid).strip(">").split()[1]
        await get(update, context, note_name, show_none=False)
    except IndexError:
        await update.effective_message.reply_text("Wrong Note ID 😾")


@cutiepii_cmd(command='save')
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    m = msg.text.split(' ', 1)
    if len(m) == 1 and not msg.reply_to_message:
        await msg.reply_text("Provide something to save")
        return
    note_name, text, data_type, content, buttons = get_data(msg)
    note_name = note_name.lower()
    if data_type is None:
        await msg.reply_text("Dude, there's no note")
        return

    sql.add_note_to_db(
        chat_id, note_name, text, data_type, buttons=buttons, file=content
    )
    
    await msg.reply_text(
        f"Yas! Added `{note_name}`.\nGet it with /get `{note_name}`, or `#{note_name}`",
        parse_mode=ParseMode.MARKDOWN,
    )

    if msg.reply_to_message and msg.reply_to_message.from_user.is_bot and not msg.text:
        if text:
            await msg.reply_text(
                "Seems like you're trying to save a message from a bot. Unfortunately, "
                "bots can't forward bot messages, so I can't save the exact message. "
                "\nI'll save all the text I can, but if you want more, you'll have to "
                "forward the message yourself, and then save it."
            )
        else:
            await msg.reply_text(
                "Bots are kinda handicapped by telegram, making it hard for bots to "
                "interact with other bots, so I can't save this message "
                "like I usually would - do you mind forwarding it and "
                "then saving that new message? Thanks!"
            )
    
    logmsg = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#SAVENOTE\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>Note:</b> {note_name}"
    )
    return logmsg



@cutiepii_cmd(command=['clear', 'delete'])
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    chat = update.effective_chat
    chat_id = chat.id
    user = update.effective_user

    if len(args) >= 1:
        notename = args[0].lower()

        if sql.rm_note(chat_id, notename):
            await update.effective_message.reply_text(f"I've removed the note '{notename}' from {html.escape(chat.title)}.", parse_mode=ParseMode.HTML)
            logmsg = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#CLEARNOTE\n"
                    f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
                    f"<b>Note:</b> {notename}"
            )
            return logmsg
        else:
            await update.effective_message.reply_text(f"You haven't saved any notes with this name yet in {html.escape(chat.title)}", parse_mode=ParseMode.HTML)
            return ''
    else:
        await update.effective_message.reply_text("Provide a notename.")
        return ''


@cutiepii_cmd(command=['removeallnotes', 'clearall', 'deleteall'])
async def clearall(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user
    member = await chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        await update.effective_message.reply_text(
            "Only the chat owner can clear all notes at once."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Delete all notes", callback_data="notes_rmall"
                    )
                ],
                [InlineKeyboardButton(text="Cancel", callback_data="notes_cancel")],
            ]
        )
        await update.effective_message.reply_text(
            f"Are you sure you would like to clear ALL notes in {chat.title}? This action cannot be undone.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )



@cutiepii_callback(pattern=r"notes_.*")
@loggable
async def clearall_btn(update: Update, context: CallbackContext):
    query = update.callback_query
    chat = update.effective_chat
    message = update.effective_message
    member = await chat.get_member(query.from_user.id)
    user = query.from_user
    if query.data == "notes_rmall":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            note_list = sql.get_all_chat_notes(chat.id)
            try:
                for notename in note_list:
                    note = notename.name.lower()
                    sql.rm_note(chat.id, note)
                await message.edit_text("Deleted all notes.")
                
                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#CLEAREDALLNOTES\n"
                    f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
                )
                return log_message
            except BadRequest:
                return

        if member.status == "administrator":
            await query.answer("Only owner of the chat can do this.")

        if member.status == "member":
            await query.answer("You need to be admin to do this.")
    elif query.data == "notes_cancel":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            await message.edit_text("Clearing of all notes has been cancelled.")
            return
        if member.status == "administrator":
            await query.answer("Only owner of the chat can do this.")
        if member.status == "member":
            await query.answer("You need to be admin to do this.")


@cutiepii_cmd(command=["notes", "saved"])
@connection_status
async def list_notes(update: Update, context: CallbackContext):
    bot = context.bot
    user = update.effective_user
    chat_id = update.effective_chat.id
    note_list = sql.get_all_chat_notes(chat_id)
    notes = len(note_list) + 1
    msg = "Get note by `/notenumber` or `#notename` \n\n  *ID*    *Note* \n"
    msg_pm = f"*Notes from {update.effective_chat.title}* \nGet note by `/notenumber` or `#notename` in group \n\n  *ID*    *Note* \n"
    for note_id, note in zip(range(1, notes), note_list):
        if note_id < 10:
            note_name = f"{note_id:2}.  `{(note.name.lower())}`\n"
        else:
            note_name = f"{note_id}.  `{(note.name.lower())}`\n"
        if len(msg) + len(note_name) > MAX_MESSAGE_LENGTH:
            await update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
            msg = ""
            msg_pm = ""
        msg += note_name
        msg_pm += note_name

    if not note_list:
        try:
            await update.effective_message.reply_text("No notes in this chat!")
        except BadRequest:
            await update.effective_message.reply_text("No notes in this chat!", do_quote=False)

    elif len(msg) != 0:
        setting = await getprivatenotes(chat_id)
        if setting == True:
            try:
                await bot.send_message(user.id, msg_pm, parse_mode=ParseMode.MARKDOWN)
            except Forbidden:
                await update.effective_message.reply_text("Please start me in PM to receive the list of notes.")
        else:
            delmsg = await update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

            cleartime = get_clearcmd(chat_id, "notes")

            if cleartime:
                # Schedule delete task (run_async removed in v20+)
                import asyncio
                async def _delete_task():
                    await asyncio.sleep(cleartime.time)
                    try:
                        await delmsg.delete()
                    except:
                        pass
                asyncio.create_task(_delete_task())


async def __import_data__(chat_id, data):
    failures = []
    for notename, notedata in data.get("extra", {}).items():
        match = FILE_MATCHER.match(notedata)
        matchsticker = STICKER_MATCHER.match(notedata)
        matchbtn = BUTTON_MATCHER.match(notedata)
        matchfile = MYFILE_MATCHER.match(notedata)
        matchphoto = MYPHOTO_MATCHER.match(notedata)
        matchaudio = MYAUDIO_MATCHER.match(notedata)
        matchvoice = MYVOICE_MATCHER.match(notedata)
        matchvideo = MYVIDEO_MATCHER.match(notedata)
        matchvn = MYVIDEONOTE_MATCHER.match(notedata)

        if match:
            failures.append(notename)
            notedata = notedata[match.end() :].strip()
            if notedata:
                sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)
        elif matchsticker:
            content = notedata[matchsticker.end() :].strip()
            if content:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.STICKER, file=content
                )
        elif matchbtn:
            parse = notedata[matchbtn.end() :].strip()
            notedata = parse.split("<###button###>")[0]
            buttons = parse.split("<###button###>")[1]
            buttons = ast.literal_eval(buttons)
            if buttons:
                sql.add_note_to_db(
                    chat_id,
                    notename[1:],
                    notedata,
                    sql.Types.BUTTON_TEXT,
                    buttons=buttons,
                )
        elif matchfile:
            file = notedata[matchfile.end() :].strip()
            file = file.split("<###TYPESPLIT###>")
            notedata = file[1]
            content = file[0]
            if content:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.DOCUMENT, file=content
                )
        elif matchphoto:
            photo = notedata[matchphoto.end() :].strip()
            photo = photo.split("<###TYPESPLIT###>")
            notedata = photo[1]
            content = photo[0]
            if content:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.PHOTO, file=content
                )
        elif matchaudio:
            audio = notedata[matchaudio.end() :].strip()
            audio = audio.split("<###TYPESPLIT###>")
            notedata = audio[1]
            content = audio[0]
            if content:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.AUDIO, file=content
                )
        elif matchvoice:
            voice = notedata[matchvoice.end() :].strip()
            voice = voice.split("<###TYPESPLIT###>")
            notedata = voice[1]
            content = voice[0]
            if content:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.VOICE, file=content
                )
        elif matchvideo:
            video = notedata[matchvideo.end() :].strip()
            video = video.split("<###TYPESPLIT###>")
            notedata = video[1]
            content = video[0]
            if content:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.VIDEO, file=content
                )
        elif matchvn:
            video_note = notedata[matchvn.end() :].strip()
            video_note = video_note.split("<###TYPESPLIT###>")
            notedata = video_note[1]
            content = video_note[0]
            if content:
                sql.add_note_to_db(
                    chat_id, notename[1:], notedata, sql.Types.VIDEO_NOTE, file=content
                )
        else:
            sql.add_note_to_db(chat_id, notename[1:], notedata, sql.Types.TEXT)

    if failures:
        with BytesIO(str.encode("\n".join(failures))) as output:
            output.name = "failed_imports.txt"
            await dispatcher.bot.send_document(
                chat_id,
                document=output,
                filename="failed_imports.txt",
                caption="These files/photos failed to import due to originating "
                "from another bot. This is a telegram API restriction, and can't "
                "be avoided. Sorry for the inconvenience!",
            )


def __stats__():
    return f"-{sql.num_notes()} notes, across {sql.num_chats()} chats."


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


async def __chat_settings__(chat_id, user_id):
    notes = sql.get_all_chat_notes(chat_id)
    return f"There are `{len(notes)}` notes in this chat."

__help__ = True

__mod_name__ = "Notes"