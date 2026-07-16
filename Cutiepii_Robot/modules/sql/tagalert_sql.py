"""
BSD 2-Clause License
Tag Alert SQL Module - Replaces Redis tag alerts
"""

from sqlalchemy import Column, Boolean, Integer
from sqlalchemy.sql.sqltypes import BigInteger
from Cutiepii_Robot.modules.sql import BASE, SESSION
import threading

INSERTION_LOCK = threading.RLock()


class TagAlert(BASE):
    __tablename__ = "tag_alerts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False)
    
    def __init__(self, chat_id, user_id):
        self.chat_id = chat_id
        self.user_id = user_id
    
    def __repr__(self):
        return f"<TagAlert(chat={self.chat_id}, user={self.user_id})>"


TagAlert.__table__.create(checkfirst=True)


def is_tag_alert_enabled(chat_id: int, user_id: int) -> bool:
    """Check if user has tag alerts enabled in a chat"""
    try:
        return bool(SESSION.query(TagAlert).filter(
            TagAlert.chat_id == chat_id,
            TagAlert.user_id == user_id
        ).first())
    finally:
        SESSION.close()


def enable_tag_alert(chat_id: int, user_id: int):
    """Enable tag alerts for a user in a chat"""
    with INSERTION_LOCK:
        exists = SESSION.query(TagAlert).filter(
            TagAlert.chat_id == chat_id,
            TagAlert.user_id == user_id
        ).first()
        
        if not exists:
            alert = TagAlert(chat_id, user_id)
            SESSION.add(alert)
            SESSION.commit()


def disable_tag_alert(chat_id: int, user_id: int):
    """Disable tag alerts for a user in a chat"""
    with INSERTION_LOCK:
        SESSION.query(TagAlert).filter(
            TagAlert.chat_id == chat_id,
            TagAlert.user_id == user_id
        ).delete()
        SESSION.commit()


def get_tag_alert_users(chat_id: int) -> set:
    """Get all users with tag alerts enabled in a chat"""
    try:
        users = SESSION.query(TagAlert).filter(
            TagAlert.chat_id == chat_id
        ).all()
        return {user.user_id for user in users}
    finally:
        SESSION.close()


def get_user_tag_chats(user_id: int) -> set:
    """Get all chats where user has tag alerts enabled"""
    try:
        chats = SESSION.query(TagAlert).filter(
            TagAlert.user_id == user_id
        ).all()
        return {chat.chat_id for chat in chats}
    finally:
        SESSION.close()
