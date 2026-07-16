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

from sqlalchemy import Column, String, BigInteger, Text, Integer, Float, DateTime
import datetime
from Cutiepii_Robot.modules.sql import BASE, SESSION
import threading


class PaidMediaPurchase(BASE):
    __tablename__ = "paid_media_purchases"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(BigInteger)
    media_id = Column(String(100))
    amount = Column(Float)  # Price/Stars
    currency = Column(String(10), default="Stars")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, customer_id, media_id, amount, currency="Stars"):
        self.customer_id = customer_id
        self.media_id = media_id
        self.amount = amount
        self.currency = currency


class PaidMediaPricing(BASE):
    __tablename__ = "paid_media_pricing"
    media_id = Column(String(100), primary_key=True)
    price = Column(Float)
    currency = Column(String(10), default="Stars")

    def __init__(self, media_id, price, currency="Stars"):
        self.media_id = media_id
        self.price = price
        self.currency = currency


PaidMediaPurchase.__table__.create(checkfirst=True)
PaidMediaPricing.__table__.create(checkfirst=True)

PM_LOCK = threading.RLock()


def log_purchase(customer_id, media_id, amount, currency="Stars"):
    with PM_LOCK:
        purchase = PaidMediaPurchase(customer_id, media_id, amount, currency)
        SESSION.add(purchase)
        SESSION.commit()
        return purchase.id


def set_pricing(media_id, price, currency="Stars"):
    with PM_LOCK:
        pricing = PaidMediaPricing(media_id, price, currency)
        SESSION.merge(pricing)
        SESSION.commit()


def get_pricing(media_id):
    try:
        return SESSION.query(PaidMediaPricing).get(media_id)
    finally:
        SESSION.close()


def get_purchases_by_customer(customer_id):
    try:
        return SESSION.query(PaidMediaPurchase).filter(PaidMediaPurchase.customer_id == customer_id).all()
    finally:
        SESSION.close()


def get_all_purchases():
    try:
        return SESSION.query(PaidMediaPurchase).all()
    finally:
        SESSION.close()
