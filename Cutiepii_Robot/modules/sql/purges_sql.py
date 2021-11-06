"""
MIT License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021 Awesome-RJ
Copyright (c) 2021, Yūki • Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

This file is part of @Cutiepii_Robot (Telegram Bot)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is

furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
#Purges_SQL for /purgefrom & /purgeto

import threading

from Cutiepii_Robot.modules.sql import BASE, SESSION
from sqlalchemy import (Column, Integer, String)


class Purges(BASE):
    __tablename__ = "purges"
    chat_id = Column(String(14), primary_key=True)
    message_from = Column(Integer, primary_key=True)


    def __init__(self, chat_id, message_from):
        self.chat_id = str(chat_id)  # ensure string
        self.message_from = message_from


    def __repr__(self):
        return "<Purges %s>" % self.chat_id


Purges.__table__.create(checkfirst=True)

PURGES_INSERTION_LOCK = threading.RLock()

def purgefrom(chat_id, message_from):
    with PURGES_INSERTION_LOCK:
        note = Purges(str(chat_id), message_from)
        SESSION.add(note)
        SESSION.commit()

def is_purgefrom(chat_id, message_from):
    try:
        return SESSION.query(Purges).get((str(chat_id), message_from))
    finally:
        SESSION.close()

def clear_purgefrom(chat_id, message_from):
    with PURGES_INSERTION_LOCK:
        note = SESSION.query(Purges).get((str(chat_id), message_from))
        if note:
            SESSION.delete(note)
            SESSION.commit()
            return True
        else:
            SESSION.close()
            return False

def show_purgefrom(chat_id):
    try:
        return SESSION.query(Purges).filter(Purges.chat_id == str(chat_id)).order_by(Purges.message_from.asc()).all()
    finally:
        SESSION.close()
