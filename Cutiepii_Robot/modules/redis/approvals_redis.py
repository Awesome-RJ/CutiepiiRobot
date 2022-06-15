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
import contextlib

from Cutiepii_Robot import REDIS

try:
    ast.literal_eval(REDIS.get("Approvals"))
except BaseException:
    REDIS.set("Approvals", "{}")


def approve(chat_id, user_id):
    approved = ast.literal_eval(REDIS.get("Approvals"))
    try:
        list = approved[chat_id]
        if user_id not in list:
            list.append(user_id)
        approved.update({chat_id: list})
    except BaseException:
        approved.update({chat_id: [user_id]})
    return REDIS.set("Approvals", str(approved))


def disapprove(chat_id, user_id):
    approved = ast.literal_eval(REDIS.get("Approvals"))
    with contextlib.suppress(BaseException):
        list = approved[chat_id]
        if user_id in list:
            list.remove(user_id)
        approved.update({chat_id: list})
    return REDIS.set("Approvals", str(approved))


def is_approved(chat_id, user_id):
    approved = ast.literal_eval(REDIS.get("Approvals"))
    try:
        list = approved[chat_id]
        if user_id in list:
            return True
        return
    except BaseException:
        return


def list_approved(chat_id):
    approved = ast.literal_eval(REDIS.get("Approvals"))
    try:
        return approved[chat_id]
    except BaseException:
        return
