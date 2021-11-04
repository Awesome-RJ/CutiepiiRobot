"""
MIT License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021 Awesome-RJ
Copyright (c) 2021, Yūki • Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

This file is part of @Cutiepii_Robot (Telegram Bot)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is

furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import ast
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
    try:
        list = approved[chat_id]
        if user_id in list:
            list.remove(user_id)
        approved.update({chat_id: list})
    except BaseException:
        pass
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
