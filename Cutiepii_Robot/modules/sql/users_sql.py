
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
import threading
from typing import List, Optional, Tuple

from Cutiepii_Robot import BOT_ID, BOT_USERNAME, LOGGER
from Cutiepii_Robot.modules.sql import BASE, SESSION, session_scope, retry_on_db_error
from sqlalchemy.sql.sqltypes import BigInteger
from sqlalchemy import (
    Column,
    ForeignKey,
    String,
    UnicodeText,
    UniqueConstraint,
    func,
    Index,
)


class Users(BASE):
    __tablename__ = "users"
    user_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(UnicodeText, index=True)

    __table_args__ = (
        Index('idx_users_username_lower', func.lower(username)),
    )

    def __init__(self, user_id: int, username: Optional[str] = None):
        self.user_id = user_id
        self.username = username

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.user_id})>"


class Chats(BASE):
    __tablename__ = "chats"
    chat_id = Column(BigInteger, primary_key=True, index=True)
    chat_name = Column(UnicodeText, nullable=False, index=True)

    def __init__(self, chat_id: int, chat_name: str):
        self.chat_id = int(chat_id)
        self.chat_name = chat_name

    def __repr__(self) -> str:
        return f"<Chat {self.chat_name} ({self.chat_id})>"


class ChatMembers(BASE):
    __tablename__ = "chat_members"
    priv_chat_id = Column(BigInteger, primary_key=True)
    chat = Column(
        BigInteger,
        ForeignKey("chats.chat_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user = Column(
        BigInteger,
        ForeignKey("users.user_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    __table_args__ = (
        UniqueConstraint("chat", "user", name="_chat_members_uc"),
        Index('idx_chat_members_chat', 'chat'),
        Index('idx_chat_members_user', 'user'),
    )

    def __init__(self, chat: int, user: int):
        self.chat = int(chat)
        self.user = user

    def __repr__(self) -> str:
        return f"<ChatMember user={self.user} in chat={self.chat}>"


Users.__table__.create(checkfirst=True)
Chats.__table__.create(checkfirst=True)
ChatMembers.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()


@retry_on_db_error(max_retries=3)
def ensure_bot_in_db() -> None:
    """Ensure bot user exists in database"""
    try:
        with INSERTION_LOCK:
            bot = Users(BOT_ID, BOT_USERNAME)
            SESSION.merge(bot)
            SESSION.commit()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to ensure bot in DB: {e}")
        SESSION.rollback()
        raise


@retry_on_db_error(max_retries=3)
def update_user(
    user_id: int, 
    username: Optional[str], 
    chat_id: Optional[int] = None, 
    chat_name: Optional[str] = None
) -> None:
    """Update or create user and optionally add to chat"""
    try:
        with INSERTION_LOCK:
            user = SESSION.query(Users).get(user_id)
            if not user:
                user = Users(user_id, username)
                SESSION.add(user)
                SESSION.flush()
            else:
                user.username = username

            if not chat_id or not chat_name:
                SESSION.commit()
                return

            chat = SESSION.query(Chats).get(int(chat_id))
            if not chat:
                chat = Chats(int(chat_id), chat_name)
                SESSION.add(chat)
                SESSION.flush()
            else:
                chat.chat_name = chat_name

            member = (
                SESSION.query(ChatMembers)
                .filter(ChatMembers.chat == chat.chat_id, ChatMembers.user == user.user_id)
                .first()
            )
            if not member:
                chat_member = ChatMembers(chat.chat_id, user.user_id)
                SESSION.add(chat_member)

            SESSION.commit()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to update user {user_id}: {e}")
        SESSION.rollback()
        raise


@retry_on_db_error(max_retries=2)
def get_userid_by_name(username: str) -> List[Users]:
    """Get all users matching username (case-insensitive)"""
    try:
        return (
            SESSION.query(Users)
            .filter(func.lower(Users.username) == username.lower())
            .all()
        )
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to get user by name {username}: {e}")
        return []
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=2)
def get_name_by_userid(user_id: int) -> Optional[Users]:
    """Get user by user_id"""
    try:
        return SESSION.query(Users).filter(Users.user_id == int(user_id)).first()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to get name by user_id {user_id}: {e}")
        return None
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=2)
def get_chat_members(chat_id: int) -> List[ChatMembers]:
    """Get all members of a chat"""
    try:
        return SESSION.query(ChatMembers).filter(ChatMembers.chat == int(chat_id)).all()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to get chat members for {chat_id}: {e}")
        return []
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=2)
def get_all_chats() -> List[Chats]:
    """Get all chats"""
    try:
        return SESSION.query(Chats).all()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to get all chats: {e}")
        return []
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=2)
def get_all_users() -> List[Users]:
    """Get all users"""
    try:
        return SESSION.query(Users).all()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to get all users: {e}")
        return []
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=2)
def get_user_num_chats(user_id: int) -> int:
    """Get number of chats a user is in"""
    try:
        return (
            SESSION.query(ChatMembers).filter(ChatMembers.user == int(user_id)).count()
        )
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to get chat count for user {user_id}: {e}")
        return 0
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=2)
def get_user_com_chats(user_id: int) -> List[str]:
    """Get all chat IDs a user is in"""
    try:
        chat_members = (
            SESSION.query(ChatMembers).filter(ChatMembers.user == int(user_id)).all()
        )
        return [str(i.chat) for i in chat_members]
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to get common chats for user {user_id}: {e}")
        return []
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=2)
def num_chats() -> int:
    """Get total number of chats"""
    try:
        return SESSION.query(Chats).count()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to get chat count: {e}")
        return 0
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=2)
def num_users() -> int:
    """Get total number of users"""
    try:
        return SESSION.query(Users).count()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to get user count: {e}")
        return 0
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=3)
def migrate_chat(old_chat_id: int, new_chat_id: int) -> None:
    """Migrate chat data from old_chat_id to new_chat_id"""
    try:
        with INSERTION_LOCK:
            chat = SESSION.query(Chats).get(int(old_chat_id))
            if chat:
                chat.chat_id = int(new_chat_id)
            SESSION.commit()

            chat_members = (
                SESSION.query(ChatMembers)
                .filter(ChatMembers.chat == int(old_chat_id))
                .all()
            )
            for member in chat_members:
                member.chat = int(new_chat_id)
            SESSION.commit()
            LOGGER.info(f"[SQL] Migrated chat {old_chat_id} to {new_chat_id}")
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to migrate chat {old_chat_id} to {new_chat_id}: {e}")
        SESSION.rollback()
        raise


# Initialize bot in database
try:
    ensure_bot_in_db()
except Exception as e:
    LOGGER.error(f"[SQL] Failed to initialize bot in database: {e}")


@retry_on_db_error(max_retries=3)
def del_user(user_id: int) -> bool:
    """Delete user and their chat memberships"""
    try:
        with INSERTION_LOCK:
            curr = SESSION.query(Users).get(user_id)
            if curr:
                SESSION.delete(curr)
                SESSION.commit()
                LOGGER.info(f"[SQL] Deleted user {user_id}")
                return True

            SESSION.query(ChatMembers).filter(ChatMembers.user == user_id).delete()
            SESSION.commit()
            SESSION.close()
        return False
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to delete user {user_id}: {e}")
        SESSION.rollback()
        return False


@retry_on_db_error(max_retries=3)
def rem_chat(chat_id: int) -> None:
    """Remove chat from database"""
    try:
        with INSERTION_LOCK:
            chat = SESSION.query(Chats).get(int(chat_id))
            if chat:
                SESSION.delete(chat)
                SESSION.commit()
                LOGGER.info(f"[SQL] Removed chat {chat_id}")
            else:
                SESSION.close()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to remove chat {chat_id}: {e}")
        SESSION.rollback()
        raise
