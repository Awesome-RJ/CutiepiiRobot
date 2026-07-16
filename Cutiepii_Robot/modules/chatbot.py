"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.
"""

import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters

from Cutiepii_Robot import dispatcher, LOGGER
from Cutiepii_Robot.modules.sql import chatbot_sql as sql
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot.modules.helper_funcs.chat_status import user_admin


@user_admin
@cutiepii_cmd(command="chatbot", can_disable=True)
async def chatbot_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle chatbot settings in group or PM."""
    message = update.effective_message
    chat = update.effective_chat

    chat_id = chat.id

    if sql.is_cutiepii(chat_id):
        buttons = [
            [InlineKeyboardButton("🔴 Disable ChatBot", callback_data=f"disable_chatbot:{chat_id}")],
            [InlineKeyboardButton("🗑️ Close", callback_data="chatbot_close")]
        ]
        await message.reply_text(
            "<b>📢 ChatBot is enabled in this chat.</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )
    else:
        buttons = [
            [InlineKeyboardButton("🟢 Enable ChatBot", callback_data=f"enable_chatbot:{chat_id}")],
            [InlineKeyboardButton("🗑️ Close", callback_data="chatbot_close")]
        ]
        await message.reply_text(
            "<b>📢 ChatBot is disabled in this chat.</b>",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML
        )


@cutiepii_callback(pattern=r"^(enable_chatbot|disable_chatbot|chatbot_close):?")
async def toggle_chatbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback handler to enable/disable chatbot."""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "chatbot_close":
        await query.message.delete()
        return

    action, chat_id = data.split(":")
    chat_id = int(chat_id)

    # Check user permissions if group
    user = query.from_user
    if query.message.chat.type != "private":
        try:
            member = await context.bot.get_chat_member(chat_id, user.id)
            if member.status not in ["creator", "administrator"]:
                await query.answer("You must be an administrator to change chatbot settings!", show_alert=True)
                return
        except Exception:
            pass

    if action == "enable_chatbot":
        sql.set_cutiepii(chat_id)
        await query.message.edit_text("<b>🟢 ChatBot has been enabled for this chat.</b>", parse_mode=ParseMode.HTML)
    elif action == "disable_chatbot":
        sql.rem_cutiepii(chat_id)
        await query.message.edit_text("<b>🔴 ChatBot has been disabled for this chat.</b>", parse_mode=ParseMode.HTML)


from datetime import datetime, timedelta

GEMINI_COOLDOWN_UNTIL = None


@cutiepii_msg(pattern=filters.TEXT & (~filters.COMMAND), group=9)
async def handle_chatbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Message handler to query AI chatbot."""
    global GEMINI_COOLDOWN_UNTIL
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not message or not chat or not user or user.is_bot:
        return

    # Chatbot is disabled by default in PM and groups, must be explicitly enabled
    if not sql.is_cutiepii(chat.id):
        return

    is_group = chat.type != "private"
    if is_group:
        # Check if the message is a reply to the bot
        replied = message.reply_to_message
        if not replied or replied.from_user.id != context.bot.id:
            # Also reply if the bot is explicitly mentioned
            bot_username = f"@{context.bot.username}"
            if not message.text or bot_username not in message.text:
                return

    query_text = message.text
    if is_group and query_text:
        # Strip bot username if present
        bot_username = f"@{context.bot.username}"
        query_text = query_text.replace(bot_username, "").strip()

    if not query_text:
        return

    # Trigger typing state safely
    try:
        await context.bot.send_chat_action(chat.id, action="typing")
    except Exception as e:
        LOGGER.warning(f"Failed to send typing chat action: {e}")

    import os
    gemini_key = os.environ.get("GEMINI_API_KEY")
    bot_response = None

    # Check if Gemini is on cooldown
    gemini_on_cooldown = False
    if GEMINI_COOLDOWN_UNTIL and datetime.now() < GEMINI_COOLDOWN_UNTIL:
        gemini_on_cooldown = True
        LOGGER.info("Gemini API is on 1-hour cooldown. Bypassing directly to OpenRouter.")

    # 1. Try Gemini API first (if key is configured and not on cooldown)
    if gemini_key and not gemini_on_cooldown:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
                async with session.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": query_text}]}],
                        "systemInstruction": {
                            "parts": [{
                                "text": "You are a flirty, funny AI chatbot named Cutiepii. Respond in casual, conversational Hinglish (Hindi written in English letters). Keep replies brief, funny, and engaging."
                            }]
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=8)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        bot_response = data['candidates'][0]['content']['parts'][0]['text']
                    elif resp.status == 429:
                        GEMINI_COOLDOWN_UNTIL = datetime.now() + timedelta(hours=1)
                        LOGGER.warning("Gemini API rate limited (429). Activating 1-hour cooldown. Falling back to OpenRouter.")
                    else:
                        LOGGER.warning(f"Gemini API returned status code {resp.status}. Falling back to OpenRouter.")
        except Exception as e:
            LOGGER.warning(f"Gemini API error: {type(e).__name__} - {str(e)[:100]}. Falling back to OpenRouter.")

    # 2. Fallback to OpenRouter API (if Gemini failed or was not configured)
    if not bot_response:
        openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
        last_status = None
        for model in ["openrouter/free", "meta-llama/llama-3.3-70b-instruct:free", "google/gemma-4-31b-it:free"]:
            try:
                async with aiohttp.ClientSession() as session:
                    url = "https://openrouter.ai/api/v1/chat/completions"
                    headers = {
                        "Authorization": f"Bearer {openrouter_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/Awesome-RJ/Cutiepii_Robot",
                        "X-Title": "Cutiepii Robot"
                    }
                    payload = {
                        "model": model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a flirty, funny AI chatbot named Cutiepii. Respond in casual, conversational Hinglish (Hindi written in English letters). Keep replies brief, funny, and engaging."
                            },
                            {
                                "role": "user",
                                "content": query_text
                            }
                        ]
                    }
                    async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        last_status = resp.status
                        if resp.status == 200:
                            data = await resp.json(content_type=None)
                            bot_response = data['choices'][0]['message']['content']
                            break
                        elif resp.status == 429:
                            LOGGER.warning(f"OpenRouter model {model} rate limited (429). Trying next fallback.")
                        else:
                            LOGGER.error(f"OpenRouter API returned status code {resp.status} for model {model}")
            except Exception as e:
                LOGGER.error(f"Error fetching OpenRouter response for model {model}: {type(e).__name__} - {str(e)[:100]}")

        if not bot_response and last_status == 402:
            bot_response = "Arey! OpenRouter API wallet mein balance khatam ho gaya hai (Insufficient Credits - Error 402). 🥺 Please reload karo!"

    if not bot_response:
        if is_group:
            await message.reply_text("❌ Chatbot is facing temporary API issues. Please try again in a moment.")
        else:
            await message.reply_text("Sorry, I'm having trouble responding right now.")
        return

    await message.reply_text(bot_response)


# Handler registration


__mod_name__ = "Chatbot"
__help__ = True
