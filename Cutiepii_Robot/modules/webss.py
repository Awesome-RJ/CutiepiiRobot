from pyrogram import filters

from Cutiepii_Robot import pgram as app, BOT_USERNAME
from Cutiepii_Robot.utils.errors import capture_err

@app.on_message(filters.command("webss", f"webss@{BOT_USERNAME}"))
@capture_err
async def take_ss(_, message):
    try:
        if len(message.command) != 2:
            await message.reply_text("Give A Url To Fetch Screenshot.")
            return
        url = message.text.split(None, 1)[1]
        m = await message.reply_text("**Taking Screenshot**")
        await m.edit("**Uploading**")
        try:
            await app.send_photo(
                message.chat.id,
                photo=f"https://webshot.amanoteam.com/print?q={url}",
            )
        except TypeError:
            await m.edit("No Such Website.")
            return
        await m.delete()
    except Exception as e:
        await message.reply_text(str(e))

__mod_name__ = "webss"
