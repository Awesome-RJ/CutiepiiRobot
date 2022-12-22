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

from sqlalchemy import Boolean
from sqlalchemy.sql.sqltypes import String
from sqlalchemy import Column

from Cutiepii_Robot.modules.sql import BASE, SESSION


class AntiLinkedChannelSettings(BASE):
    __tablename__ = "anti_linked_channel_settings"

    chat_id = Column(String(14), primary_key=True)
    setting = Column(Boolean, default=False, nullable=False)

    def __init__(self, chat_id: int, disabled: bool):
        self.chat_id = str(chat_id)
        self.setting = disabled

    def __repr__(self):
        return f"<Antilinked setting {self.chat_id} ({self.setting})>"


class AntiPinChannelSettings(BASE):
    __tablename__ = "anti_pin_channel_settings"

    chat_id = Column(String(14), primary_key=True)
    setting = Column(Boolean, default=False, nullable=False)

    def __init__(self, chat_id: int, disabled: bool):
        self.chat_id = str(chat_id)
        self.setting = disabled

    def __repr__(self):
        return f"<Antipin setting {self.chat_id} ({self.setting})>"


AntiLinkedChannelSettings.__table__.create(checkfirst=True)
ANTI_LINKED_CHANNEL_SETTING_LOCK = threading.RLock()

AntiPinChannelSettings.__table__.create(checkfirst=True)
ANTI_PIN_CHANNEL_SETTING_LOCK = threading.RLock()


def enable_linked(chat_id: int):
    with ANTI_LINKED_CHANNEL_SETTING_LOCK:
        chat = SESSION.query(AntiLinkedChannelSettings).get(str(chat_id))
        if not chat:
            chat = AntiLinkedChannelSettings(chat_id, True)

        chat.setting = True
        SESSION.add(chat)
        SESSION.commit()


def enable_pin(chat_id: int):
    with ANTI_PIN_CHANNEL_SETTING_LOCK:
        chat = SESSION.query(AntiPinChannelSettings).get(str(chat_id))
        if not chat:
            chat = AntiPinChannelSettings(chat_id, True)

        chat.setting = True
        SESSION.add(chat)
        SESSION.commit()


def disable_linked(chat_id: int):
    with ANTI_LINKED_CHANNEL_SETTING_LOCK:
        chat = SESSION.query(AntiLinkedChannelSettings).get(str(chat_id))
        if not chat:
            chat = AntiLinkedChannelSettings(chat_id, False)

        chat.setting = False
        SESSION.add(chat)
        SESSION.commit()


def disable_pin(chat_id: int):
    with ANTI_PIN_CHANNEL_SETTING_LOCK:
        chat = SESSION.query(AntiPinChannelSettings).get(str(chat_id))
        if not chat:
            chat = AntiPinChannelSettings(chat_id, False)

        chat.setting = False
        SESSION.add(chat)
        SESSION.commit()


def status_linked(chat_id: int) -> bool:
    with ANTI_LINKED_CHANNEL_SETTING_LOCK:
        d = SESSION.query(AntiLinkedChannelSettings).get(str(chat_id))
        if not d:
            return False
        return d.setting


def status_pin(chat_id: int) -> bool:
    with ANTI_PIN_CHANNEL_SETTING_LOCK:
        d = SESSION.query(AntiPinChannelSettings).get(str(chat_id))
        if not d:
            return False
        return d.setting


def migrate_chat(old_chat_id, new_chat_id):
    with ANTI_LINKED_CHANNEL_SETTING_LOCK:
        if chat := SESSION.query(AntiLinkedChannelSettings).get(
                str(old_chat_id)):
            chat.chat_id = new_chat_id
            SESSION.add(chat)

        SESSION.commit()
    with ANTI_PIN_CHANNEL_SETTING_LOCK:
        if chat := SESSION.query(AntiPinChannelSettings).get(str(old_chat_id)):
            chat.chat_id = new_chat_id
            SESSION.add(chat)

        SESSION.commit()
