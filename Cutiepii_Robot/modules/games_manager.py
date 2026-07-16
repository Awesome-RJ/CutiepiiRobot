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

import io
import time
import random
import requests
from PIL import Image
from telegram import Update
from telegram.ext import ContextTypes, filters
from telegram.constants import ParseMode
from telegram.helpers import mention_html

from Cutiepii_Robot import dispatcher, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot.modules.sql import flag_guess_sql
from Cutiepii_Robot.modules.sql import riddle_sql
from Cutiepii_Robot.modules.sql import poke_guess_sql

# ==========================================
# Guess Flag Game
# ==========================================

FLAGS = {
    "🇺🇸": ["united states", "usa", "us"],
    "🇬🇧": ["united kingdom", "uk", "britain"],
    "🇨🇦": ["canada"],
    "🇯🇵": ["japan"],
    "🇫🇷": ["france"],
    "🇩🇪": ["germany"],
    "🇮🇹": ["italy"],
    "🇦🇺": ["australia"],
    "🇮🇳": ["india"],
    "🇧🇷": ["brazil"],
    "🇷🇺": ["russia"],
    "🇨🇳": ["china"],
    "🇿🇦": ["south africa"],
    "🇲🇽": ["mexico"],
    "🇪🇸": ["spain"],
    "🇰🇷": ["south korea", "korea"],
    "🇪🇬": ["egypt"],
    "🇸🇦": ["saudi arabia"],
    "🇹🇷": ["turkey"],
    "🇦🇷": ["argentina"]
}


@cutiepii_cmd(command="flagguess", filters=filters.ChatType.GROUPS)
async def start_flag_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if context.chat_data.get("flag_active"):
        await message.reply_text("<b>Flag Guess Game</b>\nA flag guess game is already active in this chat!", parse_mode=ParseMode.HTML)
        return

    is_hard = args and args[0].lower() == "hard"
    total_time = 30 if is_hard else 60
    base_coins = 20 if is_hard else 10

    flag_emoji = random.choice(list(FLAGS.keys()))
    answers = FLAGS[flag_emoji]

    context.chat_data["flag_active"] = True
    context.chat_data["flag_details"] = {
        "flag": flag_emoji,
        "answers": answers,
        "start_time": time.time(),
        "total_time": total_time,
        "base_coins": base_coins
    }

    mode_str = "<b>HARD MODE</b>" if is_hard else "<b>NORMAL MODE</b>"
    await message.reply_text(
        f"<b>NEW FLAG GUESS GAME</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"- <b>Mode:</b> {mode_str}\n"
        f"- <b>Time Limit:</b> <code>{total_time}s</code>\n"
        f"- <b>Base Reward:</b> <code>{base_coins} coins</code>\n\n"
        f"Be the first to type the country name for this flag:\n"
        f"<span style='font-size: 40px;'>{flag_emoji}</span>",
        parse_mode=ParseMode.HTML
    )


@cutiepii_cmd(command=["flagguessstop", "flagstop"], filters=filters.ChatType.GROUPS)
async def stop_flag_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not context.chat_data.get("flag_active"):
        await message.reply_text("<b>Flag Guess Game</b>\nNo flag guess game is currently active.", parse_mode=ParseMode.HTML)
        return

    context.chat_data["flag_active"] = False
    context.chat_data["flag_details"] = None
    await message.reply_text("<b>Flag Guess Game</b>\nFlag guess game has been cancelled.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command=["flagguesstop", "flagguessleaderboard"])
async def flag_guess_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    top = flag_guess_sql.get_top_guessers()
    if not top:
        await message.reply_text("<b>No Records</b>\nNo guess history recorded yet.", parse_mode=ParseMode.HTML)
        return

    reply = "<b>FLAG GUESSING LEADERBOARD</b>\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, user in enumerate(top, 1):
        try:
            member = await context.bot.get_chat_member(update.effective_chat.id, user.user_id)
            name = member.user.first_name
        except Exception:
            name = f"User {user.user_id}"
        reply += f"{i}. {mention_html(user.user_id, name)} — <b>{user.wins} wins</b> ({user.coins} coins, {user.xp} XP)\n"

    await message.reply_text(reply, parse_mode=ParseMode.HTML)


# ==========================================
# Riddle Challenge Game
# ==========================================

RIDDLES = [
    {"q": "What has hands but cannot clap?", "a": ["clock", "a clock"]},
    {"q": "What gets wetter the more it dries?", "a": ["towel", "a towel"]},
    {"q": "What has to be broken before you can use it?", "a": ["egg", "an egg"]},
    {"q": "What has a head and a tail but no body?", "a": ["coin", "a coin"]},
    {"q": "The more of them you take, the more you leave behind. What are they?", "a": ["footsteps", "footstep"]},
    {"q": "I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?", "a": ["echo", "an echo"]},
    {"q": "You see a boat filled with people. It has not sunk, but when you look again you don’t see a single person on the boat. Why?", "a": ["all married", "they are all married", "married"]}
]


@cutiepii_cmd(command="riddle", filters=filters.ChatType.GROUPS)
async def start_riddle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if context.chat_data.get("riddle_active"):
        await message.reply_text("<b>Riddle Challenge</b>\nA riddle challenge is already active in this chat!", parse_mode=ParseMode.HTML)
        return

    is_hard = args and args[0].lower() == "hard"
    total_time = 30 if is_hard else 60
    base_coins = 20 if is_hard else 10

    chosen = random.choice(RIDDLES)

    context.chat_data["riddle_active"] = True
    context.chat_data["riddle_details"] = {
        "question": chosen["q"],
        "answers": chosen["a"],
        "start_time": time.time(),
        "total_time": total_time,
        "base_coins": base_coins
    }

    mode_str = "<b>HARD MODE</b>" if is_hard else "<b>NORMAL MODE</b>"
    await message.reply_text(
        f"<b>NEW RIDDLE CHALLENGE</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"- <b>Mode:</b> {mode_str}\n"
        f"- <b>Time Limit:</b> <code>{total_time}s</code>\n"
        f"- <b>Base Reward:</b> <code>{base_coins} coins</code>\n\n"
        f"<i>\"{chosen['q']}\"</i>\n\n"
        f"Be the first to type the correct answer to solve it!",
        parse_mode=ParseMode.HTML
    )


@cutiepii_cmd(command=["riddlestop", "rstop"], filters=filters.ChatType.GROUPS)
async def stop_riddle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not context.chat_data.get("riddle_active"):
        await message.reply_text("<b>Riddle Challenge</b>\nNo riddle challenge is currently active.", parse_mode=ParseMode.HTML)
        return

    context.chat_data["riddle_active"] = False
    context.chat_data["riddle_details"] = None
    await message.reply_text("<b>Riddle Challenge</b>\nRiddle challenge has been cancelled.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command=["riddletop", "riddleleaderboard"])
async def riddle_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    top = riddle_sql.get_top_solvers()
    if not top:
        await message.reply_text("<b>No Records</b>\nNo solvers history recorded yet.", parse_mode=ParseMode.HTML)
        return

    reply = "<b>RIDDLE CHALLENGE LEADERBOARD</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, user in enumerate(top, 1):
        try:
            member = await context.bot.get_chat_member(update.effective_chat.id, user.user_id)
            name = member.user.first_name
        except Exception:
            name = f"User {user.user_id}"
        reply += f"{i}. {mention_html(user.user_id, name)} — <b>{user.wins} solves</b> ({user.coins} coins, {user.xp} XP)\n"

    await message.reply_text(reply, parse_mode=ParseMode.HTML)


# ==========================================
# Who's That Pokémon? Game
# ==========================================

def get_pokemon_silhouette(sprite_url):
    res = requests.get(sprite_url)
    img = Image.open(io.BytesIO(res.content)).convert("RGBA")
    
    pixels = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]
            if a > 0:
                pixels[x, y] = (0, 0, 0, 255)
                
    out = io.BytesIO()
    img.save(out, "PNG")
    out.seek(0)
    return out


@cutiepii_cmd(command="pokeguess", filters=filters.ChatType.GROUPS)
async def start_poke_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if context.chat_data.get("poke_active"):
        await message.reply_text("<b>Pokémon Guess Game</b>\nA Pokémon guess round is already active in this chat!", parse_mode=ParseMode.HTML)
        return

    mode = "modern"
    if args:
        mode = args[0].lower()

    is_hard = mode == "hard"
    is_classic = mode == "classic"

    total_time = 30 if is_hard else 60
    base_coins = 20 if is_hard else 10

    poke_id = random.randint(1, 151) if is_classic else random.randint(1, 1010)

    status = await message.reply_text("<b>Pokémon Guess Game</b>\nFetching Pokémon data...", parse_mode=ParseMode.HTML)
    try:
        res = requests.get(f"https://pokeapi.co/api/v2/pokemon/{poke_id}").json()
        name = res.get("name").lower()
        sprite_url = res.get("sprites", {}).get("front_default")

        if not sprite_url:
            await status.edit_text("<b>Error</b>\nCould not fetch Pokémon image. Try again!", parse_mode=ParseMode.HTML)
            return

        silhouette_io = get_pokemon_silhouette(sprite_url)
        silhouette_io.name = "silhouette.png"

        context.chat_data["poke_active"] = True
        context.chat_data["poke_details"] = {
            "name": name,
            "sprite_url": sprite_url,
            "start_time": time.time(),
            "total_time": total_time,
            "base_coins": base_coins
        }

        mode_title = "CLASSIC MODE (Gen 1)" if is_classic else ("HARD MODE" if is_hard else "MODERN MODE (Gen 1-9)")
        await status.delete()
        await message.reply_photo(
            photo=silhouette_io,
            caption=(
                f"<b>WHO'S THAT POKÉMON?</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"- <b>Mode:</b> <code>{mode_title}</code>\n"
                f"- <b>Time Limit:</b> <code>{total_time}s</code>\n"
                f"- <b>Base Reward:</b> <code>{base_coins} coins</code>\n\n"
                f"Be the first to type the correct name of this Pokémon!"
            ),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        LOGGER.error(f"Error starting pokeguess: {e}")
        await status.edit_text("<b>Error</b>\nError loading game round. Try again!", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="pokeguessstop", filters=filters.ChatType.GROUPS)
async def stop_poke_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not context.chat_data.get("poke_active"):
        await message.reply_text("<b>Pokémon Guess Game</b>\nNo Pokémon guess game is currently active.", parse_mode=ParseMode.HTML)
        return

    context.chat_data["poke_active"] = False
    context.chat_data["poke_details"] = None
    await message.reply_text("<b>Pokémon Guess Game</b>\nPokémon guess game has been cancelled.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command=["pokeguesstop", "pokeguessleaderboard"])
async def poke_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    top = poke_guess_sql.get_top_guessers()
    if not top:
        await message.reply_text("<b>No Records</b>\nNo guessers history recorded yet.", parse_mode=ParseMode.HTML)
        return

    reply = "<b>POKÉMON GUESSING LEADERBOARD</b>\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for i, user in enumerate(top, 1):
        try:
            member = await context.bot.get_chat_member(update.effective_chat.id, user.user_id)
            name = member.user.first_name
        except Exception:
            name = f"User {user.user_id}"
        reply += f"{i}. {mention_html(user.user_id, name)} — <b>{user.wins} guesses</b> ({user.coins} coins, {user.xp} XP)\n"

    await message.reply_text(reply, parse_mode=ParseMode.HTML)


# ==========================================
# Traditional Minigames
# ==========================================

@cutiepii_cmd(command="rps", can_disable=False)
async def play_rps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    if not args:
        await message.reply_text("<b>Invalid Command Usage</b>\nUsage: <code>/rps [rock|paper|scissors]</code>", parse_mode=ParseMode.HTML)
        return

    user_choice = args[0].lower()
    choices = ["rock", "paper", "scissors"]
    if user_choice not in choices:
        await message.reply_text("<b>Invalid Choice</b>\nPlease choose rock, paper, or scissors.", parse_mode=ParseMode.HTML)
        return

    bot_choice = random.choice(choices)
    if user_choice == bot_choice:
        result = "It's a tie!"
    elif (user_choice == "rock" and bot_choice == "scissors") or \
         (user_choice == "paper" and bot_choice == "rock") or \
         (user_choice == "scissors" and bot_choice == "paper"):
        result = "You win!"
    else:
        result = "I win!"

    await message.reply_text(
        f"<b>Rock-Paper-Scissors</b>\n\n"
        f"- <b>Your Choice:</b> <code>{user_choice.capitalize()}</code>\n"
        f"- <b>My Choice:</b> <code>{bot_choice.capitalize()}</code>\n\n"
        f"<b>Result:</b> {result}",
        parse_mode=ParseMode.HTML
    )


@cutiepii_cmd(command="dice", can_disable=False)
async def roll_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_dice()


@cutiepii_cmd(command="slots", can_disable=False)
async def play_slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    emojis = ["🍎", "🍒", "🍇", "🍋", "💎", "🎰"]
    r1, r2, r3 = random.choices(emojis, k=3)
    
    result = "JACKPOT!" if r1 == r2 == r3 else "Try again!"
    await message.reply_text(
        f"<b>SLOT MACHINE SPUN</b>\n\n"
        f"[ {r1} | {r2} | {r3} ]\n\n"
        f"<b>Result:</b> {result}",
        parse_mode=ParseMode.HTML
    )


@cutiepii_cmd(command="8ball", can_disable=False)
async def ask_8ball(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    responses = [
        "It is certain.", "Without a doubt.", "Reply hazy, try again.",
        "Don't count on it.", "My sources say no.", "Very doubtful."
    ]
    await message.reply_text(f"<b>Magic 8-Ball</b>\n\n{random.choice(responses)}", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="toss", can_disable=False)
async def toss_coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    outcome = "Heads" if random.choice([True, False]) else "Tails"
    await message.reply_text(f"<b>Coin Toss Result</b>\n\nIt landed on <b>{outcome}</b>.", parse_mode=ParseMode.HTML)


# Helper to retry message sending on timeouts
async def reply_text_with_retry(message, *args, **kwargs):
    from telegram.error import TimedOut
    import asyncio
    for attempt in range(2):
        try:
            return await message.reply_text(*args, **kwargs)
        except TimedOut:
            if attempt == 1:
                raise
            await asyncio.sleep(1)

async def reply_photo_with_retry(message, *args, **kwargs):
    from telegram.error import TimedOut
    import asyncio
    for attempt in range(2):
        try:
            return await message.reply_photo(*args, **kwargs)
        except TimedOut:
            if attempt == 1:
                raise
            await asyncio.sleep(1)


# ==========================================
# Listeners
# ==========================================

@cutiepii_msg(filters.TEXT & filters.ChatType.GROUPS, group=88)
async def global_guess_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    text = message.text.lower().strip()

    # 1. Flag guess
    # 1. Flag guess
    if context.chat_data.get("flag_active"):
        details = context.chat_data.get("flag_details")
        if details:
            elapsed = time.time() - details["start_time"]
            if elapsed > details["total_time"]:
                context.chat_data["flag_active"] = False
                context.chat_data["flag_details"] = None
                await reply_text_with_retry(message, f"<b>Time's Up!</b>\n\nThe correct country was: <b>{details['answers'][0].capitalize()}</b>", parse_mode=ParseMode.HTML)
            elif text in details["answers"]:
                context.chat_data["flag_active"] = False
                context.chat_data["flag_details"] = None

                time_left = details["total_time"] - elapsed
                speed_bonus = round(5 * time_left / details["total_time"])
                coins = details["base_coins"] + speed_bonus
                xp = details["base_coins"]

                flag_guess_sql.add_win(user.id, coins, xp)
                await reply_text_with_retry(
                    message,
                    f"{mention_html(user.id, user.first_name)} <b>Guessed Correctly!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"- <b>Country:</b> <code>{details['answers'][0].capitalize()}</code>\n"
                    f"- <b>Base Reward:</b> <code>{details['base_coins']} coins</code>\n"
                    f"- <b>Speed Bonus:</b> <code>+{speed_bonus} coins</code>\n"
                    f"- <b>XP Gained:</b> <code>+{xp} XP</code>\n",
                    parse_mode=ParseMode.HTML
                )

    # 2. Riddle guess
    if context.chat_data.get("riddle_active"):
        details = context.chat_data.get("riddle_details")
        if details:
            elapsed = time.time() - details["start_time"]
            if elapsed > details["total_time"]:
                context.chat_data["riddle_active"] = False
                context.chat_data["riddle_details"] = None
                await reply_text_with_retry(message, f"<b>Time's Up!</b>\n\nThe correct answer was: <b>{details['answers'][0].capitalize()}</b>", parse_mode=ParseMode.HTML)
            elif text in details["answers"]:
                context.chat_data["riddle_active"] = False
                context.chat_data["riddle_details"] = None

                time_left = details["total_time"] - elapsed
                speed_bonus = round(5 * time_left / details["total_time"])
                coins = details["base_coins"] + speed_bonus
                xp = details["base_coins"]

                riddle_sql.add_win(user.id, coins, xp)
                await reply_text_with_retry(
                    message,
                    f"{mention_html(user.id, user.first_name)} <b>Solved the Riddle!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"- <b>Answer:</b> <code>{details['answers'][0].capitalize()}</code>\n"
                    f"- <b>Base Reward:</b> <code>{details['base_coins']} coins</code>\n"
                    f"- <b>Speed Bonus:</b> <code>+{speed_bonus} coins</code>\n"
                    f"- <b>XP Gained:</b> <code>+{xp} XP</code>\n",
                    parse_mode=ParseMode.HTML
                )

    # 3. Poke guess
    if context.chat_data.get("poke_active"):
        details = context.chat_data.get("poke_details")
        if details:
            elapsed = time.time() - details["start_time"]
            if elapsed > details["total_time"]:
                context.chat_data["poke_active"] = False
                context.chat_data["poke_details"] = None
                await reply_text_with_retry(message, f"<b>Time's Up!</b>\n\nThe Pokémon was: <b>{details['name'].capitalize()}</b>", parse_mode=ParseMode.HTML)
            elif text == details["name"]:
                context.chat_data["poke_active"] = False
                context.chat_data["poke_details"] = None

                time_left = details["total_time"] - elapsed
                speed_bonus = round(5 * time_left / details["total_time"])
                coins = details["base_coins"] + speed_bonus
                xp = details["base_coins"]

                poke_guess_sql.add_win(user.id, coins, xp)
                await reply_photo_with_retry(
                    message,
                    photo=details["sprite_url"],
                    caption=(
                        f"{mention_html(user.id, user.first_name)} <b>Guessed Correctly!</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"It was: <b>{details['name'].capitalize()}</b>!\n\n"
                        f"- <b>Base Reward:</b> <code>{details['base_coins']} coins</code>\n"
                        f"- <b>Speed Bonus:</b> <code>+{speed_bonus} coins</code>\n"
                        f"- <b>XP Gained:</b> <code>+{xp} XP</code>\n"
                    ),
                    parse_mode=ParseMode.HTML
                )


__help__ = True

__mod_name__ = "Games Manager"
