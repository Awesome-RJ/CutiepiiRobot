"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.
"""

import html
import json
import random
import re
import secrets
import string
import requests
from io import BytesIO
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Cutiepii_Robot import dispatcher, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
from Cutiepii_Robot.utils.carbon import make_carbon

# ========================================
# Command: /json [URL]
# ========================================

@cutiepii_cmd(command="json", group=480)
async def get_json_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("Please provide an API URL. Usage: `/json [URL]`", parse_mode=ParseMode.MARKDOWN)
        return

    url = args[0].strip()
    await message.reply_chat_action("typing")

    try:
        r = requests.get(url, timeout=10)
        try:
            parsed = r.json()
            formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
        except Exception:
            formatted = r.text

        if len(formatted) > 3800:
            formatted = formatted[:3800] + "\n... (truncated)"

        await message.reply_text(
            f"📥 <b>REST API Response:</b>\n\n"
            f"<pre><code class=\"language-json\">{html.escape(formatted)}</code></pre>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await message.reply_text(f"❌ <b>Request Failed:</b> {html.escape(str(e))}", parse_mode=ParseMode.HTML)


# ========================================
# Command: /webss or .webss [URL] [FULL_SIZE?]
# ========================================

@cutiepii_cmd(command="webss", group=481)
async def web_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("Please provide a website URL. Usage: `/webss [URL]`", parse_mode=ParseMode.MARKDOWN)
        return

    url = args[0].strip()
    # Normalize URL scheme
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    full_size = False
    if len(args) > 1:
        val = args[1].lower()
        if val in ["y", "yes", "true", "1"]:
            full_size = True

    await message.reply_chat_action("upload_photo")

    try:
        # mini.s-shot.ru handles full size via height=0
        height = "0" if full_size else "960"
        screenshot_url = f"https://mini.s-shot.ru/1280x{height}/png/?{url}"
        
        r = requests.get(screenshot_url, timeout=15)
        if r.status_code != 200:
            await message.reply_text("Failed to capture website screenshot.")
            return

        bio = BytesIO(r.content)
        bio.name = "webss.png"

        await message.reply_photo(
            photo=bio,
            caption=f"🖥️ <b>Screenshot of:</b> <a href='{url}'>{html.escape(url)}</a>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await message.reply_text(f"An error occurred while taking screenshot: {e}")


# ========================================
# Command: /carbon [code]
# ========================================

@cutiepii_cmd(command="carbon", group=482)
async def generate_carbon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    
    code = " ".join(context.args)
    if not code and message.reply_to_message:
        code = message.reply_to_message.text or message.reply_to_message.caption

    if not code:
        await message.reply_text("Please provide code or reply to a message containing code.")
        return

    await message.reply_chat_action("upload_photo")

    try:
        image = await make_carbon(code)
        await message.reply_photo(photo=image, caption="Generated via carbon.now.sh")
    except Exception as e:
        await message.reply_text(f"Failed to generate carbon image: {e}")


# ========================================
# Command: /commit
# ========================================

@cutiepii_cmd(command="commit", group=483)
async def funny_commit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    await message.reply_chat_action("typing")

    try:
        r = requests.get("https://whatthecommit.com/index.txt", timeout=10)
        commit_msg = r.text.strip() if r.status_code == 200 else "Initial commit"
        await message.reply_text(f"💻 <code>{html.escape(commit_msg)}</code>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"Failed to fetch commit message: {e}")


# ========================================
# Command: /runs
# ========================================

@cutiepii_cmd(command="runs", group=484)
async def runs_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    runs_responses = [
        "Running tests... all systems optimal! 🚀",
        "Runs completed! Error rate: 0.00% ✅",
        "Tests finished successfully! Cutiepii is healthy! 🟢",
        "System check: 100% operational! 📡",
        "Running diagnostics... 100% green! 🧪"
    ]
    await update.effective_message.reply_text(random.choice(runs_responses))


# ========================================
# Command: /random [Length]
# ========================================

@cutiepii_cmd(command="random", group=486)
async def generate_random_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    length = 16
    if args:
        try:
            length = int(args[0])
            if length < 8 or length > 128:
                await message.reply_text("Password length must be between 8 and 128 characters.")
                return
        except ValueError:
            await message.reply_text("Invalid length specified. Please provide a valid integer.")
            return

    # Complex secure character set
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
    password = "".join(secrets.choice(chars) for _ in range(length))

    reply_text = (
        f"🔐 <b>Complex Password Generated</b>\n"
        f"📏 <b>Length:</b> {length}\n"
        f"🔑 <b>Password:</b> <code>{html.escape(password)}</code>\n\n"
        f"<i>(Tap to copy the password above)</i>"
    )

    try:
        if update.effective_chat.type in ["group", "supergroup"]:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=reply_text,
                parse_mode=ParseMode.HTML
            )
            await message.reply_text("🔑 I have sent the generated complex password to your private chat.")
        else:
            await message.reply_text(reply_text, parse_mode=ParseMode.HTML)
    except Exception:
        await message.reply_text("🔑 Could not send password in PM. Please start me in PM first.")


# ========================================
# Command: /cheat [Language] [Query]
# ========================================

@cutiepii_cmd(command="cheat", group=487)
async def cheat_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if len(args) < 2:
        await message.reply_text("Usage: `/cheat [Language] [Query]`\nExample: `/cheat python reverse list`", parse_mode=ParseMode.MARKDOWN)
        return

    lang = args[0].strip().lower()
    query = "+".join(args[1:])

    await message.reply_chat_action("typing")

    url = f"https://cheat.sh/{lang}/{query}"
    try:
        # Pass User-Agent curl to get plain-text terminal output
        headers = {"User-Agent": "curl"}
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code != 200:
            await message.reply_text("Could not find cheatsheet for the given language and query.")
            return

        text = r.text
        # Remove ANSI escape sequences
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_text = ansi_escape.sub('', text)

        # Truncate if too long
        if len(clean_text) > 3800:
            clean_text = clean_text[:3800] + "\n... (truncated)"

        await message.reply_text(f"<pre><code>{html.escape(clean_text)}</code></pre>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")


# ========================================
# Module Help and Stats
# ========================================

__help__ = True

__mod_name__ = "Dev Helpers"
