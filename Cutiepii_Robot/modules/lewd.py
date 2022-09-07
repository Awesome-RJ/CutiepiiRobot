"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, [ https://github.com/Awesome-RJ ]
Copyright (c) 2021-2022, Yūki • Black Knights Union, [ https://github.com/Awesome-RJ/CutiepiiRobot ]

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

import os
import html
import nekos
import requests

from PIL import Image
from time import sleep
from nekos.errors import InvalidArgument
from telegram import Update
from telegram.error import BadRequest, RetryAfter, Forbidden
from telegram.ext import CommandHandler, filters, CallbackContext
from telegram.constants import ParseMode
from telegram.helpers import mention_html

import Cutiepii_Robot.modules.sql.nsfw_sql as sql
from Cutiepii_Robot import CUTIEPII_PTB, DEV_USERS
from Cutiepii_Robot.modules.helper_funcs.anonymous import user_admin
from Cutiepii_Robot.modules.log_channel import gloggable


@user_admin
@gloggable
async def add_nsfw(update: Update):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    is_nsfw = sql.is_nsfw(chat.id)
    if not is_nsfw:
        sql.set_nsfw(chat.id)
        await msg.reply_text("Activated NSFW Mode!")
        message = (
            f"<b>{chat.title}:</b>\n"
            f"ACTIVATED_NSFW\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        )
        return message
    await msg.reply_text("NSFW Mode is already Activated for this chat!")
    return ""


@user_admin
@gloggable
async def rem_nsfw(update: Update):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    is_nsfw = sql.is_nsfw(chat.id)
    if not is_nsfw:
        await msg.reply_text("NSFW Mode is already Deactivated")
        return ""
    sql.rem_nsfw(chat.id)
    await msg.reply_text("Rolled Back to SFW Mode!")
    message = (
        f"<b>{chat.title}:</b>\n"
        f"DEACTIVATED_NSFW\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
    )
    return message


async def list_nsfw_chats(update: Update, context: CallbackContext):
    chats = sql.get_all_nsfw_chats()
    text = "<b>NSFW Activated Chats</b>\n"
    for chat in chats:
        try:
            x = await context.bot.get_chat(int(*chat))
            name = x.title or x.first_name
            text += f"➛ <code>{name}</code>\n"
        except (BadRequest, Forbidden):
            sql.rem_nsfw(*chat)
        except RetryAfter as e:
            await sleep(e.retry_after)
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


async def neko(update: Update, context: CallbackContext):
    message = update.effective_message
    args = context.args
    flag = args[0]
    query = args[1]
    try:
        img = nekos.img(query)
    except InvalidArgument:
        await message.reply_text(
            f"{query} are'nt available! check available query on help!")
        return
    try:
        if flag == "-i":
            await message.reply_photo(photo=img, parse_mode=ParseMode.MARKDOWN)
        elif flag == "-d":
            await message.reply_document(document=img,
                                         parse_mode=ParseMode.MARKDOWN)
        elif flag == "-s":
            stkr = "sticker.webp"
            x = open(stkr, "wb")
            x.write(requests.get(img).content)
            await message.reply_sticker(sticker=open(stkr, "rb"))
            os.remove("sticker.webp")
        elif flag == "-v":
            await message.reply_video(video=img, parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply_text("Put flags correctly!!!")
    except Exception as excp:
        await message.reply_text(f"Failed to find image. Error: {excp}")


async def cuddle(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "cuddle"
    await msg.reply_photo(nekos.img(target))


async def feet(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "feet"
    await msg.reply_photo(nekos.img(target))


async def yuri(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "yuri"
    await msg.reply_photo(nekos.img(target))


async def trap(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "trap"
    await msg.reply_photo(nekos.img(target))


async def futanari(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "futanari"
    await msg.reply_photo(nekos.img(target))


async def hololewd(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "hololewd"
    await msg.reply_photo(nekos.img(target))


async def lewdkemo(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "lewdkemo"
    await msg.reply_photo(nekos.img(target))


async def sologif(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "solog"
    await msg.reply_photo(nekos.img(target))


async def feetgif(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "feetg"
    await msg.reply_photo(nekos.img(target))


async def cumgif(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "cum"
    await msg.reply_photo(nekos.img(target))


async def erokemo(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "erokemo"
    await msg.reply_photo(nekos.img(target))


async def lesbian(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "les"
    await msg.reply_photo(nekos.img(target))


async def wallpaper(update: Update):
    msg = update.effective_message
    target = "wallpaper"
    await msg.reply_photo(nekos.img(target))


async def lewdk(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "lewdk"
    await msg.reply_photo(nekos.img(target))


async def ngif(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "ngif"
    await msg.reply_photo(nekos.img(target))


async def tickle(update: Update):
    msg = update.effective_message
    target = "tickle"
    await msg.reply_photo(nekos.img(target))


async def lewd(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "lewd"
    await msg.reply_photo(nekos.img(target))


async def feed(update: Update):
    msg = update.effective_message
    target = "feed"
    await msg.reply_photo(nekos.img(target))


async def eroyuri(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "eroyuri"
    await msg.reply_photo(nekos.img(target))


async def eron(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "eron"
    await msg.reply_photo(nekos.img(target))


async def cum(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "cum_jpg"
    await msg.reply_photo(nekos.img(target))


async def bjgif(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "bj"
    await msg.reply_photo(nekos.img(target))


async def bj(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "blowjob"
    await msg.reply_photo(nekos.img(target))


async def nekonsfw(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "nsfw_neko_gif"
    await msg.reply_photo(nekos.img(target))


async def solo(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "solo"
    await msg.reply_photo(nekos.img(target))


async def kemonomimi(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "kemonomimi"
    await msg.reply_photo(nekos.img(target))


async def avatarlewd(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "nsfw_avatar"
    with open("temp.png", "wb") as f:
        f.write(requests.get(nekos.img(target)).content)
    img = Image.open("temp.png")
    img.save("temp.webp", "webp")
    msg.reply_document(open("temp.webp", "rb"))
    os.remove("temp.webp")


async def gasm(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "gasm"
    with open("temp.png", "wb") as f:
        f.write(requests.get(nekos.img(target)).content)
    img = Image.open("temp.png")
    img.save("temp.webp", "webp")
    msg.reply_document(open("temp.webp", "rb"))
    os.remove("temp.webp")


async def poke(update: Update):
    msg = update.effective_message
    target = "poke"
    await msg.reply_photo(nekos.img(target))


async def anal(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "anal"
    await msg.reply_photo(nekos.img(target))


async def hentai(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "hentai"
    await msg.reply_photo(nekos.img(target))


async def avatar(update: Update):
    msg = update.effective_message
    target = "nsfw_avatar"
    with open("temp.png", "wb") as f:
        f.write(requests.get(nekos.img(target)).content)
    img = Image.open("temp.png")
    img.save("temp.webp", "webp")
    msg.reply_document(open("temp.webp", "rb"))
    os.remove("temp.webp")


async def erofeet(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "erofeet"
    await msg.reply_photo(nekos.img(target))


async def holo(update: Update):
    msg = update.effective_message
    target = "holo"
    await msg.reply_photo(nekos.img(target))


async def keta(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = 'keta'
    if not target:
        await msg.reply_text("No URL was received from the API!")
        return
    await msg.reply_photo(nekos.img(target))


async def pussygif(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "pussy"
    await msg.reply_photo(nekos.img(target))


async def tits(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "tits"
    await msg.reply_photo(nekos.img(target))


async def holoero(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "holoero"
    await msg.reply_photo(nekos.img(target))


async def pussy(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "pussy_jpg"
    await msg.reply_photo(nekos.img(target))


async def hentaigif(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "random_hentai_gif"
    await msg.reply_photo(nekos.img(target))


async def classic(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "classic"
    await msg.reply_photo(nekos.img(target))


async def kuni(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "kuni"
    await msg.reply_photo(nekos.img(target))


async def waifu(update: Update):
    msg = update.effective_message
    target = "waifu"
    with open("temp.png", "wb") as f:
        f.write(requests.get(nekos.img(target)).content)
    img = Image.open("temp.png")
    img.save("temp.webp", "webp")
    msg.reply_document(open("temp.webp", "rb"))
    os.remove("temp.webp")


async def kiss(update: Update):
    msg = update.effective_message
    target = "kiss"
    await msg.reply_photo(nekos.img(target))


async def femdom(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "femdom"
    await msg.reply_photo(nekos.img(target))


async def hug(update: Update):
    msg = update.effective_message
    target = "cuddle"
    await msg.reply_photo(nekos.img(target))


async def erok(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "erok"
    await msg.reply_photo(nekos.img(target))


async def foxgirl(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "fox_girl"
    await msg.reply_photo(nekos.img(target))


async def titsgif(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "boobs"
    await msg.reply_photo(nekos.img(target))


async def ero(update: Update):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "ero"
    await msg.reply_photo(nekos.img(target))


async def smug(update: Update):
    msg = update.effective_message
    target = "smug"
    await msg.reply_photo(nekos.img(target))


async def baka(update: Update):
    msg = update.effective_message
    target = "baka"
    await msg.reply_photo(nekos.img(target))


CUTIEPII_PTB.add_handler(CommandHandler("addnsfw", add_nsfw))
CUTIEPII_PTB.add_handler(CommandHandler("rmnsfw", rem_nsfw))
CUTIEPII_PTB.add_handler(
    CommandHandler(
        "nsfwchats",
        list_nsfw_chats,
        filters=filters.User(DEV_USERS),
    ))
CUTIEPII_PTB.add_handler(CommandHandler("lewdkemo", lewdkemo))
CUTIEPII_PTB.add_handler(CommandHandler("neko", neko))
CUTIEPII_PTB.add_handler(CommandHandler("feet", feet))
CUTIEPII_PTB.add_handler(CommandHandler("yuri", yuri))
CUTIEPII_PTB.add_handler(CommandHandler("trap", trap))
CUTIEPII_PTB.add_handler(CommandHandler("futanari", futanari))
CUTIEPII_PTB.add_handler(CommandHandler("hololewd", hololewd))
CUTIEPII_PTB.add_handler(CommandHandler("sologif", sologif))
CUTIEPII_PTB.add_handler(CommandHandler("cumgif", cumgif))
CUTIEPII_PTB.add_handler(CommandHandler("erokemo", erokemo))
CUTIEPII_PTB.add_handler(CommandHandler("lesbian", lesbian))
CUTIEPII_PTB.add_handler(CommandHandler("wallpaper", wallpaper))
CUTIEPII_PTB.add_handler(CommandHandler("lewdk", lewdk))
CUTIEPII_PTB.add_handler(CommandHandler("ngif", ngif))
CUTIEPII_PTB.add_handler(CommandHandler("tickle", tickle))
CUTIEPII_PTB.add_handler(CommandHandler("lewd", lewd))
CUTIEPII_PTB.add_handler(CommandHandler("feed", feed))
CUTIEPII_PTB.add_handler(CommandHandler("eroyuri", eroyuri))
CUTIEPII_PTB.add_handler(CommandHandler("eron", eron))
CUTIEPII_PTB.add_handler(CommandHandler("cum", cum))
CUTIEPII_PTB.add_handler(CommandHandler("bjgif", bjgif))
CUTIEPII_PTB.add_handler(CommandHandler("bj", bj))
CUTIEPII_PTB.add_handler(CommandHandler("nekonsfw", nekonsfw))
CUTIEPII_PTB.add_handler(CommandHandler("solo", solo))
CUTIEPII_PTB.add_handler(CommandHandler("kemonomimi", kemonomimi))
CUTIEPII_PTB.add_handler(CommandHandler("avatarlewd", avatarlewd))
CUTIEPII_PTB.add_handler(CommandHandler("gasm", gasm))
CUTIEPII_PTB.add_handler(CommandHandler("poke", poke))
CUTIEPII_PTB.add_handler(CommandHandler("anal", anal))
CUTIEPII_PTB.add_handler(CommandHandler("hentai", hentai))
CUTIEPII_PTB.add_handler(CommandHandler("avatar", avatar))
CUTIEPII_PTB.add_handler(CommandHandler("erofeet", erofeet))
CUTIEPII_PTB.add_handler(CommandHandler("holo", holo))
CUTIEPII_PTB.add_handler(CommandHandler("tits", tits))
CUTIEPII_PTB.add_handler(CommandHandler("pussygif", pussygif))
CUTIEPII_PTB.add_handler(CommandHandler("holoero", holoero))
CUTIEPII_PTB.add_handler(CommandHandler("pussy", pussy))
CUTIEPII_PTB.add_handler(CommandHandler("hentaigif", hentaigif))
CUTIEPII_PTB.add_handler(CommandHandler("classic", classic))
CUTIEPII_PTB.add_handler(CommandHandler("kuni", kuni))
CUTIEPII_PTB.add_handler(CommandHandler("waifu", waifu))
CUTIEPII_PTB.add_handler(CommandHandler("lewd", lewd))
CUTIEPII_PTB.add_handler(CommandHandler("kiss", kiss))
CUTIEPII_PTB.add_handler(CommandHandler("femdom", femdom))
CUTIEPII_PTB.add_handler(CommandHandler("cuddle", cuddle))
CUTIEPII_PTB.add_handler(CommandHandler("hug", hug))
CUTIEPII_PTB.add_handler(CommandHandler("erok", erok))
CUTIEPII_PTB.add_handler(CommandHandler("foxgirl", foxgirl))
CUTIEPII_PTB.add_handler(CommandHandler("titsgif", titsgif))
CUTIEPII_PTB.add_handler(CommandHandler("ero", ero))
CUTIEPII_PTB.add_handler(CommandHandler("smug", smug))
CUTIEPII_PTB.add_handler(CommandHandler("baka", baka))

__help__ = """
Usage*:*
/addnsfw*:* Enable NSFW mode
/rmnsfw*:* Disable NSFW mode

Commands*:*
➛ /neko <flags> <query>: Get random images from [Nekos API](nekos.life)

*Available flags:*
-i = send as image
-d = send as document(full resolution)
-s = send as sticker
-v = send as video(only for some query)

*Available query:*
Check this : [List Query](https://telegra.ph/List-Query-of-Nekos-01-19)

➛ /feet*:* Sends Random Anime Feet Images.
➛ /yuri*:* Sends Random Yuri source Images.
➛ /trap*:* Sends Random Trap source Images.
➛ /futanari*:* Sends Random Futanari source Images.
➛ /hololewd*:* Sends Random Holo Lewds.
➛ /lewdkemo*:* Sends Random Kemo Lewds.
➛ /sologif*:* Sends Random Solo GIFs.
➛ /cumgif*:* Sends Random Cum GIFs.
➛ /erokemo*:* Sends Random Ero-Kemo Images.
➛ /lesbian*:* Sends Random Les Source Images.
➛ /lewdk*:* Sends Random Kitsune Lewds.
➛ /ngif*:* Sends Random Neko GIFs.
➛ /tickle*:* Sends Random Tickle GIFs.
➛ /lewd*:* Sends Random Lewds.
➛ /feed*:* Sends Random Feeding GIFs.
➛ /eroyuri*:* Sends Random Ero-Yuri source Images.
➛ /eron*:* Sends Random Ero-Neko source Images.
➛ /cum*:* Sends Random Cum Images.
➛ /bjgif*:* Sends Random Blow Job GIFs.
➛ /bj*:* Sends Random Blow Job source Images.
➛ /nekonsfw*:* Sends Random NSFW Neko source Images.
➛ /solo*:* Sends Random NSFW Neko GIFs.
➛ /kemonomimi*:* Sends Random KemonoMimi source Images.
➛ /avatarlewd*:* Sends Random Avater Lewd Stickers.
➛ /gasm*:* Sends Random Orgasm Stickers.
➛ /poke*:* Sends Random Poke GIFs.
➛ /anal Sends Random Anal GIFs.
➛ /hentai*:* Sends Random Hentai source Images.
➛ /avatar*:* Sends Random Avatar Stickers.
➛ /erofeet*:* Sends Random Ero-Feet source Images.
➛ /holo*:* Sends Random Holo source Images.
➛ /tits*:* Sends Random Tits source Images.
➛ /pussygif*:* Sends Random Pussy GIFs.
➛ /holoero*:* Sends Random Ero-Holo source Images.
➛ /pussy*:* Sends Random Pussy source Images.
➛ /hentaigif*:* Sends Random Hentai GIFs.
➛ /classic*:* Sends Random Classic Hentai GIFs.
➛ /kuni*:* Sends Random Pussy Lick GIFs.
➛ /waifu*:* Sends Random Waifu Stickers.
➛ /kiss*:* Sends Random Kissing GIFs.
➛ /femdom*:* Sends Random Femdom source Images.
➛ /cuddle*:* Sends Random Cuddle GIFs.
➛ /erok*:* Sends Random Ero-Kitsune source Images.
➛ /foxgirl*:* Sends Random FoxGirl source Images.
➛ /titsgif*:* Sends Random Tits GIFs.
➛ /ero*:* Sends Random Ero source Images.
➛ /smug*:* Sends Random Smug GIFs.
➛ /baka*:* Sends Random Baka Shout GIFs.
"""

__mod_name__ = "NSFW"
