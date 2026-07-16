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


class RSSFeed(BASE):
    __tablename__ = "rss_feed"

    chat_id = Column(String(14), primary_key=True)
    feed_url = Column(UnicodeText, nullable=False)
    last_entry_id = Column(UnicodeText, default="")

    def __init__(self, chat_id: int, feed_url: str, last_entry_id: str = ""):
        self.chat_id = str(chat_id)
        self.feed_url = feed_url
        self.last_entry_id = last_entry_id

    def __repr__(self):
        return f"<RSSFeed(chat={self.chat_id}, url={self.feed_url})>"


RSSFeed.__table__.create(checkfirst=True)


def get_feed(chat_id: int) -> RSSFeed:
    try:
        return SESSION.query(RSSFeed).filter(RSSFeed.chat_id == str(chat_id)).first()
    finally:
        SESSION.close()


def add_feed(chat_id: int, feed_url: str, last_entry_id: str = ""):
    with INSERTION_LOCK:
        feed = SESSION.query(RSSFeed).filter(RSSFeed.chat_id == str(chat_id)).first()
        if feed:
            feed.feed_url = feed_url
            feed.last_entry_id = last_entry_id
        else:
            feed = RSSFeed(chat_id, feed_url, last_entry_id)
            SESSION.add(feed)
        SESSION.commit()


def remove_feed(chat_id: int) -> bool:
    with INSERTION_LOCK:
        feed = SESSION.query(RSSFeed).filter(RSSFeed.chat_id == str(chat_id)).first()
        if feed:
            SESSION.delete(feed)
            SESSION.commit()
            return True
        return False


def get_all_feeds():
    try:
        return SESSION.query(RSSFeed).all()
    finally:
        SESSION.close()


def update_last_entry(chat_id: int, last_entry_id: str):
    with INSERTION_LOCK:
        feed = SESSION.query(RSSFeed).filter(RSSFeed.chat_id == str(chat_id)).first()
        if feed:
            feed.last_entry_id = last_entry_id
            SESSION.commit()
