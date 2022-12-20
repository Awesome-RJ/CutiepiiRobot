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
import time

from Cutiepii_Robot.modules.sql import BASE, SESSION
from sqlalchemy import Column, Integer, String, UnicodeText
from sqlalchemy.sql.sqltypes import BigInteger


class Reminds(BASE):
    __tablename__ = "reminds"
    chat_id = Column(String(14), primary_key=True)
    time_seconds = Column(Integer, primary_key=True)
    remind_message = Column(UnicodeText, default="")
    user_id = Column(BigInteger, default=0)

    def __init__(self, chat_id, time_seconds):
        self.chat_id = str(chat_id)
        self.time_seconds = int(time_seconds)

    def __repr__(self):
        return f"<remind in {self.chat_id} for time {self.time_seconds}>"


# Reminds.__table__.drop()
Reminds.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()

REMINDERS = {}


def set_remind(chat_id, time_sec, remind_message, user_id):
    with INSERTION_LOCK:
        reminds = SESSION.query(Reminds).get((str(chat_id), time_sec))
        if not reminds:
            reminds = Reminds(chat_id, time_sec)
        reminds.remind_message = remind_message
        reminds.user_id = user_id
        SESSION.add(reminds)
        SESSION.commit()
        if time_sec not in REMINDERS:
            REMINDERS[time_sec] = []
        REMINDERS[time_sec].append({
            "chat_id": str(chat_id),
            "message": remind_message,
            "user_id": user_id
        })


def rem_remind(chat_id, time_sec, remind_message, user_id):
    with INSERTION_LOCK:
        if reminds := SESSION.query(Reminds).get((str(chat_id), time_sec)):
            SESSION.delete(reminds)
            SESSION.commit()
            REMINDERS[time_sec].remove({
                "chat_id": str(chat_id),
                "message": remind_message,
                "user_id": user_id
            })
            return True
        SESSION.close()
        return False


def get_remind_in_chat(chat_id, timestamp):
    return (SESSION.query(Reminds).filter(
        Reminds.chat_id == str(chat_id),
        Reminds.time_seconds == timestamp).first())


def num_reminds_in_chat(chat_id):
    return (SESSION.query(Reminds).filter(
        Reminds.chat_id == str(chat_id)).count())


def get_reminds_in_chat(chat_id):
    try:
        return (SESSION.query(Reminds).filter(
            Reminds.chat_id == str(chat_id)).order_by(
                Reminds.time_seconds.asc()).all())
    finally:
        SESSION.close()


def __get_all_reminds():
    try:
        chats = SESSION.query(Reminds).all()
        for chat in chats:
            if (chat.time_seconds <= round(time.time())) or chat.user_id == 0:
                try:
                    rem_remind(chat.chat_id, chat.time_seconds,
                               chat.remind_message, chat.user_id)
                except:
                    pass
                continue
            REMINDERS[chat.time_seconds] = [{
                "chat_id": chat.chat_id,
                "message": chat.remind_message,
                "user_id": chat.user_id
            }]
    finally:
        SESSION.close()


__get_all_reminds()
