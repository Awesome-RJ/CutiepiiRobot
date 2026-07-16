"""
Guest Management & Statistics Module for Cutiepii Robot
Tracks temporary guest members, guest stats, and lists guest bots in a chat.
"""

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Cutiepii_Robot import dispatcher
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user
from Cutiepii_Robot.modules.sql import users_sql as sql


@cutiepii_cmd(command="guestinfo")
async def guest_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get information about a guest/user member in the chat."""
    message = update.effective_message
    args = context.args
    chat = update.effective_chat

    if chat.type == "private":
        await message.reply_text("This command can only be used in groups.")
        return

    user_id = await extract_user(message, args)
    if not user_id:
        await message.reply_text("I cannot extract user from this message.")
        return

    try:
        member = await chat.get_member(user_id)
        user = member.user
        
        status_map = {
            "creator": "👑 Chat Owner",
            "administrator": "🛡️ Administrator",
            "member": "👤 Regular Member",
            "restricted": "🔕 Restricted User (Guest)",
            "left": "🚪 Left Chat",
            "kicked": "🚫 Banned/Kicked",
        }
        
        status_str = status_map.get(member.status, "Unknown")
        is_bot = "Yes 🤖" if user.is_bot else "No 👤"
        
        msg = (
            f"👤 <b>Guest / Member Info</b>\n\n"
            f" ├ <b>Name:</b> {user.first_name}\n"
            f" ├ <b>ID:</b> <code>{user.id}</code>\n"
            f" ├ <b>Is Bot:</b> {is_bot}\n"
            f" └ <b>Status:</b> {status_str}\n"
        )
        await message.reply_text(msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ Error retrieving member info: {e}")


@cutiepii_cmd(command="gueststats")
async def guest_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics of members and guest users in the chat."""
    message = update.effective_message
    chat = update.effective_chat

    if chat.type == "private":
        await message.reply_text("This command can only be used in groups.")
        return

    try:
        member_count = await chat.get_member_count()
        db_members = sql.get_chat_members(chat.id)
        db_members_count = len(db_members) if db_members else 0
        
        msg = (
            f"📊 <b>Chat Guest & Member Statistics</b>\n\n"
            f" ├ 👥 <b>Telegram Member Count:</b> {member_count}\n"
            f" ├ 💾 <b>Database Registered Users:</b> {db_members_count}\n"
            f" └ 📉 <b>Guest/Unregistered Count:</b> {max(0, member_count - db_members_count)}\n"
        )
        await message.reply_text(msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"❌ Error fetching guest statistics: {e}")


__help__ = True

__mod_name__ = "Guestbot"
__command_list__ = ["guestinfo", "gueststats"]
