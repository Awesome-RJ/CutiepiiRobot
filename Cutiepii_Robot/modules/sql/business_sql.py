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
from sqlalchemy import Column, String, BigInteger, Text
from Cutiepii_Robot.modules.sql import BASE, SESSION


class BusinessConfig(BASE):
    __tablename__ = "business_config"
    user_id = Column(BigInteger, primary_key=True)
    connection_id = Column(String(255))
    greeting = Column(Text)

    def __init__(self, user_id, connection_id=None, greeting=None):
        self.user_id = user_id
        self.connection_id = connection_id
        self.greeting = greeting


class BusinessTriggers(BASE):
    __tablename__ = "business_triggers"
    user_id = Column(BigInteger, primary_key=True)
    keyword = Column(String(255), primary_key=True)
    reply = Column(Text)

    def __init__(self, user_id, keyword, reply):
        self.user_id = user_id
        self.keyword = keyword.lower()
        self.reply = reply


BusinessConfig.__table__.create(checkfirst=True)
BusinessTriggers.__table__.create(checkfirst=True)

BIZ_LOCK = threading.RLock()


def set_business_connection(user_id, connection_id):
    with BIZ_LOCK:
        config = SESSION.query(BusinessConfig).get(user_id)
        if not config:
            config = BusinessConfig(user_id, connection_id=connection_id)
            SESSION.add(config)
        else:
            config.connection_id = connection_id
        SESSION.commit()


def remove_business_connection(connection_id):
    with BIZ_LOCK:
        config = SESSION.query(BusinessConfig).filter(BusinessConfig.connection_id == connection_id).first()
        if config:
            SESSION.delete(config)
            SESSION.commit()


def get_business_connection(user_id):
    try:
        config = SESSION.query(BusinessConfig).get(user_id)
        return config.connection_id if config else None
    finally:
        SESSION.close()


def set_biz_greeting(user_id, greeting):
    with BIZ_LOCK:
        config = SESSION.query(BusinessConfig).get(user_id)
        if not config:
            config = BusinessConfig(user_id, greeting=greeting)
            SESSION.add(config)
        else:
            config.greeting = greeting
        SESSION.commit()


def get_biz_greeting(user_id):
    try:
        config = SESSION.query(BusinessConfig).get(user_id)
        return config.greeting if config else None
    finally:
        SESSION.close()


def add_biz_trigger(user_id, keyword, reply):
    with BIZ_LOCK:
        trigger = BusinessTriggers(user_id, keyword.lower(), reply)
        SESSION.merge(trigger)
        SESSION.commit()


def remove_biz_trigger(user_id, keyword):
    with BIZ_LOCK:
        trigger = SESSION.query(BusinessTriggers).get((user_id, keyword.lower()))
        if trigger:
            SESSION.delete(trigger)
            SESSION.commit()
            return True
        return False


def get_biz_triggers(user_id):
    try:
        return SESSION.query(BusinessTriggers).filter(BusinessTriggers.user_id == user_id).all()
    finally:
        SESSION.close()


def match_biz_trigger(user_id, text):
    try:
        triggers = SESSION.query(BusinessTriggers).filter(BusinessTriggers.user_id == user_id).all()
        text_lower = text.lower()
        for t in triggers:
            if t.keyword in text_lower:
                return t.reply
        return None
    finally:
        SESSION.close()
