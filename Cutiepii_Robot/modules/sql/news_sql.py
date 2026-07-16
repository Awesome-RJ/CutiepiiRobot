"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.
"""

import threading
from sqlalchemy import Column, String, UnicodeText
from Cutiepii_Robot.modules.sql import BASE, SESSION

INSERTION_LOCK = threading.RLock()


class NewsSettings(BASE):
    __tablename__ = "news_settings"

    chat_id = Column(String(14), primary_key=True)
    category = Column(String(50), default="world", nullable=False)
    keywords = Column(UnicodeText, default="")

    def __init__(self, chat_id: int, category: str = "world", keywords: str = ""):
        self.chat_id = str(chat_id)
        self.category = category
        self.keywords = keywords

    def __repr__(self):
        return f"<NewsSettings(chat={self.chat_id}, category={self.category})>"


NewsSettings.__table__.create(checkfirst=True)


def get_news_settings(chat_id: int) -> NewsSettings:
    try:
        setting = SESSION.query(NewsSettings).filter(NewsSettings.chat_id == str(chat_id)).first()
        if not setting:
            # Default settings
            return NewsSettings(chat_id, "world", "")
        return setting
    finally:
        SESSION.close()


def set_news_category(chat_id: int, category: str):
    with INSERTION_LOCK:
        setting = SESSION.query(NewsSettings).filter(NewsSettings.chat_id == str(chat_id)).first()
        if setting:
            setting.category = category
        else:
            setting = NewsSettings(chat_id, category=category)
            SESSION.add(setting)
        SESSION.commit()


def set_news_keywords(chat_id: int, keywords: str):
    with INSERTION_LOCK:
        setting = SESSION.query(NewsSettings).filter(NewsSettings.chat_id == str(chat_id)).first()
        if setting:
            setting.keywords = keywords
        else:
            setting = NewsSettings(chat_id, keywords=keywords)
            SESSION.add(setting)
        SESSION.commit()
