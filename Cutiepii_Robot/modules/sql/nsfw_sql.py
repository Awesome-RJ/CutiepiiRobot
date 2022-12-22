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

from sqlalchemy import Column, String
from Cutiepii_Robot.modules.sql import BASE, SESSION


#   |----------------------------------|
#   |  Test Module by @EverythingSuckz |
#   |        Kang with Credits         |
#   |----------------------------------|
class NSFWChats(BASE):
    __tablename__ = "nsfw_chats"
    chat_id = Column(String(14), primary_key=True)

    def __init__(self, chat_id):
        self.chat_id = chat_id


NSFWChats.__table__.create(checkfirst=True)
INSERTION_LOCK = threading.RLock()


def is_nsfw(chat_id):
    try:
        chat = SESSION.query(NSFWChats).get(str(chat_id))
        return bool(chat)
    finally:
        SESSION.close()


def set_nsfw(chat_id):
    with INSERTION_LOCK:
        nsfwchat = SESSION.query(NSFWChats).get(str(chat_id))
        if not nsfwchat:
            nsfwchat = NSFWChats(str(chat_id))
        SESSION.add(nsfwchat)
        SESSION.commit()


def rem_nsfw(chat_id):
    with INSERTION_LOCK:
        if nsfwchat := SESSION.query(NSFWChats).get(str(chat_id)):
            SESSION.delete(nsfwchat)
        SESSION.commit()


def get_all_nsfw_chats():
    try:
        return SESSION.query(NSFWChats.chat_id).all()
    finally:
        SESSION.close()
