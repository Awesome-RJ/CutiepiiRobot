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
from sqlalchemy.sql.sqltypes import BigInteger

from Cutiepii_Robot.modules.sql import BASE, SESSION


class Mods(BASE):
    __tablename__ = "moderators"
    chat_id = Column(String(14), primary_key=True)
    user_id = Column(BigInteger, primary_key=True)

    def __init__(self, chat_id, user_id):
        self.chat_id = str(chat_id)  # ensure string
        self.user_id = user_id

    def __repr__(self):
        return f"<Mod {self.user_id}>"


Mods.__table__.create(checkfirst=True)

MOD_INSERTION_LOCK = threading.RLock()


def mod(chat_id, user_id):
    with MOD_INSERTION_LOCK:
        mod_user = Mods(str(chat_id), user_id)
        SESSION.add(mod_user)
        SESSION.commit()


def is_modd(chat_id, user_id):
    try:
        return SESSION.query(Mods).get((str(chat_id), user_id))
    finally:
        SESSION.close()


def dismod(chat_id, user_id):
    with MOD_INSERTION_LOCK:
        if dismod_user := SESSION.query(Mods).get((str(chat_id), user_id)):
            SESSION.delete(dismod_user)
            SESSION.commit()
            return True
        SESSION.close()
        return False


def list_modd(chat_id):
    try:
        return (SESSION.query(Mods).filter(
            Mods.chat_id == str(chat_id)).order_by(Mods.user_id.asc()).all())
    finally:
        SESSION.close()
