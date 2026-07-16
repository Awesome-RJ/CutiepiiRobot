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

from sqlalchemy import Column, String, BigInteger, Integer
from Cutiepii_Robot.modules.sql import BASE, SESSION
import threading


class ReactionAnalytics(BASE):
    __tablename__ = "reaction_analytics"
    chat_id = Column(BigInteger, primary_key=True)
    emoji = Column(String(50), primary_key=True)
    count = Column(Integer, default=0)

    def __init__(self, chat_id, emoji, count=1):
        self.chat_id = chat_id
        self.emoji = emoji
        self.count = count


ReactionAnalytics.__table__.create(checkfirst=True)

REACTION_LOCK = threading.RLock()


def log_reaction(chat_id, emoji):
    with REACTION_LOCK:
        react = SESSION.query(ReactionAnalytics).filter(ReactionAnalytics.chat_id == chat_id, ReactionAnalytics.emoji == emoji).first()
        if not react:
            react = ReactionAnalytics(chat_id, emoji, 1)
            SESSION.add(react)
        else:
            react.count += 1
        SESSION.commit()


def get_reactions_by_chat(chat_id, limit=5):
    try:
        return SESSION.query(ReactionAnalytics).filter(ReactionAnalytics.chat_id == chat_id).order_by(ReactionAnalytics.count.desc()).limit(limit).all()
    finally:
        SESSION.close()
