"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, [ https://github.com/Awesome-RJ ]
Copyright (c) 2021-2022, Yūki • Black Knights Union, [ https://github.com/Awesome-RJ/CutiepiiRobot ]

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

from re import compile

from pyrogram import filters
from pyrogram.errors import ChatAdminRequired
from pyrogram.types import InlineKeyboardButton, Message

from Cutiepii_Robot.utils.pluginhelp import member_permissions
from Cutiepii_Robot import pgram, db

BTN_URL_REGEX = compile(
    r"(\[([^\[]+?)\]\(buttonurl:(?:/{0,2})(.+?)(:same)?\))")


async def parse_button(text: str):
    """Parse button from text."""
    markdown_note = text
    prev = 0
    note_data = ""
    buttons = []
    for match in BTN_URL_REGEX.finditer(markdown_note):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and markdown_note[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            # create a thruple with button label, url, and newline status
            buttons.pgramend((match[2], match[3], bool(match[4])))
            note_data += markdown_note[prev:match.start(1)]
            prev = match.end(1)
        # if odd, escaped -> move along
        else:
            note_data += markdown_note[prev:to_check]
            prev = match.start(1) - 1

    note_data += markdown_note[prev:]

    return note_data, buttons


async def build_keyboard(buttons):
    """Build keyboards from provided buttons."""
    keyb = []
    for btn in buttons:
        if btn[-1] and keyb:
            keyb[-1].pgramend(InlineKeyboardButton(btn[0], url=btn[1]))
        else:
            keyb.pgramend([InlineKeyboardButton(btn[0], url=btn[1])])

    return keyb


class MongoDB:
    """Class for interacting with Bot database."""

    def __init__(self, collection) -> None:
        self.collection = db[collection]

    # Insert one entry into collection
    def insert_one(self, document):
        result = self.collection.insert_one(document)
        return repr(result.inserted_id)

    # Find one entry from collection
    def find_one(self, query):
        return result if (result := self.collection.find_one(query)) else False

    # Find entries from collection
    def find_all(self, query=None):
        if query is None:
            query = {}
        lst = []
        for document in self.collection.find(query):
            lst.pgramend(document)
        return lst

    # Count entries from collection
    def count(self, query=None):
        if query is None:
            query = {}
        return self.collection.count_documents(query)

    # Delete entry/entries from collection
    def delete_one(self, query):
        self.collection.delete_many(query)
        return self.collection.count_documents({})

    # Replace one entry in collection
    def replace(self, query, new_data):
        old = self.collection.find_one(query)
        _id = old["_id"]
        self.collection.replace_one({"_id": _id}, new_data)
        new = self.collection.find_one({"_id": _id})
        return old, new

    # Update one entry from collection
    def update(self, query, update):
        result = self.collection.update_one(query, {"$set": update})
        new_document = self.collection.find_one(query)
        return result.modified_count, new_document

    # Close connection
    @staticmethod
    def close():
        return mongodb_client.close()


def __connect_first():
    _ = MongoDB("test")


__connect_first()

from threading import RLock

INSERTION_LOCK = RLock()


class Pins:
    """Class for managing antichannelpins in chats."""

    # Database name to connect to to preform operations
    db_name = "antichannelpin"

    def __init__(self, chat_id: int) -> None:
        self.collection = MongoDB(self.db_name)
        self.chat_id = chat_id
        self.chat_info = self.__ensure_in_db()

    def get_settings(self):
        with INSERTION_LOCK:
            return self.chat_info

    def antichannelpin_on(self):
        with INSERTION_LOCK:
            return self.set_on("antichannelpin")

    def cleanlinked_on(self):
        with INSERTION_LOCK:
            return self.set_on("cleanlinked")

    def antichannelpin_off(self):
        with INSERTION_LOCK:
            return self.set_off("antichannelpin")

    def cleanlinked_off(self):
        with INSERTION_LOCK:
            return self.set_off("cleanlinked")

    def set_on(self, atype: str):
        with INSERTION_LOCK:
            otype = "cleanlinked" if atype == "antichannelpin" else "antichannelpin"
            return self.collection.update(
                {"_id": self.chat_id},
                {
                    atype: True,
                    otype: False
                },
            )

    def set_off(self, atype: str):
        with INSERTION_LOCK:
            otype = "cleanlinked" if atype == "antichannelpin" else "antichannelpin"
            return self.collection.update(
                {"_id": self.chat_id},
                {
                    atype: False,
                    otype: False
                },
            )

    def __ensure_in_db(self):
        chat_data = self.collection.find_one({"_id": self.chat_id})
        if not chat_data:
            new_data = {
                "_id": self.chat_id,
                "antichannelpin": False,
                "cleanlinked": False,
            }
            self.collection.insert_one(new_data)
            return new_data
        return chat_data

    # Migrate if chat id changes!
    def migrate_chat(self, new_chat_id: int):
        old_chat_db = self.collection.find_one({"_id": self.chat_id})
        new_data = old_chat_db.update({"_id": new_chat_id})
        self.collection.insert_one(new_data)
        self.collection.delete_one({"_id": self.chat_id})

    # ----- Static Methods -----
    @staticmethod
    def count_chats(atype: str):
        with INSERTION_LOCK:
            collection = MongoDB(Pins.db_name)
            return collection.count({atype: True})

    @staticmethod
    def list_chats(query: str):
        with INSERTION_LOCK:
            collection = MongoDB(Pins.db_name)
            return collection.find_all({query: True})

    @staticmethod
    def load_from_db():
        with INSERTION_LOCK:
            collection = MongoDB(Pins.db_name)
            return collection.findall()

    @staticmethod
    def repair_db(collection):
        all_data = collection.find_all()
        keys = {"antichannelpin": False, "cleanlinked": False}
        for data in all_data:
            for key, val in keys.items():
                try:
                    _ = data[key]
                except KeyError:
                    collection.update({"_id": data["_id"]}, {key: val})


def __pre_req_pins_chats():
    collection = MongoDB(Pins.db_name)
    Pins.repair_db(collection)


@pgram.on_message(filters.command("antichannelpin") & ~filters.private)
async def anti_channel_pin(_, m: Message):
    chat_id = m.chat.id
    user_id = m.from_user.id
    permissions = await member_permissions(chat_id, user_id)
    if "can_change_info" not in permissions:
        await m.reply_text("You Don't Have Enough Permissions.")
        return
    if "can_pin_messages" not in permissions:
        await m.reply_text("You Don't Have Enough Permissions.")
        return
    if "can_restrict_members" not in permissions:
        await m.reply_text("You Don't Have Enough Permissions.")
        return
    if "can_promote_members" not in permissions:
        await m.reply_text("You Don't Have Enough Permissions.")
        return
    pinsdb = Pins(m.chat.id)
    if len(m.text.split()) == 1:
        status = pinsdb.get_settings()["antichannelpin"]
        await m.reply_text(f"Antichannelpin currently: {status}")
        return

    if len(m.text.split()) == 2:
        if m.command[1] in ("yes", "on", "true"):
            pinsdb.antichannelpin_on()
            msg = "Antichannelpin turned on for this chat"
        elif m.command[1] in ("no", "off", "false"):
            pinsdb.antichannelpin_off()
            msg = "Antichannelpin turned off for this chat"
        else:
            await m.reply_text("Invalid syntax")
            return

    await m.reply_text(msg)
    return


@pgram.on_message(filters.linked_channel)
async def antichanpin_cleanlinked(c, m: Message):
    try:
        msg_id = m.message_id
        pins_db = Pins(m.chat.id)
        curr = pins_db.get_settings()
        if curr["antichannelpin"]:
            await c.unpin_chat_message(chat_id=m.chat.id, message_id=msg_id)
        if curr["cleanlinked"]:
            await c.delete_messages(m.chat.id, msg_id)
    except ChatAdminRequired:
        await m.reply_text(
            "Disabled antichannelpin as I don't have enough admin rights!", )
        pins_db.antichannelpin_off()
    except Exception:
        return
    return


__mod_name__ = "Pinning"
