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


class AntiChannelSettings(BASE):
    __tablename__ = "anti_channel_settings"

    chat_id = Column(String(14), primary_key=True)
    setting = Column(Boolean, default=False, nullable=False)

    def __init__(self, chat_id: int, disabled: bool):
        self.chat_id = str(chat_id)
        self.setting = disabled

    def __repr__(self):
        return f"<Antiflood setting {self.chat_id} ({self.setting})>"


AntiChannelSettings.__table__.create(checkfirst=True)
ANTICHANNEL_SETTING_LOCK = threading.RLock()

def enable_antichannel(chat_id: int):
    with ANTICHANNEL_SETTING_LOCK:
        chat = SESSION.query(AntiChannelSettings).get(str(chat_id))
        if not chat:
            chat = AntiChannelSettings(str(chat_id), True)

        chat.setting = True
        SESSION.add(chat)
        SESSION.commit()


def disable_antichannel(chat_id: int):
    with ANTICHANNEL_SETTING_LOCK:
        chat = SESSION.query(AntiChannelSettings).get(str(chat_id))
        if not chat:
            chat = AntiChannelSettings(str(chat_id), False)

        chat.setting = False
        SESSION.add(chat)
        SESSION.commit()


def antichannel_status(chat_id: int) -> bool:
    with ANTICHANNEL_SETTING_LOCK:
        d = SESSION.query(AntiChannelSettings).get(str(chat_id))
        if not d:
            return False
        return d.setting




def migrate_chat(old_chat_id, new_chat_id):
    with ANTICHANNEL_SETTING_LOCK:
        if chat := SESSION.query(AntiChannelSettings).get(str(old_chat_id)):
            chat.chat_id = new_chat_id
            SESSION.add(chat)

        SESSION.commit()
