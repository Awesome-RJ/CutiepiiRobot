"""
BSD 2-Clause License
Ranking System Module
"""

import html
import random
import pytz
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode
from telegram.helpers import mention_html

from Cutiepii_Robot import dispatcher, LOGGER, REDIS, BOT_NAME
import Cutiepii_Robot.modules.sql.ranking_sql as sql
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot.modules.helper_funcs.admin_status import user_admin_check, AdminPerms
from Cutiepii_Robot.modules.helper_funcs.alternate import send_message

XP_COOLDOWN = 60


@cutiepii_msg(filters.ChatType.GROUPS, group=61)
async def rank_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    
    if not chat or not user or user.is_bot:
        return
        
    chat_id = chat.id
    user_id = user.id
    
    # Anti-Spam: Ignore forwarded messages
    if message.forward_origin:
        return
        
    # Ignore commands
    text = message.text or message.caption or ""
    if text.startswith("/"):
        return
        
    # Check if ranking is enabled in chat
    if not sql.is_ranking_enabled(chat_id):
        return
        
    # Check if user is ignored in chat
    if sql.is_user_ignored(chat_id, user_id):
        return
        
    # Check minimum character settings
    settings = sql.get_ranking_settings(chat_id)
    if len(text) < settings.min_chars:
        return
        
    # Check optional message cooldown in Redis (default settings.cooldown)
    msg_cooldown_key = f"rank:msg_cooldown:{chat_id}:{user_id}"
    is_msg_cooldown = REDIS.get(msg_cooldown_key)
    if is_msg_cooldown:
        return
        
    # Increment message count in Redis
    REDIS.incrby(f"rank:{chat_id}:{user_id}:msg", 1)
    
    # Set message cooldown
    if settings.cooldown > 0:
        REDIS.setex(msg_cooldown_key, settings.cooldown, "1")
        
    # Check cooldown for XP increment (60s)
    cooldown_key = f"rank:cooldown:{chat_id}:{user_id}"
    is_cooldown = REDIS.get(cooldown_key)
    
    if not is_cooldown:
        xp_to_add = random.randint(5, 15)
        REDIS.incrby(f"rank:{chat_id}:{user_id}:xp", xp_to_add)
        REDIS.setex(cooldown_key, XP_COOLDOWN, "1")
        
    # Mark user as dirty (needs database flush)
    REDIS.sadd("rank:dirty_users", f"{chat_id}:{user_id}")


@cutiepii_cmd(command=["rank", "mystats", "profile"], filters=filters.ChatType.GROUPS, can_disable=True)
async def rank_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    
    # Check if a user was replied to, otherwise look up the command sender
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        target_user = update.effective_user
        
    if target_user.is_bot:
        await message.reply_text("Bots do not have ranking statistics.")
        return
        
    chat_id = chat.id
    user_id = target_user.id
    
    # Fetch PostgreSQL stats
    stats = sql.get_user_stats(user_id, chat_id)
    
    # Fetch Redis cached/pending stats
    cached_msg = REDIS.get(f"rank:{chat_id}:{user_id}:msg")
    cached_xp = REDIS.get(f"rank:{chat_id}:{user_id}:xp")
    
    pending_msg = int(cached_msg) if cached_msg else 0
    pending_xp = int(cached_xp) if cached_xp else 0
    
    # Calculate real-time stats
    total_messages = (stats.all_time_messages if stats else 0) + pending_msg
    total_xp = (stats.total_xp if stats else 0) + pending_xp
    daily_messages = (stats.daily_messages if stats else 0) + pending_msg
    
    # Calculate current level
    level = int((total_xp / 100) ** 0.5) + 1
    
    # XP range for the current level
    current_lvl_xp = 100 * (level - 1) ** 2
    next_lvl_xp = 100 * level ** 2
    xp_in_level = total_xp - current_lvl_xp
    xp_needed_for_level = next_lvl_xp - current_lvl_xp
    
    # Progress bar
    bar_length = 15
    if xp_needed_for_level > 0:
        progress = max(0.0, min(1.0, xp_in_level / xp_needed_for_level))
        filled = int(progress * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        percent = int(progress * 100)
    else:
        bar = "█" * bar_length
        percent = 100
        
    # Get user rank
    user_rank = sql.get_chat_rank(chat_id, user_id)
    badges = sql.get_user_badges(user_id, chat_id)
    badges_str = " ".join(badges) if badges else "None"
    
    mention = mention_html(target_user.id, html.escape(target_user.first_name))
    
    reply = (
        f"🏆 <b>RANK DETAILS FOR {mention.upper()}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📈 <b>Level:</b> <code>Level {level}</code>\n"
        f"🏅 <b>Rank:</b> <code>#{user_rank if user_rank > 0 else 'Unranked'}</code>\n"
        f"🔥 <b>Daily Streak:</b> <code>{stats.streak if stats else 1} days</code>\n"
        f"💎 <b>Total XP:</b> <code>{total_xp} XP</code>\n"
        f"💬 <b>All-time Messages:</b> <code>{total_messages} messages</code>\n"
        f"📅 <b>Daily Messages:</b> <code>{daily_messages} messages</code>\n"
        f"🎖️ <b>Badges:</b> {badges_str}\n\n"
        f"📊 <b>Level Progress:</b>\n"
        f"<code>{bar}</code> {percent}%\n"
        f"<i>({xp_in_level}/{xp_needed_for_level} XP to Level {level + 1})</i>"
    )
    
    await message.reply_text(reply, parse_mode=ParseMode.HTML)


@cutiepii_cmd(command=["top", "leaderboard"], filters=filters.ChatType.GROUPS, can_disable=True)
async def top_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    
    chat_id = chat.id
    
    # Leaderboard types: daily, weekly, monthly, all_time, xp (default)
    sort_by = "xp"
    title_str = "TOTAL XP"
    
    if args:
        arg_lower = args[0].lower()
        if arg_lower == "daily":
            sort_by = "daily"
            title_str = "DAILY MESSAGES"
        elif arg_lower == "weekly":
            sort_by = "weekly"
            title_str = "WEEKLY MESSAGES"
        elif arg_lower == "monthly":
            sort_by = "monthly"
            title_str = "MONTHLY MESSAGES"
        elif arg_lower in ["all", "alltime", "all_time", "messages"]:
            sort_by = "all_time"
            title_str = "ALL-TIME MESSAGES"
            
    top_users = sql.get_top_users(chat_id, limit=10, sort_by=sort_by)
    
    if not top_users:
        await message.reply_text("No rankings available for this chat yet. Start chatting to gain XP!")
        return
        
    reply = (
        f"🏆 <b>CHAT LEADERBOARD ({title_str})</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    
    for idx, user_stats in enumerate(top_users, 1):
        try:
            member = await context.bot.get_chat_member(chat_id, user_stats.user_id)
            user_name = html.escape(member.user.first_name)
        except Exception:
            user_name = f"Deleted Account ({user_stats.user_id})"
            
        badges = sql.get_user_badges(user_stats.user_id, chat_id)
        badges_str = f" [{' '.join(badges)}]" if badges else ""
        
        medal = medals.get(idx, f"<code>{idx:02d}.</code>")
        
        if sort_by == "xp":
            val_str = f"Level {user_stats.level} ({user_stats.total_xp} XP, {user_stats.all_time_messages} msgs)"
        elif sort_by == "daily":
            val_str = f"{user_stats.daily_messages} msgs"
        elif sort_by == "weekly":
            val_str = f"{user_stats.weekly_messages} msgs"
        elif sort_by == "monthly":
            val_str = f"{user_stats.monthly_messages} msgs"
        else:
            val_str = f"{user_stats.all_time_messages} msgs"
            
        reply += f"{medal} <b>{user_name}</b>{badges_str} — {val_str}\n"
        
    await message.reply_text(reply, parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="daily", filters=filters.ChatType.GROUPS, can_disable=True)
async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.args = ["daily"]
    await top_cmd(update, context)


@cutiepii_cmd(command="weekly", filters=filters.ChatType.GROUPS, can_disable=True)
async def weekly_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.args = ["weekly"]
    await top_cmd(update, context)


@cutiepii_cmd(command="monthly", filters=filters.ChatType.GROUPS, can_disable=True)
async def monthly_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.args = ["monthly"]
    await top_cmd(update, context)


@cutiepii_cmd(command="alltime", filters=filters.ChatType.GROUPS, can_disable=True)
async def alltime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.args = ["alltime"]
    await top_cmd(update, context)


@cutiepii_cmd(command="streak", filters=filters.ChatType.GROUPS, can_disable=True)
async def streak_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        target_user = update.effective_user
        
    if target_user.is_bot:
        await message.reply_text("Bots do not have streaks.")
        return
        
    stats = sql.get_user_stats(target_user.id, chat.id)
    streak = stats.streak if stats else 1
    mention = mention_html(target_user.id, html.escape(target_user.first_name))
    
    await message.reply_text(
        f"🔥 {mention} has a daily message streak of <b>{streak} days</b>!",
        parse_mode=ParseMode.HTML
    )


@cutiepii_cmd(command="addbadge", filters=filters.ChatType.GROUPS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def add_badge_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    
    if not args:
        await message.reply_text("Usage:\n❍ Reply to a user: `/addbadge [BadgeText]`\n❍ By username: `/addbadge @username [BadgeText]`")
        return
        
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        badge_name = " ".join(args).strip()
    else:
        # Extract target username
        target_username = args[0]
        if not target_username.startswith("@"):
            await message.reply_text("Please provide a valid username (starting with @) or reply to a message.")
            return
        
        # Get user ID from username
        from Cutiepii_Robot.modules.users import get_user_id
        target_id = await get_user_id(target_username)
        if not target_id:
            await message.reply_text("Could not find this user. They must have sent a message in this group before.")
            return
            
        try:
            member = await context.bot.get_chat_member(chat.id, target_id)
            target_user = member.user
        except Exception as e:
            await message.reply_text(f"Failed to fetch user chat details: {e}")
            return
            
        badge_name = " ".join(args[1:]).strip()
        
    if not badge_name:
        await message.reply_text("Please specify the badge text (e.g. 👑 Admin, 🎖️ Contributor).")
        return
        
    success = sql.add_badge(target_user.id, chat.id, badge_name)
    if success:
        mention = mention_html(target_user.id, html.escape(target_user.first_name))
        await message.reply_text(
            f"Successfully granted badge <b>{badge_name}</b> to {mention}! 🎖️",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text(f"This user already has the badge '{badge_name}'.")


@cutiepii_cmd(command="removebadge", filters=filters.ChatType.GROUPS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def remove_badge_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    
    if not args:
        await message.reply_text("Usage:\n❍ Reply to a user: `/removebadge [BadgeText]`\n❍ By username: `/removebadge @username [BadgeText]`")
        return
        
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
        badge_name = " ".join(args).strip()
    else:
        # Extract target username
        target_username = args[0]
        if not target_username.startswith("@"):
            await message.reply_text("Please provide a valid username (starting with @) or reply to a message.")
            return
        
        # Get user ID from username
        from Cutiepii_Robot.modules.users import get_user_id
        target_id = await get_user_id(target_username)
        if not target_id:
            await message.reply_text("Could not find this user. They must have sent a message in this group before.")
            return
            
        try:
            member = await context.bot.get_chat_member(chat.id, target_id)
            target_user = member.user
        except Exception as e:
            await message.reply_text(f"Failed to fetch user chat details: {e}")
            return
            
        badge_name = " ".join(args[1:]).strip()
        
    if not badge_name:
        await message.reply_text("Please specify the badge text to remove.")
        return
        
    success = sql.remove_badge(target_user.id, chat.id, badge_name)
    if success:
        mention = mention_html(target_user.id, html.escape(target_user.first_name))
        await message.reply_text(
            f"Successfully removed badge <b>{badge_name}</b> from {mention}.",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text(f"User does not possess the badge '{badge_name}'.")


@cutiepii_cmd(command="badges", filters=filters.ChatType.GROUPS, can_disable=True)
async def badges_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        target_user = update.effective_user
        
    badges = sql.get_user_badges(target_user.id, chat.id)
    mention = mention_html(target_user.id, html.escape(target_user.first_name))
    
    if not badges:
        await message.reply_text(f"{mention} does not have any badges yet.", parse_mode=ParseMode.HTML)
        return
        
    reply = f"🎖️ <b>Badges earned by {mention}:</b>\n"
    for b in badges:
        reply += f"❍ <code>{b}</code>\n"
        
    await message.reply_text(reply, parse_mode=ParseMode.HTML)


# ==========================================
# Admin Commands for Ranking Configuration
# ==========================================

@cutiepii_cmd(command="resetdaily", filters=filters.ChatType.GROUPS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def reset_daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    sql.reset_chat_daily_stats(chat.id)
    await message.reply_text("✅ Daily ranking statistics have been reset for this chat!")


@cutiepii_cmd(command="settimezone", filters=filters.ChatType.GROUPS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def set_timezone_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    
    if not args:
        current_settings = sql.get_ranking_settings(chat.id)
        await message.reply_text(
            f"Usage: `/settimezone [timezone]`\n"
            f"Current timezone: <code>{html.escape(current_settings.timezone)}</code>\n"
            f"Example: `/settimezone Asia/Kolkata` or `/settimezone UTC`",
            parse_mode=ParseMode.HTML
        )
        return
        
    tz_name = args[0].strip()
    try:
        pytz.timezone(tz_name)
    except pytz.UnknownTimeZoneError:
        await message.reply_text(
            f"❌ Invalid timezone: <code>{html.escape(tz_name)}</code>.\n"
            f"Please use a standard tz name (e.g. Asia/Kolkata, UTC, America/New_York).",
            parse_mode=ParseMode.HTML
        )
        return
        
    success = sql.set_ranking_settings(chat.id, timezone=tz_name)
    if success:
        await message.reply_text(f"✅ Timezone for this chat set to <code>{html.escape(tz_name)}</code>.", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("Failed to update timezone settings.")


@cutiepii_cmd(command="enablexp", filters=filters.ChatType.GROUPS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def enable_xp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    sql.set_ranking_settings(chat.id, is_enabled=True)
    await message.reply_text("✅ Ranking system and XP gain enabled in this chat!")


@cutiepii_cmd(command="disablexp", filters=filters.ChatType.GROUPS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def disable_xp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    sql.set_ranking_settings(chat.id, is_enabled=False)
    await message.reply_text("🔒 Ranking system and XP gain disabled in this chat.")


@cutiepii_cmd(command=["setminmessages", "setminchars"], filters=filters.ChatType.GROUPS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def set_min_chars_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    
    if not args:
        current_settings = sql.get_ranking_settings(chat.id)
        await message.reply_text(
            f"Usage: `/setminmessages [min_characters]`\n"
            f"Current minimum: <code>{current_settings.min_chars}</code> characters.\n"
            f"Messages shorter than this will not count towards ranking.",
            parse_mode=ParseMode.HTML
        )
        return
        
    try:
        min_chars = int(args[0])
        if min_chars < 0:
            raise ValueError
    except ValueError:
        await message.reply_text("Please provide a valid non-negative integer.")
        return
        
    success = sql.set_ranking_settings(chat.id, min_chars=min_chars)
    if success:
        await message.reply_text(f"✅ Minimum character requirement set to <b>{min_chars}</b> characters.")
    else:
        await message.reply_text("Failed to update settings.")


@cutiepii_cmd(command="ignoredusers", filters=filters.ChatType.GROUPS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def ignored_users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args
    
    if not args:
        ignored_ids = sql.get_ignored_users(chat.id)
        if not ignored_ids:
            await message.reply_text("No users are currently ignored in this chat.")
            return
            
        reply = "🚫 <b>Ignored Users for Ranking:</b>\n"
        for uid in ignored_ids:
            try:
                member = await context.bot.get_chat_member(chat.id, uid)
                name = html.escape(member.user.first_name)
                username = f" (@{member.user.username})" if member.user.username else ""
                reply += f"❍ {name}{username} [<code>{uid}</code>]\n"
            except Exception:
                reply += f"❍ User <code>{uid}</code>\n"
        await message.reply_text(reply, parse_mode=ParseMode.HTML)
        return
        
    action = args[0].lower()
    if action not in ["add", "remove"]:
        await message.reply_text("Usage: `/ignoredusers` to list, or `/ignoredusers [add|remove] @username`")
        return
        
    if len(args) < 2 and not message.reply_to_message:
        await message.reply_text("Please specify a user (reply to their message or provide @username).")
        return
        
    if message.reply_to_message:
        target_user = message.reply_to_message.from_user
    else:
        username = args[1]
        if not username.startswith("@"):
            await message.reply_text("Please provide a valid username starting with @.")
            return
        from Cutiepii_Robot.modules.users import get_user_id
        target_id = await get_user_id(username)
        if not target_id:
            await message.reply_text("Could not find this user in the database.")
            return
        try:
            member = await context.bot.get_chat_member(chat.id, target_id)
            target_user = member.user
        except Exception as e:
            await message.reply_text(f"Error fetching user chat info: {e}")
            return
            
    if target_user.is_bot:
        await message.reply_text("Bots are already ignored by default.")
        return
        
    if action == "add":
        success = sql.ignore_user(chat.id, target_user.id)
        if success:
            await message.reply_text(f"✅ User <b>{html.escape(target_user.first_name)}</b> is now ignored from ranking.", parse_mode=ParseMode.HTML)
        else:
            await message.reply_text("This user is already ignored.")
    else:
        success = sql.unignore_user(chat.id, target_user.id)
        if success:
            await message.reply_text(f"✅ User <b>{html.escape(target_user.first_name)}</b> has been unignored from ranking.", parse_mode=ParseMode.HTML)
        else:
            await message.reply_text("This user is not currently ignored.")


# ==========================================
# Background Schedulers & Timezone Flush Logic
# ==========================================

async def flush_rankings_to_db():
    """Periodically flush Redis ranking counters to PostgreSQL"""
    dirty_users = REDIS.smembers("rank:dirty_users")
    if not dirty_users:
        return
        
    try:
        REDIS.rename("rank:dirty_users", "rank:flush_users")
    except Exception:
        return
        
    flush_users = REDIS.smembers("rank:flush_users")
    for user_key in flush_users:
        user_key_str = user_key.decode("utf-8") if isinstance(user_key, bytes) else user_key
        try:
            chat_id_str, user_id_str = user_key_str.split(":")
            chat_id = int(chat_id_str)
            user_id = int(user_id_str)
        except ValueError:
            continue
            
        pipe = REDIS.pipeline()
        pipe.get(f"rank:{chat_id}:{user_id}:msg")
        pipe.get(f"rank:{chat_id}:{user_id}:xp")
        pipe.delete(f"rank:{chat_id}:{user_id}:msg")
        pipe.delete(f"rank:{chat_id}:{user_id}:xp")
        msg_val, xp_val, _, _ = pipe.execute()
        
        messages = int(msg_val) if msg_val else 0
        xp = int(xp_val) if xp_val else 0
        
        if messages > 0 or xp > 0:
            old_level, new_level = sql.add_xp_and_messages(chat_id, user_id, xp, messages)
            
            # Leveled up! Send congratulations message
            if new_level > old_level:
                try:
                    member = await dispatcher.bot.get_chat_member(chat_id, user_id)
                    user_mention = mention_html(member.user.id, html.escape(member.user.first_name))
                    await dispatcher.bot.send_message(
                        chat_id,
                        f"🎉 <b>LEVEL UP!</b> 🎉\n\n"
                        f"Congratulations {user_mention}, you have reached <b>Level {new_level}</b>! 🚀\n"
                        f"Keep active in the chat to climb the leaderboard! 📈",
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e:
                    LOGGER.warning(f"Could not send level-up message in chat {chat_id}: {e}")
                    
    REDIS.delete("rank:flush_users")


async def check_timezone_announcements():
    """Run periodically to check if any chat timezone has crossed midnight and needs announcement + reset."""
    try:
        from Cutiepii_Robot.modules.sql import SESSION
        all_chats = SESSION.query(sql.RankingStats.chat_id).distinct().all()
        SESSION.close()
    except Exception as e:
        LOGGER.error(f"[RANKING]: Error fetching chat list: {e}")
        return
        
    for (chat_id,) in all_chats:
        try:
            settings = sql.get_ranking_settings(chat_id)
            tz_name = settings.timezone if settings else "Asia/Kolkata"
            
            try:
                tz = pytz.timezone(tz_name)
            except Exception:
                tz = pytz.timezone("Asia/Kolkata")
                
            now_local = datetime.now(tz)
            today_str = now_local.date().isoformat()
            
            last_announced = REDIS.get(f"rank:announced_date:{chat_id}")
            last_announced_str = last_announced.decode("utf-8") if last_announced else None
            
            # If not announced yet today, and it is midnight or later
            if last_announced_str != today_str:
                is_midnight = now_local.hour == 0
                is_missed_day = last_announced_str is not None and last_announced_str != today_str
                
                if is_midnight or is_missed_day:
                    REDIS.set(f"rank:announced_date:{chat_id}", today_str)
                    
                    top_users = sql.get_top_users(chat_id, limit=3, sort_by="daily")
                    if top_users:
                        reply = "🏆 <b>Daily Ranking Finished!</b>\n\n"
                        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
                        
                        count = 0
                        for idx, user_stats in enumerate(top_users, 1):
                            if user_stats.daily_messages == 0:
                                continue
                            try:
                                member = await dispatcher.bot.get_chat_member(chat_id, user_stats.user_id)
                                username = f"@{member.user.username}" if member.user.username else html.escape(member.user.first_name)
                            except Exception:
                                username = f"User ({user_stats.user_id})"
                                
                            reply += f"{medals[idx]} {username} — {user_stats.daily_messages} messages\n"
                            count += 1
                            
                        if count > 0:
                            reply += "\nCongratulations! 🎉"
                            try:
                                await dispatcher.bot.send_message(
                                    chat_id,
                                    reply,
                                    parse_mode=ParseMode.HTML
                                )
                            except Exception as err:
                                LOGGER.warning(f"Could not send daily ranking announcement in {chat_id}: {err}")
                                
                    sql.reset_chat_daily_stats(chat_id)
                    LOGGER.info(f"[RANKING]: Daily reset and announcement triggered for chat {chat_id} (Timezone: {tz_name})")
        except Exception as e:
            LOGGER.error(f"[RANKING]: Error checking daily announcement for chat {chat_id}: {e}")


async def check_timezone_jobs():
    """Background task to check timezones for daily/weekly/monthly runs"""
    # 1. Daily Reset / Announcement
    await check_timezone_announcements()
    
    # 2. Weekly & Monthly Reset Checks
    try:
        from Cutiepii_Robot.modules.sql import SESSION
        all_chats = SESSION.query(sql.RankingStats.chat_id).distinct().all()
        SESSION.close()
    except Exception:
        return
        
    for (chat_id,) in all_chats:
        try:
            settings = sql.get_ranking_settings(chat_id)
            tz_name = settings.timezone if settings else "Asia/Kolkata"
            try:
                tz = pytz.timezone(tz_name)
            except Exception:
                tz = pytz.timezone("Asia/Kolkata")
                
            now_local = datetime.now(tz)
            today_str = now_local.date().isoformat()
            
            # Weekly check (Sunday)
            if now_local.weekday() == 6:  # Sunday
                last_weekly = REDIS.get(f"rank:weekly_reset:{chat_id}")
                last_weekly_str = last_weekly.decode("utf-8") if last_weekly else None
                if last_weekly_str != today_str:
                    sql.reset_chat_weekly_stats(chat_id)
                    REDIS.set(f"rank:weekly_reset:{chat_id}", today_str)
                    LOGGER.info(f"[RANKING]: Weekly reset triggered for chat {chat_id}")
                    
            # Monthly check (1st of month)
            if now_local.day == 1:
                last_monthly = REDIS.get(f"rank:monthly_reset:{chat_id}")
                last_monthly_str = last_monthly.decode("utf-8") if last_monthly else None
                if last_monthly_str != today_str:
                    sql.reset_chat_monthly_stats(chat_id)
                    REDIS.set(f"rank:monthly_reset:{chat_id}", today_str)
                    LOGGER.info(f"[RANKING]: Monthly reset triggered for chat {chat_id}")
        except Exception as e:
            LOGGER.error(f"[RANKING]: Error checking weekly/monthly reset for {chat_id}: {e}")


# Async schedule triggers
scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
scheduler.add_job(flush_rankings_to_db, trigger="interval", seconds=30)
scheduler.add_job(check_timezone_jobs, trigger="interval", minutes=10)


def start_ranking_scheduler():
    """Start the ranking flush scheduler."""
    try:
        if not scheduler.running:
            scheduler.start()
            LOGGER.info("[RANKING]: ✅ Cache flush scheduler started successfully")
    except Exception as e:
        LOGGER.error(f"[RANKING]: ❌ Failed to start cache flush scheduler: {e}")


__help__ = True
__mod_name__ = "Ranking"
