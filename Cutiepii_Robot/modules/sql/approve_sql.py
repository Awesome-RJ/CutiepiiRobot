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
from sqlalchemy.sql.sqltypes import BigInteger

from Cutiepii_Robot import LOGGER
from Cutiepii_Robot.modules.sql import BASE, SESSION


class Approvals(BASE):
    __tablename__ = "approval"
    chat_id = Column(String(14), primary_key=True)
    user_id = Column(BigInteger, primary_key=True)

    def __init__(self, chat_id, user_id):
        self.chat_id = str(chat_id)  # ensure string
        self.user_id = user_id

    def __repr__(self):
        return "<Approve %s>" % self.user_id


Approvals.__table__.create(checkfirst=True)

APPROVE_INSERTION_LOCK = threading.RLock()
APPROVED_USERS = {}


def approve(chat_id, user_id):
    with APPROVE_INSERTION_LOCK:
        approve_user = Approvals(str(chat_id), user_id)
        SESSION.add(approve_user)
        SESSION.commit()
        
        chat_id_str = str(chat_id)
        if chat_id_str not in APPROVED_USERS:
            APPROVED_USERS[chat_id_str] = set()
        APPROVED_USERS[chat_id_str].add(int(user_id))


def is_approved(chat_id, user_id):
    return int(user_id) in APPROVED_USERS.get(str(chat_id), set())


def disapprove(chat_id, user_id):
    with APPROVE_INSERTION_LOCK:
        disapprove_user = SESSION.query(Approvals).get((str(chat_id), user_id))
        if disapprove_user:
            SESSION.delete(disapprove_user)
            SESSION.commit()
            
            chat_id_str = str(chat_id)
            if chat_id_str in APPROVED_USERS and int(user_id) in APPROVED_USERS[chat_id_str]:
                APPROVED_USERS[chat_id_str].remove(int(user_id))
            return True
        else:
            SESSION.close()
            return False


def list_approved(chat_id):
    try:
        return (
            SESSION.query(Approvals)
            .filter(Approvals.chat_id == str(chat_id))
            .order_by(Approvals.user_id.asc())
            .all()
        )
    finally:
        SESSION.close()


def __load_approvals():
    global APPROVED_USERS
    try:
        all_approvals = SESSION.query(Approvals).all()
        for x in all_approvals:
            if x.chat_id not in APPROVED_USERS:
                APPROVED_USERS[x.chat_id] = set()
            APPROVED_USERS[x.chat_id].add(int(x.user_id))
        LOGGER.info(f"[SQL] Loaded approvals for {len(APPROVED_USERS)} chats")
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to load approvals: {e}")
        APPROVED_USERS = {}
    finally:
        SESSION.close()


try:
    __load_approvals()
except Exception as e:
    LOGGER.error(f"[SQL] Failed to initialize approvals: {e}")
