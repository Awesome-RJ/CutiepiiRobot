import Helper.formating_results as format

from telethon import events

from Cutiepii_Robot.utils.nhentaiapi import Nhentaiapi as nh
from Cutiepii_Robot import telethn

class Nhentai():

    @telethn.on(events.NewMessage(pattern="/nh"))
    async def event_handler_anime(event):
        if '/nh' == event.raw_text:
            await bot.send_message(
                event.chat_id,
                'Command must be used like this\n/nh <hentai code\nexample: /nh 848264'
            )
        elif '/nh' in event.raw_text:
            text = event.raw_text.split()
            text.pop(0)
            code = " ".join(text)
            chapter = nh.get_chapter_by_code(code)
            format.manga_chapter_html(f"{code}", chapter)
            await bot.send_message(
                event.chat_id,
                "Open this in google chrome",
                file= f"{code}.html"