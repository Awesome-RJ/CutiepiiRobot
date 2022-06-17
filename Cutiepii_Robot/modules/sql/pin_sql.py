import threading

from sqlalchemy import Column, String, Boolean

from Cutiepii_Robot.modules.sql import SESSION, BASE

class CleanLinked(BASE):
    __tablename__ = "clean_linked"
    chat_id = Column(String(14), primary_key=True)
    status = Column(Boolean, default=False)

    def __init__(self, chat_id, status):
        self.chat_id = str(chat_id)
        self.status = status

class AntiChannelPin(BASE):
    __tablename__ = "anti_channelpin"
    chat_id = Column(String(14), primary_key=True)
    status = Column(Boolean, default=False)

    def __init__(self, chat_id, status):
        self.chat_id = str(chat_id)
        self.status = status

CleanLinked.__table__.create(checkfirst=True)
AntiChannelPin.__table__.create(checkfirst=True)

CLEANLINKED_LOCK = threading.RLock()
ANTICHANNELPIN_LOCK = threading.RLock()

def getCleanLinked(chat_id):
    try:
        if resultObj := SESSION.query(CleanLinked).get(str(chat_id)):
            return resultObj.status
        return False #default
    finally:
        SESSION.close()

def setCleanLinked(chat_id, status):
    with CLEANLINKED_LOCK:
        if prevObj := SESSION.query(CleanLinked).get(str(chat_id)):
            SESSION.delete(prevObj)
        newObj = CleanLinked(str(chat_id), status)
        SESSION.add(newObj)
        SESSION.commit()


def getAntiChannelPin(chat_id):
    try:
        if resultObj := SESSION.query(AntiChannelPin).get(str(chat_id)):
            return resultObj.status
        return False #default
    finally:
        SESSION.close()

def setAntiChannelPin(chat_id, status):
    with ANTICHANNELPIN_LOCK:
        if prevObj := SESSION.query(AntiChannelPin).get(str(chat_id)):
            SESSION.delete(prevObj)
        newObj = AntiChannelPin(str(chat_id), status)
        SESSION.add(newObj)
        SESSION.commit()
