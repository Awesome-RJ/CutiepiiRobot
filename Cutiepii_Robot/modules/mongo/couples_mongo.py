from Cutiepii_Robot import db
from typing import Dict, List, Union


coupledb = db.couple

async def _get_lovers(chat_id: int):
    lovers = await coupledb.find_one({"chat_id": chat_id})
    if not lovers:
        return {}
    return lovers["couple"]


async def get_couple(chat_id: int, date: str):
    lovers = await _get_lovers(chat_id)
    if date in lovers:
        return lovers[date]
    return False


async def save_couple(chat_id: int, date: str, couple: dict):
    lovers = await _get_lovers(chat_id)
    lovers[date] = couple
    await coupledb.update_one(
        {"chat_id": chat_id}, {"$set": {"couple": lovers}}, upsert=True
    )
