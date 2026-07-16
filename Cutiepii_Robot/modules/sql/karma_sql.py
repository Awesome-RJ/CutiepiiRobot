"""
BSD 2-Clause License
Karma SQL Module - Replaces karma_mongo.py
"""

from sqlalchemy import Column, String, BigInteger, Integer, Boolean, UnicodeText
from sqlalchemy.sql.sqltypes import BigInteger as BigInt
from Cutiepii_Robot.modules.sql import BASE, SESSION
from typing import Dict, Optional
import threading

INSERTION_LOCK = threading.RLock()


class Karma(BASE):
    __tablename__ = "karma"
    
    chat_id = Column(BigInt, primary_key=True)
    user_id = Column(BigInt, primary_key=True)
    karma = Column(Integer, default=0)
    
    def __init__(self, chat_id, user_id, karma=0):
        self.chat_id = chat_id
        self.user_id = user_id
        self.karma = karma
    
    def __repr__(self):
        return f"<Karma(chat={self.chat_id}, user={self.user_id}, karma={self.karma})>"


class KarmaSettings(BASE):
    __tablename__ = "karma_settings"
    
    chat_id = Column(BigInt, primary_key=True)
    karma_enabled = Column(Boolean, default=True)
    
    def __init__(self, chat_id, karma_enabled=True):
        self.chat_id = chat_id
        self.karma_enabled = karma_enabled


Karma.__table__.create(checkfirst=True)
KarmaSettings.__table__.create(checkfirst=True)


def get_karma(chat_id: int, user_id: int) -> int:
    """Get karma for a user in a chat"""
    try:
        karma = SESSION.query(Karma).filter(
            Karma.chat_id == chat_id,
            Karma.user_id == user_id
        ).first()
        return karma.karma if karma else 0
    finally:
        SESSION.close()


def update_karma(chat_id: int, user_id: int, karma_change: int) -> int:
    """Update karma for a user"""
    with INSERTION_LOCK:
        karma = SESSION.query(Karma).filter(
            Karma.chat_id == chat_id,
            Karma.user_id == user_id
        ).first()
        
        if karma:
            karma.karma += karma_change
        else:
            karma = Karma(chat_id, user_id, karma_change)
            SESSION.add(karma)
        
        SESSION.commit()
        return karma.karma


def set_karma(chat_id: int, user_id: int, karma_value: int):
    """Set karma to specific value"""
    with INSERTION_LOCK:
        karma = SESSION.query(Karma).filter(
            Karma.chat_id == chat_id,
            Karma.user_id == user_id
        ).first()
        
        if karma:
            karma.karma = karma_value
        else:
            karma = Karma(chat_id, user_id, karma_value)
            SESSION.add(karma)
        
        SESSION.commit()


def get_top_karma(chat_id: int, limit: int = 10) -> list:
    """Get top karma users in a chat"""
    try:
        return SESSION.query(Karma).filter(
            Karma.chat_id == chat_id,
            Karma.karma > 0
        ).order_by(Karma.karma.desc()).limit(limit).all()
    finally:
        SESSION.close()


def get_bottom_karma(chat_id: int, limit: int = 10) -> list:
    """Get bottom karma users in a chat"""
    try:
        return SESSION.query(Karma).filter(
            Karma.chat_id == chat_id,
            Karma.karma < 0
        ).order_by(Karma.karma.asc()).limit(limit).all()
    finally:
        SESSION.close()


def get_global_karma(user_id: int) -> int:
    """Get total karma across all chats"""
    try:
        total = SESSION.query(Karma).filter(
            Karma.user_id == user_id
        ).with_entities(
            Karma.karma
        ).all()
        return sum(k[0] for k in total if k[0] > 0)
    finally:
        SESSION.close()


def get_karma_stats() -> Dict[str, int]:
    """Get karma statistics"""
    try:
        chats = SESSION.query(Karma.chat_id).distinct().count()
        total_karma = SESSION.query(Karma).filter(Karma.karma > 0).count()
        return {"chats_count": chats, "karmas_count": total_karma}
    finally:
        SESSION.close()


def is_karma_enabled(chat_id: int) -> bool:
    """Check if karma is enabled in a chat"""
    try:
        settings = SESSION.query(KarmaSettings).filter(
            KarmaSettings.chat_id == chat_id
        ).first()
        return settings.karma_enabled if settings else True
    finally:
        SESSION.close()


def enable_karma(chat_id: int):
    """Enable karma in a chat"""
    with INSERTION_LOCK:
        settings = SESSION.query(KarmaSettings).filter(
            KarmaSettings.chat_id == chat_id
        ).first()
        
        if settings:
            settings.karma_enabled = True
        else:
            settings = KarmaSettings(chat_id, True)
            SESSION.add(settings)
        
        SESSION.commit()


def disable_karma(chat_id: int):
    """Disable karma in a chat"""
    with INSERTION_LOCK:
        settings = SESSION.query(KarmaSettings).filter(
            KarmaSettings.chat_id == chat_id
        ).first()
        
        if settings:
            settings.karma_enabled = False
        else:
            settings = KarmaSettings(chat_id, False)
            SESSION.add(settings)
        
        SESSION.commit()
