"""
SQL Module for Language Preferences
Stores user and chat language preferences
"""

from sqlalchemy import Column, String, BigInteger
from Cutiepii_Robot.modules.sql import BASE, SESSION


class ChatLang(BASE):
    """Chat language preference."""
    
    __tablename__ = "chat_lang"
    
    chat_id = Column(BigInteger, primary_key=True)
    lang_code = Column(String(10), nullable=False, default="en")
    
    def __init__(self, chat_id: int, lang_code: str = "en"):
        self.chat_id = chat_id
        self.lang_code = lang_code
    
    def __repr__(self):
        return f"<ChatLang(chat_id={self.chat_id}, lang_code={self.lang_code})>"


class UserLang(BASE):
    """User language preference."""
    
    __tablename__ = "user_lang"
    
    user_id = Column(BigInteger, primary_key=True)
    lang_code = Column(String(10), nullable=False, default="en")
    
    def __init__(self, user_id: int, lang_code: str = "en"):
        self.user_id = user_id
        self.lang_code = lang_code
    
    def __repr__(self):
        return f"<UserLang(user_id={self.user_id}, lang_code={self.lang_code})>"


ChatLang.__table__.create(checkfirst=True)
UserLang.__table__.create(checkfirst=True)


# Caches
CHAT_LANG_CACHE = {}
USER_LANG_CACHE = {}


def set_chat_lang(chat_id: int, lang_code: str):
    """Set language for a chat."""
    CHAT_LANG_CACHE[chat_id] = lang_code
    try:
        chat_lang = SESSION.query(ChatLang).get(chat_id)
        if chat_lang:
            chat_lang.lang_code = lang_code
        else:
            chat_lang = ChatLang(chat_id, lang_code)
            SESSION.add(chat_lang)
        SESSION.commit()
    except Exception as e:
        SESSION.rollback()
        print(f"Error setting chat language: {e}")
    finally:
        SESSION.close()


def get_chat_lang(chat_id: int) -> str:
    """Get language for a chat."""
    if chat_id in CHAT_LANG_CACHE:
        return CHAT_LANG_CACHE[chat_id]
    try:
        chat_lang = SESSION.query(ChatLang).get(chat_id)
        if chat_lang:
            CHAT_LANG_CACHE[chat_id] = chat_lang.lang_code
            return chat_lang.lang_code
        CHAT_LANG_CACHE[chat_id] = "en"
        return "en"
    finally:
        SESSION.close()


def set_user_lang(user_id: int, lang_code: str):
    """Set language for a user."""
    USER_LANG_CACHE[user_id] = lang_code
    try:
        user_lang = SESSION.query(UserLang).get(user_id)
        if user_lang:
            user_lang.lang_code = lang_code
        else:
            user_lang = UserLang(user_id, lang_code)
            SESSION.add(user_lang)
        SESSION.commit()
    except Exception as e:
        SESSION.rollback()
        print(f"Error setting user language: {e}")
    finally:
        SESSION.close()


def get_user_lang(user_id: int) -> str:
    """Get language for a user."""
    if user_id in USER_LANG_CACHE:
        return USER_LANG_CACHE[user_id]
    try:
        user_lang = SESSION.query(UserLang).get(user_id)
        if user_lang:
            USER_LANG_CACHE[user_id] = user_lang.lang_code
            return user_lang.lang_code
        USER_LANG_CACHE[user_id] = "en"
        return "en"
    finally:
        SESSION.close()


def get_lang(chat_id: int = None, user_id: int = None) -> str:
    """
    Get language preference.
    Priority: Chat language > User language > Default (English)
    """
    if chat_id:
        lang = get_chat_lang(chat_id)
        if lang != "en":
            return lang
    
    if user_id:
        lang = get_user_lang(user_id)
        if lang != "en":
            return lang
    
    return "en"
