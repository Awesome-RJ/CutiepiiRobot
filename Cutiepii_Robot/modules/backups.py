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

import json
import os
import time

import Cutiepii_Robot.modules.sql.blacklist_sql as blacklistsql
import Cutiepii_Robot.modules.sql.locks_sql as locksql
import Cutiepii_Robot.modules.sql.notes_sql as sql
import Cutiepii_Robot.modules.sql.rules_sql as rulessql

from io import BytesIO
from telegram import Update
from telegram.constants import ParseMode, ChatAction
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
from Cutiepii_Robot.modules.helper_funcs.alternate import typing_action
from Cutiepii_Robot.modules.helper_funcs.admin_status import user_admin_check, AdminPerms
from Cutiepii_Robot import LOGGER
from Cutiepii_Robot.modules.connection import connected

@cutiepii_cmd(command='import', rate_limit_calls=2, rate_limit_window=300, add_error_handler=True)
@typing_action
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def import_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    conn = await connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = await dispatcher.bot.get_chat(conn)
        chat_name = chat.title
    else:
        if update.effective_message.chat.type == "private":
            await update.effective_message.reply_text("This is a group only command!")
            return ""

        chat = update.effective_chat
        chat_name = update.effective_message.chat.title

    if msg.reply_to_message and msg.reply_to_message.document:
        try:
            file_info = await context.bot.get_file(msg.reply_to_message.document.file_id)
        except BadRequest:
            await msg.reply_text(
                "Try downloading and uploading the file yourself again, This one seem broken to me!",
            )
            return

        with BytesIO() as file:
            await file_info.download_to_memory(out=file)
            file.seek(0)
            data = json.load(file)

        if len(data) > 1 and str(chat.id) not in data:
            await msg.reply_text(
                "There are more than one group in this file and the chat.id is not same! How am i supposed to import it?",
            )
            return

        try:
            if data.get(str(chat.id)) is None:
                if conn:
                    text = "Backup comes from another chat, I can't return another chat to chat *{}*".format(
                        chat_name,
                    )
                else:
                    text = "Backup comes from another chat, I can't return another chat to this chat"
                return await msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            return await msg.reply_text("There was a problem while importing the data!")
        try:
            if str(BOT_ID) != str(data[str(chat.id)]["bot"]):
                await msg.reply_text(
                    "Backup from another bot that is not suggested might cause the problem, documents, photos, videos, audios, records might not work as it should be.",
                )
        except Exception:
            pass
        if str(chat.id) in data:
            data = data[str(chat.id)]["hashes"]
        else:
            data = data[list(data.keys())[0]]["hashes"]

        try:
            for mod in DATA_IMPORT:
                if asyncio.iscoroutinefunction(mod.__import_data__):
                    await mod.__import_data__(str(chat.id), data)
                else:
                    mod.__import_data__(str(chat.id), data)
        except Exception:
            await msg.reply_text(
                f"An error occurred while recovering your data. The process failed. If you experience a problem with this, please take it to @{SUPPORT_CHAT}",
            )

            LOGGER.exception(
                "Imprt for the chat %s with the name %s failed.",
                str(chat.id),
                str(chat.title),
            )
            return

        if conn:
            text = "Backup fully restored on *{}*.".format(chat_name)
        else:
            text = "Backup fully restored"
        await msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@cutiepii_cmd(command='export', rate_limit_calls=1, rate_limit_window=300, add_error_handler=True)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):  # sourcery no-metrics
    chat_data = context.chat_data
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    chat_id = update.effective_chat.id
    current_chat_id = update.effective_chat.id
    conn = await connected(context.bot, update, chat, user.id, need_admin=True)
    if conn:
        chat = await dispatcher.bot.get_chat(conn)
        chat_id = conn
    else:
        if update.effective_message.chat.type == "private":
            await update.effective_message.reply_text("This is a group only command!")
            return ""
        chat = update.effective_chat
        chat_id = update.effective_chat.id

    jam = time.time()
    new_jam = jam + 10800
    checkchat = get_chat(chat_id, chat_data)
    if checkchat.get("status"):
        if jam <= int(checkchat.get("value")):
            timeformatt = time.strftime(
                "%H:%M:%S %d/%m/%Y", time.localtime(checkchat.get("value")),
            )
            await update.effective_message.reply_text(
                "You can only backup once a day!\nYou can backup again in about `{}`".format(
                    timeformatt,
                ),
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        else:
            if user.id != OWNER_ID:
                put_chat(chat_id, new_jam, chat_data)
    elif user.id != OWNER_ID:
        put_chat(chat_id, new_jam, chat_data)

    note_list = sql.get_all_chat_notes(chat_id)
    backup = {}
    buttonlist = []
    namacat = ""
    isicat = ""
    rules = ""
    count = 0
    # Notes
    for note in note_list:
        count += 1
        namacat += "{}<###splitter###>".format(note.name)
        if note.msgtype == 1:
            tombol = sql.get_buttons(chat_id, note.name)
            for btn in tombol:
                if btn.same_line:
                    buttonlist.append(
                        ("{}".format(btn.name), "{}".format(btn.url), True),
                    )
                else:
                    buttonlist.append(
                        ("{}".format(btn.name), "{}".format(btn.url), False),
                    )
            isicat += "###button###: {}<###button###>{}<###splitter###>".format(
                note.value, str(buttonlist),
            )
            buttonlist.clear()
        elif note.msgtype == 2:
            isicat += "###sticker###:{}<###splitter###>".format(note.file)
        elif note.msgtype in (3, 4, 5, 6, 7, 8):
            types = {3: "file", 4: "photo", 5: "audio", 6: "voice", 7: "video", 8: "video_note"}
            isicat += "###{}###:{}<###TYPESPLIT###>{}<###splitter###>".format(
                types[note.msgtype], note.file, note.value,
            )
        else:
            isicat += "{}<###splitter###>".format(note.value)
    notes = {
        "#{}".format(namacat.split("<###splitter###>")[x]): "{}".format(
            isicat.split("<###splitter###>")[x],
        )
        for x in range(count)
    }
    rules = rulessql.get_rules(chat_id)
    bl = list(blacklistsql.get_chat_blacklist(chat_id))
    disabledcmd = list(disabledsql.get_all_disabled(chat_id))
    curr_locks = locksql.get_locks(chat_id)
    curr_restr = locksql.get_restr(chat_id)

    locked_lock = {}
    if curr_locks:
        locked_lock = {
            "sticker": curr_locks.sticker,
            "audio": curr_locks.audio,
            "voice": curr_locks.voice,
            "document": curr_locks.document,
            "video": curr_locks.video,
            "contact": curr_locks.contact,
            "photo": curr_locks.photo,
            "gif": curr_locks.gif,
            "url": curr_locks.url,
            "bots": curr_locks.bots,
            "forward": curr_locks.forward,
            "game": curr_locks.game,
            "location": curr_locks.location,
            "rtl": curr_locks.rtl,
        }

    locked_restr = {}
    if curr_restr:
        locked_restr = {
            "messages": curr_restr.messages,
            "media": curr_restr.media,
            "other": curr_restr.other,
            "previews": curr_restr.preview,
            "all": all(
                [
                    curr_restr.messages,
                    curr_restr.media,
                    curr_restr.other,
                    curr_restr.preview,
                ],
            ),
        }

    locks = {"locks": locked_lock, "restrict": locked_restr}
    backup[chat_id] = {
        "bot": BOT_ID,
        "hashes": {
            "info": {"rules": rules},
            "extra": notes,
            "blacklist": bl,
            "disabled": disabledcmd,
            "locks": locks,
        },
    }
    baccinfo = json.dumps(backup, indent=4)
    file_name = "{}{}.json".format(BOT_USERNAME, chat_id)
    with open(file_name, "w") as f:
        f.write(str(baccinfo))
    
    await context.bot.send_chat_action(current_chat_id, ChatAction.UPLOAD_DOCUMENT)
    tgl = time.strftime("%H:%M:%S - %d/%m/%Y", time.localtime(time.time()))
    with open(file_name, "rb") as f:
        await context.bot.send_document(
            current_chat_id,
            document=f,
            caption=("*Successfully Exported backup:*\nChat: `{}`\nChat ID: `{}`\nOn: `{}`\n"
                    "\nNote: This `{}-Backup` was specially made for notes.").format(
                chat.title, chat_id, tgl, BOT_USERNAME
            ),
            reply_to_message_id=msg.message_id,
            parse_mode=ParseMode.MARKDOWN,
        )
    os.remove(file_name)  # Cleaning file


# Temporary data
def put_chat(chat_id, value, chat_data):
    # LOGGER.debug(chat_data)
    status = value is not False
    chat_data[chat_id] = {"backups": {"status": status, "value": value}}


def get_chat(chat_id, chat_data):
    # LOGGER.debug(chat_data)
    try:
        return chat_data[chat_id]["backups"]
    except KeyError:
        return {"status": False, "value": False}


__help__ = True

__mod_name__ = "Backups"
