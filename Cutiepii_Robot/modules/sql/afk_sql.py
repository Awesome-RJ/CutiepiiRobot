"""
BSD 2-Clause License
AFK SQL Module - Replaces afk_redis.py
Enhanced with better tracking and history
"""

from sqlalchemy import Column, String, BigInteger, UnicodeText, DateTime, Boolean
from sqlalchemy.sql.sqltypes import BigInteger as BigInt
from Cutiepii_Robot.modules.sql import BASE, SESSION
from datetime import datetime, timezone
import threading

INSERTION_LOCK = threading.RLock()


class AFKSettings(BASE):
    __tablename__ = "afk_settings"
    
    chat_id = Column(String(14), primary_key=True)
    auto_delete = Column(Boolean, default=True, nullable=False)
    
    def __init__(self, chat_id: int, auto_delete: bool = True):
        self.chat_id = str(chat_id)
        self.auto_delete = auto_delete


AFKSettings.__table__.create(checkfirst=True)


class AFK(BASE):
    __tablename__ = "afk"
    
    user_id = Column(BigInt, primary_key=True)
    reason = Column(UnicodeText, default="")
    time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __init__(self, user_id, reason=""):
        self.user_id = user_id
        self.reason = reason
        self.time = datetime.now(timezone.utc)
    
    def __repr__(self):
        return f"<AFK(user={self.user_id}, reason={self.reason[:20]})>"


AFK.__table__.create(checkfirst=True)


def is_afk(user_id: int) -> bool:
    """Check if user is AFK"""
    try:
        return bool(SESSION.query(AFK).filter(AFK.user_id == user_id).first())
    finally:
        SESSION.close()


def set_afk(user_id: int, reason: str = ""):
    """Set user as AFK"""
    with INSERTION_LOCK:
        afk = SESSION.query(AFK).filter(AFK.user_id == user_id).first()
        
        if afk:
            afk.reason = reason
            afk.time = datetime.now(timezone.utc)
        else:
            afk = AFK(user_id, reason)
            SESSION.add(afk)
        
        SESSION.commit()


def get_afk_reason(user_id: int) -> str:
    """Get AFK reason"""
    try:
        afk = SESSION.query(AFK).filter(AFK.user_id == user_id).first()
        return afk.reason if afk else ""
    finally:
        SESSION.close()


def get_afk_time(user_id: int) -> datetime:
    """Get when user went AFK"""
    try:
        afk = SESSION.query(AFK).filter(AFK.user_id == user_id).first()
        return afk.time if afk else None
    finally:
        SESSION.close()


def remove_afk(user_id: int) -> bool:
    """Remove AFK status"""
    with INSERTION_LOCK:
        afk = SESSION.query(AFK).filter(AFK.user_id == user_id).first()
        if afk:
            SESSION.delete(afk)
            SESSION.commit()
            return True
        return False


def check_afk_status(user_id: int):
    try:
        return SESSION.query(AFK).filter(AFK.user_id == user_id).first()
    finally:
        SESSION.close()


# Aliases for compatibility
start_afk = set_afk
afk_reason = get_afk_reason
end_afk = remove_afk
is_user_afk = is_afk
rm_afk = remove_afk


def is_afk_delete(chat_id: int) -> bool:
    """Check if AFK auto-delete is enabled for the group (default True)"""
    try:
        setting = SESSION.query(AFKSettings).filter(AFKSettings.chat_id == str(chat_id)).first()
        return setting.auto_delete if setting else True
    except Exception:
        return True
    finally:
        SESSION.close()


def set_afk_delete(chat_id: int, status: bool):
    """Enable or disable AFK auto-delete for the group"""
    with INSERTION_LOCK:
        setting = SESSION.query(AFKSettings).filter(AFKSettings.chat_id == str(chat_id)).first()
        if setting:
            setting.auto_delete = status
        else:
            setting = AFKSettings(chat_id, status)
            SESSION.add(setting)
        SESSION.commit()
