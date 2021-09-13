import os

import requests
import wget
from pyrogram import filters

from Cutiepii_Robot import pgram, BOT_USERNAME
from Cutiepii_Robot.utils.saavnhelp import get_arg


@pgram.on_message(filters.command("saavn", f"saavn@{BOT_USERNAME}"))
async def song(client, message):
    args = get_arg(message) + " " + "song"
    if args.startswith(" "):
        await message.reply("<b> Song name required!! </b>")
        return ""
    m = await message.reply_text(
        "Downloading the song, Please wait..."
    )
    try:
        r = requests.get(f"https://jostapi.herokuapp.com/saavn?query={args}")
    except Exception as e:
        await m.edit(str(e))
        return
    sname = r.json()[0]["song"]
    slink = r.json()[0]["media_url"]
    ssingers = r.json()[0]["singers"]
    file = wget.download(slink)
    ffile = file.replace("mp4", "m4a")
    os.rename(file, ffile)
    await message.reply_audio(audio=ffile, title=sname, performer=ssingers)
    os.remove(ffile)
    await m.delete()
