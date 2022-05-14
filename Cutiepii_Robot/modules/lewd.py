"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2022, Yūki • Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

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
from telegram import Update
from telegram.error import BadRequest, RetryAfter, Forbidden
from telegram.ext import CallbackContext, CommandHandler
from telegram.helpers import mention_html


import Cutiepii_Robot.modules.sql.nsfw_sql as sql
from Cutiepii_Robot import CUTIEPII_PTB
from Cutiepii_Robot.modules.helper_funcs.anonymous import user_admin
from Cutiepii_Robot.modules.helper_funcs.filters import CustomFilters
from Cutiepii_Robot.modules.log_channel import gloggable


@user_admin
@gloggable
async def add_nsfw(update: Update, context: CallbackContext):
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
    else:
        await msg.reply_text("NSFW Mode is already Activated for this chat!")
        return ""



@user_admin
@gloggable
async def rem_nsfw(update: Update, context: CallbackContext):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    is_nsfw = sql.is_nsfw(chat.id)
    if not is_nsfw:
        await msg.reply_text("NSFW Mode is already Deactivated")
        return ""
    else:
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
            sleep(e.retry_after)
    await message.reply_text(text, parse_mode="HTML")



async def neko(update: Update, context: CallbackContext):
    msg = update.effective_message
    target = "neko"
    await msg.reply_photo(nekos.img(target))


async def cuddle(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "cuddle"
    await msg.reply_photo(nekos.img(target))


async def feet(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "feet"
    await msg.reply_photo(nekos.img(target))


async def yuri(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "yuri"
    await msg.reply_photo(nekos.img(target))


async def trap(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "trap"
    await msg.reply_photo(nekos.img(target))


async def futanari(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "futanari"
    await msg.reply_photo(nekos.img(target))


async def hololewd(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "hololewd"
    await msg.reply_photo(nekos.img(target))


async def lewdkemo(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "lewdkemo"
    await msg.reply_photo(nekos.img(target))



async def sologif(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "solog"
    await msg.reply_photo(nekos.img(target))



async def feetgif(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "feetg"
    await msg.reply_photo(nekos.img(target))


async def cumgif(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "cum"
    await msg.reply_photo(nekos.img(target))


async def erokemo(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "erokemo"
    await msg.reply_photo(nekos.img(target))


async def lesbian(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "les"
    await msg.reply_photo(nekos.img(target))


async def wallpaper(update: Update, context: CallbackContext):
    msg = update.effective_message
    target = "wallpaper"
    await msg.reply_photo(nekos.img(target))


async def lewdk(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "lewdk"
    await msg.reply_photo(nekos.img(target))


async def ngif(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "ngif"
    await msg.reply_photo(nekos.img(target))



async def tickle(update: Update, context: CallbackContext):
     msg = update.effective_message
     target = "tickle"
     await msg.reply_photo(nekos.img(target))


async def lewd(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "lewd"
    await msg.reply_photo(nekos.img(target))



async def feed(update: Update, context: CallbackContext):
    msg = update.effective_message
    target = "feed"
    await msg.reply_photo(nekos.img(target))



async def eroyuri(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "eroyuri"
    await msg.reply_photo(nekos.img(target))


async def eron(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "eron"
    await msg.reply_photo(nekos.img(target))


async def cum(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "cum_jpg"
    await msg.reply_photo(nekos.img(target))


async def bjgif(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "bj"
    await msg.reply_photo(nekos.img(target))


async def bj(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "blowjob"
    await msg.reply_photo(nekos.img(target))


async def nekonsfw(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "nsfw_neko_gif"
    await msg.reply_photo(nekos.img(target))


async def solo(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "solo"
    await msg.reply_photo(nekos.img(target))


async def kemonomimi(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "kemonomimi"
    await msg.reply_photo(nekos.img(target))


async def avatarlewd(update: Update, context: CallbackContext):
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


async def gasm(update: Update, context: CallbackContext):
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



async def poke(update: Update, context: CallbackContext):
    msg = update.effective_message
    target = "poke"
    await msg.reply_photo(nekos.img(target))



async def anal(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "anal"
    await msg.reply_photo(nekos.img(target))


async def hentai(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "hentai"
    await msg.reply_photo(nekos.img(target))


async def avatar(update: Update, context: CallbackContext):
    msg = update.effective_message
    target = "nsfw_avatar"
    with open("temp.png", "wb") as f:
        f.write(requests.get(nekos.img(target)).content)
    img = Image.open("temp.png")
    img.save("temp.webp", "webp")
    msg.reply_document(open("temp.webp", "rb"))
    os.remove("temp.webp")


async def erofeet(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "erofeet"
    await msg.reply_photo(nekos.img(target))


async def holo(update: Update, context: CallbackContext):
    msg = update.effective_message
    target = "holo"
    await msg.reply_photo(nekos.img(target))


async def keta(update: Update, context: CallbackContext):
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


async def pussygif(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "pussy"
    await msg.reply_photo(nekos.img(target))


async def tits(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "tits"
    await msg.reply_photo(nekos.img(target))


async def holoero(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "holoero"
    await msg.reply_photo(nekos.img(target))


async def pussy(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "pussy_jpg"
    await msg.reply_photo(nekos.img(target))


async def hentaigif(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "random_hentai_gif"
    await msg.reply_photo(nekos.img(target))


async def classic(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "classic"
    await msg.reply_photo(nekos.img(target))


async def kuni(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "kuni"
    await msg.reply_photo(nekos.img(target))



async def waifu(update: Update, context: CallbackContext):
    msg = update.effective_message
    target = "waifu"
    with open("temp.png", "wb") as f:
        f.write(requests.get(nekos.img(target)).content)
    img = Image.open("temp.png")
    img.save("temp.webp", "webp")
    msg.reply_document(open("temp.webp", "rb"))
    os.remove("temp.webp")



async def kiss(update: Update, context: CallbackContext):
    msg = update.effective_message
    target = "kiss"
    await msg.reply_photo(nekos.img(target))



async def femdom(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "femdom"
    await msg.reply_photo(nekos.img(target))



async def hug(update: Update, context: CallbackContext):
    msg = update.effective_message
    target = "cuddle"
    await msg.reply_photo(nekos.img(target))



async def erok(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "erok"
    await msg.reply_photo(nekos.img(target))



async def foxgirl(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "fox_girl"
    await msg.reply_photo(nekos.img(target))



async def titsgif(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "boobs"
    await msg.reply_photo(nekos.img(target))



async def ero(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    if update.effective_message.chat.type != "private":
        is_nsfw = sql.is_nsfw(chat_id)
        if not is_nsfw:
            return
    msg = update.effective_message
    target = "ero"
    await msg.reply_photo(nekos.img(target))



async def smug(update: Update, context: CallbackContext):
    msg = update.effective_message
    target = "smug"
    await msg.reply_photo(nekos.img(target))



async def baka(update: Update, context: CallbackContext):
    msg = update.effective_message
    target = "baka"
    await msg.reply_photo(nekos.img(target))



ADD_NSFW_HANDLER = CommandHandler("addnsfw", add_nsfw)
REMOVE_NSFW_HANDLER = CommandHandler("rmnsfw", rem_nsfw)
LIST_NSFW_CHATS_HANDLER = CommandHandler(
    "nsfwchats", list_nsfw_chats, filters=CustomFilters.dev_filter)
LEWDKEMO_HANDLER = CommandHandler("lewdkemo", lewdkemo)
NEKO_HANDLER = CommandHandler("neko", neko)
FEET_HANDLER = CommandHandler("feet", feet)
YURI_HANDLER = CommandHandler("yuri", yuri)
TRAP_HANDLER = CommandHandler("trap", trap)
FUTANARI_HANDLER = CommandHandler("futanari", futanari)
HOLOLEWD_HANDLER = CommandHandler("hololewd", hololewd)
SOLOGIF_HANDLER = CommandHandler("sologif", sologif)
CUMGIF_HANDLER = CommandHandler("cumgif", cumgif)
EROKEMO_HANDLER = CommandHandler("erokemo", erokemo)
LESBIAN_HANDLER = CommandHandler("lesbian", lesbian)
WALLPAPER_HANDLER = CommandHandler("wallpaper", wallpaper)
LEWDK_HANDLER = CommandHandler("lewdk", lewdk)
NGIF_HANDLER = CommandHandler("ngif", ngif)
TICKLE_HANDLER = CommandHandler("tickle", tickle)
LEWD_HANDLER = CommandHandler("lewd", lewd)
FEED_HANDLER = CommandHandler("feed", feed)
EROYURI_HANDLER = CommandHandler("eroyuri", eroyuri)
ERON_HANDLER = CommandHandler("eron", eron)
CUM_HANDLER = CommandHandler("cum", cum)
BJGIF_HANDLER = CommandHandler("bjgif", bjgif)
BJ_HANDLER = CommandHandler("bj", bj)
NEKONSFW_HANDLER = CommandHandler("nekonsfw", nekonsfw)
SOLO_HANDLER = CommandHandler("solo", solo)
KEMONOMIMI_HANDLER = CommandHandler("kemonomimi", kemonomimi)
AVATARLEWD_HANDLER = CommandHandler("avatarlewd", avatarlewd)
GASM_HANDLER = CommandHandler("gasm", gasm)
POKE_HANDLER = CommandHandler("poke", poke)
ANAL_HANDLER = CommandHandler("anal", anal)
HENTAI_HANDLER = CommandHandler("hentai", hentai)
AVATAR_HANDLER = CommandHandler("avatar", avatar)
EROFEET_HANDLER = CommandHandler("erofeet", erofeet)
HOLO_HANDLER = CommandHandler("holo", holo)
TITS_HANDLER = CommandHandler("tits", tits)
PUSSYGIF_HANDLER = CommandHandler("pussygif", pussygif)
HOLOERO_HANDLER = CommandHandler("holoero", holoero)
PUSSY_HANDLER = CommandHandler("pussy", pussy)
HENTAIGIF_HANDLER = CommandHandler("hentaigif", hentaigif)
CLASSIC_HANDLER = CommandHandler("classic", classic)
KUNI_HANDLER = CommandHandler("kuni", kuni)
WAIFU_HANDLER = CommandHandler("waifu", waifu)
LEWD_HANDLER = CommandHandler("lewd", lewd)
KISS_HANDLER = CommandHandler("kiss", kiss)
FEMDOM_HANDLER = CommandHandler("femdom", femdom)
CUDDLE_HANDLER = CommandHandler("cuddle", cuddle)
HUG_HANDLER = CommandHandler("hug", hug)
EROK_HANDLER = CommandHandler("erok", erok)
FOXGIRL_HANDLER = CommandHandler("foxgirl", foxgirl)
TITSGIF_HANDLER = CommandHandler("titsgif", titsgif)
ERO_HANDLER = CommandHandler("ero", ero)
SMUG_HANDLER = CommandHandler("smug", smug)
BAKA_HANDLER = CommandHandler("baka", baka)


CUTIEPII_PTB.add_handler(ADD_NSFW_HANDLER)
CUTIEPII_PTB.add_handler(REMOVE_NSFW_HANDLER)
CUTIEPII_PTB.add_handler(LIST_NSFW_CHATS_HANDLER)
CUTIEPII_PTB.add_handler(LEWDKEMO_HANDLER)
CUTIEPII_PTB.add_handler(NEKO_HANDLER)
CUTIEPII_PTB.add_handler(FEET_HANDLER)
CUTIEPII_PTB.add_handler(YURI_HANDLER)
CUTIEPII_PTB.add_handler(TRAP_HANDLER)
CUTIEPII_PTB.add_handler(FUTANARI_HANDLER)
CUTIEPII_PTB.add_handler(HOLOLEWD_HANDLER)
CUTIEPII_PTB.add_handler(SOLOGIF_HANDLER)
CUTIEPII_PTB.add_handler(CUMGIF_HANDLER)
CUTIEPII_PTB.add_handler(EROKEMO_HANDLER)
CUTIEPII_PTB.add_handler(LESBIAN_HANDLER)
CUTIEPII_PTB.add_handler(WALLPAPER_HANDLER)
CUTIEPII_PTB.add_handler(LEWDK_HANDLER)
CUTIEPII_PTB.add_handler(NGIF_HANDLER)
CUTIEPII_PTB.add_handler(TICKLE_HANDLER)
CUTIEPII_PTB.add_handler(LEWD_HANDLER)
CUTIEPII_PTB.add_handler(FEED_HANDLER)
CUTIEPII_PTB.add_handler(EROYURI_HANDLER)
CUTIEPII_PTB.add_handler(ERON_HANDLER)
CUTIEPII_PTB.add_handler(CUM_HANDLER)
CUTIEPII_PTB.add_handler(BJGIF_HANDLER)
CUTIEPII_PTB.add_handler(BJ_HANDLER)
CUTIEPII_PTB.add_handler(NEKONSFW_HANDLER)
CUTIEPII_PTB.add_handler(SOLO_HANDLER)
CUTIEPII_PTB.add_handler(KEMONOMIMI_HANDLER)
CUTIEPII_PTB.add_handler(AVATARLEWD_HANDLER)
CUTIEPII_PTB.add_handler(GASM_HANDLER)
CUTIEPII_PTB.add_handler(POKE_HANDLER)
CUTIEPII_PTB.add_handler(ANAL_HANDLER)
CUTIEPII_PTB.add_handler(HENTAI_HANDLER)
CUTIEPII_PTB.add_handler(AVATAR_HANDLER)
CUTIEPII_PTB.add_handler(EROFEET_HANDLER)
CUTIEPII_PTB.add_handler(HOLO_HANDLER)
CUTIEPII_PTB.add_handler(TITS_HANDLER)
CUTIEPII_PTB.add_handler(PUSSYGIF_HANDLER)
CUTIEPII_PTB.add_handler(HOLOERO_HANDLER)
CUTIEPII_PTB.add_handler(PUSSY_HANDLER)
CUTIEPII_PTB.add_handler(HENTAIGIF_HANDLER)
CUTIEPII_PTB.add_handler(CLASSIC_HANDLER)
CUTIEPII_PTB.add_handler(KUNI_HANDLER)
CUTIEPII_PTB.add_handler(WAIFU_HANDLER)
CUTIEPII_PTB.add_handler(LEWD_HANDLER)
CUTIEPII_PTB.add_handler(KISS_HANDLER)
CUTIEPII_PTB.add_handler(FEMDOM_HANDLER)
CUTIEPII_PTB.add_handler(CUDDLE_HANDLER)
CUTIEPII_PTB.add_handler(EROK_HANDLER)
CUTIEPII_PTB.add_handler(FOXGIRL_HANDLER)
CUTIEPII_PTB.add_handler(TITSGIF_HANDLER)
CUTIEPII_PTB.add_handler(ERO_HANDLER)
CUTIEPII_PTB.add_handler(SMUG_HANDLER)
CUTIEPII_PTB.add_handler(BAKA_HANDLER)

__handlers__ = [
    ADD_NSFW_HANDLER,
    REMOVE_NSFW_HANDLER,
    LIST_NSFW_CHATS_HANDLER,
    NEKO_HANDLER,
    FEET_HANDLER,
    YURI_HANDLER,
    TRAP_HANDLER,
    FUTANARI_HANDLER,
    HOLOLEWD_HANDLER,
    SOLOGIF_HANDLER,
    CUMGIF_HANDLER,
    EROKEMO_HANDLER,
    LESBIAN_HANDLER,
    WALLPAPER_HANDLER,
    LEWDK_HANDLER,
    NGIF_HANDLER,
    TICKLE_HANDLER,
    LEWD_HANDLER,
    FEED_HANDLER,
    EROYURI_HANDLER,
    ERON_HANDLER,
    CUM_HANDLER,
    BJGIF_HANDLER,
    BJ_HANDLER,
    NEKONSFW_HANDLER,
    SOLO_HANDLER,
    KEMONOMIMI_HANDLER,
    AVATARLEWD_HANDLER,
    GASM_HANDLER,
    POKE_HANDLER,
    ANAL_HANDLER,
    HENTAI_HANDLER,
    AVATAR_HANDLER,
    EROFEET_HANDLER,
    HOLO_HANDLER,
    TITS_HANDLER,
    PUSSYGIF_HANDLER,
    HOLOERO_HANDLER,
    PUSSY_HANDLER,
    HENTAIGIF_HANDLER,
    CLASSIC_HANDLER,
    KUNI_HANDLER,
    WAIFU_HANDLER,
    LEWD_HANDLER,
    KISS_HANDLER,
    FEMDOM_HANDLER,
    LEWDKEMO_HANDLER,
    CUDDLE_HANDLER,
    EROK_HANDLER,
    FOXGIRL_HANDLER,
    TITSGIF_HANDLER,
    ERO_HANDLER,
    SMUG_HANDLER,
    BAKA_HANDLER,
]

__help__ = """
Usage*:*
/addnsfw*:* Enable NSFW mode
/rmnsfw*:* Disable NSFW mode
 
Commands*:*   
➛ /neko*:* Sends Random SFW Neko source Images.
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
