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

from sqlalchemy import Column, String, BigInteger, Integer
from Cutiepii_Robot.modules.sql import BASE, SESSION
import threading


class FlagGuessUser(BASE):
    __tablename__ = "flag_guess_users"
    user_id = Column(BigInteger, primary_key=True)
    wins = Column(Integer, default=0)
    coins = Column(Integer, default=0)
    xp = Column(Integer, default=0)

    def __init__(self, user_id, wins=0, coins=0, xp=0):
        self.user_id = user_id
        self.wins = wins
        self.coins = coins
        self.xp = xp


FlagGuessUser.__table__.create(checkfirst=True)

FG_LOCK = threading.RLock()


def add_win(user_id, coins, xp):
    with FG_LOCK:
        user = SESSION.query(FlagGuessUser).get(user_id)
        if not user:
            user = FlagGuessUser(user_id, wins=1, coins=coins, xp=xp)
            SESSION.add(user)
        else:
            user.wins += 1
            user.coins += coins
            user.xp += xp
        SESSION.commit()


def get_top_guessers(limit=10):
    try:
        return SESSION.query(FlagGuessUser).order_by(FlagGuessUser.wins.desc()).limit(limit).all()
    finally:
        SESSION.close()
