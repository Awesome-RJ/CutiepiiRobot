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

import datetime
import threading
from sqlalchemy import Column, String, BigInteger, DateTime
from Cutiepii_Robot.modules.sql import BASE, SESSION


class EventsInfo(BASE):
    __tablename__ = "events_info"
    event_key = Column(String(100), primary_key=True)
    creator_id = Column(BigInteger)
    status = Column(String(20), default="active")  # active, ended
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, event_key, creator_id):
        self.event_key = event_key.lower().strip()
        self.creator_id = creator_id


class EventParticipants(BASE):
    __tablename__ = "event_participants"
    event_key = Column(String(100), primary_key=True)
    user_id = Column(BigInteger, primary_key=True)
    joined_at = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, event_key, user_id):
        self.event_key = event_key.lower().strip()
        self.user_id = user_id


EventsInfo.__table__.create(checkfirst=True)
EventParticipants.__table__.create(checkfirst=True)

EVENTS_LOCK = threading.RLock()


def create_event(event_key, creator_id):
    with EVENTS_LOCK:
        event = EventsInfo(event_key, creator_id)
        SESSION.merge(event)
        SESSION.commit()


def end_event(event_key):
    with EVENTS_LOCK:
        event = SESSION.query(EventsInfo).get(event_key.lower().strip())
        if event:
            event.status = "ended"
            SESSION.commit()
            return True
        return False


def get_active_events():
    try:
        return SESSION.query(EventsInfo).filter(EventsInfo.status == "active").all()
    finally:
        SESSION.close()


def get_recent_history(limit=5):
    try:
        return SESSION.query(EventsInfo).filter(EventsInfo.status == "ended").order_by(EventsInfo.created_at.desc()).limit(limit).all()
    finally:
        SESSION.close()


def join_event(event_key, user_id):
    with EVENTS_LOCK:
        event = SESSION.query(EventsInfo).get(event_key.lower().strip())
        if not event or event.status != "active":
            return False, "This event is not active or does not exist."

        # Check if already joined
        exists = SESSION.query(EventParticipants).get((event_key.lower().strip(), user_id))
        if exists:
            return False, "You have already joined this event!"

        participant = EventParticipants(event_key, user_id)
        SESSION.add(participant)
        SESSION.commit()
        return True, "Success"


def get_event_participants(event_key):
    try:
        return SESSION.query(EventParticipants).filter(EventParticipants.event_key == event_key.lower().strip()).all()
    finally:
        SESSION.close()
