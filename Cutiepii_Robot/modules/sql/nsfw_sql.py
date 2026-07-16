"""
BSD 2-Clause License
NSFW SQL Module - Replaces nsfw_mongo.py
"""

from sqlalchemy import Column, Boolean
from sqlalchemy.sql.sqltypes import BigInteger
from Cutiepii_Robot.modules.sql import BASE, SESSION
import threading

INSERTION_LOCK = threading.RLock()


class NSFWSettings(BASE):
    __tablename__ = "nsfw_settings"
    
    chat_id = Column(BigInteger, primary_key=True)
    enabled = Column(Boolean, default=False)
    
    def __init__(self, chat_id, enabled=False):
        self.chat_id = chat_id
        self.enabled = enabled
    
    def __repr__(self):
        return f"<NSFWSettings(chat={self.chat_id}, enabled={self.enabled})>"


NSFWSettings.__table__.create(checkfirst=True)


def is_nsfw_enabled(chat_id: int) -> bool:
    """Check if NSFW filter is enabled"""
    try:
        settings = SESSION.query(NSFWSettings).filter(
            NSFWSettings.chat_id == chat_id
        ).first()
        return settings.enabled if settings else False
    finally:
        SESSION.close()


def enable_nsfw(chat_id: int):
    """Enable NSFW filter"""
    with INSERTION_LOCK:
        settings = SESSION.query(NSFWSettings).filter(
            NSFWSettings.chat_id == chat_id
        ).first()
        
        if settings:
            settings.enabled = True
        else:
            settings = NSFWSettings(chat_id, True)
            SESSION.add(settings)
        
        SESSION.commit()


def disable_nsfw(chat_id: int):
    """Disable NSFW filter"""
    with INSERTION_LOCK:
        settings = SESSION.query(NSFWSettings).filter(
            NSFWSettings.chat_id == chat_id
        ).first()
        
        if settings:
            settings.enabled = False
        else:
            settings = NSFWSettings(chat_id, False)
            SESSION.add(settings)
        
        SESSION.commit()


def get_all_nsfw_chats() -> list:
    """Get all chats with NSFW enabled"""
    try:
        return SESSION.query(NSFWSettings).filter(
            NSFWSettings.enabled == True
        ).all()
    finally:
        SESSION.close()
