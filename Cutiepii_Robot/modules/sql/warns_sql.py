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
from typing import List, Tuple, Optional

from Cutiepii_Robot import LOGGER
from Cutiepii_Robot.modules.sql import BASE, SESSION, retry_on_db_error
from sqlalchemy import Boolean, Column, Integer, String, UnicodeText, distinct, func, Index
from sqlalchemy.sql.sqltypes import BigInteger
from sqlalchemy.dialects import postgresql


class Warns(BASE):
    __tablename__ = "warns"

    user_id = Column(BigInteger, primary_key=True, index=True)
    chat_id = Column(String(14), primary_key=True, index=True)
    num_warns = Column(Integer, default=0)
    reasons = Column(postgresql.ARRAY(UnicodeText))

    __table_args__ = (
        Index('idx_warns_user', 'user_id'),
        Index('idx_warns_chat', 'chat_id'),
    )

    def __init__(self, user_id: int, chat_id: str):
        self.user_id = user_id
        self.chat_id = str(chat_id)
        self.num_warns = 0
        self.reasons = []

    def __repr__(self) -> str:
        return f"<Warns user={self.user_id} chat={self.chat_id} count={self.num_warns}>"


class WarnFilters(BASE):
    __tablename__ = "warn_filters"
    chat_id = Column(String(14), primary_key=True, index=True)
    keyword = Column(UnicodeText, primary_key=True, nullable=False)
    reply = Column(UnicodeText, nullable=False)

    __table_args__ = (
        Index('idx_warn_filters_chat', 'chat_id'),
    )

    def __init__(self, chat_id: str, keyword: str, reply: str):
        self.chat_id = str(chat_id)
        self.keyword = keyword
        self.reply = reply

    def __repr__(self) -> str:
        return f"<WarnFilter chat={self.chat_id} keyword='{self.keyword}'>"

    def __eq__(self, other) -> bool:
        return bool(
            isinstance(other, WarnFilters)
            and self.chat_id == other.chat_id
            and self.keyword == other.keyword,
        )


class WarnSettings(BASE):
    __tablename__ = "warn_settings"
    chat_id = Column(String(14), primary_key=True, index=True)
    warn_limit = Column(Integer, default=3)
    soft_warn = Column(Boolean, default=False)
    warn_mode = Column(Integer, default=0)

    def __init__(self, chat_id: str, warn_limit: int = 3, soft_warn: bool = False, warn_mode: int = 0):
        self.chat_id = str(chat_id)
        self.warn_limit = warn_limit
        self.soft_warn = soft_warn
        self.warn_mode = warn_mode
        
    def __repr__(self) -> str:
        return f"<WarnSettings chat={self.chat_id} limit={self.warn_limit} soft={self.soft_warn} mode={self.warn_mode}>"


Warns.__table__.create(checkfirst=True)
WarnFilters.__table__.create(checkfirst=True)
WarnSettings.__table__.create(checkfirst=True)

WARN_INSERTION_LOCK = threading.RLock()
WARN_FILTER_INSERTION_LOCK = threading.RLock()
WARN_SETTINGS_LOCK = threading.RLock()

WARN_FILTERS = {}


@retry_on_db_error(max_retries=3)
def warn_user(user_id: int, chat_id: int, reason: Optional[str] = None) -> Tuple[int, List[str]]:
    """Add a warn to user in chat"""
    try:
        with WARN_INSERTION_LOCK:
            warned_user = SESSION.query(Warns).get((user_id, str(chat_id)))
            if not warned_user:
                warned_user = Warns(user_id, str(chat_id))

            warned_user.num_warns += 1
            if reason:
                warned_user.reasons = warned_user.reasons + [reason]

            reasons = warned_user.reasons
            num = warned_user.num_warns

            SESSION.add(warned_user)
            SESSION.commit()
            
            LOGGER.info(f"[SQL] Warned user {user_id} in chat {chat_id} (total: {num})")
            return num, reasons
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to warn user {user_id} in chat {chat_id}: {e}")
        SESSION.rollback()
        raise


def remove_warn(user_id, chat_id):
    with WARN_INSERTION_LOCK:
        removed = False
        warned_user = SESSION.query(Warns).get((user_id, str(chat_id)))

        if warned_user and warned_user.num_warns > 0:
            warned_user.num_warns -= 1
            warned_user.reasons = warned_user.reasons[:-1]
            SESSION.add(warned_user)
            SESSION.commit()
            removed = True

        SESSION.close()
        return removed


def reset_warns(user_id, chat_id):
    with WARN_INSERTION_LOCK:
        warned_user = SESSION.query(Warns).get((user_id, str(chat_id)))
        if warned_user:
            warned_user.num_warns = 0
            warned_user.reasons = []

            SESSION.add(warned_user)
            SESSION.commit()
        SESSION.close()


@retry_on_db_error(max_retries=2)
def get_warns(user_id: int, chat_id: int) -> Optional[Tuple[int, List[str]]]:
    """Get warns for user in chat"""
    try:
        user = SESSION.query(Warns).get((user_id, str(chat_id)))
        if not user:
            return None
        reasons = user.reasons
        num = user.num_warns
        return num, reasons
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to get warns for user {user_id} in chat {chat_id}: {e}")
        return None
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=2)
def get_chat_warns(chat_id: int) -> List[Warns]:
    """Get all warns in a chat"""
    try:
        return SESSION.query(Warns).filter(Warns.chat_id == str(chat_id), Warns.num_warns > 0).all()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to get chat warns for chat {chat_id}: {e}")
        return []
    finally:
        SESSION.close()


def add_warn_filter(chat_id, keyword, reply):
    with WARN_FILTER_INSERTION_LOCK:
        warn_filt = WarnFilters(str(chat_id), keyword, reply)

        if keyword not in WARN_FILTERS.get(str(chat_id), []):
            WARN_FILTERS[str(chat_id)] = sorted(
                WARN_FILTERS.get(str(chat_id), []) + [keyword],
                key=lambda x: (-len(x), x),
            )

        SESSION.merge(warn_filt)  # merge to avoid duplicate key issues
        SESSION.commit()


def remove_warn_filter(chat_id, keyword):
    with WARN_FILTER_INSERTION_LOCK:
        warn_filt = SESSION.query(WarnFilters).get((str(chat_id), keyword))
        if warn_filt:
            if keyword in WARN_FILTERS.get(str(chat_id), []):  # sanity check
                WARN_FILTERS.get(str(chat_id), []).remove(keyword)

            SESSION.delete(warn_filt)
            SESSION.commit()
            return True
        SESSION.close()
        return False


def get_chat_warn_triggers(chat_id):
    return WARN_FILTERS.get(str(chat_id), set())


def get_chat_warn_filters(chat_id):
    try:
        return (
            SESSION.query(WarnFilters).filter(WarnFilters.chat_id == str(chat_id)).all()
        )
    finally:
        SESSION.close()


def get_warn_filter(chat_id, keyword):
    try:
        return SESSION.query(WarnFilters).get((str(chat_id), keyword))
    finally:
        SESSION.close()


def set_warn_limit(chat_id, warn_limit):
    with WARN_SETTINGS_LOCK:
        curr_setting = SESSION.query(WarnSettings).get(str(chat_id))
        if not curr_setting:
            curr_setting = WarnSettings(chat_id, warn_limit=warn_limit)

        curr_setting.warn_limit = warn_limit

        SESSION.add(curr_setting)
        SESSION.commit()


def set_warn_strength(chat_id, soft_warn):
    with WARN_SETTINGS_LOCK:
        curr_setting = SESSION.query(WarnSettings).get(str(chat_id))
        if not curr_setting:
            curr_setting = WarnSettings(chat_id, soft_warn=soft_warn)

        curr_setting.soft_warn = soft_warn

        SESSION.add(curr_setting)
        SESSION.commit()


def get_warn_setting(chat_id):
    try:
        setting = SESSION.query(WarnSettings).get(str(chat_id))
        if setting:
            return setting.warn_limit, setting.soft_warn, setting.warn_mode
        else:
            return 3, False, 1

    finally:
        SESSION.close()

def set_warn_mode(chat_id, warn_mode):
    with WARN_SETTINGS_LOCK:
        curr_setting = SESSION.query(WarnSettings).get(str(chat_id))
        if not curr_setting:
            curr_setting = WarnSettings(chat_id, warn_mode=warn_mode)

        curr_setting.warn_mode = warn_mode

        SESSION.add(curr_setting)
        SESSION.commit()

@retry_on_db_error(max_retries=2)
def num_warns() -> int:
    """Get total number of warns across all chats"""
    try:
        return SESSION.query(func.sum(Warns.num_warns)).scalar() or 0
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to count warns: {e}")
        return 0
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=2)
def num_warn_chats() -> int:
    """Get number of chats with warns"""
    try:
        return SESSION.query(func.count(distinct(Warns.chat_id))).scalar()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to count warn chats: {e}")
        return 0
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=2)
def num_warn_filters() -> int:
    """Get total number of warn filters"""
    try:
        return SESSION.query(WarnFilters).count()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to count warn filters: {e}")
        return 0
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=2)
def num_warn_chat_filters(chat_id: int) -> int:
    """Get number of warn filters in a chat"""
    try:
        return (
            SESSION.query(WarnFilters.chat_id)
            .filter(WarnFilters.chat_id == str(chat_id))
            .count()
        )
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to count warn filters for chat {chat_id}: {e}")
        return 0
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=2)
def num_warn_filter_chats() -> int:
    """Get number of chats with warn filters"""
    try:
        return SESSION.query(func.count(distinct(WarnFilters.chat_id))).scalar()
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to count warn filter chats: {e}")
        return 0
    finally:
        SESSION.close()


def __load_chat_warn_filters() -> None:
    """Load warn filters into memory cache"""
    global WARN_FILTERS
    try:
        chats = SESSION.query(WarnFilters.chat_id).distinct().all()
        for (chat_id,) in chats:
            WARN_FILTERS[chat_id] = []

        all_filters = SESSION.query(WarnFilters).all()
        for x in all_filters:
            WARN_FILTERS[x.chat_id] += [x.keyword]

        WARN_FILTERS = {
            x: sorted(set(y), key=lambda i: (-len(i), i))
            for x, y in WARN_FILTERS.items()
        }
        LOGGER.info(f"[SQL] Loaded warn filters for {len(WARN_FILTERS)} chats")
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to load warn filters: {e}")
        WARN_FILTERS = {}
    finally:
        SESSION.close()


@retry_on_db_error(max_retries=3)
def migrate_chat(old_chat_id: int, new_chat_id: int) -> None:
    """Migrate warn data from old_chat_id to new_chat_id"""
    try:
        with WARN_INSERTION_LOCK:
            chat_notes = (
                SESSION.query(Warns).filter(Warns.chat_id == str(old_chat_id)).all()
            )
            for note in chat_notes:
                note.chat_id = str(new_chat_id)
            SESSION.commit()

        with WARN_FILTER_INSERTION_LOCK:
            chat_filters = (
                SESSION.query(WarnFilters)
                .filter(WarnFilters.chat_id == str(old_chat_id))
                .all()
            )
            for filt in chat_filters:
                filt.chat_id = str(new_chat_id)
            SESSION.commit()
            old_warn_filt = WARN_FILTERS.get(str(old_chat_id))
            if old_warn_filt is not None:
                WARN_FILTERS[str(new_chat_id)] = old_warn_filt
                del WARN_FILTERS[str(old_chat_id)]

        with WARN_SETTINGS_LOCK:
            chat_settings = (
                SESSION.query(WarnSettings)
                .filter(WarnSettings.chat_id == str(old_chat_id))
                .all()
            )
            for setting in chat_settings:
                setting.chat_id = str(new_chat_id)
            SESSION.commit()
        
        LOGGER.info(f"[SQL] Migrated warn data from {old_chat_id} to {new_chat_id}")
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to migrate warn data: {e}")
        SESSION.rollback()
        raise


# Load settings on module import
try:
    __load_chat_warn_filters()
except Exception as e:
    LOGGER.error(f"[SQL] Failed to initialize warns module: {e}")
