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
from sqlalchemy import Column, String, UnicodeText


class BlacklistUsers(BASE):
    __tablename__ = "blacklistusers"
    user_id = Column(String(14), primary_key=True)
    reason = Column(UnicodeText)

    def __init__(self, user_id, reason=None):
        self.user_id = user_id
        self.reason = reason


BlacklistUsers.__table__.create(checkfirst=True)

BLACKLIST_LOCK = threading.RLock()
BLACKLIST_USERS = set()


def blacklist_user(user_id, reason=None):
    with BLACKLIST_LOCK:
        user = SESSION.query(BlacklistUsers).get(str(user_id))
        if not user:
            user = BlacklistUsers(str(user_id), reason)
        else:
            user.reason = reason

        SESSION.add(user)
        SESSION.commit()
        __load_blacklist_userid_list()


def unblacklist_user(user_id):
    with BLACKLIST_LOCK:
        if user := SESSION.query(BlacklistUsers).get(str(user_id)):
            SESSION.delete(user)

        SESSION.commit()
        __load_blacklist_userid_list()


def get_reason(user_id):
    if user := SESSION.query(BlacklistUsers).get(str(user_id)):
        rep = user.reason
    else:
        rep = ""
    SESSION.close()
    return rep


def is_user_blacklisted(user_id):
    return user_id in BLACKLIST_USERS


def __load_blacklist_userid_list():
    global BLACKLIST_USERS
    try:
        BLACKLIST_USERS = {
            int(x.user_id)
            for x in SESSION.query(BlacklistUsers).all()
        }
    finally:
        SESSION.close()


__load_blacklist_userid_list()
