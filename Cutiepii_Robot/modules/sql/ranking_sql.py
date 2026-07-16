"""
BSD 2-Clause License
Ranking SQL Module
"""

from sqlalchemy import Column, String, Integer, DateTime, Date, ForeignKey, func, UniqueConstraint, Boolean
from sqlalchemy.sql.sqltypes import BigInteger
from Cutiepii_Robot.modules.sql import BASE, SESSION
from datetime import datetime, date
import threading
import pytz

INSERTION_LOCK = threading.RLock()


class RankingStats(BASE):
    __tablename__ = "ranking_stats"

    user_id = Column(BigInteger, primary_key=True)
    chat_id = Column(BigInteger, primary_key=True)
    
    daily_messages = Column(Integer, default=0)
    weekly_messages = Column(Integer, default=0)
    monthly_messages = Column(Integer, default=0)
    all_time_messages = Column(Integer, default=0)
    
    daily_xp = Column(Integer, default=0)
    weekly_xp = Column(Integer, default=0)
    monthly_xp = Column(Integer, default=0)
    total_xp = Column(Integer, default=0)
    
    level = Column(Integer, default=1)
    streak = Column(Integer, default=0)
    last_message = Column(DateTime, default=datetime.utcnow)

    def __init__(self, user_id, chat_id, xp=0, messages=0):
        self.user_id = user_id
        self.chat_id = chat_id
        self.daily_messages = messages
        self.weekly_messages = messages
        self.monthly_messages = messages
        self.all_time_messages = messages
        self.daily_xp = xp
        self.weekly_xp = xp
        self.monthly_xp = xp
        self.total_xp = xp
        self.level = 1
        self.streak = 1
        self.last_message = datetime.utcnow()

    def __repr__(self):
        return f"<RankingStats(user={self.user_id}, chat={self.chat_id}, level={self.level}, xp={self.total_xp})>"


class RankingHistory(BASE):
    __tablename__ = "ranking_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, default=date.today)
    user_id = Column(BigInteger, nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    messages = Column(Integer, default=0)
    xp = Column(Integer, default=0)
    rank = Column(Integer, nullable=False)

    def __init__(self, chat_id, user_id, messages, xp, rank, entry_date=None):
        self.chat_id = chat_id
        self.user_id = user_id
        self.messages = messages
        self.xp = xp
        self.rank = rank
        self.date = entry_date or date.today()


class RankingBadges(BASE):
    __tablename__ = "ranking_badges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    badge_name = Column(String(100), nullable=False)
    earned_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "chat_id", "badge_name", name="_user_chat_badge_uc"),
    )

    def __init__(self, user_id, chat_id, badge_name):
        self.user_id = user_id
        self.chat_id = chat_id
        self.badge_name = badge_name
        self.earned_at = datetime.utcnow()


class RankingSettings(BASE):
    __tablename__ = "ranking_settings"

    chat_id = Column(BigInteger, primary_key=True)
    is_enabled = Column(Boolean, default=True)
    timezone = Column(String(50), default="Asia/Kolkata")
    min_chars = Column(Integer, default=0)
    cooldown = Column(Integer, default=3)

    def __init__(self, chat_id, is_enabled=True, timezone="Asia/Kolkata", min_chars=0, cooldown=3):
        self.chat_id = chat_id
        self.is_enabled = is_enabled
        self.timezone = timezone
        self.min_chars = min_chars
        self.cooldown = cooldown


class RankingIgnoredUsers(BASE):
    __tablename__ = "ranking_ignored_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False)
    user_id = Column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint("chat_id", "user_id", name="_chat_ignored_user_uc"),
    )

    def __init__(self, chat_id, user_id):
        self.chat_id = chat_id
        self.user_id = user_id


# Create tables if they don't exist
RankingStats.__table__.create(checkfirst=True)
RankingHistory.__table__.create(checkfirst=True)
RankingBadges.__table__.create(checkfirst=True)
RankingSettings.__table__.create(checkfirst=True)
RankingIgnoredUsers.__table__.create(checkfirst=True)


def get_user_stats(user_id: int, chat_id: int) -> RankingStats:
    """Get stats for a single user in a chat"""
    try:
        return SESSION.query(RankingStats).filter(
            RankingStats.user_id == user_id,
            RankingStats.chat_id == chat_id
        ).first()
    finally:
        SESSION.close()


def get_ranking_settings(chat_id: int) -> RankingSettings:
    try:
        settings = SESSION.query(RankingSettings).filter(RankingSettings.chat_id == chat_id).first()
        if not settings:
            with INSERTION_LOCK:
                settings = RankingSettings(chat_id)
                SESSION.add(settings)
                SESSION.commit()
        return settings
    finally:
        SESSION.close()


def set_ranking_settings(chat_id: int, **kwargs) -> bool:
    with INSERTION_LOCK:
        settings = SESSION.query(RankingSettings).filter(RankingSettings.chat_id == chat_id).first()
        if not settings:
            settings = RankingSettings(chat_id)
            SESSION.add(settings)
            
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        try:
            SESSION.commit()
            return True
        except Exception:
            SESSION.rollback()
            return False


def is_ranking_enabled(chat_id: int) -> bool:
    try:
        settings = SESSION.query(RankingSettings).filter(RankingSettings.chat_id == chat_id).first()
        return settings.is_enabled if settings else True
    finally:
        SESSION.close()


def ignore_user(chat_id: int, user_id: int) -> bool:
    with INSERTION_LOCK:
        exists = SESSION.query(RankingIgnoredUsers).filter(
            RankingIgnoredUsers.chat_id == chat_id,
            RankingIgnoredUsers.user_id == user_id
        ).first()
        if exists:
            return False
        ignored = RankingIgnoredUsers(chat_id, user_id)
        SESSION.add(ignored)
        SESSION.commit()
        return True


def unignore_user(chat_id: int, user_id: int) -> bool:
    with INSERTION_LOCK:
        ignored = SESSION.query(RankingIgnoredUsers).filter(
            RankingIgnoredUsers.chat_id == chat_id,
            RankingIgnoredUsers.user_id == user_id
        ).first()
        if ignored:
            SESSION.delete(ignored)
            SESSION.commit()
            return True
        return False


def is_user_ignored(chat_id: int, user_id: int) -> bool:
    try:
        exists = SESSION.query(RankingIgnoredUsers).filter(
            RankingIgnoredUsers.chat_id == chat_id,
            RankingIgnoredUsers.user_id == user_id
        ).first()
        return exists is not None
    finally:
        SESSION.close()


def get_ignored_users(chat_id: int) -> list:
    try:
        users = SESSION.query(RankingIgnoredUsers).filter(
            RankingIgnoredUsers.chat_id == chat_id
        ).all()
        return [u.user_id for u in users]
    finally:
        SESSION.close()


def get_today_in_timezone(tz_name: str) -> date:
    try:
        tz = pytz.timezone(tz_name)
    except Exception:
        tz = pytz.timezone("Asia/Kolkata")
    return datetime.now(tz).date()


def add_xp_and_messages(chat_id: int, user_id: int, xp: int, messages: int) -> tuple:
    """Atomically add XP and message count to user stats in PostgreSQL. Returns (old_level, new_level)"""
    with INSERTION_LOCK:
        stats = SESSION.query(RankingStats).filter(
            RankingStats.user_id == user_id,
            RankingStats.chat_id == chat_id
        ).first()

        # Fetch chat timezone settings
        settings = SESSION.query(RankingSettings).filter(RankingSettings.chat_id == chat_id).first()
        tz_name = settings.timezone if settings else "Asia/Kolkata"
        today = get_today_in_timezone(tz_name)

        old_level = 1
        new_level = 1
        
        if stats:
            old_level = stats.level
            stats.daily_messages += messages
            stats.weekly_messages += messages
            stats.monthly_messages += messages
            stats.all_time_messages += messages
            
            stats.daily_xp += xp
            stats.weekly_xp += xp
            stats.monthly_xp += xp
            stats.total_xp += xp
            
            # Streak calculation
            if stats.last_message:
                # Convert stored UTC last_message to the configured timezone date
                last_msg_utc = stats.last_message.replace(tzinfo=pytz.utc)
                try:
                    tz = pytz.timezone(tz_name)
                except Exception:
                    tz = pytz.timezone("Asia/Kolkata")
                last_msg_date = last_msg_utc.astimezone(tz).date()
                
                days_diff = (today - last_msg_date).days
                if days_diff == 1:
                    stats.streak += 1
                elif days_diff > 1:
                    stats.streak = 1
            else:
                stats.streak = 1

            # Simple level formula: level = int((total_xp / 100) ** 0.5) + 1
            level_calc = int((stats.total_xp / 100) ** 0.5) + 1
            if level_calc > stats.level:
                stats.level = level_calc
            
            stats.last_message = datetime.utcnow()
            new_level = stats.level
        else:
            stats = RankingStats(user_id, chat_id, xp, messages)
            stats.streak = 1
            SESSION.add(stats)
            
        SESSION.commit()
        return old_level, new_level


def get_top_users(chat_id: int, limit: int = 10, sort_by: str = "xp") -> list:
    """Get top users in a chat sorted by xp or messages"""
    try:
        query = SESSION.query(RankingStats).filter(RankingStats.chat_id == chat_id)
        
        if sort_by == "daily":
            query = query.order_by(RankingStats.daily_messages.desc(), RankingStats.daily_xp.desc())
        elif sort_by == "weekly":
            query = query.order_by(RankingStats.weekly_messages.desc(), RankingStats.weekly_xp.desc())
        elif sort_by == "monthly":
            query = query.order_by(RankingStats.monthly_messages.desc(), RankingStats.monthly_xp.desc())
        elif sort_by == "all_time":
            query = query.order_by(RankingStats.all_time_messages.desc(), RankingStats.total_xp.desc())
        else: # default is total xp
            query = query.order_by(RankingStats.total_xp.desc())
            
        return query.limit(limit).all()
    finally:
        SESSION.close()


def add_badge(user_id: int, chat_id: int, badge_name: str) -> bool:
    """Grant a badge to a user. Returns True if granted, False if already has it."""
    with INSERTION_LOCK:
        exists = SESSION.query(RankingBadges).filter(
            RankingBadges.user_id == user_id,
            RankingBadges.chat_id == chat_id,
            RankingBadges.badge_name == badge_name
        ).first()
        
        if exists:
            return False
            
        badge = RankingBadges(user_id, chat_id, badge_name)
        SESSION.add(badge)
        SESSION.commit()
        return True


def remove_badge(user_id: int, chat_id: int, badge_name: str) -> bool:
    """Remove a badge from a user. Returns True if removed, False otherwise."""
    with INSERTION_LOCK:
        badge = SESSION.query(RankingBadges).filter(
            RankingBadges.user_id == user_id,
            RankingBadges.chat_id == chat_id,
            RankingBadges.badge_name == badge_name
        ).first()
        
        if badge:
            SESSION.delete(badge)
            SESSION.commit()
            return True
        return False


def get_user_badges(user_id: int, chat_id: int) -> list:
    """Get list of badges earned by a user in a chat"""
    try:
        badges = SESSION.query(RankingBadges).filter(
            RankingBadges.user_id == user_id,
            RankingBadges.chat_id == chat_id
        ).all()
        return [b.badge_name for b in badges]
    finally:
        SESSION.close()


def get_chat_rank(chat_id: int, user_id: int) -> int:
    """Get the numeric rank of a user in a chat based on total XP"""
    try:
        subquery = SESSION.query(
            RankingStats.user_id,
            func.rank().over(order_by=RankingStats.total_xp.desc()).label("rank")
        ).filter(RankingStats.chat_id == chat_id).subquery()
        
        result = SESSION.query(subquery.c.rank).filter(subquery.c.user_id == user_id).first()
        return result[0] if result else 0
    finally:
        SESSION.close()


def reset_chat_daily_stats(chat_id: int):
    """Reset daily counters and snapshot history for a single chat."""
    with INSERTION_LOCK:
        top_users = SESSION.query(RankingStats).filter(RankingStats.chat_id == chat_id).order_by(RankingStats.total_xp.desc()).all()
        for rank_idx, stats in enumerate(top_users, 1):
            history_entry = RankingHistory(
                chat_id=chat_id,
                user_id=stats.user_id,
                messages=stats.daily_messages,
                xp=stats.daily_xp,
                rank=rank_idx
            )
            SESSION.add(history_entry)
            
        SESSION.query(RankingStats).filter(RankingStats.chat_id == chat_id).update({
            RankingStats.daily_messages: 0,
            RankingStats.daily_xp: 0
        })
        SESSION.commit()


def reset_chat_weekly_stats(chat_id: int):
    """Reset weekly counters in database for a single chat."""
    with INSERTION_LOCK:
        SESSION.query(RankingStats).filter(RankingStats.chat_id == chat_id).update({
            RankingStats.weekly_messages: 0,
            RankingStats.weekly_xp: 0
        })
        SESSION.commit()


def reset_chat_monthly_stats(chat_id: int):
    """Reset monthly counters in database for a single chat."""
    with INSERTION_LOCK:
        SESSION.query(RankingStats).filter(RankingStats.chat_id == chat_id).update({
            RankingStats.monthly_messages: 0,
            RankingStats.monthly_xp: 0
        })
        SESSION.commit()


def reset_daily_stats():
    """Reset daily counters globally (fallback/scheduler)"""
    with INSERTION_LOCK:
        all_chats = SESSION.query(RankingStats.chat_id).distinct().all()
        for (chat_id,) in all_chats:
            reset_chat_daily_stats(chat_id)


def reset_weekly_stats():
    """Reset weekly counters globally (fallback/scheduler)"""
    with INSERTION_LOCK:
        all_chats = SESSION.query(RankingStats.chat_id).distinct().all()
        for (chat_id,) in all_chats:
            reset_chat_weekly_stats(chat_id)


def reset_monthly_stats():
    """Reset monthly counters globally (fallback/scheduler)"""
    with INSERTION_LOCK:
        all_chats = SESSION.query(RankingStats.chat_id).distinct().all()
        for (chat_id,) in all_chats:
            reset_chat_monthly_stats(chat_id)
