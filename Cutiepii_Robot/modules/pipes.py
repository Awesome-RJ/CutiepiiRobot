"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.
"""

import html
from telethon import events, TelegramClient
from telethon.sessions import StringSession
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Cutiepii_Robot import (
    dispatcher,
    telethn,
    LOGGER,
    OWNER_ID,
    DEV_USERS,
    API_ID,
    API_HASH,
    STRING_SESSION,
)
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd

# In-memory pipes (Temporary: destroyed on restart)
BOT_PIPES = {}
USERBOT_PIPES = {}

userbot = None


async def start_userbot_if_needed():
    """Initializes and starts the userbot client if it isn't running yet."""
    global userbot
    if userbot is not None:
        return

    if not STRING_SESSION:
        raise ValueError("STRING_SESSION is not configured in Config.")

    LOGGER.info("[PIPES]: Starting Userbot client...")
    userbot = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

    # Register the userbot message handler
    @userbot.on(events.NewMessage)
    async def userbot_handler(event):
        chat_id = event.chat_id
        # Check integer matches
        if chat_id in USERBOT_PIPES:
            target = USERBOT_PIPES[chat_id]
            try:
                await userbot.forward_messages(target, event.message)
            except Exception as e:
                LOGGER.error(f"[PIPES]: Userbot forward error: {e}")
        # Check string matches (fallback)
        elif str(chat_id) in USERBOT_PIPES:
            target = USERBOT_PIPES[str(chat_id)]
            try:
                await userbot.forward_messages(int(target), event.message)
            except Exception as e:
                LOGGER.error(f"[PIPES]: Userbot forward error: {e}")

    await userbot.start()
    LOGGER.info("[PIPES]: ✅ Userbot client started successfully!")


# Register the main bot client handler on startup
@telethn.on(events.NewMessage)
async def telethn_handler(event):
    chat_id = event.chat_id
    # Check integer matches
    if chat_id in BOT_PIPES:
        target = BOT_PIPES[chat_id]
        try:
            await telethn.forward_messages(target, event.message)
        except Exception as e:
            LOGGER.error(f"[PIPES]: Bot forward error: {e}")
    # Check string matches (fallback)
    elif str(chat_id) in BOT_PIPES:
        target = BOT_PIPES[str(chat_id)]
        try:
            await telethn.forward_messages(int(target), event.message)
        except Exception as e:
            LOGGER.error(f"[PIPES]: Bot forward error: {e}")


# ========================================
# Command Handlers
# ========================================

@cutiepii_cmd(command="activate_pipe", group=450)
async def activate_pipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args

    # Developer/Owner authentication only
    if user.id != OWNER_ID and user.id not in DEV_USERS:
        await message.reply_text("This module is only for developers!")
        return

    if len(args) < 3:
        await message.reply_text("Usage: `/activate_pipe [FROM_CHAT_ID] [TO_CHAT_ID] [BOT|USERBOT]`", parse_mode=ParseMode.MARKDOWN)
        return

    from_chat = args[0].strip()
    to_chat = args[1].strip()
    client_type = args[2].strip().upper()

    if client_type not in ["BOT", "USERBOT"]:
        await message.reply_text("Client type must be either 'BOT' or 'USERBOT'.")
        return

    try:
        from_id = int(from_chat)
    except ValueError:
        from_id = from_chat

    try:
        to_id = int(to_chat)
    except ValueError:
        to_id = to_chat

    if client_type == "BOT":
        BOT_PIPES[from_id] = to_id
        await message.reply_text(
            f"✅ <b>Pipe Activated</b>\n\n"
            f"❍ <b>From:</b> <code>{from_chat}</code>\n"
            f"❍ <b>To:</b> <code>{to_chat}</code>\n"
            f"❍ <b>Client:</b> BOT",
            parse_mode=ParseMode.HTML
        )
    else:
        if not STRING_SESSION:
            await message.reply_text("❌ STRING_SESSION is not set in Config! Cannot use USERBOT client.")
            return

        try:
            await start_userbot_if_needed()
            USERBOT_PIPES[from_id] = to_id
            await message.reply_text(
                f"✅ <b>Pipe Activated</b>\n\n"
                f"❍ <b>From:</b> <code>{from_chat}</code>\n"
                f"❍ <b>To:</b> <code>{to_chat}</code>\n"
                f"❍ <b>Client:</b> USERBOT",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            await message.reply_text(f"❌ Failed to start userbot client: {e}")


@cutiepii_cmd(command="deactivate_pipe", group=451)
async def deactivate_pipe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args

    # Developer/Owner authentication only
    if user.id != OWNER_ID and user.id not in DEV_USERS:
        await message.reply_text("This module is only for developers!")
        return

    if not args:
        await message.reply_text("Usage: `/deactivate_pipe [FROM_CHAT_ID]`", parse_mode=ParseMode.MARKDOWN)
        return

    from_chat = args[0].strip()
    removed = False
    
    try:
        from_chat_int = int(from_chat)
    except ValueError:
        from_chat_int = None

    if from_chat_int in BOT_PIPES:
        del BOT_PIPES[from_chat_int]
        removed = True
    elif from_chat in BOT_PIPES:
        del BOT_PIPES[from_chat]
        removed = True

    if from_chat_int in USERBOT_PIPES:
        del USERBOT_PIPES[from_chat_int]
        removed = True
    elif from_chat in USERBOT_PIPES:
        del USERBOT_PIPES[from_chat]
        removed = True

    if removed:
        await message.reply_text(f"✅ Pipe from <code>{from_chat}</code> deactivated successfully.", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(f"No active pipe found from <code>{from_chat}</code>.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="show_pipes", group=452)
async def show_pipes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    # Developer/Owner authentication only
    if user.id != OWNER_ID and user.id not in DEV_USERS:
        await message.reply_text("This module is only for developers!")
        return

    if not BOT_PIPES and not USERBOT_PIPES:
        await message.reply_text("No active pipes found.")
        return

    reply = "📋 <b>Active Message Pipes:</b>\n\n"
    if BOT_PIPES:
        reply += "🤖 <b>Bot Pipes:</b>\n"
        for f, t in BOT_PIPES.items():
            reply += f"❍ <code>{f}</code> ➔ <code>{t}</code>\n"
        reply += "\n"
    if USERBOT_PIPES:
        reply += "👤 <b>Userbot Pipes:</b>\n"
        for f, t in USERBOT_PIPES.items():
            reply += f"❍ <code>{f}</code> ➔ <code>{t}</code>\n"
    
    await message.reply_text(reply.strip(), parse_mode=ParseMode.HTML)


# Module Help string
__help__ = True

__mod_name__ = "Pipes"
