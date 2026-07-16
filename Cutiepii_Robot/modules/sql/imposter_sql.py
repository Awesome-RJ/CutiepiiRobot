from sqlalchemy import Column, String, Boolean
from sqlalchemy.sql.sqltypes import BigInteger
from Cutiepii_Robot.modules.sql import BASE, SESSION
import threading

INSERTION_LOCK = threading.RLock()

class ImposterUser(BASE):
    __tablename__ = "imposter_users"
    
    user_id = Column(BigInteger, primary_key=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    username = Column(String(255))

    def __init__(self, user_id, first_name, last_name, username):
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username

class ImposterChat(BASE):
    __tablename__ = "imposter_chats"
    
    chat_id = Column(BigInteger, primary_key=True)
    enabled = Column(Boolean, default=False)

    def __init__(self, chat_id, enabled=True):
        self.chat_id = chat_id
        self.enabled = enabled

ImposterUser.__table__.create(checkfirst=True)
ImposterChat.__table__.create(checkfirst=True)

def is_imposter_enabled(chat_id: int) -> bool:
    try:
        chat = SESSION.query(ImposterChat).filter(ImposterChat.chat_id == chat_id).first()
        return chat.enabled if chat else False
    finally:
        SESSION.close()

def enable_imposter(chat_id: int):
    with INSERTION_LOCK:
        chat = SESSION.query(ImposterChat).filter(ImposterChat.chat_id == chat_id).first()
        if not chat:
            chat = ImposterChat(chat_id, True)
            SESSION.add(chat)
        else:
            chat.enabled = True
        SESSION.commit()

def disable_imposter(chat_id: int):
    with INSERTION_LOCK:
        chat = SESSION.query(ImposterChat).filter(ImposterChat.chat_id == chat_id).first()
        if chat:
            chat.enabled = False
            SESSION.commit()

def check_user(user_id: int, first_name: str, last_name: str, username: str):
    with INSERTION_LOCK:
        user = SESSION.query(ImposterUser).filter(ImposterUser.user_id == user_id).first()
        if not user:
            user = ImposterUser(user_id, first_name, last_name, username)
            SESSION.add(user)
            SESSION.commit()
            return None
        
        changes = []
        if user.first_name != first_name:
            changes.append(("first_name", user.first_name, first_name))
            user.first_name = first_name
        if user.last_name != last_name:
            changes.append(("last_name", user.last_name, last_name))
            user.last_name = last_name
        if user.username != username:
            changes.append(("username", user.username, username))
            user.username = username
            
        if changes:
            SESSION.commit()
            return changes
        return None
