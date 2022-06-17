import threading

from Cutiepii_Robot.modules.sql import BASE, SESSION
from sqlalchemy import Integer, String, Column, UnicodeText


class ClearCmd(BASE):
    __tablename__ = "clear_cmd"
    chat_id = Column(String(14), primary_key=True)
    cmd = Column(UnicodeText, primary_key=True, nullable=False)
    time = Column(Integer)

    def __init__(self, chat_id, cmd, time):
        self.chat_id = chat_id
        self.cmd = cmd
        self.time = time


ClearCmd.__table__.create(checkfirst=True)

CLEAR_CMD_LOCK = threading.RLock()


def get_allclearcmd(chat_id):
    try:
        return SESSION.query(ClearCmd).filter(ClearCmd.chat_id == str(chat_id)).all()
    finally:
        SESSION.close()


def get_clearcmd(chat_id, cmd):
    try:
        if clear_cmd := SESSION.query(ClearCmd).get((str(chat_id), cmd)):
            return clear_cmd
        return False
    finally:
        SESSION.close()


def set_clearcmd(chat_id, cmd, time):
    with CLEAR_CMD_LOCK:
        clear_cmd = SESSION.query(ClearCmd).get((str(chat_id), cmd))
        if not clear_cmd:
            clear_cmd = ClearCmd(str(chat_id), cmd, time)

        clear_cmd.time = time
        SESSION.add(clear_cmd)
        SESSION.commit()


def del_clearcmd(chat_id, cmd):
    with CLEAR_CMD_LOCK:
        if del_cmd := SESSION.query(ClearCmd).get((str(chat_id), cmd)):
            SESSION.delete(del_cmd)
            SESSION.commit()
            return True
        SESSION.close()
        return False


def del_allclearcmd(chat_id):
    with CLEAR_CMD_LOCK:
        if (
            del_cmd := SESSION.query(ClearCmd)
            .filter(ClearCmd.chat_id == str(chat_id))
            .all()
        ):
            for cmd in del_cmd:
                SESSION.delete(cmd)
                SESSION.commit()
            return True
        SESSION.close()
        return False


def migrate_chat(old_chat_id, new_chat_id):
    with CLEAR_CMD_LOCK:
        chat_filters = (
            SESSION.query(ClearCmd)
            .filter(ClearCmd.chat_id == str(old_chat_id))
            .all()
        )
        for filt in chat_filters:
            filt.chat_id = str(new_chat_id)
        SESSION.commit()
