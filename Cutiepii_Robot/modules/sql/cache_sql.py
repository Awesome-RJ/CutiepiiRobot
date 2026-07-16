"""
BSD 2-Clause License
Cache SQL Module - Replaces Redis cache functionality
For storing temporary data like tag alerts, admin cache, etc.
"""

from sqlalchemy import Column, String, BigInteger, UnicodeText, DateTime, Integer
from sqlalchemy.sql.sqltypes import BigInteger as BigInt
from Cutiepii_Robot.modules.sql import BASE, SESSION
from datetime import datetime, timezone, timedelta
import threading
import json

INSERTION_LOCK = threading.RLock()


class KeyValueCache(BASE):
    __tablename__ = "key_value_cache"
    
    key = Column(String(255), primary_key=True)
    value = Column(UnicodeText, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def __init__(self, key, value, ttl=None):
        self.key = key
        self.value = value
        self.created_at = datetime.now(timezone.utc)
        if ttl:
            self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)


class SetCache(BASE):
    __tablename__ = "set_cache"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(255), nullable=False, index=True)
    value = Column(String(255), nullable=False)
    
    def __init__(self, key, value):
        self.key = key
        self.value = value


class HashCache(BASE):
    __tablename__ = "hash_cache"
    
    key = Column(String(255), primary_key=True)
    field = Column(String(255), primary_key=True)
    value = Column(UnicodeText, nullable=False)
    
    def __init__(self, key, field, value):
        self.key = key
        self.field = field
        self.value = value


KeyValueCache.__table__.create(checkfirst=True)
SetCache.__table__.create(checkfirst=True)
HashCache.__table__.create(checkfirst=True)


# ===========================
# Key-Value Operations
# ===========================

def cache_set(key: str, value: str, ttl: int = None):
    """Set a key-value pair with optional TTL"""
    with INSERTION_LOCK:
        cache = SESSION.query(KeyValueCache).filter(
            KeyValueCache.key == key
        ).first()
        
        if cache:
            cache.value = value
            if ttl:
                cache.expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl)
        else:
            cache = KeyValueCache(key, value, ttl)
            SESSION.add(cache)
        
        SESSION.commit()


def cache_get(key: str) -> str:
    """Get value by key"""
    try:
        cache = SESSION.query(KeyValueCache).filter(
            KeyValueCache.key == key
        ).first()
        
        if not cache:
            return None
        
        # Check expiration
        if cache.expires_at and cache.expires_at < datetime.now(timezone.utc):
            cache_delete(key)
            return None
        
        return cache.value
    finally:
        SESSION.close()


def cache_delete(key: str):
    """Delete a key"""
    with INSERTION_LOCK:
        SESSION.query(KeyValueCache).filter(
            KeyValueCache.key == key
        ).delete()
        SESSION.commit()


def cache_exists(key: str) -> bool:
    """Check if key exists and is not expired"""
    return cache_get(key) is not None


# ===========================
# Set Operations
# ===========================

def cache_sadd(key: str, *values):
    """Add values to a set"""
    with INSERTION_LOCK:
        for value in values:
            # Check if already exists
            exists = SESSION.query(SetCache).filter(
                SetCache.key == key,
                SetCache.value == str(value)
            ).first()
            
            if not exists:
                cache_item = SetCache(key, str(value))
                SESSION.add(cache_item)
        
        SESSION.commit()


def cache_smembers(key: str) -> set:
    """Get all members of a set"""
    try:
        members = SESSION.query(SetCache).filter(
            SetCache.key == key
        ).all()
        return {m.value for m in members}
    finally:
        SESSION.close()


def cache_srem(key: str, *values):
    """Remove values from a set"""
    with INSERTION_LOCK:
        for value in values:
            SESSION.query(SetCache).filter(
                SetCache.key == key,
                SetCache.value == str(value)
            ).delete()
        SESSION.commit()


def cache_sismember(key: str, value: str) -> bool:
    """Check if value is in set"""
    try:
        return bool(SESSION.query(SetCache).filter(
            SetCache.key == key,
            SetCache.value == str(value)
        ).first())
    finally:
        SESSION.close()


# ===========================
# Hash Operations
# ===========================

def cache_hset(key: str, field: str, value: str):
    """Set hash field"""
    with INSERTION_LOCK:
        cache = SESSION.query(HashCache).filter(
            HashCache.key == key,
            HashCache.field == field
        ).first()
        
        if cache:
            cache.value = value
        else:
            cache = HashCache(key, field, value)
            SESSION.add(cache)
        
        SESSION.commit()


def cache_hget(key: str, field: str) -> str:
    """Get hash field"""
    try:
        cache = SESSION.query(HashCache).filter(
            HashCache.key == key,
            HashCache.field == field
        ).first()
        return cache.value if cache else None
    finally:
        SESSION.close()


def cache_hgetall(key: str) -> dict:
    """Get all hash fields"""
    try:
        items = SESSION.query(HashCache).filter(
            HashCache.key == key
        ).all()
        return {item.field: item.value for item in items}
    finally:
        SESSION.close()


def cache_hdel(key: str, *fields):
    """Delete hash fields"""
    with INSERTION_LOCK:
        for field in fields:
            SESSION.query(HashCache).filter(
                HashCache.key == key,
                HashCache.field == field
            ).delete()
        SESSION.commit()


# ===========================
# Cleanup Functions
# ===========================

def cleanup_expired():
    """Remove expired cache entries"""
    with INSERTION_LOCK:
        SESSION.query(KeyValueCache).filter(
            KeyValueCache.expires_at != None,
            KeyValueCache.expires_at < datetime.now(timezone.utc)
        ).delete()
        SESSION.commit()


def clear_cache_prefix(prefix: str):
    """Clear all cache entries with a specific prefix"""
    with INSERTION_LOCK:
        # Key-value
        SESSION.query(KeyValueCache).filter(
            KeyValueCache.key.like(f"{prefix}%")
        ).delete(synchronize_session=False)
        
        # Sets
        SESSION.query(SetCache).filter(
            SetCache.key.like(f"{prefix}%")
        ).delete(synchronize_session=False)
        
        # Hashes
        SESSION.query(HashCache).filter(
            HashCache.key.like(f"{prefix}%")
        ).delete(synchronize_session=False)
        
        SESSION.commit()


# ===========================
# JSON Helper Functions
# ===========================

def cache_set_json(key: str, data: dict, ttl: int = None):
    """Store JSON data"""
    cache_set(key, json.dumps(data), ttl)


def cache_get_json(key: str) -> dict:
    """Get JSON data"""
    value = cache_get(key)
    if value:
        try:
            return json.loads(value)
        except:
            return None
    return None
