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

from Cutiepii_Robot.modules.sql import BASE, SESSION
from sqlalchemy import Boolean, Column, Integer, String, UnicodeText, distinct, func
from sqlalchemy.sql.sqltypes import BigInteger
from sqlalchemy.dialects import postgresql


class Warns(BASE):
    __tablename__ = "warns"

    user_id = Column(BigInteger, primary_key=True)
    chat_id = Column(String(14), primary_key=True)
    num_warns = Column(Integer, default=0)
    reasons = Column(postgresql.ARRAY(UnicodeText))

    def __init__(self, user_id, chat_id):
        self.user_id = user_id
        self.chat_id = str(chat_id)
        self.num_warns = 0
        self.reasons = []

    def __repr__(self):
        return f"<{self.num_warns} warns for {self.user_id} in {self.chat_id} for reasons {self.reasons}>"


class WarnFilters(BASE):
    __tablename__ = "warn_filters"
    chat_id = Column(String(14), primary_key=True)
    keyword = Column(UnicodeText, primary_key=True, nullable=False)
    reply = Column(UnicodeText, nullable=False)

    def __init__(self, chat_id, keyword, reply):
        self.chat_id = str(chat_id)  # ensure string
        self.keyword = keyword
        self.reply = reply

    def __repr__(self):
        return f"<Permissions for {self.chat_id}>"

    def __eq__(self, other):
        return (isinstance(other, WarnFilters)
                and self.chat_id == other.chat_id
                and self.keyword == other.keyword, )


class WarnSettings(BASE):
    __tablename__ = "warn_settings"
    chat_id = Column(String(14), primary_key=True)
    warn_limit = Column(Integer, default=3)
    soft_warn = Column(Boolean, default=False)

    def __init__(self, chat_id, warn_limit=3, soft_warn=False):
        self.chat_id = str(chat_id)
        self.warn_limit = warn_limit
        self.soft_warn = soft_warn

    def __repr__(self):
        return f"<{self.chat_id} has {self.warn_limit} possible warns.>"


Warns.__table__.create(checkfirst=True)
WarnFilters.__table__.create(checkfirst=True)
WarnSettings.__table__.create(checkfirst=True)

WARN_INSERTION_LOCK = threading.RLock()
WARN_FILTER_INSERTION_LOCK = threading.RLock()
WARN_SETTINGS_LOCK = threading.RLock()

WARN_FILTERS = {}


def warn_user(user_id, chat_id, reason=None):
    with WARN_INSERTION_LOCK:
        warned_user = SESSION.query(Warns).get((user_id, str(chat_id)))
        if not warned_user:
            warned_user = Warns(user_id, str(chat_id))

        warned_user.num_warns += 1
        if reason:
            warned_user.reasons = warned_user.reasons + [
                reason,
            ]  # TODO:: double check this wizardry

        reasons = warned_user.reasons
        num = warned_user.num_warns

        SESSION.add(warned_user)
        SESSION.commit()

        return num, reasons


def remove_warn(user_id, chat_id):
    with WARN_INSERTION_LOCK:
        removed = False
        warned_user = SESSION.query(Warns).get((user_id, str(chat_id)))

        if warned_user and warned_user.num_warns > 0:
            warned_user.num_warns -= 1
            warned_user.reasons = warned_user.reasons[:-1]
            SESSION.add(warned_user)
            SESSION.commit()
            removed = True

        SESSION.close()
        return removed


def reset_warns(user_id, chat_id):
    with WARN_INSERTION_LOCK:
        if warned_user := SESSION.query(Warns).get((user_id, str(chat_id))):
            warned_user.num_warns = 0
            warned_user.reasons = []

            SESSION.add(warned_user)
            SESSION.commit()
        SESSION.close()


def get_warns(user_id, chat_id):
    try:
        user = SESSION.query(Warns).get((user_id, str(chat_id)))
        if not user:
            return None
        reasons = user.reasons
        num = user.num_warns
        return num, reasons
    finally:
        SESSION.close()


def add_warn_filter(chat_id, keyword, reply):
    with WARN_FILTER_INSERTION_LOCK:
        warn_filt = WarnFilters(str(chat_id), keyword, reply)

        if keyword not in WARN_FILTERS.get(str(chat_id), []):
            WARN_FILTERS[str(chat_id)] = sorted(
                WARN_FILTERS.get(str(chat_id), []) + [keyword],
                key=lambda x: (-len(x), x),
            )

        SESSION.merge(warn_filt)  # merge to avoid duplicate key issues
        SESSION.commit()


def remove_warn_filter(chat_id, keyword):
    with WARN_FILTER_INSERTION_LOCK:
        if warn_filt := SESSION.query(WarnFilters).get(
            (str(chat_id), keyword)):
            if keyword in WARN_FILTERS.get(str(chat_id), []):  # sanity check
                WARN_FILTERS.get(str(chat_id), []).remove(keyword)

            SESSION.delete(warn_filt)
            SESSION.commit()
            return True
        SESSION.close()
        return False


def get_chat_warn_triggers(chat_id):
    return WARN_FILTERS.get(str(chat_id), set())


def get_chat_warn_filters(chat_id):
    try:
        return (SESSION.query(WarnFilters).filter(
            WarnFilters.chat_id == str(chat_id)).all())
    finally:
        SESSION.close()


def get_warn_filter(chat_id, keyword):
    try:
        return SESSION.query(WarnFilters).get((str(chat_id), keyword))
    finally:
        SESSION.close()


def set_warn_limit(chat_id, warn_limit):
    with WARN_SETTINGS_LOCK:
        curr_setting = SESSION.query(WarnSettings).get(str(chat_id))
        if not curr_setting:
            curr_setting = WarnSettings(chat_id, warn_limit=warn_limit)

        curr_setting.warn_limit = warn_limit

        SESSION.add(curr_setting)
        SESSION.commit()


def set_warn_strength(chat_id, soft_warn):
    with WARN_SETTINGS_LOCK:
        curr_setting = SESSION.query(WarnSettings).get(str(chat_id))
        if not curr_setting:
            curr_setting = WarnSettings(chat_id, soft_warn=soft_warn)

        curr_setting.soft_warn = soft_warn

        SESSION.add(curr_setting)
        SESSION.commit()


def get_warn_setting(chat_id):
    try:
        if setting := SESSION.query(WarnSettings).get(str(chat_id)):
            return setting.warn_limit, setting.soft_warn
        return 3, False

    finally:
        SESSION.close()


def num_warns():
    try:
        return SESSION.query(func.sum(Warns.num_warns)).scalar() or 0
    finally:
        SESSION.close()


def num_warn_chats():
    try:
        return SESSION.query(func.count(distinct(Warns.chat_id))).scalar()
    finally:
        SESSION.close()


def num_warn_filters():
    try:
        return SESSION.query(WarnFilters).count()
    finally:
        SESSION.close()


def num_warn_chat_filters(chat_id):
    try:
        return (SESSION.query(WarnFilters.chat_id).filter(
            WarnFilters.chat_id == str(chat_id)).count())
    finally:
        SESSION.close()


def num_warn_filter_chats():
    try:
        return SESSION.query(func.count(distinct(
            WarnFilters.chat_id))).scalar()
    finally:
        SESSION.close()


def __load_chat_warn_filters():
    global WARN_FILTERS
    try:
        chats = SESSION.query(WarnFilters.chat_id).distinct().all()
        for (chat_id, ) in chats:  # remove tuple by ( ,)
            WARN_FILTERS[chat_id] = []

        all_filters = SESSION.query(WarnFilters).all()
        for x in all_filters:
            WARN_FILTERS[x.chat_id] += [x.keyword]

        WARN_FILTERS = {
            x: sorted(set(y), key=lambda i: (-len(i), i))
            for x, y in WARN_FILTERS.items()
        }

    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with WARN_INSERTION_LOCK:
        chat_notes = (SESSION.query(Warns).filter(
            Warns.chat_id == str(old_chat_id)).all())
        for note in chat_notes:
            note.chat_id = str(new_chat_id)
        SESSION.commit()

    with WARN_FILTER_INSERTION_LOCK:
        chat_filters = (SESSION.query(WarnFilters).filter(
            WarnFilters.chat_id == str(old_chat_id)).all())
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)
        SESSION.commit()
        old_warn_filt = WARN_FILTERS.get(str(old_chat_id))
        if old_warn_filt is not None:
            WARN_FILTERS[str(new_chat_id)] = old_warn_filt
            del WARN_FILTERS[str(old_chat_id)]

    with WARN_SETTINGS_LOCK:
        chat_settings = (SESSION.query(WarnSettings).filter(
            WarnSettings.chat_id == str(old_chat_id)).all())
        for setting in chat_settings:
            setting.chat_id = str(new_chat_id)
        SESSION.commit()


__load_chat_warn_filters()
