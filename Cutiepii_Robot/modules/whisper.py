from telethon import events, Button
import logging
from telethon.tl.functions.users import GetFullUserRequest as us
from Cutiepii_Robot import telethn as bot

logging.basicConfig(level=logging.INFO)

db = {}


@bot.on(events.NewMessage(pattern="^[!?@/]Cutiepii_Robot$"))
async def stsrt(event):
    await event.reply("**Heya, I am a Whisper Bot function for Cutiepii!**",
                      buttons=[[Button.switch_inline("Go Inline", query="")]])


@bot.on(events.InlineQuery())
async def die(event):
    if len(event.text) != 0:
        return
    me = (await bot.get_me()).username
    dn = event.builder.article(
        title="It's a whisper bot!",
        description="It's a whisper Bot function for Cutiepii!\n(c) Reeshuxd",
        text=
        f"**It's a whisper bot**\n`@{me} wspr Username|Message`\n**(c) Reeshuxd**",
        buttons=[[Button.switch_inline(" Go Inline ", query="wspr ")]])
    await event.answer([dn])


@bot.on(events.InlineQuery(pattern="wspr"))
async def inline(event):
    me = (await bot.get_me()).username
    try:
        inp = event.text.split(None, 1)[1]
        user, msg = inp.split("|")
    except IndexError:
        await event.answer([],
                           switch_pm=f"@{me} [Username]|[Message]",
                           switch_pm_param="whisper")
    except ValueError:
        await event.answer([],
                           switch_pm="Give a message too!",
                           switch_pm_param="whisper")
    try:
        ui = await bot(us(user))
    except BaseException:
        await event.answer([],
                           switch_pm="Invalid User ID/Username",
                           switch_pm_param="whisper")
        return
    db.update({"user_id": ui.user.id, "msg": msg, "self": event.sender.id})
    text = f"""
A Whisper Has Been Sent
To [{ui.user.first_name}](tg://user?id={ui.user.id})!
Click The Below Button To See The Message!
**Note:** __Only {ui.user.first_name} can open this!__
    """
    dn = event.builder.article(
        title="Its a secret message! Sssh",
        description="It's a secret message! Sssh!",
        text=text,
        buttons=[[Button.inline(" Show Message! ", data="wspr")]])
    await event.answer([dn],
                       switch_pm="It's a secret message! Sssh",
                       switch_pm_param="whisper")


@bot.on(events.CallbackQuery(data="wspr"))
async def ws(event):
    user = int(db["user_id"])
    lol = [int(db["self"]), user]
    if event.sender.id not in lol:
        await event.answer("🔐 This message is not for you!", alert=True)
        return
    msg = db["msg"]
    if msg == []:
        await event.anwswer(
            "Oops!\nIt's looks like message got deleted from my server!",
            alert=True)
        return
    await event.answer(msg, alert=True)
