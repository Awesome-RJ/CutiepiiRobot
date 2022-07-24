
"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, [ https://github.com/Awesome-RJ ]
Copyright (c) 2021-2022, Yūki • Black Knights Union, [ https://github.com/Awesome-RJ/CutiepiiRobot ]

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

from Cutiepii_Robot import CUTIEPII_PTB
from Cutiepii_Robot.modules.sql import BASE, SESSION
from sqlalchemy.sql.sqltypes import BigInteger
from sqlalchemy import (
    Column,
    ForeignKey,
    String,
    UnicodeText,
    UniqueConstraint,
    func,
)


class Users(BASE):
    __tablename__ = "users"
    user_id = Column(BigInteger, primary_key=True)
    username = Column(UnicodeText)

    def __init__(self, user_id, username=None):
        self.user_id = user_id
        self.username = username

    def __repr__(self):
        return f"<User {self.username} ({self.user_id})>"


class Chats(BASE):
    __tablename__ = "chats"
    chat_id = Column(String(14), primary_key=True)
    chat_name = Column(UnicodeText, nullable=False)

    def __init__(self, chat_id, chat_name):
        self.chat_id = str(chat_id)
        self.chat_name = chat_name

    def __repr__(self):
        return f"<Chat {self.chat_name} ({self.chat_id})>"


class ChatMembers(BASE):
    __tablename__ = "chat_members"
    priv_chat_id = Column(BigInteger, primary_key=True)
    # NOTE: Use dual primary key instead of private primary key?
    chat = Column(
        String(14),
        ForeignKey("chats.chat_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    user = Column(
        BigInteger,
        ForeignKey("users.user_id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
    )
    __table_args__ = (UniqueConstraint("chat", "user", name="_chat_members_uc"),)

    def __init__(self, chat, user):
        self.chat = chat
        self.user = user

    def __repr__(self):
        return f"<Chat user {self.user.username} ({self.user.user_id}) in chat {self.chat.chat_name} ({self.chat.chat_id})>"


Users.__table__.create(checkfirst=True)
Chats.__table__.create(checkfirst=True)
ChatMembers.__table__.create(checkfirst=True)

INSERTION_LOCK = threading.RLock()


def ensure_bot_in_db():
    with INSERTION_LOCK:
        bot = Users(1241223850, "Cutiepii_Robot")
        SESSION.merge(bot)
        SESSION.commit()


def update_user(user_id, username, chat_id=None, chat_name=None):
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

        chat = SESSION.query(Chats).get(str(chat_id))
        if not chat:
            chat = Chats(str(chat_id), chat_name)
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


def get_userid_by_name(username):
    try:
        return (
            SESSION.query(Users)
            .filter(func.lower(Users.username) == username.lower())
            .all()
        )
    finally:
        SESSION.close()


def get_name_by_userid(user_id):
    try:
        return SESSION.query(Users).get(Users.user_id == int(user_id)).first()
    finally:
        SESSION.close()


def get_chat_members(chat_id):
    try:
        return SESSION.query(ChatMembers).filter(ChatMembers.chat == str(chat_id)).all()
    finally:
        SESSION.close()


def get_all_chats():
    try:
        return SESSION.query(Chats).all()
    finally:
        SESSION.close()


def get_all_users():
    try:
        return SESSION.query(Users).all()
    finally:
        SESSION.close()


def get_user_num_chats(user_id):
    try:
        return (
            SESSION.query(ChatMembers).filter(ChatMembers.user == int(user_id)).count()
        )
    finally:
        SESSION.close()


def get_user_com_chats(user_id):
    try:
        chat_members = (
            SESSION.query(ChatMembers).filter(ChatMembers.user == int(user_id)).all()
        )
        return [i.chat for i in chat_members]
    finally:
        SESSION.close()


def num_chats():
    try:
        return SESSION.query(Chats).count()
    finally:
        SESSION.close()


def num_users():
    try:
        return SESSION.query(Users).count()
    finally:
        SESSION.close()


def migrate_chat(old_chat_id, new_chat_id):
    with INSERTION_LOCK:
        chat = SESSION.query(Chats).get(str(old_chat_id))
        if chat:
            chat.chat_id = str(new_chat_id)
            SESSION.add(chat)

        SESSION.flush()

        chat_members = (
            SESSION.query(ChatMembers)
            .filter(ChatMembers.chat == str(old_chat_id))
            .all()
        )
        for member in chat_members:
            member.chat = str(new_chat_id)
            SESSION.add(member)

        SESSION.commit()


ensure_bot_in_db()


def del_user(user_id):
    with INSERTION_LOCK:
        if curr := SESSION.query(Users).get(user_id):
            SESSION.delete(curr)
            SESSION.commit()
            return True

        ChatMembers.query.filter(ChatMembers.user == user_id).delete()
        SESSION.commit()
        SESSION.close()
    return False


def rem_chat(chat_id):
    with INSERTION_LOCK:
        if chat := SESSION.query(Chats).get(str(chat_id)):
            SESSION.delete(chat)
            SESSION.commit()
        else:
            SESSION.close()
