"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.
"""

import json
import random
from datetime import date
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from Cutiepii_Robot import dispatcher, telethn, REDIS, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
from Cutiepii_Robot.modules.sql import couples_sql as sql

# List of couple image URLs
IMAGE_URLS = [
    "https://files.catbox.moe/5zsvmu.jpg",
    "https://files.catbox.moe/wte8ko.jpg",
    "https://files.catbox.moe/uy4ydt.jpg",
    "https://files.catbox.moe/37uyq0.jpg",
    "https://files.catbox.moe/gikzhy.jpg"
]


@cutiepii_cmd(command=["couple", "couples", "ship", "detect_gay"])
async def couple(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Choose the couple of the day."""
    chat = update.effective_chat
    message = update.effective_message

    if chat.type == "private":
        await message.reply_text("This command can only be used in groups.")
        return

    chat_id = chat.id
    today = date.today()

    # Check if a couple is already chosen for today
    existing_couple = sql.get_couple(chat_id, today)

    if existing_couple:
        user1_id, user2_id = existing_couple
        try:
            user1 = await context.bot.get_chat_member(chat_id, user1_id)
            user2 = await context.bot.get_chat_member(chat_id, user2_id)
            user1_name = user1.user.first_name
            user2_name = user2.user.first_name
        except Exception:
            user1_name = "User 1"
            user2_name = "User 2"

        male_mention = f"<a href='tg://user?id={user1_id}'>{user1_name}</a>"
        female_mention = f"<a href='tg://user?id={user2_id}'>{user2_name}</a>"
    else:
        # Fetch members and choose a couple of the day
        try:
            members = []
            async for user in telethn.iter_participants(chat_id):
                if not user.bot and not user.deleted:
                    members.append(user)

            if len(members) < 2:
                await message.reply_text("Not enough members to choose a couple.")
                return

            male = random.choice(members)
            female = random.choice([m for m in members if m.id != male.id])

            sql.set_couple(chat_id, male.id, female.id, today)

            male_mention = f"<a href='tg://user?id={male.id}'>{male.first_name}</a>"
            female_mention = f"<a href='tg://user?id={female.id}'>{female.first_name}</a>"
        except Exception as e:
            LOGGER.exception(e)
            await message.reply_text("An error occurred while choosing a couple.")
            return

    img_url = random.choice(IMAGE_URLS)
    caption = (
        f"🎀  <b>𝒞❁𝓊𝓅𝓁𝑒 ❀𝒻 𝒯𝒽𝑒 𝒟𝒶𝓎</b>  🎀\n"
        f"╭──────────────\n"
        f"┊•➢ {male_mention} + {female_mention} = 💞\n"
        f"╰───•➢♡"
    )
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=img_url,
        caption=caption,
        parse_mode=ParseMode.HTML
    )


@cutiepii_cmd(command=["mywaifu", "mywaifuu"])
async def waifu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Find today's waifu for a user."""
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.type == "private":
        await message.reply_text("This command can only be used in groups.")
        return

    chat_id = chat.id
    user_id = user.id
    user_mention = f"<a href='tg://user?id={user_id}'>{user.first_name}</a>"

    waifu_key = f"waifu_{chat_id}_{user_id}"
    cached_waifu = REDIS.get(waifu_key)

    if cached_waifu:
        try:
            data = json.loads(cached_waifu)
            waifu_id = data["waifu_id"]
            waifu_name = data["waifu_name"]
            bond = data["bond"]
            photo_file_id = data.get("photo_file_id")
        except Exception:
            cached_waifu = None

    if not cached_waifu:
        # Find a random waifu among chat members
        try:
            members = []
            async for member in telethn.iter_participants(chat_id):
                if not member.bot and not member.deleted and member.id != user_id:
                    members.append(member)

            if not members:
                await message.reply_text("Couldn't find any eligible waifu for you in this chat!")
                return

            waifu_choice = random.choice(members)
            waifu_id = waifu_choice.id
            waifu_name = waifu_choice.first_name
            bond = random.randint(0, 100)

            # Fetch a random waifu image from the API
            import requests
            api_photo = None
            try:
                res = requests.get("https://api.waifu.pics/sfw/waifu", timeout=5)
                if res.status_code == 200:
                    api_photo = res.json().get("url")
            except Exception as e:
                LOGGER.warning(f"Error fetching waifu image from waifu.pics: {e}")
                # Fallback to nekos.best
                try:
                    res = requests.get("https://nekos.best/api/v2/waifu", timeout=5)
                    if res.status_code == 200:
                        results = res.json().get("results", [])
                        if results:
                            api_photo = results[0].get("url")
                except Exception as fallback_err:
                    LOGGER.error(f"Error fetching waifu image from nekos.best: {fallback_err}")

            # Cache in Redis for 24 hours
            waifu_data = {
                "waifu_id": waifu_id,
                "waifu_name": waifu_name,
                "bond": bond,
                "photo_file_id": api_photo
            }
            REDIS.setex(waifu_key, 86400, json.dumps(waifu_data))
            photo_file_id = api_photo
        except Exception as e:
            LOGGER.exception(e)
            await message.reply_text("An error occurred while finding your waifu.")
            return

    waifu_mention = f"<a href='tg://user?id={waifu_id}'>{waifu_name}</a>"
    caption = (
        f"✨ <b>{user_mention}'s Today's Waifu</b> ✨\n"
        f"╭──────────────\n"
        f"┊•➢ {waifu_mention}\n"
        f"┊•➢ <b>Bond Percentage:</b> {bond}%\n"
        f"╰───•➢♡"
    )

    try:
        if photo_file_id:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo_file_id,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
        else:
            await message.reply_text(
                caption,
                parse_mode=ParseMode.HTML
            )
    except BadRequest:
        # Fallback if cached photo fails
        await message.reply_text(
            caption,
            parse_mode=ParseMode.HTML
        )


@cutiepii_cmd(command=["myhusbando"])
async def myhusbando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Find today's husbando for a user."""
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.type == "private":
        await message.reply_text("This command can only be used in groups.")
        return

    chat_id = chat.id
    user_id = user.id
    user_mention = f"<a href='tg://user?id={user_id}'>{user.first_name}</a>"

    husbando_key = f"husbando_{chat_id}_{user_id}"
    cached_husbando = REDIS.get(husbando_key)

    if cached_husbando:
        try:
            data = json.loads(cached_husbando)
            husbando_id = data["husbando_id"]
            husbando_name = data["husbando_name"]
            bond = data["bond"]
            photo_file_id = data.get("photo_file_id")
        except Exception:
            cached_husbando = None

    if not cached_husbando:
        try:
            members = []
            async for member in telethn.iter_participants(chat_id):
                if not member.bot and not member.deleted and member.id != user_id:
                    members.append(member)

            if not members:
                await message.reply_text("Couldn't find any eligible husbando for you in this chat!")
                return

            husbando_choice = random.choice(members)
            husbando_id = husbando_choice.id
            husbando_name = husbando_choice.first_name
            bond = random.randint(0, 100)

            # Fetch a random image from the API
            import requests
            api_photo = None
            try:
                res = requests.get("https://api.waifu.pics/sfw/waifu", timeout=5)
                if res.status_code == 200:
                    api_photo = res.json().get("url")
            except Exception as e:
                LOGGER.warning(f"Error fetching husbando image from waifu.pics: {e}")
                # Fallback to nekos.best (using husbando endpoint since nekos.best supports it)
                try:
                    res = requests.get("https://nekos.best/api/v2/husbando", timeout=5)
                    if res.status_code == 200:
                        results = res.json().get("results", [])
                        if results:
                            api_photo = results[0].get("url")
                except Exception as fallback_err:
                    LOGGER.error(f"Error fetching husbando image from nekos.best: {fallback_err}")

            husbando_data = {
                "husbando_id": husbando_id,
                "husbando_name": husbando_name,
                "bond": bond,
                "photo_file_id": api_photo
            }
            REDIS.setex(husbando_key, 86400, json.dumps(husbando_data))
            photo_file_id = api_photo
        except Exception as e:
            LOGGER.exception(e)
            await message.reply_text("An error occurred while finding your husbando.")
            return

    husbando_mention = f"<a href='tg://user?id={husbando_id}'>{husbando_name}</a>"
    caption = (
        f"✨ <b>{user_mention}'s Today's Husbando</b> ✨\n"
        f"╭──────────────\n"
        f"┊•➢ {husbando_mention}\n"
        f"┊•➢ <b>Bond Percentage:</b> {bond}%\n"
        f"╰───•➢♡"
    )

    try:
        if photo_file_id:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo_file_id,
                caption=caption,
                parse_mode=ParseMode.HTML
            )
        else:
            await message.reply_text(
                caption,
                parse_mode=ParseMode.HTML
            )
    except BadRequest:
        await message.reply_text(
            caption,
            parse_mode=ParseMode.HTML
        )


__help__ = True

__mod_name__ = "Waifu"
