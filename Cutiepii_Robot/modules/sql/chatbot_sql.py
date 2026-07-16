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

import threading

from sqlalchemy import Column, String
from Cutiepii_Robot.modules.sql import BASE, SESSION

class CutiepiiChats(BASE):
    __tablename__ = "cutiepii_chats"
    chat_id = Column(String(14), primary_key=True)

    def __init__(self, chat_id):
        self.chat_id = chat_id

CutiepiiChats.__table__.create(checkfirst=True)
INSERTION_LOCK = threading.RLock()


# Migration from old kuki_chats table to cutiepii_chats table if it exists
def migrate_kuki_to_cutiepii():
    try:
        from sqlalchemy import inspect, text
        with INSERTION_LOCK:
            engine = SESSION.bind
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            if "kuki_chats" in tables:
                # Retrieve all chat_ids from kuki_chats
                result = SESSION.execute(text("SELECT chat_id FROM kuki_chats")).fetchall()
                if result:
                    for row in result:
                        chat_id = row[0]
                        # Check if it already exists in cutiepii_chats
                        existing = SESSION.query(CutiepiiChats).get(str(chat_id))
                        if not existing:
                            SESSION.add(CutiepiiChats(str(chat_id)))
                    SESSION.commit()
    except Exception:
        SESSION.rollback()
    finally:
        SESSION.close()

migrate_kuki_to_cutiepii()


def is_cutiepii(chat_id):
    try:
        chat = SESSION.query(CutiepiiChats).get(str(chat_id))
        return bool(chat)
    finally:
        SESSION.close()

def set_cutiepii(chat_id):
    with INSERTION_LOCK:
        cutiepiichat = SESSION.query(CutiepiiChats).get(str(chat_id))
        if not cutiepiichat:
            cutiepiichat = CutiepiiChats(str(chat_id))
        SESSION.add(cutiepiichat)
        SESSION.commit()

def rem_cutiepii(chat_id):
    with INSERTION_LOCK:
        cutiepiichat = SESSION.query(CutiepiiChats).get(str(chat_id))
        if cutiepiichat:
            SESSION.delete(cutiepiichat)
        SESSION.commit()


def get_all_cutiepii_chats():
    try:
        return SESSION.query(CutiepiiChats.chat_id).all()
    finally:
        SESSION.close()
