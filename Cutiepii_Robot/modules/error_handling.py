"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.
"""

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
import traceback
import html
import random
import re
import io
from Cutiepii_Robot.modules.helper_funcs.misc import upload_text
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import ParseMode
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility
from Cutiepii_Robot import TOKEN, dispatcher, DEV_USERS, OWNER_ID, LOGGER

class ErrorsDict(dict):
    "A custom dict to store errors and their count"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __contains__(self, error):
        if not hasattr(error, "identifier") or not error.identifier:
            error.identifier = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5))
        for e in self:
            if type(e) is type(error) and e.args == error.args:
                self[e] += 1
                return True
        self[error] = 0
        return False


errors = ErrorsDict()


def redact_sensitive(text: str) -> str:
    if not text:
        return text
    # List of sensitive items to redact
    sensitive_keys = [TOKEN]
    
    # Try to import other sensitive config values if available
    try:
        from Cutiepii_Robot import DATABASE_URL
        if DATABASE_URL:
            sensitive_keys.append(DATABASE_URL)
    except ImportError:
        pass

    try:
        from Cutiepii_Robot import BACKUP_PASS
        if BACKUP_PASS:
            sensitive_keys.append(BACKUP_PASS)
    except ImportError:
        pass

    # Clean text
    for key in sensitive_keys:
        if key and len(str(key)) > 5:
            text = text.replace(str(key), "[REDACTED_SENSITIVE_DATA]")
            
    # Redact database password if DB URL is formatted as postgres://user:password@host:port/db
    text = re.sub(r'postgres://[^:]+:([^@]+)@', 'postgres://***:[REDACTED_PASSWORD]@', text)
    text = re.sub(r'postgresql://[^:]+:([^@]+)@', 'postgresql://***:[REDACTED_PASSWORD]@', text)
    
    return text


async def error_callback(update: Update, context: CallbackContext):
    if not context.error:
        return

    from telegram.error import NetworkError, TimedOut, RetryAfter
    if isinstance(context.error, (NetworkError, TimedOut, RetryAfter)):
        # Just log network issues as warnings instead of spamming error notifications
        LOGGER.warning(f"[Network/Telegram API issue]: {context.error}")
        return

    # Redact token and db URLs from exception representation
    raw_error_str = str(context.error)
    e = html.escape(redact_sensitive(raw_error_str))

    # Format traceback
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = redact_sensitive("".join(tb_list))

    # Store identifier on the error object
    identifier = getattr(context.error, "identifier", None)
    if not identifier:
        identifier = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5))
        context.error.identifier = identifier

    # Check if we should notify user / chat
    if update and update.effective_chat and update.effective_chat.type != "channel":
        try:
            # Check if this error is rate-limited
            if context.error not in errors:
                await context.bot.send_message(
                    update.effective_chat.id,
                    f"⚠️ <b>An unexpected error occurred!</b>\n"
                    f"<b>Error:</b> <code>{e}</code>\n"
                    f"<i>Incident ID: #{identifier}. The issue has been logged and reported to my developers.</i>",
                    parse_mode=ParseMode.HTML,
                )
        except Exception as exc:
            LOGGER.debug(f"Could not send error message to user chat: {exc}")

    # Deduplicate errors to avoid spamming the developer chat
    if context.error in errors:
        return

    # Build developer traceback message
    user_info = "None"
    chat_info = "None"
    callback_info = "None"
    message_info = "None"
    update_str = "No update available"

    if update:
        try:
            import json
            update_str = json.dumps(update.to_dict(), indent=2, ensure_ascii=False)
            update_str = redact_sensitive(update_str)
        except Exception:
            pass

        if update.effective_user:
            user_info = f"{update.effective_user.first_name} (ID: {update.effective_user.id})"
        if update.effective_chat:
            chat_info = f"{update.effective_chat.title or 'Private'} (ID: {update.effective_chat.id})"
        if update.callback_query:
            callback_info = update.callback_query.data
        if update.effective_message and update.effective_message.text:
            message_info = update.effective_message.text

    full_log_message = (
        f"Incident ID: #{identifier}\n"
        f"User: {user_info}\n"
        f"Chat: {chat_info}\n"
        f"Callback data: {callback_info}\n"
        f"Message: {message_info}\n\n"
        f"Update Payload:\n{update_str}\n\n"
        f"Full Traceback:\n{tb}"
    )

    paste_url = None
    try:
        paste_url = upload_text(full_log_message)
    except Exception as upload_err:
        LOGGER.error(f"Failed to upload error log to paste service: {upload_err}")

    # Fallback to file sending if PrivateBin is down
    if not paste_url:
        error_file = io.BytesIO(full_log_message.encode("utf-8"))
        error_file.name = f"error_{identifier}.txt"
        try:
            await context.bot.send_document(
                chat_id=OWNER_ID,
                document=error_file,
                caption=f"⚠️ <b>Exception Captured (PrivateBin Offline):</b>\n"
                        f"🏷️ <b>Incident ID:</b> #{identifier}\n"
                        f"❌ <b>Error:</b> <code>{e}</code>",
                parse_mode=ParseMode.HTML,
            )
        except Exception as send_doc_err:
            LOGGER.error(f"Failed to send error document to OWNER_ID: {send_doc_err}")
        return

    # Send error notification to developer with PrivateBin link and expandable traceback preview
    try:
        buttons = [
            [InlineKeyboardButton("📋 View PrivateBin Paste", url=paste_url)],
            [InlineKeyboardButton("❌ Close", callback_data="close_msg")]
        ]
        # Keep the formatted traceback snippet safe to send via HTML
        tb_snippet = html.escape(tb[:3000])
        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"⚠️ <b>Exception Captured:</b>\n"
                 f"🏷️ <b>Incident ID:</b> #{identifier}\n"
                 f"❌ <b>Error:</b> <code>{html.escape(str(e))}</code>\n\n"
                 f"🔍 <b>Traceback:</b>\n"
                 f"<blockquote expandable><pre><code class=\"language-python\">{tb_snippet}</code></pre></blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML,
        )
    except Exception as send_msg_err:
        LOGGER.error(f"Failed to send error message to OWNER_ID: {send_msg_err}")


@cutiepii_cmd(command="errors")
async def list_errors(update: Update, context: CallbackContext):
    if update.effective_user.id not in DEV_USERS:
        return
    e = dict(sorted(errors.items(), key=lambda item: item[1], reverse=True))
    msg = "<b>Errors List:</b>\n"
    for x, value in e.items():
        msg += f"- <code>{type(x).__name__}:</code> <b>{value} occurrences</b> #{x.identifier}\n"

    msg += f"{len(errors)} unique errors have occurred since startup."
    if len(msg) > 4096:
        errors_file = io.BytesIO(msg.encode("utf-8"))
        errors_file.name = "errors_msg.txt"
        await context.bot.send_document(
            update.effective_chat.id,
            errors_file,
            caption='Too many errors have occurred..',
            parse_mode=ParseMode.HTML,
        )
        return
    await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)

dispatcher.add_error_handler(error_callback)
