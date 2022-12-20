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

import threading

from sqlalchemy import Column, String, UnicodeText, Boolean, Integer, distinct, func

from Cutiepii_Robot import LOGGER
from Cutiepii_Robot.modules.helper_funcs.msg_types import Types
from Cutiepii_Robot.modules.sql import BASE, SESSION


class CustomFilters(BASE):
    __tablename__ = "cust_filters"
    chat_id = Column(String(14), primary_key=True)
    keyword = Column(UnicodeText, primary_key=True, nullable=False)
    reply = Column(UnicodeText, nullable=False)
    is_sticker = Column(Boolean, nullable=False, default=False)
    is_document = Column(Boolean, nullable=False, default=False)
    is_image = Column(Boolean, nullable=False, default=False)
    is_audio = Column(Boolean, nullable=False, default=False)
    is_voice = Column(Boolean, nullable=False, default=False)
    is_video = Column(Boolean, nullable=False, default=False)

    has_buttons = Column(Boolean, nullable=False, default=False)
    # NOTE: Here for legacy purposes, to ensure older filters don't mess up.
    has_markdown = Column(Boolean, nullable=False, default=False)

    # NEW FILTER
    # alter table cust_filters add column reply_text text;
    # alter table cust_filters add column file_type integer default 1;
    # alter table cust_filters add column file_id text;
    reply_text = Column(UnicodeText)
    file_type = Column(Integer, nullable=False, default=1)
    file_id = Column(UnicodeText, default=None)

    def __init__(
        self,
        chat_id,
        keyword,
        reply,
        is_sticker=False,
        is_document=False,
        is_image=False,
        is_audio=False,
        is_voice=False,
        is_video=False,
        has_buttons=False,
        reply_text=None,
        file_type=1,
        file_id=None,
    ):
        self.chat_id = str(chat_id)  # ensure string
        self.keyword = keyword
        self.reply = reply
        self.is_sticker = is_sticker
        self.is_document = is_document
        self.is_image = is_image
        self.is_audio = is_audio
        self.is_voice = is_voice
        self.is_video = is_video
        self.has_buttons = has_buttons
        self.has_markdown = True

        self.reply_text = reply_text
        self.file_type = file_type
        self.file_id = file_id

    def __repr__(self):
        return f"<Permissions for {self.chat_id}>"

    def __eq__(self, other):
        return (isinstance(other, CustomFilters)
                and self.chat_id == other.chat_id
                and self.keyword == other.keyword, )


class NewCustomFilters(BASE):
    __tablename__ = "cust_filters_new"
    chat_id = Column(String(14), primary_key=True)
    keyword = Column(UnicodeText, primary_key=True, nullable=False)
    text = Column(UnicodeText)
    file_type = Column(Integer, nullable=False, default=1)
    file_id = Column(UnicodeText, default=None)

    def __init__(self, chat_id, keyword, text, file_type, file_id):
        self.chat_id = str(chat_id)  # ensure string
        self.keyword = keyword
        self.text = text
        self.file_type = file_type
        self.file_id = file_id

    def __repr__(self):
        return f"<Filter for {self.chat_id}>"

    def __eq__(self, other):
        return isinstance(
            other, CustomFilters
        ) and self.chat_id == other.chat_id and self.keyword == other.keyword


class Buttons(BASE):
    __tablename__ = "cust_filter_urls"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(String(14), primary_key=True)
    keyword = Column(UnicodeText, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    url = Column(UnicodeText, nullable=False)
    same_line = Column(Boolean, default=False)

    def __init__(self, chat_id, keyword, name, url, same_line=False):
        self.chat_id = str(chat_id)
        self.keyword = keyword
        self.name = name
        self.url = url
        self.same_line = same_line


CustomFilters.__table__.create(checkfirst=True)
Buttons.__table__.create(checkfirst=True)

CUST_FILT_LOCK = threading.RLock()
BUTTON_LOCK = threading.RLock()
CHAT_FILTERS = {}


def get_all_filters():
    try:
        return SESSION.query(CustomFilters).all()
    finally:
        SESSION.close()


def add_filter(
    chat_id,
    keyword,
    reply,
    is_sticker=False,
    is_document=False,
    is_image=False,
    is_audio=False,
    is_voice=False,
    is_video=False,
    buttons=None,
):

    if buttons is None:
        buttons = []

    with CUST_FILT_LOCK:
        if prev := SESSION.query(CustomFilters).get((str(chat_id), keyword)):
            with BUTTON_LOCK:
                prev_buttons = (SESSION.query(Buttons).filter(
                    Buttons.chat_id == str(chat_id),
                    Buttons.keyword == keyword).all())
                for btn in prev_buttons:
                    SESSION.delete(btn)
            SESSION.delete(prev)

        filt = CustomFilters(
            str(chat_id),
            keyword,
            reply,
            is_sticker,
            is_document,
            is_image,
            is_audio,
            is_voice,
            is_video,
            bool(buttons),
        )

        if keyword not in CHAT_FILTERS.get(str(chat_id), []):
            CHAT_FILTERS[str(chat_id)] = sorted(
                CHAT_FILTERS.get(str(chat_id), []) + [keyword],
                key=lambda x: (-len(x), x),
            )

        SESSION.add(filt)
        SESSION.commit()

    for b_name, url, same_line in buttons:
        add_note_button_to_db(chat_id, keyword, b_name, url, same_line)


def new_add_filter(chat_id, keyword, reply_text, file_type, file_id, buttons):

    if buttons is None:
        buttons = []

    with CUST_FILT_LOCK:
        if prev := SESSION.query(CustomFilters).get((str(chat_id), keyword)):
            with BUTTON_LOCK:
                prev_buttons = (SESSION.query(Buttons).filter(
                    Buttons.chat_id == str(chat_id),
                    Buttons.keyword == keyword).all())
                for btn in prev_buttons:
                    SESSION.delete(btn)
            SESSION.delete(prev)

        filt = CustomFilters(
            str(chat_id),
            keyword,
            reply="there is should be a new reply",
            is_sticker=False,
            is_document=False,
            is_image=False,
            is_audio=False,
            is_voice=False,
            is_video=False,
            has_buttons=bool(buttons),
            reply_text=reply_text,
            file_type=file_type.value,
            file_id=file_id,
        )

        if keyword not in CHAT_FILTERS.get(str(chat_id), []):
            CHAT_FILTERS[str(chat_id)] = sorted(
                CHAT_FILTERS.get(str(chat_id), []) + [keyword],
                key=lambda x: (-len(x), x),
            )

        SESSION.add(filt)
        SESSION.commit()

    for b_name, url, same_line in buttons:
        add_note_button_to_db(chat_id, keyword, b_name, url, same_line)


def remove_filter(chat_id, keyword):
    with CUST_FILT_LOCK:
        if filt := SESSION.query(CustomFilters).get((str(chat_id), keyword)):
            if keyword in CHAT_FILTERS.get(str(chat_id), []):  # Sanity check
                CHAT_FILTERS.get(str(chat_id), []).remove(keyword)

            with BUTTON_LOCK:
                prev_buttons = (SESSION.query(Buttons).filter(
                    Buttons.chat_id == str(chat_id),
                    Buttons.keyword == keyword).all())
                for btn in prev_buttons:
                    SESSION.delete(btn)

            SESSION.delete(filt)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def get_chat_triggers(chat_id):
    return CHAT_FILTERS.get(str(chat_id), set())


def get_chat_filters(chat_id):
    try:
        return (SESSION.query(CustomFilters).filter(
            CustomFilters.chat_id == str(chat_id)).order_by(
                func.length(CustomFilters.keyword).desc()).order_by(
                    CustomFilters.keyword.asc()).all())
    finally:
        SESSION.close()


def get_filter(chat_id, keyword):
    try:
        return SESSION.query(CustomFilters).get((str(chat_id), keyword))
    finally:
        SESSION.close()


def add_note_button_to_db(chat_id, keyword, b_name, url, same_line):
    with BUTTON_LOCK:
        button = Buttons(chat_id, keyword, b_name, url, same_line)
        SESSION.add(button)
        SESSION.commit()


def get_buttons(chat_id, keyword):
    try:
        return (SESSION.query(Buttons).filter(
            Buttons.chat_id == str(chat_id),
            Buttons.keyword == keyword).order_by(Buttons.id).all())
    finally:
        SESSION.close()


def num_filters():
    try:
        return SESSION.query(CustomFilters).count()
    finally:
        SESSION.close()


def num_chats():
    try:
        return SESSION.query(func.count(distinct(
            CustomFilters.chat_id))).scalar()
    finally:
        SESSION.close()


def __load_chat_filters():
    global CHAT_FILTERS
    try:
        chats = SESSION.query(CustomFilters.chat_id).distinct().all()
        for (chat_id, ) in chats:  # remove tuple by ( ,)
            CHAT_FILTERS[chat_id] = []

        all_filters = SESSION.query(CustomFilters).all()
        for x in all_filters:
            CHAT_FILTERS[x.chat_id] += [x.keyword]

        CHAT_FILTERS = {
            x: sorted(set(y), key=lambda i: (-len(i), i))
            for x, y in CHAT_FILTERS.items()
        }

    finally:
        SESSION.close()


# ONLY USE FOR MIGRATE OLD FILTERS TO NEW FILTERS
def __migrate_filters():
    try:
        all_filters = SESSION.query(CustomFilters).distinct().all()
        for x in all_filters:
            if x.is_document:
                file_type = Types.DOCUMENT
            elif x.is_image:
                file_type = Types.PHOTO
            elif x.is_video:
                file_type = Types.VIDEO
            elif x.is_sticker:
                file_type = Types.STICKER
            elif x.is_audio:
                file_type = Types.AUDIO
            elif x.is_voice:
                file_type = Types.VOICE
            else:
                file_type = Types.TEXT

            LOGGER.debug(x.chat_id, x.keyword, x.reply, file_type.value)
            if file_type == Types.TEXT:
                filt = CustomFilters(
                    str(x.chat_id),
                    x.keyword,
                    x.reply,
                    file_type.value,
                    None,
                )
            else:
                filt = CustomFilters(
                    str(x.chat_id),
                    x.keyword,
                    None,
                    file_type.value,
                    x.reply,
                )

            SESSION.add(filt)
            SESSION.commit()

    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with CUST_FILT_LOCK:
        chat_filters = (SESSION.query(CustomFilters).filter(
            CustomFilters.chat_id == str(old_chat_id)).all())
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)
        SESSION.commit()
        if old_filt := CHAT_FILTERS.get(str(old_chat_id)):
            CHAT_FILTERS[str(new_chat_id)] = old_filt
            del CHAT_FILTERS[str(old_chat_id)]

        with BUTTON_LOCK:
            chat_buttons = (SESSION.query(Buttons).filter(
                Buttons.chat_id == str(old_chat_id)).all())
            for btn in chat_buttons:
                btn.chat_id = str(new_chat_id)
            SESSION.commit()


__load_chat_filters()
