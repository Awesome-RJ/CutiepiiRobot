import os
import html
import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.error import BadRequest

from telethon import TelegramClient
from telethon.sessions import StringSession
import telethon.errors as tl_errors

try:
    from pyrogram import Client as PyroClient
    import pyrogram.errors as pyro_errors
except ImportError:
    PyroClient = None

from Cutiepii_Robot import dispatcher, API_ID, API_HASH, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, cutiepii_msg

# Dictionary to hold states: user_id -> state dict
SGEN_STATES = {}

ASK_QUES = "<b>» Please choose the library for which you want to generate a string session:</b>\n\n<i>Note: Your credentials are processed in-memory and are never saved.</i>"

CHOICE_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Pyrogram User", callback_data="sgen_pyro"),
        InlineKeyboardButton("Telethon User", callback_data="sgen_tele")
    ],
    [
        InlineKeyboardButton("Pyrogram Bot", callback_data="sgen_pyro_bot"),
        InlineKeyboardButton("Telethon Bot", callback_data="sgen_tele_bot")
    ]
])


async def handle_send_code(update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict, phone: str):
    user_id = update.effective_user.id
    message = update.effective_message
    
    status_msg = await message.reply_text("`Connecting to Telegram...`", parse_mode=ParseMode.MARKDOWN)
    
    try:
        if state["type"] == "tele":
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            await client.connect()
            code_req = await client.send_code_request(phone)
            state["client"] = client
            state["phone_code_hash"] = code_req.phone_code_hash
        else:
            # Pyrogram User
            if not PyroClient:
                await status_msg.edit_text("Pyrogram is not available on this bot.")
                SGEN_STATES.pop(user_id, None)
                return
            client = PyroClient(":memory:", api_id=API_ID, api_hash=API_HASH, in_memory=True)
            await client.connect()
            code_req = await client.send_code(phone)
            state["client"] = client
            state["phone_code_hash"] = code_req.phone_code_hash
        
        state["step"] = "waiting_otp"
        await status_msg.edit_text(
            "✅ Code request sent successfully!\n\n"
            "Please enter the **OTP code** you received from Telegram (e.g. 12345 or 1-2-3-4-5):\n\n"
            "💡 <i>Tip: Send /cancel to cancel at any time.</i>",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        LOGGER.exception("Error in handle_send_code")
        await status_msg.edit_text(f"❌ Failed to send code request:\n<code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)
        if "client" in state:
            try:
                await state["client"].disconnect()
            except Exception:
                pass
        SGEN_STATES.pop(user_id, None)


async def handle_verify_otp(update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict, otp: str):
    user_id = update.effective_user.id
    message = update.effective_message
    client = state["client"]
    phone = state["phone"]
    phone_code_hash = state["phone_code_hash"]
    
    status_msg = await message.reply_text("`Verifying OTP...`", parse_mode=ParseMode.MARKDOWN)
    otp = otp.replace("-", "").replace(" ", "")
    
    try:
        session_str = None
        if state["type"] == "tele":
            try:
                await client.sign_in(phone, otp, phone_code_hash=phone_code_hash)
                session_str = client.session.save()
            except tl_errors.SessionPasswordNeededError:
                state["step"] = "waiting_2fa"
                await status_msg.edit_text("🔒 Two-Factor Authentication (2FA) is enabled on your account.\n\nPlease enter your **2FA Password**:")
                return
        else:
            # Pyrogram User
            try:
                await client.sign_in(phone, phone_code_hash, otp)
                session_str = await client.export_session_string()
            except pyro_errors.SessionPasswordNeeded:
                state["step"] = "waiting_2fa"
                await status_msg.edit_text("🔒 Two-Factor Authentication (2FA) is enabled on your account.\n\nPlease enter your **2FA Password**:")
                return

        if session_str:
            await status_msg.edit_text(
                "✅ <b>Session string generated successfully!</b>\n\n"
                f"<code>{session_str}</code>\n\n"
                "⚠️ <b>WARNING:</b> Keep this string session private! Never share it with anyone.",
                parse_mode=ParseMode.HTML
            )
        else:
            await status_msg.edit_text("❌ Failed to generate session string.")
        
        try:
            await client.disconnect()
        except Exception:
            pass
        SGEN_STATES.pop(user_id, None)
        
    except Exception as e:
        LOGGER.exception("Error in handle_verify_otp")
        await status_msg.edit_text(f"❌ Verification failed:\n<code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)
        try:
            await client.disconnect()
        except Exception:
            pass
        SGEN_STATES.pop(user_id, None)


async def handle_verify_2fa(update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict, password: str):
    user_id = update.effective_user.id
    message = update.effective_message
    client = state["client"]
    
    status_msg = await message.reply_text("`Verifying 2FA Password...`", parse_mode=ParseMode.MARKDOWN)
    
    try:
        session_str = None
        if state["type"] == "tele":
            await client.sign_in(password=password)
            session_str = client.session.save()
        else:
            # Pyrogram User
            await client.check_password(password)
            session_str = await client.export_session_string()
            
        if session_str:
            await status_msg.edit_text(
                "✅ <b>Session string generated successfully!</b>\n\n"
                f"<code>{session_str}</code>\n\n"
                "⚠️ <b>WARNING:</b> Keep this string session private! Never share it with anyone.",
                parse_mode=ParseMode.HTML
            )
        else:
            await status_msg.edit_text("❌ Failed to generate session string.")
            
        try:
            await client.disconnect()
        except Exception:
            pass
        SGEN_STATES.pop(user_id, None)
        
    except Exception as e:
        LOGGER.exception("Error in handle_verify_2fa")
        await status_msg.edit_text(f"❌ 2FA Verification failed:\n<code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)
        try:
            await client.disconnect()
        except Exception:
            pass
        SGEN_STATES.pop(user_id, None)


async def handle_bot_login(update: Update, context: ContextTypes.DEFAULT_TYPE, state: dict, bot_token: str):
    user_id = update.effective_user.id
    message = update.effective_message
    
    status_msg = await message.reply_text("`Logging in as Bot...`", parse_mode=ParseMode.MARKDOWN)
    
    try:
        session_str = None
        if state["type"] == "tele_bot":
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            await client.connect()
            await client.login(bot_token=bot_token)
            session_str = client.session.save()
            await client.disconnect()
        else:
            # Pyrogram Bot
            if not PyroClient:
                await status_msg.edit_text("Pyrogram is not available on this bot.")
                SGEN_STATES.pop(user_id, None)
                return
            client = PyroClient(":memory:", api_id=API_ID, api_hash=API_HASH, bot_token=bot_token, in_memory=True)
            await client.connect()
            session_str = await client.export_session_string()
            await client.disconnect()
            
        if session_str:
            await status_msg.edit_text(
                "✅ <b>Bot Session string generated successfully!</b>\n\n"
                f"<code>{session_str}</code>\n\n"
                "⚠️ <b>WARNING:</b> Keep this string session private! Never share it with anyone.",
                parse_mode=ParseMode.HTML
            )
        else:
            await status_msg.edit_text("❌ Failed to generate session string.")
            
        SGEN_STATES.pop(user_id, None)
        
    except Exception as e:
        LOGGER.exception("Error in handle_bot_login")
        await status_msg.edit_text(f"❌ Bot login failed:\n<code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)
        SGEN_STATES.pop(user_id, None)


@cutiepii_msg(pattern=filters.ChatType.PRIVATE & filters.TEXT, group=12)
async def sgen_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user_id = update.effective_user.id
    
    if user_id not in SGEN_STATES:
        return
    
    state = SGEN_STATES[user_id]
    text = message.text.strip() if message.text else ""
    
    if text == "/cancel":
        if "client" in state:
            try:
                await state["client"].disconnect()
            except Exception:
                pass
        SGEN_STATES.pop(user_id, None)
        await message.reply_text("❌ Session generation cancelled.")
        return

    if text.startswith("/"):
        if "client" in state:
            try:
                await state["client"].disconnect()
            except Exception:
                pass
        SGEN_STATES.pop(user_id, None)
        return

    step = state["step"]
    session_type = state["type"]
    
    if step == "waiting_phone":
        state["phone"] = text
        if "bot" in session_type:
            await handle_bot_login(update, context, state, text)
        else:
            await handle_send_code(update, context, state, text)
            
    elif step == "waiting_otp":
        await handle_verify_otp(update, context, state, text)
        
    elif step == "waiting_2fa":
        await handle_verify_2fa(update, context, state, text)


@cutiepii_cmd(command="sgen")
async def sgen_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    
    if message.chat.type != "private":
        await message.reply_text("❌ This command can only be used in private chats (PM).")
        return
        
    await message.reply_text(ASK_QUES, reply_markup=CHOICE_KEYBOARD, parse_mode=ParseMode.HTML)


@cutiepii_callback(pattern=r"^sgen_")
async def sgen_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    choice = query.data
    
    if choice not in ("sgen_pyro", "sgen_tele", "sgen_pyro_bot", "sgen_tele_bot"):
        return
        
    session_type = choice.replace("sgen_", "")
    
    SGEN_STATES[user_id] = {
        "type": session_type,
        "step": "waiting_phone"
    }
    
    if "bot" in session_type:
        await query.edit_message_text(
            "🤖 <b>Bot Session Generation Selected.</b>\n\n"
            "Please enter your **Bot Token** (obtained from @BotFather):\n\n"
            "💡 <i>Tip: Send /cancel to cancel at any time.</i>",
            parse_mode=ParseMode.HTML
        )
    else:
        await query.edit_message_text(
            "👤 <b>User Session Generation Selected.</b>\n\n"
            "Please enter your **Phone Number** (with country code, e.g. +1234567890):\n\n"
            "💡 <i>Tip: Send /cancel to cancel at any time.</i>",
            parse_mode=ParseMode.HTML
        )


# Register Handlers

__mod_name__ = "Session Gen"

__help__ = True
