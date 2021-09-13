import os
import requests

from pyrogram import filters
from json import JSONDecodeError

from Cutiepii_Robot.utils.pluginhelpers import admins_only, edit_or_reply, fetch_audio
from Cutiepii_Robot import pgram, BOT_USERNAME


@pgram.on_message(filters.command(["identify", "shazam", f"shazam@{BOT_USERNAME}"]))
@admins_only
async def shazamm(client, message):
    kek = await edit_or_reply(message, "`Shazaming In Progress!`")
    if not message.reply_to_message:
        await kek.edit("Reply To The Audio.")
        return
    if os.path.exists("friday.mp3"):
        os.remove("friday.mp3")
    kkk = await fetch_audio(client, message)
    downloaded_file_name = kkk
    f = {"file": (downloaded_file_name, open(downloaded_file_name, "rb"))}
    await kek.edit("**Searching For This Song In Cutiepii's DataBase.**")
    r = requests.post("https://starkapi.herokuapp.com/shazam/", files=f)
    try:
        xo = r.json()
    except JSONDecodeError:
        await kek.edit(
            "`Seems Like Our Server Has Some Issues, Please Try Again Later!`"
        )
        return
    if xo.get("success") is False:
        await kek.edit("`Song Not Found IN Database. Please Try Again.`")
        os.remove(downloaded_file_name)
        return
    xoo = xo.get("response")
    zz = xoo[1]
    zzz = zz.get("track")
    zzz.get("sections")[3]
    nt = zzz.get("images")
    image = nt.get("coverarthq")
    by = zzz.get("subtitle")
    title = zzz.get("title")
    messageo = f"""<b>Song Shazamed.</b>
<b>Song Name : </b>{title}
<b>Song By : </b>{by}
<u><b>Identified Using @Cutiepii_Robot - Join our support @Black_Knights_Union_Support</b></u>
<i>Powered by @Yuki_Netowrk</i>
"""
    await client.send_photo(message.chat.id, image, messageo, parse_mode="HTML")
    os.remove(downloaded_file_name)
    await kek.delete()
