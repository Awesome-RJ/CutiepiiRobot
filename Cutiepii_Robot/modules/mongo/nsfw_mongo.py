from Cutiepii_Robot import db
from typing import Dict, List, Union


nsfwdb = db.nsfw

"""NSFW System"""

async def is_nsfw_on(chat_id: int) -> bool:
    chat = await nsfwdb.find_one({"chat_id": chat_id})
    if not chat:
        return True
    return False


async def nsfw_on(chat_id: int):
    is_nsfw = await is_nsfw_on(chat_id)
    if is_nsfw:
        return
    return await nsfwdb.delete_one({"chat_id": chat_id})


async def nsfw_off(chat_id: int):
    is_nsfw = await is_nsfw_on(chat_id)
    if not is_nsfw:
        return
    return await nsfwdb.insert_one({"chat_id": chat_id})
