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
from typing import Union

from Cutiepii_Robot.modules.sql import BASE, SESSION
from sqlalchemy.sql.sqltypes import BigInteger
from sqlalchemy import Boolean, Column, String


class ReportingUserSettings(BASE):
    __tablename__ = "user_report_settings"
    user_id = Column(BigInteger, primary_key=True)
    should_report = Column(Boolean, default=True)

    def __init__(self, user_id):
        self.user_id = user_id

    def __repr__(self):
        return f"<User report settings ({self.user_id})>"


class ReportingChatSettings(BASE):
    __tablename__ = "chat_report_settings"
    chat_id = Column(String(14), primary_key=True)
    should_report = Column(Boolean, default=True)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)

    def __repr__(self):
        return f"<Chat report settings ({self.chat_id})>"


ReportingUserSettings.__table__.create(checkfirst=True)
ReportingChatSettings.__table__.create(checkfirst=True)

CHAT_LOCK = threading.RLock()
USER_LOCK = threading.RLock()


def chat_should_report(chat_id: Union[str, int]) -> bool:
    try:
        if chat_setting := SESSION.query(ReportingChatSettings).get(
                str(chat_id)):
            return chat_setting.should_report
        return False
    finally:
        SESSION.close()


def user_should_report(user_id: int) -> bool:
    try:
        if user_setting := SESSION.query(ReportingUserSettings).get(user_id):
            return user_setting.should_report
        return True
    finally:
        SESSION.close()


def set_chat_setting(chat_id: Union[int, str], setting: bool):
    with CHAT_LOCK:
        chat_setting = SESSION.query(ReportingChatSettings).get(str(chat_id))
        if not chat_setting:
            chat_setting = ReportingChatSettings(chat_id)

        chat_setting.should_report = setting
        SESSION.add(chat_setting)
        SESSION.commit()


def set_user_setting(user_id: int, setting: bool):
    with USER_LOCK:
        user_setting = SESSION.query(ReportingUserSettings).get(user_id)
        if not user_setting:
            user_setting = ReportingUserSettings(user_id)

        user_setting.should_report = setting
        SESSION.add(user_setting)
        SESSION.commit()


def migrate_chat(old_chat_id, new_chat_id):
    with CHAT_LOCK:
        chat_notes = (SESSION.query(ReportingChatSettings).filter(
            ReportingChatSettings.chat_id == str(old_chat_id)).all())
        for note in chat_notes:
            note.chat_id = str(new_chat_id)
        SESSION.commit()
