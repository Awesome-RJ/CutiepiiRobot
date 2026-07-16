"""
BSD 2-Clause License
Couples SQL Module - Replaces couples_mongo.py
"""

from sqlalchemy import Column, String, Date
from sqlalchemy.sql.sqltypes import BigInteger
from Cutiepii_Robot.modules.sql import BASE, SESSION
from datetime import date
import threading

INSERTION_LOCK = threading.RLock()


class Couple(BASE):
    __tablename__ = "couples"
    
    chat_id = Column(BigInteger, primary_key=True)
    couple_date = Column(Date, primary_key=True)
    user1_id = Column(BigInteger, nullable=False)
    user2_id = Column(BigInteger, nullable=False)
    
    def __init__(self, chat_id, user1_id, user2_id, couple_date=None):
        self.chat_id = chat_id
        self.user1_id = user1_id
        self.user2_id = user2_id
        self.couple_date = couple_date or date.today()
    
    def __repr__(self):
        return f"<Couple(chat={self.chat_id}, users=({self.user1_id}, {self.user2_id}))>"


Couple.__table__.create(checkfirst=True)


def get_couple(chat_id: int, couple_date: date = None) -> tuple:
    """Get couple of the day for a chat"""
    if not couple_date:
        couple_date = date.today()
    
    try:
        couple = SESSION.query(Couple).filter(
            Couple.chat_id == chat_id,
            Couple.couple_date == couple_date
        ).first()
        
        if couple:
            return (couple.user1_id, couple.user2_id)
        return None
    finally:
        SESSION.close()


def set_couple(chat_id: int, user1_id: int, user2_id: int, couple_date: date = None):
    """Set couple of the day"""
    if not couple_date:
        couple_date = date.today()
    
    with INSERTION_LOCK:
        couple = SESSION.query(Couple).filter(
            Couple.chat_id == chat_id,
            Couple.couple_date == couple_date
        ).first()
        
        if couple:
            couple.user1_id = user1_id
            couple.user2_id = user2_id
        else:
            couple = Couple(chat_id, user1_id, user2_id, couple_date)
            SESSION.add(couple)
        
        SESSION.commit()


def get_user_couple_history(user_id: int) -> list:
    """Get all couples a user has been part of"""
    try:
        from sqlalchemy import or_
        couples = SESSION.query(Couple).filter(
            or_(Couple.user1_id == user_id, Couple.user2_id == user_id)
        ).order_by(Couple.couple_date.desc()).limit(10).all()
        return couples
    finally:
        SESSION.close()
