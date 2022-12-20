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

import ast
import threading

from Cutiepii_Robot import CUTIEPII_PTB, LOGGER
from Cutiepii_Robot.modules.sql import BASE, SESSION
from telegram.error import BadRequest, Forbidden
from sqlalchemy import Boolean, Column, Integer, String, UnicodeText
from sqlalchemy.sql.sqltypes import BigInteger


class Federations(BASE):
    __tablename__ = "feds"
    owner_id = Column(String(14))
    fed_name = Column(UnicodeText)
    fed_id = Column(UnicodeText, primary_key=True)
    fed_rules = Column(UnicodeText)
    fed_log = Column(UnicodeText)
    fed_users = Column(UnicodeText)

    def __init__(self, owner_id, fed_name, fed_id, fed_rules, fed_log,
                 fed_users):
        self.owner_id = owner_id
        self.fed_name = fed_name
        self.fed_id = fed_id
        self.fed_rules = fed_rules
        self.fed_log = fed_log
        self.fed_users = fed_users


class ChatF(BASE):
    __tablename__ = "chat_feds"
    chat_id = Column(String(14), primary_key=True)
    chat_name = Column(UnicodeText)
    fed_id = Column(UnicodeText)

    def __init__(self, chat_id, chat_name, fed_id):
        self.chat_id = chat_id
        self.chat_name = chat_name
        self.fed_id = fed_id


class BansF(BASE):
    __tablename__ = "bans_feds"
    fed_id = Column(UnicodeText, primary_key=True)
    user_id = Column(String(14), primary_key=True)
    first_name = Column(UnicodeText, nullable=False)
    last_name = Column(UnicodeText)
    user_name = Column(UnicodeText)
    reason = Column(UnicodeText, default="")
    time = Column(Integer, default=0)

    def __init__(self, fed_id, user_id, first_name, last_name, user_name,
                 reason, time):
        self.fed_id = fed_id
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.user_name = user_name
        self.reason = reason
        self.time = time


class FedsUserSettings(BASE):
    __tablename__ = "feds_settings"
    user_id = Column(BigInteger, primary_key=True)
    should_report = Column(Boolean, default=True)

    def __init__(self, user_id):
        self.user_id = user_id

    def __repr__(self):
        return f"<Feds report settings ({self.user_id})>"


class FedSubs(BASE):
    __tablename__ = "feds_subs"
    fed_id = Column(UnicodeText, primary_key=True)
    fed_subs = Column(UnicodeText, primary_key=True, nullable=False)

    def __init__(self, fed_id, fed_subs):
        self.fed_id = fed_id
        self.fed_subs = fed_subs

    def __repr__(self):
        return f"<Fed {self.fed_id} subscribes for {self.fed_subs}>"


# Dropping db
# Federations.__table__.drop()
# ChatF.__table__.drop()
# BansF.__table__.drop()
# FedSubs.__table__.drop()

Federations.__table__.create(checkfirst=True)
ChatF.__table__.create(checkfirst=True)
BansF.__table__.create(checkfirst=True)
FedsUserSettings.__table__.create(checkfirst=True)
FedSubs.__table__.create(checkfirst=True)

FEDS_LOCK = threading.RLock()
CHAT_FEDS_LOCK = threading.RLock()
FEDS_SETTINGS_LOCK = threading.RLock()
FEDS_SUBSCRIBER_LOCK = threading.RLock()

FEDERATION_BYNAME = {}
FEDERATION_BYOWNER = {}
FEDERATION_BYFEDID = {}

FEDERATION_CHATS = {}
FEDERATION_CHATS_BYID = {}

FEDERATION_BANNED_FULL = {}
FEDERATION_BANNED_USERID = {}

FEDERATION_NOTIFICATION = {}
FEDS_SUBSCRIBER = {}
MYFEDS_SUBSCRIBER = {}


def get_fed_info(fed_id):
    get = FEDERATION_BYFEDID.get(str(fed_id))
    if get is None:
        return False
    return get


def get_fed_id(chat_id):
    get = FEDERATION_CHATS.get(str(chat_id))
    if get is None:
        return False
    return get["fid"]


def get_fed_name(chat_id):
    get = FEDERATION_CHATS.get(str(chat_id))
    if get is None:
        return False
    return get["chat_name"]


def get_user_fban(fed_id, user_id):
    if not FEDERATION_BANNED_FULL.get(fed_id):
        return False, False, False
    user_info = FEDERATION_BANNED_FULL[fed_id].get(user_id)
    if not user_info:
        return None, None, None
    return user_info["first_name"], user_info["reason"], user_info["time"]


def get_user_admin_fed_name(user_id):
    return [
        FEDERATION_BYFEDID[f]["fname"] for f in FEDERATION_BYFEDID
        if int(user_id) in ast.literal_eval(
            ast.literal_eval(FEDERATION_BYFEDID[f]["fusers"])["members"])
    ]


def get_user_owner_fed_name(user_id):
    return [
        FEDERATION_BYFEDID[f]["fname"] for f in FEDERATION_BYFEDID
        if int(user_id) == int(
            ast.literal_eval(FEDERATION_BYFEDID[f]["fusers"])["owner"])
    ]


def get_user_admin_fed_full(user_id):
    return [{
        "fed_id": f,
        "fed": FEDERATION_BYFEDID[f]
    } for f in FEDERATION_BYFEDID if int(user_id) in ast.literal_eval(
        ast.literal_eval(FEDERATION_BYFEDID[f]["fusers"])["members"])]


def get_user_owner_fed_full(user_id):
    return [{
        "fed_id": f,
        "fed": FEDERATION_BYFEDID[f]
    } for f in FEDERATION_BYFEDID if int(user_id) == int(
        ast.literal_eval(FEDERATION_BYFEDID[f]["fusers"])["owner"])]


def get_user_fbanlist(user_id):
    banlist = FEDERATION_BANNED_FULL
    user_name = ""
    fedname = []
    for x in banlist:
        if banlist[x].get(user_id):
            if not user_name:
                user_name = banlist[x][user_id].get("first_name")
            fedname.append([x, banlist[x][user_id].get("reason")])
    return user_name, fedname


def new_fed(owner_id, fed_name, fed_id):
    with FEDS_LOCK:
        fed = Federations(
            str(owner_id),
            fed_name,
            str(fed_id),
            "Rules is not set in this federation.",
            None,
            str({
                "owner": str(owner_id),
                "members": "[]"
            }),
        )
        SESSION.add(fed)
        SESSION.commit()
        FEDERATION_BYOWNER[str(owner_id)] = {
            "fid": str(fed_id),
            "fname": fed_name,
            "frules": "Rules is not set in this federation.",
            "flog": None,
            "fusers": str({
                "owner": str(owner_id),
                "members": "[]"
            }),
        }
        FEDERATION_BYFEDID[str(fed_id)] = {
            "owner": str(owner_id),
            "fname": fed_name,
            "frules": "Rules is not set in this federation.",
            "flog": None,
            "fusers": str({
                "owner": str(owner_id),
                "members": "[]"
            }),
        }
        FEDERATION_BYNAME[fed_name] = {
            "fid": str(fed_id),
            "owner": str(owner_id),
            "frules": "Rules is not set in this federation.",
            "flog": None,
            "fusers": str({
                "owner": str(owner_id),
                "members": "[]"
            }),
        }
        return fed


def del_fed(fed_id):
    with FEDS_LOCK:
        getcache = FEDERATION_BYFEDID.get(fed_id)
        if getcache is None:
            return False
        # Variables
        getfed = FEDERATION_BYFEDID.get(fed_id)
        owner_id = getfed["owner"]
        fed_name = getfed["fname"]
        # Delete from cache
        FEDERATION_BYOWNER.pop(owner_id)
        FEDERATION_BYFEDID.pop(fed_id)
        FEDERATION_BYNAME.pop(fed_name)
        if FEDERATION_CHATS_BYID.get(fed_id):
            for x in FEDERATION_CHATS_BYID[fed_id]:
                if delchats := SESSION.query(ChatF).get(str(x)):
                    SESSION.delete(delchats)
                    SESSION.commit()
                FEDERATION_CHATS.pop(x)
            FEDERATION_CHATS_BYID.pop(fed_id)
        if getall := FEDERATION_BANNED_USERID.get(fed_id):
            for x in getall:
                if banlist := SESSION.query(BansF).get((fed_id, str(x))):
                    SESSION.delete(banlist)
                    SESSION.commit()
        if FEDERATION_BANNED_USERID.get(fed_id):
            FEDERATION_BANNED_USERID.pop(fed_id)
        if FEDERATION_BANNED_FULL.get(fed_id):
            FEDERATION_BANNED_FULL.pop(fed_id)
        if getall := MYFEDS_SUBSCRIBER.get(fed_id):
            for x in getall:
                if getsubs := SESSION.query(FedSubs).get((fed_id, str(x))):
                    SESSION.delete(getsubs)
                    SESSION.commit()
        if FEDS_SUBSCRIBER.get(fed_id):
            FEDS_SUBSCRIBER.pop(fed_id)
        if MYFEDS_SUBSCRIBER.get(fed_id):
            MYFEDS_SUBSCRIBER.pop(fed_id)
        if curr := SESSION.query(Federations).get(fed_id):
            SESSION.delete(curr)
            SESSION.commit()
        return True


def rename_fed(fed_id, owner_id, newname):
    with FEDS_LOCK:
        fed = SESSION.query(Federations).get(fed_id)
        if not fed:
            return False
        fed.fed_name = newname
        SESSION.commit()

        # Update the dicts
        oldname = FEDERATION_BYFEDID[str(fed_id)]["fname"]
        tempdata = FEDERATION_BYNAME[oldname]
        FEDERATION_BYNAME.pop(oldname)

        FEDERATION_BYOWNER[str(owner_id)]["fname"] = newname
        FEDERATION_BYFEDID[str(fed_id)]["fname"] = newname
        FEDERATION_BYNAME[newname] = tempdata
        return True


def chat_join_fed(fed_id, chat_name, chat_id):
    with FEDS_LOCK:
        r = ChatF(chat_id, chat_name, fed_id)
        SESSION.add(r)
        FEDERATION_CHATS[str(chat_id)] = {
            "chat_name": chat_name,
            "fid": fed_id
        }
        checkid = FEDERATION_CHATS_BYID.get(fed_id)
        if checkid is None:
            FEDERATION_CHATS_BYID[fed_id] = []
        FEDERATION_CHATS_BYID[fed_id].append(str(chat_id))
        SESSION.commit()
        return r


def search_fed_by_name(fed_name):
    allfed = FEDERATION_BYNAME.get(fed_name)
    if allfed is None:
        return False
    return allfed


def search_user_in_fed(fed_id, user_id):
    getfed = FEDERATION_BYFEDID.get(fed_id)
    if getfed is None:
        return False
    getfed = ast.literal_eval(getfed["fusers"])["members"]
    return user_id in ast.literal_eval(getfed)


def user_demote_fed(fed_id, user_id):
    with FEDS_LOCK:
        # Variables
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        owner_id = getfed["owner"]
        fed_name = getfed["fname"]
        fed_rules = getfed["frules"]
        fed_log = getfed["flog"]
        # Temp set
        try:
            members = ast.literal_eval(
                ast.literal_eval(getfed["fusers"])["members"])
        except ValueError:
            return False
        members.remove(user_id)
        # Set user
        FEDERATION_BYOWNER[str(owner_id)]["fusers"] = str(
            {
                "owner": str(owner_id),
                "members": str(members)
            }, )
        FEDERATION_BYFEDID[str(fed_id)]["fusers"] = str(
            {
                "owner": str(owner_id),
                "members": str(members)
            }, )
        FEDERATION_BYNAME[fed_name]["fusers"] = str(
            {
                "owner": str(owner_id),
                "members": str(members)
            }, )
        # Set on database
        fed = Federations(
            str(owner_id),
            fed_name,
            str(fed_id),
            fed_rules,
            fed_log,
            str({
                "owner": str(owner_id),
                "members": str(members)
            }),
        )
        SESSION.merge(fed)
        SESSION.commit()
        return True


def user_join_fed(fed_id, user_id):
    with FEDS_LOCK:
        # Variables
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        owner_id = getfed["owner"]
        fed_name = getfed["fname"]
        fed_rules = getfed["frules"]
        fed_log = getfed["flog"]
        # Temp set
        members = ast.literal_eval(
            ast.literal_eval(getfed["fusers"])["members"])
        members.append(user_id)
        # Set user
        FEDERATION_BYOWNER[str(owner_id)]["fusers"] = str(
            {
                "owner": str(owner_id),
                "members": str(members)
            }, )
        FEDERATION_BYFEDID[str(fed_id)]["fusers"] = str(
            {
                "owner": str(owner_id),
                "members": str(members)
            }, )
        FEDERATION_BYNAME[fed_name]["fusers"] = str(
            {
                "owner": str(owner_id),
                "members": str(members)
            }, )
        # Set on database
        fed = Federations(
            str(owner_id),
            fed_name,
            str(fed_id),
            fed_rules,
            fed_log,
            str({
                "owner": str(owner_id),
                "members": str(members)
            }),
        )
        SESSION.merge(fed)
        SESSION.commit()
        __load_all_feds_chats()
        return True


def chat_leave_fed(chat_id):
    with FEDS_LOCK:
        # Set variables
        fed_info = FEDERATION_CHATS.get(str(chat_id))
        if fed_info is None:
            return False
        fed_id = fed_info["fid"]
        # Delete from cache
        FEDERATION_CHATS.pop(str(chat_id))
        FEDERATION_CHATS_BYID[str(fed_id)].remove(str(chat_id))
        # Delete from db
        curr = SESSION.query(ChatF).all()
        for U in curr:
            if int(U.chat_id) == int(chat_id):
                SESSION.delete(U)
                SESSION.commit()
        return True


def all_fed_chats(fed_id):
    with FEDS_LOCK:
        getfed = FEDERATION_CHATS_BYID.get(fed_id)
        if getfed is None:
            return []
        return getfed


def all_fed_users(fed_id):
    with FEDS_LOCK:
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        if getfed is None:
            return False
        fed_owner = ast.literal_eval(
            ast.literal_eval(getfed["fusers"])["owner"])
        fed_admins = ast.literal_eval(
            ast.literal_eval(getfed["fusers"])["members"])
        fed_admins.append(fed_owner)
        return fed_admins


def all_fed_members(fed_id):
    with FEDS_LOCK:
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        return ast.literal_eval(ast.literal_eval(getfed["fusers"])["members"])


def set_frules(fed_id, rules):
    with FEDS_LOCK:
        # Variables
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        owner_id = getfed["owner"]
        fed_name = getfed["fname"]
        fed_members = getfed["fusers"]
        fed_rules = str(rules)
        fed_log = getfed["flog"]
        # Set user
        FEDERATION_BYOWNER[str(owner_id)]["frules"] = fed_rules
        FEDERATION_BYFEDID[str(fed_id)]["frules"] = fed_rules
        FEDERATION_BYNAME[fed_name]["frules"] = fed_rules
        # Set on database
        fed = Federations(
            str(owner_id),
            fed_name,
            str(fed_id),
            fed_rules,
            fed_log,
            str(fed_members),
        )
        SESSION.merge(fed)
        SESSION.commit()
        return True


def get_frules(fed_id):
    with FEDS_LOCK:
        return FEDERATION_BYFEDID[str(fed_id)]["frules"]


def fban_user(fed_id, user_id, first_name, last_name, user_name, reason, time):
    with FEDS_LOCK:
        r = SESSION.query(BansF).all()
        for I in r:
            if I.fed_id == fed_id and int(I.user_id) == int(user_id):
                SESSION.delete(I)

        r = BansF(
            str(fed_id),
            str(user_id),
            first_name,
            last_name,
            user_name,
            reason,
            time,
        )

        SESSION.add(r)
        try:
            SESSION.commit()
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.commit()
        __load_all_feds_banned()
        return r


def multi_fban_user(
    multi_fed_id,
    multi_user_id,
    multi_first_name,
    multi_last_name,
    multi_user_name,
    multi_reason,
):
    counter = 0
    time = 0
    for x in enumerate(multi_fed_id):
        fed_id = multi_fed_id[x]
        user_id = multi_user_id[x]
        first_name = multi_first_name[x]
        last_name = multi_last_name[x]
        user_name = multi_user_name[x]
        reason = multi_reason[x]
        r = SESSION.query(BansF).all()
        for I in r:
            if I.fed_id == fed_id and int(I.user_id) == int(user_id):
                SESSION.delete(I)

        r = BansF(
            str(fed_id),
            str(user_id),
            first_name,
            last_name,
            user_name,
            reason,
            time,
        )

        SESSION.add(r)
        counter += 1
        if str(str(counter)[-2:]) == "00":
            LOGGER.debug(user_id)
            LOGGER.debug(first_name)
            LOGGER.debug(reason)
            LOGGER.debug(counter)
    try:
        SESSION.commit()
    except:
        SESSION.rollback()
        return False
    finally:
        SESSION.commit()
    __load_all_feds_banned()
    LOGGER.debug("Done")
    return counter


def un_fban_user(fed_id, user_id):
    with FEDS_LOCK:
        r = SESSION.query(BansF).all()
        for I in r:
            if I.fed_id == fed_id and int(I.user_id) == int(user_id):
                SESSION.delete(I)
        try:
            SESSION.commit()
        except Exception:
            SESSION.rollback()
            return False
        finally:
            SESSION.commit()
        __load_all_feds_banned()
        return I


def get_fban_user(fed_id, user_id):
    list_fbanned = FEDERATION_BANNED_USERID.get(fed_id)
    if list_fbanned is None:
        FEDERATION_BANNED_USERID[fed_id] = []
    if user_id not in FEDERATION_BANNED_USERID[fed_id]:
        return False, None, None
    r = SESSION.query(BansF).all()
    reason = None
    for I in r:
        if I.fed_id == fed_id and int(I.user_id) == int(user_id):
            reason = I.reason
            time = I.time
    return True, reason, time


def get_all_fban_users(fed_id):
    list_fbanned = FEDERATION_BANNED_USERID.get(fed_id)
    if list_fbanned is None:
        FEDERATION_BANNED_USERID[fed_id] = []
    return FEDERATION_BANNED_USERID[fed_id]


def get_all_fban_users_target(fed_id, user_id):
    list_fbanned = FEDERATION_BANNED_FULL.get(fed_id)
    if list_fbanned is None:
        FEDERATION_BANNED_FULL[fed_id] = []
        return False
    return list_fbanned[str(user_id)]


def get_all_fban_users_global():
    total = []
    for x in list(FEDERATION_BANNED_USERID):
        total.extend(iter(FEDERATION_BANNED_USERID[x]))
    return total


def get_all_feds_users_global():
    return [FEDERATION_BYFEDID[x] for x in list(FEDERATION_BYFEDID)]


def search_fed_by_id(fed_id):
    get = FEDERATION_BYFEDID.get(fed_id)
    return False if get is None else get


def user_feds_report(user_id: int) -> bool:
    user_setting = FEDERATION_NOTIFICATION.get(str(user_id))
    if user_setting is None:
        user_setting = True
    return user_setting


def set_feds_setting(user_id: int, setting: bool):
    with FEDS_SETTINGS_LOCK:
        user_setting = SESSION.query(FedsUserSettings).get(user_id)
        if not user_setting:
            user_setting = FedsUserSettings(user_id)

        user_setting.should_report = setting
        FEDERATION_NOTIFICATION[str(user_id)] = setting
        SESSION.add(user_setting)
        SESSION.commit()


async def get_fed_log(fed_id):
    fed_setting = FEDERATION_BYFEDID.get(str(fed_id))
    if fed_setting is None:
        fed_setting = False
        return fed_setting
    if fed_setting.get("flog") is None:
        return False
    if fed_setting.get("flog"):
        try:
            await CUTIEPII_PTB.bot.get_chat(fed_setting.get("flog"))
        except (BadRequest, Forbidden):
            set_fed_log(fed_id, None)
            return False
        return fed_setting.get("flog")
    return False


def set_fed_log(fed_id, chat_id):
    with FEDS_LOCK:
        # Variables
        getfed = FEDERATION_BYFEDID.get(str(fed_id))
        owner_id = getfed["owner"]
        fed_name = getfed["fname"]
        fed_members = getfed["fusers"]
        fed_rules = getfed["frules"]
        fed_log = str(chat_id)
        # Set user
        FEDERATION_BYOWNER[str(owner_id)]["flog"] = fed_log
        FEDERATION_BYFEDID[str(fed_id)]["flog"] = fed_log
        FEDERATION_BYNAME[fed_name]["flog"] = fed_log
        # Set on database
        fed = Federations(
            str(owner_id),
            fed_name,
            str(fed_id),
            fed_rules,
            fed_log,
            str(fed_members),
        )
        SESSION.merge(fed)
        SESSION.commit()
        LOGGER.debug(fed_log)
        return True


def subs_fed(fed_id, my_fed):
    if check := get_spec_subs(fed_id, my_fed):
        return False
    with FEDS_SUBSCRIBER_LOCK:
        subsfed = FedSubs(fed_id, my_fed)

        SESSION.merge(subsfed)  # merge to avoid duplicate key issues
        SESSION.commit()
        #Temporary Data For Subbed Feds
        if FEDS_SUBSCRIBER.get(fed_id, set()) == set():
            FEDS_SUBSCRIBER[fed_id] = {my_fed}
        else:
            FEDS_SUBSCRIBER.get(fed_id, set()).add(my_fed)
        # Temporary data for Fed Subs
        if MYFEDS_SUBSCRIBER.get(my_fed, set()) == set():
            MYFEDS_SUBSCRIBER[my_fed] = {fed_id}
        else:
            MYFEDS_SUBSCRIBER.get(my_fed, set()).add(fed_id)
        return True


def unsubs_fed(fed_id, my_fed):
    with FEDS_SUBSCRIBER_LOCK:
        if getsubs := SESSION.query(FedSubs).get((fed_id, my_fed)):
            if my_fed in FEDS_SUBSCRIBER.get(fed_id, set()):  # sanity check
                FEDS_SUBSCRIBER.get(fed_id, set()).remove(my_fed)
            if fed_id in MYFEDS_SUBSCRIBER.get(my_fed, set()):  # sanity check
                MYFEDS_SUBSCRIBER.get(my_fed, set()).remove(fed_id)

            SESSION.delete(getsubs)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def get_all_subs(fed_id):
    return FEDS_SUBSCRIBER.get(fed_id, set())


def get_spec_subs(fed_id, fed_target):
    if FEDS_SUBSCRIBER.get(fed_id, set()) == set():
        return {}
    return FEDS_SUBSCRIBER.get(fed_id, fed_target)


def get_mysubs(my_fed):
    return list(MYFEDS_SUBSCRIBER.get(my_fed))


def get_subscriber(fed_id):
    return FEDS_SUBSCRIBER.get(fed_id, set())


def __load_all_feds():
    try:
        feds = SESSION.query(Federations).all()
        for x in feds:  # remove tuple by ( ,)
            # Fed by Owner
            check = FEDERATION_BYOWNER.get(x.owner_id)
            if check is None:
                FEDERATION_BYOWNER[x.owner_id] = []
            FEDERATION_BYOWNER[str(x.owner_id)] = {
                "fid": str(x.fed_id),
                "fname": x.fed_name,
                "frules": x.fed_rules,
                "flog": x.fed_log,
                "fusers": str(x.fed_users),
            }
            # Fed By FedId
            check = FEDERATION_BYFEDID.get(x.fed_id)
            if check is None:
                FEDERATION_BYFEDID[x.fed_id] = []
            FEDERATION_BYFEDID[str(x.fed_id)] = {
                "owner": str(x.owner_id),
                "fname": x.fed_name,
                "frules": x.fed_rules,
                "flog": x.fed_log,
                "fusers": str(x.fed_users),
            }
            # Fed By Name
            check = FEDERATION_BYNAME.get(x.fed_name)
            if check is None:
                FEDERATION_BYNAME[x.fed_name] = []
            FEDERATION_BYNAME[x.fed_name] = {
                "fid": str(x.fed_id),
                "owner": str(x.owner_id),
                "frules": x.fed_rules,
                "flog": x.fed_log,
                "fusers": str(x.fed_users),
            }
    finally:
        SESSION.close()


def __load_all_feds_chats():
    global FEDERATION_CHATS, FEDERATION_CHATS_BYID
    try:
        qall = SESSION.query(ChatF).all()
        FEDERATION_CHATS = {}
        FEDERATION_CHATS_BYID = {}
        for x in qall:
            # Federation Chats
            check = FEDERATION_CHATS.get(x.chat_id)
            if check is None:
                FEDERATION_CHATS[x.chat_id] = {}
            FEDERATION_CHATS[x.chat_id] = {
                "chat_name": x.chat_name,
                "fid": x.fed_id
            }
            # Federation Chats By ID
            check = FEDERATION_CHATS_BYID.get(x.fed_id)
            if check is None:
                FEDERATION_CHATS_BYID[x.fed_id] = []
            FEDERATION_CHATS_BYID[x.fed_id].append(x.chat_id)
    finally:
        SESSION.close()


def __load_all_feds_banned():
    global FEDERATION_BANNED_USERID, FEDERATION_BANNED_FULL
    try:
        FEDERATION_BANNED_USERID = {}
        FEDERATION_BANNED_FULL = {}
        qall = SESSION.query(BansF).all()
        for x in qall:
            check = FEDERATION_BANNED_USERID.get(x.fed_id)
            if check is None:
                FEDERATION_BANNED_USERID[x.fed_id] = []
            if int(x.user_id) not in FEDERATION_BANNED_USERID[x.fed_id]:
                FEDERATION_BANNED_USERID[x.fed_id].append(int(x.user_id))
            check = FEDERATION_BANNED_FULL.get(x.fed_id)
            if check is None:
                FEDERATION_BANNED_FULL[x.fed_id] = {}
            FEDERATION_BANNED_FULL[x.fed_id][x.user_id] = {
                "first_name": x.first_name,
                "last_name": x.last_name,
                "user_name": x.user_name,
                "reason": x.reason,
                "time": x.time,
            }
    finally:
        SESSION.close()


def __load_all_feds_settings():
    try:
        getuser = SESSION.query(FedsUserSettings).all()
        for x in getuser:
            FEDERATION_NOTIFICATION[str(x.user_id)] = x.should_report
    finally:
        SESSION.close()


def __load_feds_subscriber():
    global FEDS_SUBSCRIBER
    global MYFEDS_SUBSCRIBER
    try:
        feds = SESSION.query(FedSubs.fed_id).distinct().all()
        for (fed_id, ) in feds:  # remove tuple by ( ,)
            FEDS_SUBSCRIBER[fed_id] = []
            MYFEDS_SUBSCRIBER[fed_id] = []

        all_fedsubs = SESSION.query(FedSubs).all()
        for x in all_fedsubs:
            FEDS_SUBSCRIBER[x.fed_id] += [x.fed_subs]
            try:
                MYFEDS_SUBSCRIBER[x.fed_subs] += [x.fed_id]
            except (KeyError, IndexError):
                if getsubs := SESSION.query(FedSubs).get(
                    (x.fed_id, x.fed_subs)):
                    SESSION.delete(getsubs)
                    SESSION.commit()

        FEDS_SUBSCRIBER = {x: set(y) for x, y in FEDS_SUBSCRIBER.items()}
        MYFEDS_SUBSCRIBER = {x: set(y) for x, y in MYFEDS_SUBSCRIBER.items()}

    finally:
        SESSION.close()


__load_all_feds()
__load_all_feds_chats()
__load_all_feds_banned()
__load_all_feds_settings()
__load_feds_subscriber()
