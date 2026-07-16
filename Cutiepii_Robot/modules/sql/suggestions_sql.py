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

from sqlalchemy import Column, String, BigInteger, Text, Integer
from Cutiepii_Robot.modules.sql import BASE, SESSION
import threading


class SuggestedPost(BASE):
    __tablename__ = "suggested_posts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    channel_id = Column(String(100))
    post_text = Column(Text)
    media_file_id = Column(String(255))
    media_type = Column(String(50))  # photo, video, document, etc.
    status = Column(String(20), default="pending")  # pending, approved, declined

    def __init__(self, user_id, channel_id, post_text, media_file_id=None, media_type=None):
        self.user_id = user_id
        self.channel_id = str(channel_id).strip()
        self.post_text = post_text
        self.media_file_id = media_file_id
        self.media_type = media_type


SuggestedPost.__table__.create(checkfirst=True)

SUGG_LOCK = threading.RLock()


def add_suggestion(user_id, channel_id, post_text, media_file_id=None, media_type=None):
    with SUGG_LOCK:
        sugg = SuggestedPost(user_id, channel_id, post_text, media_file_id, media_type)
        SESSION.add(sugg)
        SESSION.commit()
        return sugg.id


def get_suggestion(sugg_id):
    try:
        return SESSION.query(SuggestedPost).get(sugg_id)
    finally:
        SESSION.close()


def update_status(sugg_id, status):
    with SUGG_LOCK:
        sugg = SESSION.query(SuggestedPost).get(sugg_id)
        if sugg:
            sugg.status = status
            SESSION.commit()
            return True
        return False
