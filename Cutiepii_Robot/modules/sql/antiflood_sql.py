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
from typing import Tuple, Optional

from sqlalchemy import String, Column, Integer, UnicodeText, Index, text
from sqlalchemy.sql.sqltypes import BigInteger

from Cutiepii_Robot import LOGGER
from Cutiepii_Robot.modules.sql import SESSION, BASE, retry_on_db_error

DEF_COUNT = 1
DEF_LIMIT = 0
DEF_OBJ = (None, DEF_COUNT, DEF_LIMIT)


class FloodControl(BASE):
    __tablename__ = "antiflood"
    chat_id = Column(String(14), primary_key=True, index=True)
    user_id = Column(BigInteger, index=True)
    count = Column(Integer, default=DEF_COUNT)
    limit = Column(Integer, default=DEF_LIMIT)

    __table_args__ = (
        Index('idx_antiflood_chat', 'chat_id'),
    )

    def __init__(self, chat_id: str):
        self.chat_id = str(chat_id)

    def __repr__(self) -> str:
        return f"<FloodControl chat={self.chat_id} limit={self.limit}>"


class FloodSettings(BASE):
    __tablename__ = "antiflood_settings"
    chat_id = Column(String(14), primary_key=True, index=True)
    flood_type = Column(Integer, default=1)
    value = Column(UnicodeText, default="0")

    def __init__(self, chat_id: str, flood_type: int = 1, value: str = "0"):
        self.chat_id = str(chat_id)
        self.flood_type = flood_type
        self.value = value

    def __repr__(self) -> str:
        return f"<FloodSettings chat={self.chat_id} type={self.flood_type} value={self.value}>"


FloodControl.__table__.create(checkfirst=True)
FloodSettings.__table__.create(checkfirst=True)

# Migrate older table schemas to support newer fields if they exist
try:
    SESSION.execute(text("ALTER TABLE antiflood_settings ADD COLUMN IF NOT EXISTS flood_type INTEGER DEFAULT 1"))
    SESSION.commit()
except Exception as e:
    LOGGER.error(f"[SQL] Failed to alter table antiflood_settings for flood_type: {e}")
    SESSION.rollback()

try:
    SESSION.execute(text("ALTER TABLE antiflood_settings ADD COLUMN IF NOT EXISTS value TEXT DEFAULT '0'"))
    SESSION.commit()
except Exception as e:
    LOGGER.error(f"[SQL] Failed to alter table antiflood_settings for value: {e}")
    SESSION.rollback()

INSERTION_FLOOD_LOCK = threading.RLock()
INSERTION_FLOOD_SETTINGS_LOCK = threading.RLock()

CHAT_FLOOD = {}


@retry_on_db_error(max_retries=3)
def set_flood(chat_id: int, amount: int) -> None:
    """Set flood limit for a chat"""
    try:
        with INSERTION_FLOOD_LOCK:
            flood = SESSION.query(FloodControl).get(str(chat_id))
            if not flood:
                flood = FloodControl(str(chat_id))

            flood.user_id = None
            flood.limit = amount

            CHAT_FLOOD[str(chat_id)] = (None, DEF_COUNT, amount)

            SESSION.add(flood)
            SESSION.commit()
            LOGGER.info(f"[SQL] Set flood limit for chat {chat_id} to {amount}")
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to set flood for chat {chat_id}: {e}")
        SESSION.rollback()
        raise


def update_flood(chat_id: str, user_id) -> bool:
    if str(chat_id) in CHAT_FLOOD:
        curr_user_id, count, limit = CHAT_FLOOD.get(str(chat_id), DEF_OBJ)

        if limit == 0:  # no antiflood
            return False

        if user_id != curr_user_id or user_id is None:  # other user
            CHAT_FLOOD[str(chat_id)] = (user_id, DEF_COUNT, limit)
            return False

        count += 1
        if count > limit:  # too many msgs, kick
            CHAT_FLOOD[str(chat_id)] = (None, DEF_COUNT, limit)
            return True

        # default -> update
        CHAT_FLOOD[str(chat_id)] = (user_id, count, limit)
        return False


def get_flood_limit(chat_id: int) -> int:
    """Get flood limit for a chat"""
    return CHAT_FLOOD.get(str(chat_id), DEF_OBJ)[2]


@retry_on_db_error(max_retries=3)
def set_flood_strength(chat_id: int, flood_type: int, value: str) -> None:
    """Set flood action type and value
    flood_type:
        1 = ban
        2 = kick
        3 = mute
        4 = tban
        5 = tmute
    """
    try:
        with INSERTION_FLOOD_SETTINGS_LOCK:
            curr_setting = SESSION.query(FloodSettings).get(str(chat_id))
            if not curr_setting:
                curr_setting = FloodSettings(
                    chat_id, flood_type=int(flood_type), value=value,
                )

            curr_setting.flood_type = int(flood_type)
            curr_setting.value = str(value)

            SESSION.add(curr_setting)
            SESSION.commit()
            LOGGER.info(f"[SQL] Set flood strength for chat {chat_id}: type={flood_type}, value={value}")
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to set flood strength for chat {chat_id}: {e}")
        SESSION.rollback()
        raise


@retry_on_db_error(max_retries=2)
def get_flood_setting(chat_id: int) -> Tuple[int, str]:
    """Get flood settings for a chat"""
    try:
        setting = SESSION.query(FloodSettings).get(str(chat_id))
        if setting:
            return setting.flood_type, setting.value
        else:
            return 1, "0"
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to get flood setting for chat {chat_id}: {e}")
        return 1, "0"
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=3)
def migrate_chat(old_chat_id: int, new_chat_id: int) -> None:
    """Migrate flood settings from old_chat_id to new_chat_id"""
    try:
        with INSERTION_FLOOD_LOCK:
            flood = SESSION.query(FloodControl).get(str(old_chat_id))
            if flood:
                CHAT_FLOOD[str(new_chat_id)] = CHAT_FLOOD.get(str(old_chat_id), DEF_OBJ)
                flood.chat_id = str(new_chat_id)
                SESSION.commit()
                LOGGER.info(f"[SQL] Migrated flood settings from {old_chat_id} to {new_chat_id}")

            SESSION.close()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to migrate flood settings: {e}")
        SESSION.rollback()
        raise


def __load_flood_settings() -> None:
    """Load flood settings into memory cache"""
    global CHAT_FLOOD
    try:
        all_chats = SESSION.query(FloodControl).all()
        CHAT_FLOOD = {chat.chat_id: (None, DEF_COUNT, chat.limit) for chat in all_chats}
        LOGGER.info(f"[SQL] Loaded flood settings for {len(CHAT_FLOOD)} chats")
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to load flood settings: {e}")
        CHAT_FLOOD = {}
    finally:
        SESSION.close()


# Load settings on module import
try:
    __load_flood_settings()
except Exception as e:
    LOGGER.error(f"[SQL] Failed to initialize flood settings: {e}")
