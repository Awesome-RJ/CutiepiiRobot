"""
BSD 2-Clause License
Karma Module for Cutiepii Robot
SQL-based with enhanced decorators
"""

import re
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

from Cutiepii_Robot import dispatcher, BOT_USERNAME
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd, cutiepii_msg, rate_limit
from Cutiepii_Robot.modules.sql import karma_sql

# Karma reaction patterns (no (?i) - use re.IGNORECASE when compiling to avoid Python 3.12 "global flags" error)
UPVOTE_PATTERN = r"^(\+|\+\+|\+1|thx|tnx|ty|tq|thank\s?you|thanx|thanks|pro|cool|good|agree|makasih|👍|baby|love|🖤|❣️|💝|💖|💕|❤|💘|\+\+\s?.+)$"
DOWNVOTE_PATTERN = r"^(-|--|-1|👎|💔|noob|weak|fuck\s?off|nub|not\scool|disagree|worst|bad|--\s?.+)$"
UPVOTE_REGEX = re.compile(UPVOTE_PATTERN, re.IGNORECASE)
DOWNVOTE_REGEX = re.compile(DOWNVOTE_PATTERN, re.IGNORECASE)


@rate_limit(max_calls=10, time_window=60)
@cutiepii_msg(pattern=filters.TEXT & filters.ChatType.GROUPS & filters.REPLY & filters.Regex(UPVOTE_REGEX), group=3)
async def upvote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle upvote reactions"""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not karma_sql.is_karma_enabled(chat.id):
        return

    if not message.reply_to_message:
        return

    if not message.reply_to_message.from_user:
        return

    # Check pattern
    if not UPVOTE_REGEX.match(message.text):
        return

    # Can't upvote yourself
    if message.reply_to_message.from_user.id == user.id:
        return

    # Bots don't have karma
    if message.reply_to_message.from_user.is_bot:
        return

    replied_user = message.reply_to_message.from_user
    new_karma = karma_sql.update_karma(chat.id, replied_user.id, 1)

    await message.reply_text(
        f"Karma for {replied_user.mention_html()} increased.\n"
        f"Current karma: <b>{new_karma}</b>",
        parse_mode=ParseMode.HTML
    )


@rate_limit(max_calls=10, time_window=60)
@cutiepii_msg(pattern=filters.TEXT & filters.ChatType.GROUPS & filters.REPLY & filters.Regex(DOWNVOTE_REGEX), group=4)
async def downvote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle downvote reactions"""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not karma_sql.is_karma_enabled(chat.id):
        return

    if not message.reply_to_message:
        return

    if not message.reply_to_message.from_user:
        return

    # Check pattern
    if not DOWNVOTE_REGEX.match(message.text):
        return

    # Can't downvote yourself
    if message.reply_to_message.from_user.id == user.id:
        return

    # Bots don't have karma
    if message.reply_to_message.from_user.is_bot:
        return

    replied_user = message.reply_to_message.from_user
    new_karma = karma_sql.update_karma(chat.id, replied_user.id, -1)

    await message.reply_text(
        f"Karma for {replied_user.mention_html()} decreased.\n"
        f"Current karma: <b>{new_karma}</b>",
        parse_mode=ParseMode.HTML
    )


@cutiepii_cmd(command="karma", rate_limit_calls=5, rate_limit_window=60)
async def karma_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check karma for a user or show top 10 leaderboard"""
    message = update.effective_message
    chat = update.effective_chat

    if not karma_sql.is_karma_enabled(chat.id):
        await message.reply_text("<b>System Disabled</b>\nThe karma system is disabled in this chat.", parse_mode=ParseMode.HTML)
        return

    # If no reply, show leaderboard
    if not message.reply_to_message:
        await karma_stats(update, context)
        return

    # Check replied user's karma
    target_user = message.reply_to_message.from_user
    if not target_user:
        await message.reply_text("<b>Error</b>\nCould not find replied user.", parse_mode=ParseMode.HTML)
        return

    karma_value = karma_sql.get_karma(chat.id, target_user.id)
    await message.reply_text(
        f"Karma for {target_user.mention_html()}:\n"
        f"<b>{karma_value}</b> points",
        parse_mode=ParseMode.HTML
    )


@cutiepii_cmd(command="karma_toggle", group=50)
async def karma_toggle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable or disable karma system"""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args

    # Check if user is admin
    chat_member = await chat.get_member(user.id)
    if chat_member.status not in ["creator", "administrator"]:
        await message.reply_text("<b>Action Denied</b>\nOnly administrators can configure the karma system.", parse_mode=ParseMode.HTML)
        return

    if not args:
        status = "enabled" if karma_sql.is_karma_enabled(chat.id) else "disabled"
        await message.reply_text(f"Karma system is currently <b>{status}</b>.", parse_mode=ParseMode.HTML)
        return

    action = args[0].lower().strip()
    if action in ["enable", "on", "yes"]:
        karma_sql.enable_karma(chat.id)
        await message.reply_text("<b>System Enabled</b>\nKarma system has been enabled.", parse_mode=ParseMode.HTML)
    elif action in ["disable", "off", "no"]:
        karma_sql.disable_karma(chat.id)
        await message.reply_text("<b>System Disabled</b>\nKarma system has been disabled.", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("<b>Invalid Command Usage</b>\nUsage: <code>/karma_toggle [ENABLE|DISABLE]</code>", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command=["karmastat", "topkarma"], rate_limit_calls=3, rate_limit_window=60)
async def karma_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show top karma users"""
    message = update.effective_message
    chat = update.effective_chat

    if not karma_sql.is_karma_enabled(chat.id):
        await message.reply_text("<b>System Disabled</b>\nThe karma system is disabled in this chat.", parse_mode=ParseMode.HTML)
        return

    # Get top users (limit 10)
    top_users = karma_sql.get_top_karma(chat.id, limit=10)

    text = "<b>Karma Leaderboard</b>\n\n"
    if top_users:
        text += "<b>Top Users:</b>\n"
        for idx, karma_obj in enumerate(top_users, 1):
            try:
                user = await context.bot.get_chat(karma_obj.user_id)
                text += f"{idx}. {user.first_name}: <b>{karma_obj.karma}</b>\n"
            except:
                text += f"{idx}. User {karma_obj.user_id}: <b>{karma_obj.karma}</b>\n"
    else:
        text += "No positive karma recorded yet.\n"

    await message.reply_text(text, parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="karmaon", group=50)
async def karma_on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    chat_member = await chat.get_member(user.id)
    if chat_member.status not in ["creator", "administrator"]:
        await message.reply_text("<b>Action Denied</b>\nOnly administrators can enable/disable the karma system.", parse_mode=ParseMode.HTML)
        return

    karma_sql.enable_karma(chat.id)
    await message.reply_text("<b>System Enabled</b>\nKarma system has been enabled.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="karmaoff", group=50)
async def karma_off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    chat_member = await chat.get_member(user.id)
    if chat_member.status not in ["creator", "administrator"]:
        await message.reply_text("<b>Action Denied</b>\nOnly administrators can enable/disable the karma system.", parse_mode=ParseMode.HTML)
        return

    karma_sql.disable_karma(chat.id)
    await message.reply_text("<b>System Disabled</b>\nKarma system has been disabled.", parse_mode=ParseMode.HTML)


# Register handlers



__mod_name__ = "Karma"
__help__ = True
