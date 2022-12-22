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

import threading

from sqlalchemy import Column, UnicodeText, Boolean

from Cutiepii_Robot.modules.sql import BASE, SESSION


class CleanerBlueTextChatSettings(BASE):
    __tablename__ = "cleaner_bluetext_chat_setting"
    chat_id = Column(UnicodeText, primary_key=True)
    is_enable = Column(Boolean, default=False)

    def __init__(self, chat_id, is_enable):
        self.chat_id = chat_id
        self.is_enable = is_enable

    def __repr__(self):
        return f"clean blue text for {self.chat_id}"


class CleanerBlueTextChat(BASE):
    __tablename__ = "cleaner_bluetext_chat_ignore_commands"
    chat_id = Column(UnicodeText, primary_key=True)
    command = Column(UnicodeText, primary_key=True)

    def __init__(self, chat_id, commands):
        self.chat_id = chat_id
        self.commands = commands


class CleanerBlueTextGlobal(BASE):
    __tablename__ = "cleaner_bluetext_global_ignore_commands"
    command = Column(UnicodeText, primary_key=True)

    def __init__(self, commands):
        self.commands = commands


CleanerBlueTextChatSettings.__table__.create(checkfirst=True)
CleanerBlueTextChat.__table__.create(checkfirst=True)
CleanerBlueTextGlobal.__table__.create(checkfirst=True)

CLEANER_CHAT_SETTINGS = threading.RLock()
CLEANER_CHAT_LOCK = threading.RLock()
CLEANER_GLOBAL_LOCK = threading.RLock()

CLEANER_CHATS = {}
GLOBAL_IGNORE_COMMANDS = set()


def set_cleanbt(chat_id, is_enable):
    with CLEANER_CHAT_SETTINGS:
        if curr := SESSION.query(CleanerBlueTextChatSettings).get(
                str(chat_id)):
            SESSION.delete(curr)

        newcurr = CleanerBlueTextChatSettings(str(chat_id), is_enable)

        SESSION.add(newcurr)
        SESSION.commit()


def chat_ignore_command(chat_id, ignore):
    ignore = ignore.lower()
    with CLEANER_CHAT_LOCK:
        ignored = SESSION.query(CleanerBlueTextChat).get(
            (str(chat_id), ignore))

        if not ignored:

            if str(chat_id) not in CLEANER_CHATS:
                CLEANER_CHATS.setdefault(str(chat_id), {
                    "setting": False,
                    "commands": set()
                })

            CLEANER_CHATS[str(chat_id)]["commands"].add(ignore)

            ignored = CleanerBlueTextChat(str(chat_id), ignore)
            SESSION.add(ignored)
            SESSION.commit()
            return True
        SESSION.close()
        return False


def chat_unignore_command(chat_id, unignore):
    unignore = unignore.lower()
    with CLEANER_CHAT_LOCK:
        if unignored := SESSION.query(CleanerBlueTextChat).get(
            (str(chat_id), unignore)):
            if str(chat_id) not in CLEANER_CHATS:
                CLEANER_CHATS.setdefault(str(chat_id), {
                    "setting": False,
                    "commands": set()
                })
            if unignore in CLEANER_CHATS.get(str(chat_id)).get("commands"):
                CLEANER_CHATS[str(chat_id)]["commands"].remove(unignore)

            SESSION.delete(unignored)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def global_ignore_command(commands):
    commands = frozenset({command.lower()})
    with CLEANER_GLOBAL_LOCK:
        ignored = SESSION.query(CleanerBlueTextGlobal).get(str(commands))

        if not ignored:
            GLOBAL_IGNORE_COMMANDS.add(commands)

            ignored = CleanerBlueTextGlobal(str(commands))
            SESSION.add(ignored)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def global_unignore_command(commands):
    commands = frozenset({command.lower()})
    with CLEANER_GLOBAL_LOCK:
        if unignored := SESSION.query(CleanerBlueTextGlobal).get(
                str(commands)):
            if command in GLOBAL_IGNORE_COMMANDS:
                GLOBAL_IGNORE_COMMANDS.remove(commands)

            SESSION.delete(commands)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def is_command_ignored(chat_id, commands):
    if frozenset({command.lower()}) in GLOBAL_IGNORE_COMMANDS:
        return True

    if str(chat_id) in CLEANER_CHATS and frozenset(
        {command.lower()}) in CLEANER_CHATS.get(str(chat_id)).get("commands"):
        return True

    return False


def is_enabled(chat_id):
    try:
        if resultcurr := SESSION.query(CleanerBlueTextChatSettings).get(
                str(chat_id)):
            return resultcurr.is_enable
        return False  #default
    finally:
        SESSION.close()


def get_all_ignored(chat_id):
    if str(chat_id) in CLEANER_CHATS:
        LOCAL_IGNORE_COMMANDS = CLEANER_CHATS.get(str(chat_id)).get("commands")
    else:
        LOCAL_IGNORE_COMMANDS = set()

    return GLOBAL_IGNORE_COMMANDS, LOCAL_IGNORE_COMMANDS


def __load_cleaner_list():
    global GLOBAL_IGNORE_COMMANDS

    try:
        GLOBAL_IGNORE_COMMANDS = {
            x.command
            for x in SESSION.query(CleanerBlueTextGlobal).all()
        }
    finally:
        SESSION.close()

    try:
        for x in SESSION.query(CleanerBlueTextChatSettings).all():
            CLEANER_CHATS.setdefault(x.chat_id, {
                "setting": False,
                "commands": set()
            })
            CLEANER_CHATS[x.chat_id]["setting"] = x.is_enable
    finally:
        SESSION.close()

    try:
        for x in SESSION.query(CleanerBlueTextChat).all():
            CLEANER_CHATS.setdefault(x.chat_id, {
                "setting": False,
                "commands": set()
            })
            CLEANER_CHATS[x.chat_id]["commands"].add(x.command)
    finally:
        SESSION.close()


__load_cleaner_list()
