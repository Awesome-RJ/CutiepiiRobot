import threading

from sqlalchemy import Column, String
from Cutiepii_Robot.modules.sql import BASE, SESSION
class CutiepiiChats(BASE):
    __tablename__ = "cutiepii_chats"
    chat_id = Column(String(14), primary_key=True)

    def __init__(self, chat_id):
        self.chat_id = chat_id

CutiepiiChats.__table__.create(checkfirst=True)
INSERTION_LOCK = threading.RLock()


def is_cutiepii(chat_id):
    try:
        chat = SESSION.query(CutiepiiChats).get(str(chat_id))
        return bool(chat)
    finally:
        SESSION.close()

def set_cutiepii(chat_id):
    with INSERTION_LOCK:
        cutiepiichat = SESSION.query(CutiepiiChats).get(str(chat_id))
        if not cutiepiichat:
            cutiepiichat = CutiepiiChats(str(chat_id))
        SESSION.add(cutiepiichat)
        SESSION.commit()

def rem_cutiepii(chat_id):
    with INSERTION_LOCK:
        cutiepiichat = SESSION.query(CutiepiiChats).get(str(chat_id))
        if cutiepiichat:
            SESSION.delete(cutiepiichat)
        SESSION.commit()


def get_all_cutiepii_chats():
    try:
        return SESSION.query(CutiepiiChats.chat_id).all()
    finally:
        SESSION.close()
