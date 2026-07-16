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

from sqlalchemy import Column, String, BigInteger, Integer, DateTime
import datetime
from Cutiepii_Robot.modules.sql import BASE, SESSION
import threading


class StoryLog(BASE):
    __tablename__ = "story_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    story_id = Column(String(50))
    action = Column(String(20))  # view, like, interaction
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, user_id, story_id, action="view"):
        self.user_id = user_id
        self.story_id = story_id
        self.action = action


StoryLog.__table__.create(checkfirst=True)

STORY_LOCK = threading.RLock()


def log_story_action(user_id, story_id, action="view"):
    with STORY_LOCK:
        log = StoryLog(user_id, story_id, action)
        SESSION.add(log)
        SESSION.commit()


def get_story_stats(story_id):
    try:
        views = SESSION.query(StoryLog).filter(StoryLog.story_id == story_id, StoryLog.action == "view").count()
        likes = SESSION.query(StoryLog).filter(StoryLog.story_id == story_id, StoryLog.action == "like").count()
        return {"views": views, "likes": likes}
    finally:
        SESSION.close()
