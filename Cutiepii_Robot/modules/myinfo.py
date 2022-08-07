import asyncio
import re
import datetime

from telethon import events, custom
from Cutiepii_Robot import telethn as bot
from Cutiepii_Robot.events import register

edit_time = 5
""" =======================CONSTANTS====================== """
file1 = "https://telegra.ph/file/11cfb0be7163d32c51259.jpg"
file2 = "https://telegra.ph/file/444028d9b3daccc947a2d.jpg"
file3 = "https://telegra.ph/file/fdf47498b208bc63000b4.jpg"
file4 = "https://telegra.ph/file/e8f3310b943b8b8699dcd.jpg"
file5 = "https://telegra.ph/file/401cb7f6216764ebab161.jpg"
""" =======================CONSTANTS====================== """


@register(pattern="/myinfo")
async def proboyx(event):
    betsy = event.sender.first_name
    button = [[custom.Button.inline("Click Here", data="information")]]
    on = await bot.send_file(
        event.chat_id,
        file=file2,
        caption=
        f"♡ Hey {betsy}, I'm Cutiepii\n♡ I'm Created By [Black Knights Union](https://t.me/Black_Knights_Union_Support)\n♡ Click The Button Below To Get Your Info",
        buttons=button)

    await asyncio.sleep(edit_time)
    ok = await bot.edit_message(event.chat_id, on, file=file3, buttons=button)

    await asyncio.sleep(edit_time)
    ok2 = await bot.edit_message(event.chat_id, ok, file=file5, buttons=button)

    await asyncio.sleep(edit_time)
    ok3 = await bot.edit_message(event.chat_id,
                                 ok2,
                                 file=file1,
                                 buttons=button)

    await asyncio.sleep(edit_time)
    ok7 = await bot.edit_message(event.chat_id,
                                 ok6,
                                 file=file4,
                                 buttons=button)

    await asyncio.sleep(edit_time)
    ok4 = await bot.edit_message(event.chat_id,
                                 ok3,
                                 file=file2,
                                 buttons=button)

    await asyncio.sleep(edit_time)
    ok5 = await bot.edit_message(event.chat_id,
                                 ok4,
                                 file=file1,
                                 buttons=button)

    await asyncio.sleep(edit_time)
    ok6 = await bot.edit_message(event.chat_id,
                                 ok5,
                                 file=file3,
                                 buttons=button)

    await asyncio.sleep(edit_time)
    ok7 = await bot.edit_message(event.chat_id,
                                 ok6,
                                 file=file5,
                                 buttons=button)

    await asyncio.sleep(edit_time)
    ok7 = await bot.edit_message(event.chat_id,
                                 ok6,
                                 file=file4,
                                 buttons=button)


@bot.on(events.callbackquery.CallbackQuery(data=re.compile(b"information")))
async def callback_query_handler(event):
    try:
        boy = event.sender_id
        PRO = await bot.get_entity(boy)
        NEKO = "YOUR DETAILS BY NEKO \n\n"
        NEKO += f"FIRST NAME : {PRO.first_name} \n"
        NEKO += f"LAST NAME : {PRO.last_name}\n"
        NEKO += f"YOU BOT : {PRO.bot} \n"
        NEKO += f"RESTRICTED : {PRO.restricted} \n"
        NEKO += f"USER ID : {boy}\n"
        NEKO += f"USERNAME : {PRO.username}\n"
        await event.answer(NEKO, alert=True)
    except Exception as e:
        await event.reply(f"{e}")


__mod_name__ = "myinfo"
__command_list__ = ["myinfo"]
