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

import random

from Cutiepii_Robot import pgram
from Cutiepii_Robot.utils.errors import capture_err
from Cutiepii_Robot.modules.mongo.couples_mongo import get_couple, save_couple
from pyrogram import filters
from datetime import datetime


# Date and time
def dt():
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M")
    return dt_string.split(' ')


def dt_tom():
    return str(int(dt()[0].split('/')[0]) + 1)+"/" + \
        dt()[0].split('/')[1]+"/" + dt()[0].split('/')[2]


today = str(dt()[0])
tomorrow = str(dt_tom())


@pgram.on_message(filters.command("couples") & ~filters.edited)
@capture_err
async def couple(_, message):
    if message.chat.type == "private":
        await message.reply_text("This command only works in groups.")
        return
    try:
        chat_id = message.chat.id
        is_selected = await get_couple(chat_id, today)
        if not is_selected:
            list_of_users = []
            async for i in pgram.iter_chat_members(message.chat.id):
                if not i.user.is_bot:
                    list_of_users.append(i.user.id)
            if len(list_of_users) < 2:
                await message.reply_text("Not enough users")
                return
            c1_id = random.choice(list_of_users)
            c2_id = random.choice(list_of_users)
            while c1_id == c2_id:
                c1_id = random.choice(list_of_users)
            c1_mention = (await pgram.get_users(c1_id)).mention
            c2_mention = (await pgram.get_users(c2_id)).mention

            couple_selection_message = f"""**Couple of the day:**
{c1_mention} + {c2_mention} = 💜
__New couple of the day may be chosen at 12AM {tomorrow}__"""
            await pgram.send_message(
                message.chat.id,
                text=couple_selection_message
            )
            couple = {
                "c1_id": c1_id,
                "c2_id": c2_id
            }
            await save_couple(chat_id, today, couple)

        else:
            c1_id = int(is_selected['c1_id'])
            c2_id = int(is_selected['c2_id'])
            c1_name = (await pgram.get_users(c1_id)).first_name
            c2_name = (await pgram.get_users(c2_id)).first_name
            couple_selection_message = f"""Couple of the day:
[{c1_name}](tg://openmessage?user_id={c1_id}) + [{c2_name}](tg://openmessage?user_id={c2_id}) = 💜
__New couple of the day may be chosen at 12AM {tomorrow}__"""
            await pgram.send_message(
                message.chat.id,
                text=couple_selection_message
            )
    except Exception as e:
        print(e)
        await message.reply_text(e)


__mod_name__ = "Couples"
