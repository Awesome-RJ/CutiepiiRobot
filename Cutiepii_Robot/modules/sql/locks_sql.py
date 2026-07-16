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

# New chat added -> setup permissions
import threading

from sqlalchemy import Column, String, Boolean, text

from Cutiepii_Robot.modules.sql import SESSION, BASE
from Cutiepii_Robot import LOGGER


class Permissions(BASE):
    __tablename__ = "permissions"
    chat_id = Column(String(14), primary_key=True)
    # Booleans are for "is this locked", _NOT_ "is this allowed"
    audio = Column(Boolean, default=False)
    voice = Column(Boolean, default=False)
    contact = Column(Boolean, default=False)
    video = Column(Boolean, default=False)
    videonote = Column(Boolean, default=False)
    document = Column(Boolean, default=False)
    photo = Column(Boolean, default=False)
    sticker = Column(Boolean, default=False)
    gif = Column(Boolean, default=False)
    url = Column(Boolean, default=False)
    bots = Column(Boolean, default=False)
    forward = Column(Boolean, default=False)
    game = Column(Boolean, default=False)
    location = Column(Boolean, default=False)
    rtl = Column(Boolean, default=False)
    button = Column(Boolean, default=False)
    egame = Column(Boolean, default=False)
    inline = Column(Boolean, default=False)
    apk = Column(Boolean, default=False)
    doc = Column(Boolean, default=False)
    exe = Column(Boolean, default=False)
    jpg = Column(Boolean, default=False)
    mp3 = Column(Boolean, default=False)
    pdf = Column(Boolean, default=False)
    txt = Column(Boolean, default=False)
    xml = Column(Boolean, default=False)
    zip = Column(Boolean, default=False)
    phone = Column(Boolean, default=False)
    command = Column(Boolean, default=False)
    email = Column(Boolean, default=False)
    anonchannel = Column(Boolean, default=False)
    forwardchannel = Column(Boolean, default=False)
    forwardbot = Column(Boolean, default=False)
    videonote = Column(Boolean, default=False)
    album = Column(Boolean, default=False)
    cashtag = Column(Boolean, default=False)
    checklist = Column(Boolean, default=False)
    comment = Column(Boolean, default=False)
    emojionly = Column(Boolean, default=False)
    forwardstory = Column(Boolean, default=False)
    forwarduser = Column(Boolean, default=False)
    guestbot = Column(Boolean, default=False)
    outsidereaction = Column(Boolean, default=False)
    reaction = Column(Boolean, default=False)
    zalgo = Column(Boolean, default=False)
    emoji = Column(Boolean, default=False)
    emojicustom = Column(Boolean, default=False)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)  # ensure string
        self.audio = False
        self.voice = False
        self.contact = False
        self.video = False
        self.videonote = False
        self.document = False
        self.photo = False
        self.sticker = False
        self.gif = False
        self.url = False
        self.bots = False
        self.forward = False
        self.game = False
        self.location = False
        self.rtl = False
        self.button = False
        self.egame = False
        self.inline = False
        self.apk = False
        self.doc = False
        self.exe = False
        self.jpg = False
        self.mp3 = False
        self.pdf = False
        self.txt = False
        self.xml = False
        self.zip = False
        self.phone = False
        self.command = False
        self.email = False
        self.anonchannel = False
        self.forwardchannel = False
        self.forwardbot = False
        self.album = False
        self.cashtag = False
        self.checklist = False
        self.comment = False
        self.emojionly = False
        self.forwardstory = False
        self.forwarduser = False
        self.guestbot = False
        self.outsidereaction = False
        self.reaction = False
        self.zalgo = False
        self.emoji = False
        self.emojicustom = False

    def __repr__(self):
        return "<Permissions for %s>" % self.chat_id


class Restrictions(BASE):
    __tablename__ = "restrictions"
    chat_id = Column(String(14), primary_key=True)
    # Booleans are for "is this restricted", _NOT_ "is this allowed"
    messages = Column(Boolean, default=False)
    media = Column(Boolean, default=False)
    other = Column(Boolean, default=False)
    preview = Column(Boolean, default=False)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)  # ensure string
        self.messages = False
        self.media = False
        self.other = False
        self.preview = False

    def __repr__(self):
        return "<Restrictions for %s>" % self.chat_id

class LockConfig(BASE):
    __tablename__ = "lock_config"
    chat_id = Column(String(14), primary_key=True)
    warn = Column(Boolean, default=False)

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)  # ensure string
        self.warn = False

    def __repr__(self):
        return "<Restrictions for %s>" % self.chat_id

# For those who faced database error, Just uncomment the
# line below and run bot for 1 time & remove that line!

Permissions.__table__.create(checkfirst=True)
# Permissions.__table__.drop()
Restrictions.__table__.create(checkfirst=True)
LockConfig.__table__.create(checkfirst=True)

# Database ALTER TABLE migrations for new lock types
for col in ["album", "cashtag", "checklist", "comment", "emojionly", "forwardstory", "forwarduser", "guestbot", "outsidereaction", "reaction", "zalgo", "emoji", "emojicustom"]:
    try:
        SESSION.execute(text(f"ALTER TABLE permissions ADD COLUMN {col} BOOLEAN DEFAULT FALSE"))
        SESSION.commit()
    except Exception:
        SESSION.rollback()

PERM_LOCK = threading.RLock()
RESTR_LOCK = threading.RLock()
CONF_LOCK = threading.RLock()

# Memory caches for zero-latency lookups on message handling
PERMISSIONS_CACHE = {}
RESTRICTIONS_CACHE = {}
LOCK_CONFIG_CACHE = {}


def set_lockconf(chat_id, should_warn):
    with CONF_LOCK:
        lock_setting = SESSION.query(LockConfig).get(str(chat_id))
        if not lock_setting:
            lock_setting = LockConfig(str(chat_id))

        lock_setting.warn = should_warn
        SESSION.add(lock_setting)
        SESSION.commit()
        LOCK_CONFIG_CACHE[str(chat_id)] = should_warn


def init_permissions(chat_id, reset=False):
    with PERM_LOCK:
        curr_perm = SESSION.query(Permissions).get(str(chat_id))
        if reset and curr_perm:
            SESSION.delete(curr_perm)
            SESSION.flush()
        perm = Permissions(str(chat_id))
        SESSION.add(perm)
        SESSION.commit()
        PERMISSIONS_CACHE[str(chat_id)] = {c.name: getattr(perm, c.name) for c in perm.__table__.columns}
        return perm


def init_restrictions(chat_id, reset=False):
    with RESTR_LOCK:
        curr_restr = SESSION.query(Restrictions).get(str(chat_id))
        if reset and curr_restr:
            SESSION.delete(curr_restr)
            SESSION.flush()
        restr = Restrictions(str(chat_id))
        SESSION.add(restr)
        SESSION.commit()
        RESTRICTIONS_CACHE[str(chat_id)] = {c.name: getattr(restr, c.name) for c in restr.__table__.columns}
        return restr


def update_lock(chat_id, lock_type, locked):
    with PERM_LOCK:
        curr_perm = SESSION.query(Permissions).get(str(chat_id))
        if not curr_perm:
            curr_perm = init_permissions(chat_id)

        match lock_type:
            case "audio":
                curr_perm.audio = locked
            case "voice":
                curr_perm.voice = locked
            case "contact":
                curr_perm.contact = locked
            case "video":
                curr_perm.video = locked
            case "videonote":
                curr_perm.videonote = locked
            case "document":
                curr_perm.document = locked
            case "photo":
                curr_perm.photo = locked
            case "sticker":
                curr_perm.sticker = locked
            case "gif":
                curr_perm.gif = locked
            case "url":
                curr_perm.url = locked
            case "bots":
                curr_perm.bots = locked
            case "forward":
                curr_perm.forward = locked
            case "game":
                curr_perm.game = locked
            case "location":
                curr_perm.location = locked
            case "rtl":
                curr_perm.rtl = locked
            case "button":
                curr_perm.button = locked
            case "egame":
                curr_perm.egame = locked
            case "inline":
                curr_perm.inline = locked
            case "apk":
                curr_perm.apk = locked
            case "doc":
                curr_perm.doc = locked
            case "exe":
                curr_perm.exe = locked
            case "jpg":
                curr_perm.jpg = locked
            case "mp3":
                curr_perm.mp3 = locked
            case "pdf":
                curr_perm.pdf = locked
            case "txt":
                curr_perm.txt = locked
            case "xml":
                curr_perm.xml = locked
            case "zip":
                curr_perm.zip = locked
            case "phone":
                curr_perm.phone = locked
            case "command":
                curr_perm.command = locked
            case "email":
                curr_perm.email = locked
            case "anonchannel":
                curr_perm.anonchannel = locked
            case "forwardchannel":
                curr_perm.forwardchannel = locked
            case "forwardbot":
                curr_perm.forwardbot = locked
            case "album":
                curr_perm.album = locked
            case "cashtag":
                curr_perm.cashtag = locked
            case "checklist":
                curr_perm.checklist = locked
            case "comment":
                curr_perm.comment = locked
            case "emojionly":
                curr_perm.emojionly = locked
            case "forwardstory":
                curr_perm.forwardstory = locked
            case "forwarduser":
                curr_perm.forwarduser = locked
            case "guestbot":
                curr_perm.guestbot = locked
            case "outsidereaction":
                curr_perm.outsidereaction = locked
            case "reaction":
                curr_perm.reaction = locked
            case "zalgo":
                curr_perm.zalgo = locked
            case "emoji":
                curr_perm.emoji = locked
            case "emojicustom":
                curr_perm.emojicustom = locked

        SESSION.add(curr_perm)
        SESSION.commit()
        PERMISSIONS_CACHE[str(chat_id)] = {c.name: getattr(curr_perm, c.name) for c in curr_perm.__table__.columns}


def update_restriction(chat_id, restr_type, locked):
    with RESTR_LOCK:
        curr_restr = SESSION.query(Restrictions).get(str(chat_id))
        if not curr_restr:
            curr_restr = init_restrictions(chat_id)

        match restr_type:
            case "messages":
                curr_restr.messages = locked
            case "media":
                curr_restr.media = locked
            case "other":
                curr_restr.other = locked
            case "previews":
                curr_restr.preview = locked
            case "all":
                curr_restr.messages = locked
                curr_restr.media = locked
                curr_restr.other = locked
                curr_restr.preview = locked
        SESSION.add(curr_restr)
        SESSION.commit()
        RESTRICTIONS_CACHE[str(chat_id)] = {c.name: getattr(curr_restr, c.name) for c in curr_restr.__table__.columns}


def is_locked(chat_id, lock_type):
    curr_perm = PERMISSIONS_CACHE.get(str(chat_id))
    if not curr_perm:
        return False
    return curr_perm.get(lock_type, False)


def is_restr_locked(chat_id, lock_type):
    curr_restr = RESTRICTIONS_CACHE.get(str(chat_id))
    if not curr_restr:
        return False

    if lock_type == "all":
        return (
            curr_restr.get("messages", False)
            and curr_restr.get("media", False)
            and curr_restr.get("other", False)
            and curr_restr.get("preview", False)
        )
    elif lock_type == "previews":
        return curr_restr.get("preview", False)
    return curr_restr.get(lock_type, False)


def get_locks(chat_id):
    try:
        return SESSION.query(Permissions).get(str(chat_id))
    finally:
        SESSION.close()


def get_restr(chat_id):
    try:
        return SESSION.query(Restrictions).get(str(chat_id))
    finally:
        SESSION.close()


def get_lockconf(chat_id) -> bool:
    return LOCK_CONFIG_CACHE.get(str(chat_id), False)


def migrate_chat(old_chat_id, new_chat_id):
    with PERM_LOCK:
        perms = SESSION.query(Permissions).get(str(old_chat_id))
        if perms:
            perms.chat_id = str(new_chat_id)
            PERMISSIONS_CACHE[str(new_chat_id)] = {c.name: getattr(perms, c.name) for c in perms.__table__.columns}
            if str(old_chat_id) in PERMISSIONS_CACHE:
                del PERMISSIONS_CACHE[str(old_chat_id)]
        SESSION.commit()

    with RESTR_LOCK:
        rest = SESSION.query(Restrictions).get(str(old_chat_id))
        if rest:
            rest.chat_id = str(new_chat_id)
            RESTRICTIONS_CACHE[str(new_chat_id)] = {c.name: getattr(rest, c.name) for c in rest.__table__.columns}
            if str(old_chat_id) in RESTRICTIONS_CACHE:
                del RESTRICTIONS_CACHE[str(old_chat_id)]
        SESSION.commit()


def __load_locks():
    global PERMISSIONS_CACHE, RESTRICTIONS_CACHE, LOCK_CONFIG_CACHE
    try:
        all_perms = SESSION.query(Permissions).all()
        for perm in all_perms:
            PERMISSIONS_CACHE[perm.chat_id] = {c.name: getattr(perm, c.name) for c in perm.__table__.columns}
        
        all_restrs = SESSION.query(Restrictions).all()
        for restr in all_restrs:
            RESTRICTIONS_CACHE[restr.chat_id] = {c.name: getattr(restr, c.name) for c in restr.__table__.columns}
            
        all_configs = SESSION.query(LockConfig).all()
        for config in all_configs:
            LOCK_CONFIG_CACHE[config.chat_id] = config.warn
            
        LOGGER.info(f"[SQL] Loaded locks: {len(PERMISSIONS_CACHE)} perms, {len(RESTRICTIONS_CACHE)} restrictions, {len(LOCK_CONFIG_CACHE)} configs")
    except Exception as e:
        LOGGER.error(f"[SQL] Failed to load locks into memory: {e}")
    finally:
        SESSION.close()


try:
    __load_locks()
except Exception as e:
    LOGGER.error(f"[SQL] Failed to initialize locks module: {e}")
