"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

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

import html
import random
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler

from Cutiepii_Robot import dispatcher, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd, cutiepii_callback


# ==========================================
# Anime / Waifu / Neko Image APIs
# ==========================================

def fetch_anime_image(mode: str, category: str) -> str:
    # 1. Try waifu.pics
    try:
        res = requests.get(f"https://api.waifu.pics/{mode}/{category}", timeout=5)
        if res.status_code == 200:
            return res.json().get("url")
    except Exception as e:
        LOGGER.warning(f"Failed to fetch from waifu.pics for {mode}/{category}: {e}")

    # 2. Try nekos.best fallback for SFW categories
    if mode == "sfw":
        try:
            res = requests.get(f"https://nekos.best/api/v2/{category}", timeout=5)
            if res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    return results[0].get("url")
        except Exception as e:
            LOGGER.warning(f"Failed to fetch from nekos.best fallback for {category}: {e}")

    raise RuntimeError("Could not retrieve image from any server.")


@cutiepii_cmd(command="waifu", can_disable=False)
async def sfw_waifu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    try:
        url = fetch_anime_image("sfw", "waifu")
        await message.reply_photo(photo=url, caption="Here is your SFW Waifu! ✨")
    except Exception as e:
        await message.reply_text("⚠️ <b>Connection error:</b> Could not retrieve image from servers. Please try again later.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="neko", can_disable=False)
async def sfw_neko(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    try:
        url = fetch_anime_image("sfw", "neko")
        await message.reply_photo(photo=url, caption="Here is your Neko! 🐱")
    except Exception as e:
        await message.reply_text("⚠️ <b>Connection error:</b> Could not retrieve image from servers. Please try again later.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="sfw", can_disable=False)
async def sfw_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Waifu", callback_data="pics_sfw_waifu"),
            InlineKeyboardButton("Neko", callback_data="pics_sfw_neko")
        ],
        [
            InlineKeyboardButton("Shinobu", callback_data="pics_sfw_shinobu"),
            InlineKeyboardButton("Megumin", callback_data="pics_sfw_megumin")
        ]
    ])
    await message.reply_text("🏮 <b>SFW Image Category Hub:</b>", reply_markup=keyboard, parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="nsfw", can_disable=False)
async def nsfw_hub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    if chat.type != "private":
        await message.reply_text("❌ NSFW categories can only be accessed in PM/Private Chat!")
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Waifu (NSFW)", callback_data="pics_nsfw_waifu"),
            InlineKeyboardButton("Neko (NSFW)", callback_data="pics_nsfw_neko")
        ],
        [
            InlineKeyboardButton("Trap", callback_data="pics_nsfw_trap"),
            InlineKeyboardButton("Blowjob", callback_data="pics_nsfw_blowjob")
        ]
    ])
    await message.reply_text("🔞 <b>NSFW Category Hub (PM Only):</b>", reply_markup=keyboard, parse_mode=ParseMode.HTML)


@cutiepii_callback(pattern=r"^pics_")
async def pics_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    mode = data[1] # sfw / nsfw
    category = data[2] # waifu / neko etc

    try:
        url = fetch_anime_image(mode, category)
        await query.message.reply_photo(photo=url, caption=f"Category: <code>{category}</code> ({mode.upper()})", parse_mode=ParseMode.HTML)
    except Exception as e:
        await query.message.reply_text("⚠️ <b>Connection error:</b> Could not retrieve image from servers. Please try again later.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="nekobest", can_disable=False)
async def neko_best(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    category = args[0].lower() if args else "neko"

    try:
        res = requests.get(f"https://nekos.best/api/v2/{category}").json()
        results = res.get("results", [])
        if results:
            url = results[0].get("url")
            await message.reply_photo(photo=url, caption=f"Here is your high-quality {category}! 🌸")
        else:
            await message.reply_text("No results found for that category.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")


# ==========================================
# Guess Games
# ==========================================

@cutiepii_cmd(command="guesscharacter", can_disable=False)
async def guess_character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    char_id = random.randint(1, 500)
    try:
        res = requests.get(f"https://api.jikan.moe/v4/characters/{char_id}").json()
        data = res.get("data", {})
        if data:
            name = data.get("name")
            image_url = data.get("images", {}).get("jpg", {}).get("image_url")
            context.chat_data["guess_char"] = name
            await message.reply_photo(
                photo=image_url,
                caption="🕵️‍♂️ <b>Who's That Character?</b>\n\nUse `/guess [name]` to answer!",
                parse_mode=ParseMode.HTML
            )
        else:
            await message.reply_text("Could not fetch character at the moment. Try again!")
    except Exception:
        await message.reply_text("Could not load character. Try again!")


@cutiepii_cmd(command="guessanime", can_disable=False)
async def guess_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    anime_id = random.randint(1, 200)
    try:
        res = requests.get(f"https://api.jikan.moe/v4/anime/{anime_id}").json()
        data = res.get("data", {})
        if data:
            title = data.get("title")
            synopsis = data.get("synopsis")
            if synopsis:
                synopsis = synopsis[:300] + "..."
            context.chat_data["guess_anime"] = title
            await message.reply_text(
                f"📖 <b>Guess the Anime (Synopsis):</b>\n\n"
                f"<i>\"{synopsis}\"</i>\n\n"
                f"Use `/guess [name]` to answer!",
                parse_mode=ParseMode.HTML
            )
        else:
            await message.reply_text("Could not load anime synopsis. Try again!")
    except Exception:
        await message.reply_text("Could not load anime synopsis. Try again!")


@cutiepii_cmd(command="guessquote", can_disable=False)
async def guess_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    quotes = [
        {"quote": "If you don't like your destiny, don't accept it. Instead have the courage to change it the way you want it to be!", "anime": "Naruto"},
        {"quote": "I am the hope of the universe. I am the answer to all living things that cry out for peace.", "anime": "Dragon Ball Z"},
        {"quote": "If you win, you live. If you lose, you die. If you don't fight, you can't win!", "anime": "Attack on Titan"},
        {"quote": "People's dreams... Have no end!", "anime": "One Piece"}
    ]
    chosen = random.choice(quotes)
    context.chat_data["guess_anime"] = chosen["anime"]
    await message.reply_text(
        f"💬 <b>Guess the Anime by Quote:</b>\n\n"
        f"<i>\"{chosen['quote']}\"</i>\n\n"
        f"Use `/guess [name]` to answer!",
        parse_mode=ParseMode.HTML
    )


@cutiepii_cmd(command="guess", can_disable=False)
async def submit_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    if not args:
        await message.reply_text("Please provide your guess!")
        return

    user_guess = " ".join(args).lower().strip()
    correct_char = context.chat_data.get("guess_char")
    correct_anime = context.chat_data.get("guess_anime")

    if correct_char and correct_char.lower().strip() in user_guess:
        context.chat_data["guess_char"] = None
        await message.reply_text(f"🎉 <b>Correct!</b> The character was indeed <b>{correct_char}</b>!", parse_mode=ParseMode.HTML)
    elif correct_anime and correct_anime.lower().strip() in user_guess:
        context.chat_data["guess_anime"] = None
        await message.reply_text(f"🎉 <b>Correct!</b> The anime was indeed <b>{correct_anime}</b>!", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("❌ Incorrect guess! Keep trying!")


# ==========================================
# Hunter Abilities
# ==========================================

@cutiepii_cmd(command="animequote", can_disable=False)
async def anime_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    quotes = [
        {"quote": "Fear is not evil. It tells you what your weakness is.", "character": "Gildarts Clive", "anime": "Fairy Tail"},
        {"quote": "Whatever you lose, you'll find it again. But what you throw away you'll never get back.", "character": "Kenshin Himura", "anime": "Rurouni Kenshin"},
        {"quote": "To know sorrow is not evil, but to know you can't be sorrowed is.", "character": "Hachiman Hikigaya", "anime": "My Teen Romantic Comedy SNAFU"}
    ]
    chosen = random.choice(quotes)
    await message.reply_text(
        f"💬 <b>Anime Quote</b>\n\n"
        f"<i>\"{chosen['quote']}\"</i>\n\n"
        f"👤 <b>Character:</b> {chosen['character']}\n"
        f"📺 <b>Anime:</b> {chosen['anime']}",
        parse_mode=ParseMode.HTML
    )


@cutiepii_cmd(command="nen", can_disable=False)
async def nen_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    categories = ["Enhancer", "Transmuter", "Conjurer", "Emitter", "Manipulator", "Specialist"]
    chosen = random.choice(categories)
    await message.reply_text(f"⚡️ <b>Nen Scan Complete!</b>\n\nYour Nen category type is: <b>{chosen}</b>!", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="aura", can_disable=False)
async def aura_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    level = random.randint(1000, 1200000)
    await message.reply_text(f"🔮 <b>Aura Scanner:</b>\n\nDetected Aura Power Level: <code>{level}</code>!", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="animefate", can_disable=False)
async def anime_fate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    fates = [
        "You will become the next Hokage of the Leaf Village!",
        "You will locate the legendary One Piece and rule the seas!",
        "You will be selected by a Shinigami to receive a Death Note.",
        "You will successfully join the Survey Corps and defeat Titans!"
    ]
    await message.reply_text(f"🔮 <b>Anime Fate Prediction:</b>\n\n{random.choice(fates)}")


# ==========================================
# Info Bureau
# ==========================================

@cutiepii_cmd(command="amv", can_disable=False)
async def search_coub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    if args:
        query = "%20".join(args)
        url = f"https://coub.com/api/v2/search/coubs?q={query}"
    else:
        url = "https://coub.com/api/v2/timeline/trending"
        
    try:
        res = requests.get(url).json()
        coubs = res.get("coubs", [])
        if coubs:
            chosen = random.choice(coubs)
            permalink = chosen.get("permalink")
            title = chosen.get("title")
            await message.reply_text(f"🎥 <b>AMV/Coub Video:</b> {title}\n\nLink: https://coub.com/view/{permalink}", parse_mode=ParseMode.HTML)
        else:
            await message.reply_text("No coub videos found.")
    except Exception as e:
        await message.reply_text(f"Error fetching Coub: {e}")


@cutiepii_cmd(command="randomanime", can_disable=False)
async def random_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    try:
        res = requests.get("https://api.jikan.moe/v4/random/anime").json()
        data = res.get("data", {})
        if data:
            title = data.get("title")
            synopsis = data.get("synopsis", "No synopsis available.")
            url = data.get("url")
            await message.reply_text(f"📺 <b>Random Anime Recommendation:</b>\n\n🌸 <b>{title}</b>\n\n<i>{synopsis[:400]}...</i>\n\nLink: {url}", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"Error: {e}")


@cutiepii_cmd(command="recents", can_disable=False)
async def recent_episodes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    try:
        res = requests.get("https://api.jikan.moe/v4/seasons/now?limit=5").json()
        data = res.get("data", [])
        if data:
            reply = "📺 <b>Recently Aired / Current Season Episodes:</b>\n\n"
            for anime in data:
                title = anime.get("title")
                eps = anime.get("episodes", "N/A")
                score = anime.get("score", "N/A")
                reply += f"❍ <b>{title}</b> (Score: {score}, Episodes: {eps})\n"
            await message.reply_text(reply, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"Error: {e}")


@cutiepii_cmd(command="schedule", can_disable=False)
async def airing_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    day = args[0].lower() if args else "monday"
    try:
        res = requests.get(f"https://api.jikan.moe/v4/schedules?filter={day}").json()
        data = res.get("data", [])
        if data:
            reply = f"📅 <b>Airing Schedule for {day.capitalize()}:</b>\n\n"
            for anime in data[:10]:
                title = anime.get("title")
                time = anime.get("broadcast", {}).get("time", "N/A")
                reply += f"❍ <b>{title}</b> at <code>{time}</code>\n"
            await message.reply_text(reply, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(f"No schedule found for {day}.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")


@cutiepii_cmd(command="recommend", can_disable=False)
async def recommend_anime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    if not args:
        await message.reply_text("Usage: `/recommend [anime_name]`")
        return
    query = "%20".join(args)
    try:
        search_res = requests.get(f"https://api.jikan.moe/v4/anime?q={query}&limit=1").json()
        anime_data = search_res.get("data", [])
        if not anime_data:
            await message.reply_text("Anime not found.")
            return
        
        anime_id = anime_data[0]["mal_id"]
        title = anime_data[0]["title"]
        
        rec_res = requests.get(f"https://api.jikan.moe/v4/anime/{anime_id}/recommendations").json()
        recs = rec_res.get("data", [])
        if recs:
            reply = f"✨ <b>Recommendations for {title}:</b>\n\n"
            for r in recs[:5]:
                entry = r.get("entry", {})
                r_title = entry.get("title")
                reply += f"❍ <b>{r_title}</b>\n"
            await message.reply_text(reply, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(f"No recommendations found for {title}.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")

__help__ = True

__mod_name__ = "Anime Hub"
