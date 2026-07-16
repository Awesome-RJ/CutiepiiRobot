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
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import mention_html

from Cutiepii_Robot import dispatcher, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd


# ==========================================
# Social Interactions
# ==========================================

@cutiepii_cmd(command="slap", can_disable=False)
async def slap_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    replied = message.reply_to_message

    target = replied.from_user if replied else user
    slaps = [
        f"{mention_html(user.id, user.first_name)} slapped {mention_html(target.id, target.first_name)} with a giant trout.",
        f"{mention_html(user.id, user.first_name)} slaps {mention_html(target.id, target.first_name)} across the face."
    ]
    await message.reply_text(random.choice(slaps), parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="pat", can_disable=False)
async def pat_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    replied = message.reply_to_message

    target = replied.from_user if replied else user
    pats = [
        f"{mention_html(user.id, user.first_name)} gently pats {mention_html(target.id, target.first_name)} on the head.",
        f"{mention_html(user.id, user.first_name)} gives {mention_html(target.id, target.first_name)} a warm soft pat."
    ]
    await message.reply_text(random.choice(pats), parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="runs", can_disable=False)
async def runs_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    statuses = [
        "runs away to the forest.",
        "runs directly into a wall.",
        "sprints away like a ninja."
    ]
    await message.reply_text(random.choice(statuses))


# ==========================================
# Text Formatting
# ==========================================

@cutiepii_cmd(command="shout", can_disable=False)
async def shout_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    if not args:
        await message.reply_text("<b>Invalid Command Usage</b>\nUsage: <code>/shout [text]</code>", parse_mode=ParseMode.HTML)
        return

    text = " ".join(args).upper()
    shouted = " ".join(char for char in text)
    await message.reply_text(shouted)


@cutiepii_cmd(command="weebify", can_disable=False)
async def weebify_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    if not args:
        await message.reply_text("<b>Invalid Command Usage</b>\nUsage: <code>/weebify [text]</code>", parse_mode=ParseMode.HTML)
        return

    text = " ".join(args)
    normal = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    weeb = "αвc∂єfgнιjкℓмησρqяѕтυνωxуzαвc∂єfgнιjкℓмησρqяѕтυνωxуz"
    trans = str.maketrans(normal, weeb)
    await message.reply_text(text.translate(trans))


@cutiepii_cmd(command="thonkify", can_disable=False)
async def thonkify_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    text = " ".join(args) if args else "Hmm"
    await message.reply_text(text)


# ==========================================
# Animations
# ==========================================

@cutiepii_cmd(command="kill", can_disable=False)
async def kill_anim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await update.effective_message.reply_text("<b>Termination Sequence</b>\nPreparing target...", parse_mode=ParseMode.HTML)
    await asyncio.sleep(1)
    await message.edit_text("<b>Termination Sequence</b>\nAiming...", parse_mode=ParseMode.HTML)
    await asyncio.sleep(1)
    await message.edit_text("<b>Termination Sequence</b>\nUser terminated.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="love", can_disable=False)
async def love_anim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await update.effective_message.reply_text("Sending love...", parse_mode=ParseMode.HTML)
    for hearts in ["Sending love [Level 1]...", "Sending love [Level 2]...", "Sending love [Level 3]...", "LOVE SENT!"]:
        await asyncio.sleep(0.8)
        await message.edit_text(hearts)


@cutiepii_cmd(command="hacks", can_disable=False)
async def hacks_anim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await update.effective_message.reply_text("<b>System Intrusion</b>\nInitiating hack...", parse_mode=ParseMode.HTML)
    for progress in [10, 45, 80, 100]:
        await asyncio.sleep(0.8)
        if progress == 100:
            await message.edit_text("<b>System Intrusion</b>\nSystem Hacked 100%! Access Granted.", parse_mode=ParseMode.HTML)
        else:
            await message.edit_text(f"<b>System Intrusion</b>\nHacking database: {progress}%...", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="bombs", can_disable=False)
async def bombs_anim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await update.effective_message.reply_text("<b>Detonation Sequence</b>\nBomb planted...", parse_mode=ParseMode.HTML)
    for timer in ["3...", "2...", "1...", "BOOM! Detonation complete."]:
        await asyncio.sleep(0.8)
        await message.edit_text(timer)


@cutiepii_cmd(command="moon", can_disable=False)
async def moon_anim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await update.effective_message.reply_text("Changing phases...")
    for phase in ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous", "Full Moon", "Waning Gibbous", "Third Quarter", "Waning Crescent", "CYCLE COMPLETE!"]:
        await asyncio.sleep(0.6)
        await message.edit_text(phase)


@cutiepii_cmd(command="clock", can_disable=False)
async def clock_anim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = await update.effective_message.reply_text("Ticking...")
    for time_step in ["12:00", "03:00", "06:00", "09:00", "12:00 DING DING DING!"]:
        await asyncio.sleep(0.6)
        await message.edit_text(time_step)


# ==========================================
# Fun Jokes & Excuse APIs
# ==========================================

@cutiepii_cmd(command="chuck", can_disable=False)
async def chuck_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    try:
        res = requests.get("https://api.chucknorris.io/jokes/random").json()
        await message.reply_text(res.get("value"))
    except Exception as e:
        await message.reply_text(f"<b>Error</b>\nAn error occurred: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="momma", can_disable=False)
async def momma_joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    jokes = [
        "Yo momma's so fat, when she fell she made the Grand Canyon!",
        "Yo momma's so old, she walked out of a museum and the alarm went off!",
        "Yo momma's so slow, it takes her a year to tell you what day it is."
    ]
    await message.reply_text(random.choice(jokes))


@cutiepii_cmd(command="excuse", can_disable=False)
async def get_excuse(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    excuses = [
        "My dog ate my homework.",
        "My internet went down because of a solar flare.",
        "I was busy saving the hidden leaf village.",
        "My aura levels were too low to operate devices."
    ]
    await message.reply_text(random.choice(excuses))


@cutiepii_cmd(command="buzz", can_disable=False)
async def get_buzz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    buzz = [
        "Leverage agile frameworks to provide a robust synopsis.",
        "Iterative approaches to corporate synergy paradigms.",
        "Overall value proposition of cloud-native ecosystem structures."
    ]
    await message.reply_text(random.choice(buzz))


@cutiepii_cmd(command="techy", can_disable=False)
async def get_techy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    phrases = [
        "Recompiling the neural network bypass pathway.",
        "Bypassing the firewall via local DNS redirection.",
        "Overclocking the core processor to increase S-rank calculation speeds."
    ]
    await message.reply_text(random.choice(phrases))


@cutiepii_cmd(command="advice", can_disable=False)
async def get_advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    try:
        res = requests.get("https://api.adviceslip.com/advice").json()
        await message.reply_text(res.get("slip", {}).get("advice", "Always check your limits."))
    except Exception as e:
        await message.reply_text(f"<b>Error</b>\nAn error occurred: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="advicesearch", can_disable=False)
async def search_advice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    if not args:
        await message.reply_text("<b>Invalid Command Usage</b>\nUsage: <code>/advicesearch [topic]</code>", parse_mode=ParseMode.HTML)
        return
    topic = args[0]
    try:
        res = requests.get(f"https://api.adviceslip.com/advice/search/{topic}").json()
        slips = res.get("slips", [])
        if slips:
            await message.reply_text(random.choice(slips).get("advice"))
        else:
            await message.reply_text("No advice found for that topic.")
    except Exception as e:
        await message.reply_text(f"<b>Error</b>\nAn error occurred: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="insult", can_disable=False)
async def get_insult(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    insults = [
        "You're like a cloud. When you disappear, it's a beautiful day.",
        "I'd agree with you but then we'd both be wrong.",
        "Your power level is under 5!"
    ]
    await message.reply_text(random.choice(insults))


@cutiepii_cmd(command="jokeapi", can_disable=False)
async def get_jokeapi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    category = args[0] if args else "Any"
    try:
        res = requests.get(f"https://v2.jokeapi.dev/joke/{category}?safe-mode").json()
        if res.get("type") == "single":
            await message.reply_text(res.get("joke"))
        else:
            await message.reply_text(f"{res.get('setup')}\n\n... {res.get('delivery')}")
    except Exception as e:
        await message.reply_text(f"<b>Error</b>\nAn error occurred: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="corporate", can_disable=False)
async def corporate_buzz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_buzz(update, context)


# ==========================================
# Utilities
# ==========================================

@cutiepii_cmd(command="fakeid", can_disable=False)
async def fake_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    first_names = ["Hiroshi", "Takashi", "Kenji", "Akira", "Minato"]
    last_names = ["Sato", "Suzuki", "Takahashi", "Tanaka", "Watanabe"]
    jobs = ["Tech Hunter", "Huntsman", "Spellcaster", "Nen Trainer"]
    
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    job = random.choice(jobs)
    fake_age = random.randint(18, 60)
    
    reply = (
        f"<b>GENERATED FAKE IDENTITY</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"- <b>Full Name:</b> <code>{name}</code>\n"
        f"- <b>Age:</b> <code>{fake_age}</code>\n"
        f"- <b>Occupation:</b> <code>{job}</code>\n"
        f"- <b>Status:</b> S-Rank Certified\n"
    )
    await message.reply_text(reply, parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="space", can_disable=False)
async def nasa_space(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    try:
        res = requests.get("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY").json()
        url = res.get("url")
        title = res.get("title")
        explanation = res.get("explanation", "")[:300] + "..."
        await message.reply_photo(photo=url, caption=f"<b>{title}</b>\n\n{explanation}", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"<b>Error</b>\nFailed to load APOD: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="country", can_disable=False)
async def country_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    if not args:
        await message.reply_text("<b>Invalid Command Usage</b>\nUsage: <code>/country [name]</code>", parse_mode=ParseMode.HTML)
        return

    name = args[0]
    try:
        res = requests.get(f"https://restcountries.com/v3.1/name/{name}").json()
        if isinstance(res, list) and res:
            data = res[0]
            common_name = data.get("name", {}).get("common")
            capital = data.get("capital", ["None"])[0]
            region = data.get("region")
            population = data.get("population")
            flag = data.get("flags", {}).get("png")
            
            reply = (
                f"<b>Country Statistics: {common_name}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"- <b>Capital:</b> <code>{capital}</code>\n"
                f"- <b>Region:</b> <code>{region}</code>\n"
                f"- <b>Population:</b> <code>{population:,}</code>\n"
            )
            await message.reply_photo(photo=flag, caption=reply, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text("<b>Error</b>\nCountry not found.", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"<b>Error</b>\nError fetching country info: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)


__help__ = True

__mod_name__ = "Social Fun"
