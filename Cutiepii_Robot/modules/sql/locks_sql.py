"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, [ https://github.com/Awesome-RJ ]
Copyright (c) 2021-2022, Yūki • Black Knights Union, [ https://github.com/Awesome-RJ/CutiepiiRobot ]

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

from sqlalchemy import Column, String, Boolean

from Cutiepii_Robot.modules.sql import SESSION, BASE


class Permissions(BASE):
    __tablename__ = "permissions"
    chat_id = Column(String(14), primary_key=True)
    # Booleans are for "is this locked", _NOT_ "is this allowed"
    audio = Column(Boolean, default=False)
    voice = Column(Boolean, default=False)
    contact = Column(Boolean, default=False)
    video = Column(Boolean, default=False)
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

    def __init__(self, chat_id):
        self.chat_id = str(chat_id)  # ensure string
        self.audio = False
        self.voice = False
        self.contact = False
        self.video = False
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

    def __repr__(self):
        return f"<Permissions for {self.chat_id}>"


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
        return f"<Restrictions for {self.chat_id}>"


# For those who faced database error, Just uncomment the
# line below and run bot for 1 time & remove that line!

Permissions.__table__.create(checkfirst=True)
# Permissions.__table__.drop()
Restrictions.__table__.create(checkfirst=True)

PERM_LOCK = threading.RLock()
RESTR_LOCK = threading.RLock()


def init_permissions(chat_id, reset=False):
    curr_perm = SESSION.query(Permissions).get(str(chat_id))
    if reset:
        SESSION.delete(curr_perm)
        SESSION.flush()
    perm = Permissions(str(chat_id))
    SESSION.add(perm)
    SESSION.commit()
    return perm


def init_restrictions(chat_id, reset=False):
    curr_restr = SESSION.query(Restrictions).get(str(chat_id))
    if reset:
        SESSION.delete(curr_restr)
        SESSION.flush()
    restr = Restrictions(str(chat_id))
    SESSION.add(restr)
    SESSION.commit()
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

        SESSION.add(curr_perm)
        SESSION.commit()


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


def is_locked(chat_id, lock_type):
    curr_perm = SESSION.query(Permissions).get(str(chat_id))
    SESSION.close()

    if not curr_perm:
        return False

    match lock_type:
        case "sticker":
            return curr_perm.sticker
        case "photo":
            return curr_perm.photo
        case "audio":
            return curr_perm.audio
        case "voice":
            return curr_perm.voice
        case "contact":
            return curr_perm.contact
        case "video":
            return curr_perm.video
        case "document":
            return curr_perm.document
        case "gif":
            return curr_perm.gif
        case "url":
            return curr_perm.url
        case "bots":
            return curr_perm.bots
        case "forward":
            return curr_perm.forward
        case "game":
            return curr_perm.game
        case "location":
            return curr_perm.location
        case "rtl":
            return curr_perm.rtl
        case "button":
            return curr_perm.button
        case "egame":
            return curr_perm.egame
        case "inline":
            return curr_perm.inline
        case "apk":
            return curr_perm.apk
        case "doc":
            return curr_perm.doc
        case "exe":
            return curr_perm.exe
        case "jpg":
            return curr_perm.jpg
        case "mp3":
            return curr_perm.mp3
        case "pdf":
            return curr_perm.pdf
        case "txt":
            return curr_perm.txt
        case "xml":
            return curr_perm.xml
        case "zip":
            return curr_perm.zip


def is_restr_locked(chat_id, lock_type):
    curr_restr = SESSION.query(Restrictions).get(str(chat_id))
    SESSION.close()

    if not curr_restr:
        return False

    match lock_type:
        case "messages":
            return curr_restr.messages
        case "media":
            return curr_restr.media
        case "other":
            return curr_restr.other
        case "previews":
            return curr_restr.preview
        case "all":
            return (
                curr_restr.messages
                and curr_restr.media
                and curr_restr.other
                and curr_restr.preview
            )


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


def migrate_chat(old_chat_id, new_chat_id):
    with PERM_LOCK:
        if perms := SESSION.query(Permissions).get(str(old_chat_id)):
            perms.chat_id = str(new_chat_id)
        SESSION.commit()

    with RESTR_LOCK:
        if rest := SESSION.query(Restrictions).get(str(old_chat_id)):
            rest.chat_id = str(new_chat_id)
        SESSION.commit()
