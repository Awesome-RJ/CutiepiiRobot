"""
BSD 2-Clause License
Confession SQL Module
"""

from sqlalchemy import Column, String, Integer, DateTime, UniqueConstraint, Boolean
from sqlalchemy.sql.sqltypes import BigInteger
from Cutiepii_Robot.modules.sql import BASE, SESSION
from datetime import datetime
import threading

INSERTION_LOCK = threading.RLock()


class Confessions(BASE):
    __tablename__ = "confessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(BigInteger, nullable=False)
    receiver_id = Column(BigInteger, nullable=False)
    sent_message_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_revealed = Column(Boolean, default=False)

    def __init__(self, sender_id, receiver_id, sent_message_id=None):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.sent_message_id = sent_message_id
        self.timestamp = datetime.utcnow()
        self.is_revealed = False

    def __repr__(self):
        return f"<Confession(id={self.id}, sender={self.sender_id}, receiver={self.receiver_id})>"


class ConfessionBlocks(BASE):
    __tablename__ = "confession_blocks"

    chat_id = Column(BigInteger, primary_key=True)

    def __init__(self, chat_id):
        self.chat_id = chat_id

    def __repr__(self):
        return f"<ConfessionBlock(chat_id={self.chat_id})>"


class ConfessionStrikes(BASE):
    __tablename__ = "confession_strikes"

    user_id = Column(BigInteger, primary_key=True)
    strikes = Column(Integer, default=0)

    def __init__(self, user_id, strikes=0):
        self.user_id = user_id
        self.strikes = strikes

    def __repr__(self):
        return f"<ConfessionStrikes(user_id={self.user_id}, strikes={self.strikes})>"


Confessions.__table__.create(checkfirst=True)
ConfessionBlocks.__table__.create(checkfirst=True)
ConfessionStrikes.__table__.create(checkfirst=True)


def add_confession(sender_id: int, receiver_id: int, sent_message_id: int = None) -> int:
    with INSERTION_LOCK:
        conf = Confessions(sender_id, receiver_id, sent_message_id)
        SESSION.add(conf)
        SESSION.commit()
        return conf.id


def get_confession(confession_id: int) -> Confessions:
    try:
        return SESSION.query(Confessions).filter(Confessions.id == confession_id).first()
    finally:
        SESSION.close()


def update_confession_message(confession_id: int, sent_message_id: int):
    with INSERTION_LOCK:
        conf = SESSION.query(Confessions).filter(Confessions.id == confession_id).first()
        if conf:
            conf.sent_message_id = sent_message_id
            SESSION.commit()


def reveal_confession(confession_id: int) -> bool:
    with INSERTION_LOCK:
        conf = SESSION.query(Confessions).filter(Confessions.id == confession_id).first()
        if conf:
            conf.is_revealed = True
            SESSION.commit()
            return True
        return False


def block_confessions(chat_id: int) -> bool:
    with INSERTION_LOCK:
        exists = SESSION.query(ConfessionBlocks).filter(ConfessionBlocks.chat_id == chat_id).first()
        if exists:
            return False
        block = ConfessionBlocks(chat_id)
        SESSION.add(block)
        SESSION.commit()
        return True


def unblock_confessions(chat_id: int) -> bool:
    with INSERTION_LOCK:
        block = SESSION.query(ConfessionBlocks).filter(ConfessionBlocks.chat_id == chat_id).first()
        if block:
            SESSION.delete(block)
            SESSION.commit()
            return True
        return False


def is_confessions_blocked(chat_id: int) -> bool:
    try:
        exists = SESSION.query(ConfessionBlocks).filter(ConfessionBlocks.chat_id == chat_id).first()
        return exists is not None
    finally:
        SESSION.close()


def add_strike(user_id: int) -> int:
    with INSERTION_LOCK:
        strike = SESSION.query(ConfessionStrikes).filter(ConfessionStrikes.user_id == user_id).first()
        if strike:
            strike.strikes += 1
        else:
            strike = ConfessionStrikes(user_id, strikes=1)
            SESSION.add(strike)
        SESSION.commit()
        return strike.strikes


def get_strikes(user_id: int) -> int:
    try:
        strike = SESSION.query(ConfessionStrikes).filter(ConfessionStrikes.user_id == user_id).first()
        return strike.strikes if strike else 0
    finally:
        SESSION.close()


def reset_strikes(user_id: int) -> bool:
    with INSERTION_LOCK:
        strike = SESSION.query(ConfessionStrikes).filter(ConfessionStrikes.user_id == user_id).first()
        if strike:
            strike.strikes = 0
            SESSION.commit()
            return True
        return False
