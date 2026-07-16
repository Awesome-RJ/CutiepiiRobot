import html
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.error import BadRequest

from Cutiepii_Robot import dispatcher, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot.modules.helper_funcs.admin_status import user_admin_check, AdminPerms, user_is_admin, bot_admin_check
from Cutiepii_Robot.modules.sql import imposter_sql as sql

@cutiepii_cmd(command="imposter")
async def imposter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.type == "private":
        await message.reply_text("This command can only be used in groups.")
        return

    # Check if user is admin
    if not await user_is_admin(update, user.id):
        await message.reply_text("Only administrators can configure Imposter.")
        return

    if sql.is_imposter_enabled(chat.id):
        button = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔴 Disable Imposter", callback_data=f"disable_imposter:{chat.id}")],
                [InlineKeyboardButton("🗑️ Close", callback_data="imposter_close")]
            ]
        )
        await message.reply_text("<b>📢 Imposter is enabled in this chat.</b>", reply_markup=button, parse_mode=ParseMode.HTML)
    else:
        button = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🟢 Enable Imposter", callback_data=f"enable_imposter:{chat.id}")],
                [InlineKeyboardButton("🗑️ Close", callback_data="imposter_close")]
            ]
        )
        await message.reply_text("<b>📢 Imposter is disabled in this chat.</b>", reply_markup=button, parse_mode=ParseMode.HTML)

@cutiepii_callback(pattern=r"^(enable_imposter|disable_imposter):")
async def toggle_imposters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    chat = update.effective_chat

    # Check if user is admin
    if not await user_is_admin(update, user.id):
        await query.answer("You must be an admin to toggle Imposter settings.", show_alert=True)
        return

    action, chat_id = query.data.split(":")
    chat_id = int(chat_id)

    if action == "enable_imposter":
        sql.enable_imposter(chat_id)
        await query.message.edit_text("<b>🟢 Imposter has been enabled for this chat.</b>", parse_mode=ParseMode.HTML)
    elif action == "disable_imposter":
        sql.disable_imposter(chat_id)
        await query.message.edit_text("<b>🔴 Imposter has been disabled for this chat.</b>", parse_mode=ParseMode.HTML)
        
    await query.answer()

@cutiepii_callback(pattern=r"^imposter_close$")
async def close_imposter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    if not await user_is_admin(update, user.id):
        await query.answer("You must be an admin to close this.", show_alert=True)
        return
    await query.message.delete()
    await query.answer()

@cutiepii_msg(filters.TEXT & ~filters.UpdateType.EDITED_MESSAGE & filters.ChatType.GROUPS, group=9)
async def imposter_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message

    if not chat or not message:
        return

    if not sql.is_imposter_enabled(chat.id):
        return

    user = message.from_user
    if not user or user.is_bot:
        return

    changes = sql.check_user(user.id, user.first_name, user.last_name, user.username)
    if changes:
        change_details = "\n".join(
            f"❍ <b>{field.replace('_', ' ').capitalize()}:</b>\n"
            f"   - <b>Previous:</b> {html.escape(old) if old else 'None'}\n"
            f"   - <b>Updated:</b> {html.escape(new) if new else 'None'}"
            for field, old, new in changes
        )

        user_mention = f"<a href='tg://user?id={user.id}'>{html.escape(user.first_name)}</a>"
        announcement = (
            f"🔔 <b>User Profile Update Detected</b>\n\n"
            f"👤 <b>User:</b> {user_mention} ({user.id})\n\n"
            f"{change_details}"
        )

        try:
            await message.reply_text(announcement, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        except BadRequest as e:
            LOGGER.error(f"Failed to send imposter alert: {e}")



__mod_name__ = "Imposter"

__help__ = True

__handlers__ = [
]
