"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.
"""

import html
import json
import uuid
import base64
import string
import secrets
import hashlib
import requests
import random

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd

# ========================================
# Command: /search [query]
# ========================================

@cutiepii_cmd(command="search", group=411)
async def duck_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    
    # Get search query
    if not context.args:
        await message.reply_text("<b>Usage:</b>\n<code>/search &lt;query&gt;</code>", parse_mode=ParseMode.HTML)
        return

    query = " ".join(context.args)
    await message.reply_chat_action("typing")

    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
        r = requests.get(url, timeout=10)
        
        if r.status_code != 200:
            await message.reply_text("Search engine is currently offline. Please try again later.")
            return

        data = r.json()
        abstract = data.get("AbstractText", "")
        source_url = data.get("AbstractURL", "")
        heading = data.get("Heading", "")

        if abstract:
            reply_text = f"<b>Search Result: {html.escape(heading)}</b>\n\n"
            reply_text += f"{html.escape(abstract)}\n\n"
            if source_url:
                reply_text += f"<a href='{source_url}'>Read more on DuckDuckGo</a>"
            await message.reply_text(reply_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return

        # Fallback to related topics if abstract is empty
        related = data.get("RelatedTopics", [])
        if related and isinstance(related, list):
            reply_text = f"<b>Search Results for: {html.escape(query)}</b>\n\n"
            count = 0
            for topic in related:
                text = topic.get("Text", "")
                topic_url = topic.get("FirstURL", "")
                if text and topic_url and count < 3:
                    reply_text += f"• {html.escape(text)}\n  <a href='{topic_url}'>Source Link</a>\n\n"
                    count += 1
            if count > 0:
                await message.reply_text(reply_text.strip(), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
                return

        await message.reply_text(f"No instant answers found for: <b>{html.escape(query)}</b>", parse_mode=ParseMode.HTML)

    except Exception as e:
        await message.reply_text(f"An error occurred while executing search: {e}")


# ========================================
# Command: /genpass [length] or /passgen [length]
# ========================================

@cutiepii_cmd(command=["genpass", "passgen"], group=412)
async def generate_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    # Check command name to determine default length
    cmd = message.text.split()[0][1:].split("@")[0].lower()
    default_length = 12 if cmd == "passgen" else 16

    length = default_length
    if args:
        try:
            length = int(args[0])
            if length < 8 or length > 64:
                await message.reply_text("Password length must be between 8 and 64 characters.")
                return
        except ValueError:
            await message.reply_text("Invalid length specified. Please provide a valid integer.")
            return

    # Use secure character set
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
    password = "".join(secrets.choice(chars) for _ in range(length))

    reply_text = (
        f"<b>Secure Password Generated</b>\n"
        f"<b>Length:</b> {length}\n"
        f"<b>Password:</b> <code>{html.escape(password)}</code>\n\n"
        f"<i>(Tap to copy the password above)</i>"
    )
    
    try:
        # Send password in PM if triggered in group to maintain security, or reply directly if triggered in PM
        if update.effective_chat.type in ["group", "supergroup"]:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=reply_text,
                parse_mode=ParseMode.HTML
            )
            await message.reply_text("I have sent the generated secure password to your private chat.")
        else:
            await message.reply_text(reply_text, parse_mode=ParseMode.HTML)
    except Exception:
        # Fallback if user hasn't started the bot in PM
        await message.reply_text(
            "Could not send password in PM. Please start me in PM first or use the command inside my private chat."
        )


# ========================================
# Command: /hash [text]
# ========================================

@cutiepii_cmd(command="hash", group=413)
async def calculate_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    
    if not context.args:
        await message.reply_text("<b>Usage:</b>\n<code>/hash &lt;text&gt;</code>", parse_mode=ParseMode.HTML)
        return

    text = " ".join(context.args)
    text_bytes = text.encode("utf-8")

    md5_hash = hashlib.md5(text_bytes).hexdigest()
    sha256_hash = hashlib.sha256(text_bytes).hexdigest()
    sha512_hash = hashlib.sha512(text_bytes).hexdigest()

    reply_text = (
        "<b>Computed Hashes</b>\n\n"
        f"<b>Original Text:</b> <i>{html.escape(text)}</i>\n\n"
        f"<b>MD5:</b>\n<code>{md5_hash}</code>\n\n"
        f"<b>SHA-256:</b>\n<code>{sha256_hash}</code>\n\n"
        f"<b>SHA-512:</b>\n<code>{sha512_hash}</code>"
    )
    await message.reply_text(reply_text, parse_mode=ParseMode.HTML)


# ========================================
# Command: /b64en [text]
# ========================================

@cutiepii_cmd(command="b64en", group=414)
async def base64_encode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not context.args:
        await message.reply_text("<b>Usage:</b>\n<code>/b64en &lt;text&gt;</code>", parse_mode=ParseMode.HTML)
        return

    text = " ".join(context.args)
    encoded = base64.b64encode(text.encode("utf-8")).decode("utf-8")

    reply_text = (
        "<b>Base64 Encoded Result</b>\n\n"
        f"<code>{encoded}</code>"
    )
    await message.reply_text(reply_text, parse_mode=ParseMode.HTML)


# ========================================
# Command: /b64de [base64_string]
# ========================================

@cutiepii_cmd(command="b64de", group=415)
async def base64_decode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not context.args:
        await message.reply_text("<b>Usage:</b>\n<code>/b64de &lt;base64_string&gt;</code>", parse_mode=ParseMode.HTML)
        return

    encoded_str = context.args[0].strip()

    try:
        decoded = base64.b64decode(encoded_str.encode("utf-8")).decode("utf-8")
        reply_text = (
            "<b>Base64 Decoded Result</b>\n\n"
            f"<code>{html.escape(decoded)}</code>"
        )
        await message.reply_text(reply_text, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"Failed to decode Base64 string. Please verify the format. Error: {html.escape(str(e))}", parse_mode=ParseMode.HTML)


# ========================================
# Command: /uuid
# ========================================

@cutiepii_cmd(command="uuid", group=416)
async def generate_uuid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    new_uuid = str(uuid.uuid4())
    reply_text = (
        "<b>Generated UUIDv4</b>\n\n"
        f"<code>{new_uuid}</code>"
    )
    await message.reply_text(reply_text, parse_mode=ParseMode.HTML)


# ========================================
# Command: /jsonformat [json]
# ========================================

@cutiepii_cmd(command="jsonformat", group=417)
async def format_json(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not context.args:
        await message.reply_text("<b>Usage:</b>\n<code>/jsonformat &lt;json&gt;</code>", parse_mode=ParseMode.HTML)
        return

    json_str = " ".join(context.args).strip()

    try:
        parsed_json = json.loads(json_str)
        formatted = json.dumps(parsed_json, indent=2, ensure_ascii=False)
        
        if len(formatted) > 3800:
            formatted = formatted[:3800] + "\n... (truncated due to Telegram message length limit)"

        reply_text = (
            "<b>Formatted JSON</b>\n\n"
            f"<pre><code class=\"language-json\">{html.escape(formatted)}</code></pre>"
        )
        await message.reply_text(reply_text, parse_mode=ParseMode.HTML)
    except json.JSONDecodeError as e:
        await message.reply_text(f"<b>Invalid JSON Syntax</b>\n\n<code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"An error occurred while formatting JSON: {html.escape(str(e))}", parse_mode=ParseMode.HTML)


# ========================================
# Command: /decide [question]
# ========================================

@cutiepii_cmd(command="decide", group=420)
async def decide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("<b>Usage:</b>\n<code>/decide &lt;question&gt;</code>", parse_mode=ParseMode.HTML)
        return

    question = " ".join(args)
    answers = [
        "It is certain.",
        "It is decidedly so.",
        "Without a doubt.",
        "Yes, definitely.",
        "You may rely on it.",
        "As I see it, yes.",
        "Most likely.",
        "Outlook good.",
        "Yes.",
        "Signs point to yes.",
        "Reply hazy, try again.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don't count on it.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Very doubtful."
    ]
    ans = random.choice(answers)

    reply_text = (
        "<b>Magic 8 Ball Says</b>\n\n"
        f"<b>Question:</b> <i>{html.escape(question)}</i>\n"
        f"<b>Answer:</b> {ans}"
    )
    await message.reply_text(reply_text, parse_mode=ParseMode.HTML)


import ast
import operator
from io import BytesIO

# Supported math operators for safe /calc
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: lambda x: x
}

def safe_math_eval(node):
    if isinstance(node, ast.Constant):  # python >= 3.8 (including 3.14+)
        return node.value
    elif hasattr(ast, "Num") and isinstance(node, ast.Num):  # python < 3.8
        return node.n
    elif isinstance(node, ast.BinOp):
        return SAFE_OPERATORS[type(node.op)](safe_math_eval(node.left), safe_math_eval(node.right))
    elif isinstance(node, ast.UnaryOp):
        return SAFE_OPERATORS[type(node.op)](safe_math_eval(node.operand))
    raise TypeError(f"Unsupported operation: {node}")


# ========================================
# Command: /calc [expression]
# ========================================

@cutiepii_cmd(command="calc", group=414)
async def calc_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("<b>Usage:</b>\n<code>/calc &lt;expression&gt;</code>", parse_mode=ParseMode.HTML)
        return

    expr = "".join(args).replace(" ", "")
    await message.reply_chat_action("typing")

    try:
        parsed = ast.parse(expr, mode='eval')
        result = safe_math_eval(parsed.body)
        await message.reply_text(
            "<b>Calculation Result</b>\n\n"
            f"<b>Expression:</b> <code>{html.escape(expr)}</code>\n"
            f"<b>Result:</b> <code>{result}</code>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await message.reply_text(f"<b>Calculation Failed:</b> {html.escape(str(e))}", parse_mode=ParseMode.HTML)


# ========================================
# Command: /iplookup [ip address]
# ========================================

@cutiepii_cmd(command="iplookup", group=415)
async def ip_lookup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("<b>Usage:</b>\n<code>/iplookup &lt;IP&gt;</code>", parse_mode=ParseMode.HTML)
        return

    ip = args[0].strip()
    await message.reply_chat_action("typing")

    url = f"http://ip-api.com/json/{ip}"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            await message.reply_text("Failed to connect to IP API portal.")
            return

        data = r.json()
        if data.get("status") == "fail":
            await message.reply_text(f"<b>Lookup Failed:</b> {html.escape(data.get('message', 'Invalid IP address'))}", parse_mode=ParseMode.HTML)
            return

        reply = (
            "<b>IP Address Details</b>\n\n"
            f"- <b>IP:</b> <code>{html.escape(data.get('query'))}</code>\n"
            f"- <b>Country:</b> {html.escape(data.get('country', 'N/A'))} ({html.escape(data.get('countryCode', 'N/A'))})\n"
            f"- <b>Region:</b> {html.escape(data.get('regionName', 'N/A'))}\n"
            f"- <b>City:</b> {html.escape(data.get('city', 'N/A'))} (ZIP: {html.escape(data.get('zip', 'N/A'))})\n"
            f"- <b>Timezone:</b> {html.escape(data.get('timezone', 'N/A'))}\n"
            f"- <b>ISP:</b> {html.escape(data.get('isp', 'N/A'))}\n"
            f"- <b>ASN:</b> {html.escape(data.get('as', 'N/A'))}"
        )
        await message.reply_text(reply, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"An error occurred: {html.escape(str(e))}", parse_mode=ParseMode.HTML)


# ========================================
# Command: /qr [text or url]
# ========================================

@cutiepii_cmd(command="qr", group=416)
async def generate_qr_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("<b>Usage:</b>\n<code>/qr &lt;text/link&gt;</code>", parse_mode=ParseMode.HTML)
        return

    text = " ".join(args).strip()
    await message.reply_chat_action("upload_photo")

    try:
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={requests.utils.quote(text)}"
        r = requests.get(qr_url, timeout=15)
        
        if r.status_code != 200:
            await message.reply_text("Failed to generate QR code.")
            return

        bio = BytesIO(r.content)
        bio.name = "qr.png"

        await message.reply_photo(
            photo=bio,
            caption="<b>Generated QR Code</b>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await message.reply_text(f"An error occurred while generating QR code: {html.escape(str(e))}", parse_mode=ParseMode.HTML)


# ========================================
# Command: /shortener [url]
# ========================================

@cutiepii_cmd(command="shortener", group=417)
async def url_shortener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("<b>Usage:</b>\n<code>/shortener &lt;URL&gt;</code>", parse_mode=ParseMode.HTML)
        return

    url = args[0].strip()
    await message.reply_chat_action("typing")

    try:
        r = requests.get(f"http://tinyurl.com/api-create.php?url={requests.utils.quote(url)}", timeout=10)
        if r.status_code != 200:
            await message.reply_text("Failed to connect to TinyURL API.")
            return

        short_url = r.text.strip()
        await message.reply_text(
            "<b>Link Shortener Result</b>\n\n"
            f"- <b>Original:</b> {html.escape(url)}\n"
            f"- <b>Short URL:</b> <code>{short_url}</code>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await message.reply_text(f"An error occurred while shortening URL: {html.escape(str(e))}", parse_mode=ParseMode.HTML)


# ========================================
# Module Help and Stats
# ========================================

__help__ = True

__mod_name__ = "Dev Utils"
