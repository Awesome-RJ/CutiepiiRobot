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
from typing import Set, Tuple, Dict, Optional

from sqlalchemy import func, distinct, Column, String, UnicodeText, Integer, Index

from Cutiepii_Robot import LOGGER
from Cutiepii_Robot.modules.sql import SESSION, BASE, retry_on_db_error


class BlackListFilters(BASE):
    __tablename__ = "blacklist"
    chat_id = Column(String(14), primary_key=True, index=True)
    trigger = Column(UnicodeText, primary_key=True, nullable=False)
    trig_act = Column(Integer, default=0)

    __table_args__ = (
        Index('idx_blacklist_chat', 'chat_id'),
        Index('idx_blacklist_trigger', 'trigger'),
    )

    def __init__(self, chat_id: str, trigger: str, trig_act: int):
        self.chat_id = str(chat_id)
        self.trigger = trigger
        self.trig_act = int(trig_act)

    def __repr__(self) -> str:
        return f"<BlacklistFilter chat={self.chat_id} trigger='{self.trigger}' action={self.trig_act}>"

    def __eq__(self, other) -> bool:
        return bool(
            isinstance(other, BlackListFilters)
            and self.chat_id == other.chat_id
            and self.trigger == other.trigger
            and self.trig_act == other.trig_act
        )


class BlacklistSettings(BASE):
    __tablename__ = "blacklist_settings"
    chat_id = Column(String(14), primary_key=True, index=True)
    blacklist_type = Column(Integer, default=1)
    value = Column(UnicodeText, default="0")

    def __init__(self, chat_id: str, blacklist_type: int = 1, value: str = "0"):
        self.chat_id = str(chat_id)
        self.blacklist_type = blacklist_type
        self.value = value

    def __repr__(self) -> str:
        return f"<BlacklistSettings chat={self.chat_id} type={self.blacklist_type} value={self.value}>"


BlackListFilters.__table__.create(checkfirst=True)
BlacklistSettings.__table__.create(checkfirst=True)

BLACKLIST_FILTER_INSERTION_LOCK = threading.RLock()
BLACKLIST_SETTINGS_INSERTION_LOCK = threading.RLock()

CHAT_BLACKLISTS = {}
CHAT_SETTINGS_BLACKLISTS = {}


@retry_on_db_error(max_retries=3)
def add_to_blacklist(chat_id: int, trigger: str, action: int) -> bool:
    """Add blacklist filter to chat (max 100 per chat)"""
    try:
        with BLACKLIST_FILTER_INSERTION_LOCK:
            global CHAT_BLACKLISTS
            if len(CHAT_BLACKLISTS.get(str(chat_id), set())) >= 100:
                LOGGER.warning(f"[SQL] Chat {chat_id} reached blacklist limit (100)")
                return False
            
            blacklist_filt = BlackListFilters(str(chat_id), trigger, action)

            SESSION.merge(blacklist_filt)
            SESSION.commit()
            
            if CHAT_BLACKLISTS.get(str(chat_id), set()) == set():
                CHAT_BLACKLISTS[str(chat_id)] = {(trigger, action)}
            else:
                CHAT_BLACKLISTS.get(str(chat_id), set()).add((trigger, action))
            
            LOGGER.info(f"[SQL] Added blacklist '{trigger}' to chat {chat_id}")
            return True
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to add blacklist to chat {chat_id}: {e}")
        SESSION.rollback()
        return False


def rm_from_blacklist(chat_id, trigger):
    with BLACKLIST_FILTER_INSERTION_LOCK:
        blacklist_filt = SESSION.query(BlackListFilters).get((str(chat_id), trigger))
        if blacklist_filt:
            chatbl = CHAT_BLACKLISTS.get(str(chat_id))
            bl = set(filter(lambda x: x[0] == trigger, chatbl)).pop()
            if bl in CHAT_BLACKLISTS.get(str(chat_id), set()):  # sanity check
                CHAT_BLACKLISTS.get(str(chat_id), set()).remove(bl)

            SESSION.delete(blacklist_filt)
            SESSION.commit()
            return True

        SESSION.close()
        return False

def get_chat_blacklist(chat_id: int) -> Set[Tuple[str, int]]:
    """Get all blacklist filters for a chat"""
    return CHAT_BLACKLISTS.get(str(chat_id), set())


@retry_on_db_error(max_retries=2)
def num_blacklist_filters() -> int:
    """Get total number of blacklist filters"""
    try:
        return SESSION.query(BlackListFilters).count()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to count blacklist filters: {e}")
        return 0
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=2)
def num_blacklist_chat_filters(chat_id: int) -> int:
    """Get number of blacklist filters in a chat"""
    try:
        return (
            SESSION.query(BlackListFilters.chat_id)
            .filter(BlackListFilters.chat_id == str(chat_id))
            .count()
        )
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to count blacklist filters for chat {chat_id}: {e}")
        return 0
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=2)
def num_blacklist_filter_chats() -> int:
    """Get number of chats with blacklist filters"""
    try:
        return SESSION.query(func.count(distinct(BlackListFilters.chat_id))).scalar()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to count blacklist chats: {e}")
        return 0
    finally:
        SESSION.close()


def set_blacklist_strength(chat_id, blacklist_type, value):
    # for blacklist_type
    # 0 = nothing
    # 1 = delete
    # 2 = warn
    # 3 = mute
    # 4 = kick
    # 5 = ban
    # 6 = tban
    # 7 = tmute
    with BLACKLIST_SETTINGS_INSERTION_LOCK:
        global CHAT_SETTINGS_BLACKLISTS
        curr_setting = SESSION.query(BlacklistSettings).get(str(chat_id))
        if not curr_setting:
            curr_setting = BlacklistSettings(
                chat_id, blacklist_type=int(blacklist_type), value=value
            )

        curr_setting.blacklist_type = int(blacklist_type)
        curr_setting.value = str(value)
        CHAT_SETTINGS_BLACKLISTS[str(chat_id)] = {
            "blacklist_type": int(blacklist_type),
            "value": value,
        }

        SESSION.add(curr_setting)
        SESSION.commit()


def get_blacklist_setting(chat_id: int) -> Tuple[int, str]:
    """Get blacklist settings for a chat"""
    try:
        setting = CHAT_SETTINGS_BLACKLISTS.get(str(chat_id))
        if setting:
            return setting["blacklist_type"], setting["value"]
        else:
            return 1, "0"
    finally:
        SESSION.close()


def __load_chat_blacklists() -> None:
    """Load blacklist filters into memory cache"""
    global CHAT_BLACKLISTS
    try:
        chats = SESSION.query(BlackListFilters.chat_id).distinct().all()
        for (chat_id,) in chats:
            CHAT_BLACKLISTS[chat_id] = []

        all_filters = SESSION.query(BlackListFilters).all()
        for x in all_filters:
            CHAT_BLACKLISTS[x.chat_id] += [(x.trigger, x.trig_act)]

        CHAT_BLACKLISTS = {x: set(y) for x, y in CHAT_BLACKLISTS.items()}
        LOGGER.info(f"[SQL] Loaded blacklists for {len(CHAT_BLACKLISTS)} chats")
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to load blacklists: {e}")
        CHAT_BLACKLISTS = {}
    finally:
        SESSION.close()


def __load_chat_settings_blacklists() -> None:
    """Load blacklist settings into memory cache"""
    global CHAT_SETTINGS_BLACKLISTS
    try:
        chats_settings = SESSION.query(BlacklistSettings).all()
        for x in chats_settings:
            CHAT_SETTINGS_BLACKLISTS[x.chat_id] = {
                "blacklist_type": x.blacklist_type,
                "value": x.value,
            }
        LOGGER.info(f"[SQL] Loaded blacklist settings for {len(CHAT_SETTINGS_BLACKLISTS)} chats")
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to load blacklist settings: {e}")
        CHAT_SETTINGS_BLACKLISTS = {}
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=3)
def migrate_chat(old_chat_id: int, new_chat_id: int) -> None:
    """Migrate blacklist filters from old_chat_id to new_chat_id"""
    try:
        with BLACKLIST_FILTER_INSERTION_LOCK:
            chat_filters = (
                SESSION.query(BlackListFilters)
                .filter(BlackListFilters.chat_id == str(old_chat_id))
                .all()
            )
            for filt in chat_filters:
                filt.chat_id = str(new_chat_id)
            SESSION.commit()
            LOGGER.info(f"[SQL] Migrated blacklist filters from {old_chat_id} to {new_chat_id}")
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to migrate blacklist filters: {e}")
        SESSION.rollback()
        raise


# Load settings on module import
try:
    __load_chat_blacklists()
    __load_chat_settings_blacklists()
except Exception as e:
    LOGGER.error(f"[SQL] Failed to initialize blacklist module: {e}")