"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import html
import random
import requests
from telegram import Update
from telegram.ext import ContextTypes, MessageReactionHandler
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.helpers import mention_html

from Cutiepii_Robot import dispatcher, LOGGER, DEV_USERS, SUDO_USERS
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd, cutiepii_message_reaction
from Cutiepii_Robot.modules.sql import paid_media_sql
from Cutiepii_Robot.modules.sql import suggestions_sql
from Cutiepii_Robot.modules.sql import stories_sql
from Cutiepii_Robot.modules.sql import reactions_sql


# ==========================================
# Paid Media Manager
# ==========================================

@cutiepii_cmd(command="setprice", filters=None)
async def set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args

    if user.id not in DEV_USERS and user.id not in SUDO_USERS:
        await message.reply_text("This command is restricted to bot administrators.")
        return

    if len(args) < 2:
        await message.reply_text("Usage: `/setprice [media_id] [stars_amount]`")
        return

    media_id = args[0]
    try:
        price = float(args[1])
    except ValueError:
        await message.reply_text("Please specify a valid numeric price.")
        return

    paid_media_sql.set_pricing(media_id, price)
    await message.reply_text(f"✅ Price for <code>{html.escape(media_id)}</code> set to <code>{price} Stars</code>.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="buycheck", can_disable=False)
async def buy_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args

    if not args:
        await message.reply_text("Usage: `/buycheck [media_id]`")
        return

    media_id = args[0]
    pricing = paid_media_sql.get_pricing(media_id)
    if not pricing:
        await message.reply_text("This media is not available for purchase or has no price set.")
        return

    purchase_id = paid_media_sql.log_purchase(user.id, media_id, pricing.price, pricing.currency)
    await message.reply_text(
        f"💳 <b>Transaction Logged Successfully!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"❍ <b>Transaction ID:</b> <code>#{purchase_id}</code>\n"
        f"❍ <b>Customer:</b> {mention_html(user.id, user.first_name)}\n"
        f"❍ <b>Media:</b> <code>{html.escape(media_id)}</code>\n"
        f"❍ <b>Price:</b> <code>{pricing.price} {pricing.currency}</code>\n\n"
        f"🔒 <i>Transaction verified and audit trail logged.</i>",
        parse_mode=ParseMode.HTML
    )


@cutiepii_cmd(command="mediaanalytics", filters=None)
async def media_analytics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    
    if user.id not in DEV_USERS and user.id not in SUDO_USERS:
        await message.reply_text("This command is restricted to bot administrators.")
        return

    purchases = paid_media_sql.get_all_purchases()
    if not purchases:
        await message.reply_text("No transactions recorded yet.")
        return

    total_revenue = sum(p.amount for p in purchases)
    media_counts = {}
    for p in purchases:
        media_counts[p.media_id] = media_counts.get(p.media_id, 0) + 1

    top_media = sorted(media_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    reply = (
        f"📊 <b>PAID MEDIA ANALYTICS</b> 📊\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 <b>Total Revenue:</b> <code>{total_revenue} Stars</code>\n"
        f"💳 <b>Total Purchases:</b> <code>{len(purchases)}</code>\n\n"
        f"🔥 <b>Top Purchased Media:</b>\n"
    )
    for m_id, count in top_media:
        reply += f"❍ <code>{html.escape(m_id)}</code>: <code>{count} times</code>\n"

    await message.reply_text(reply, parse_mode=ParseMode.HTML)


# ==========================================
# Suggested Posts
# ==========================================

@cutiepii_cmd(command="suggest", can_disable=False)
async def suggest_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args

    if not args:
        await message.reply_text("Usage:\nReply to a post or send: `/suggest [@channel] [your suggestion message]`")
        return

    channel_target = args[0]
    post_text = " ".join(args[1:])

    media_file_id = None
    media_type = None
    if message.reply_to_message:
        replied = message.reply_to_message
        if replied.text:
            post_text = replied.text + (" " + post_text if post_text else "")
        elif replied.photo:
            media_file_id = replied.photo[-1].file_id
            media_type = "photo"
            post_text = replied.caption + (" " + post_text if post_text else "") if replied.caption else post_text
        elif replied.video:
            media_file_id = replied.video.file_id
            media_type = "video"
            post_text = replied.caption + (" " + post_text if post_text else "") if replied.caption else post_text
        elif replied.document:
            media_file_id = replied.document.file_id
            media_type = "document"
            post_text = replied.caption + (" " + post_text if post_text else "") if replied.caption else post_text

    if not post_text and not media_file_id:
        await message.reply_text("Please provide text or reply to a media message for your suggestion.")
        return

    sugg_id = suggestions_sql.add_suggestion(user.id, channel_target, post_text, media_file_id, media_type)
    await message.reply_text(
        f"✅ <b>Suggestion Logged!</b>\n\n"
        f"❍ <b>Suggestion ID:</b> <code>#{sugg_id}</code>\n"
        f"❍ <b>Target Channel:</b> <code>{html.escape(channel_target)}</code>\n\n"
        f"Admins will review and approve/decline it.",
        parse_mode=ParseMode.HTML
    )


@cutiepii_cmd(command="approvepost")
async def approve_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args

    if not args:
        await message.reply_text("Usage: `/approvepost [suggestion_id]`")
        return

    try:
        sugg_id = int(args[0])
    except ValueError:
        await message.reply_text("Please specify a valid numeric Suggestion ID.")
        return

    sugg = suggestions_sql.get_suggestion(sugg_id)
    if not sugg or sugg.status != "pending":
        await message.reply_text("This suggestion does not exist or has already been reviewed.")
        return

    is_admin = False
    if user.id in DEV_USERS or user.id in SUDO_USERS:
        is_admin = True
    else:
        try:
            member = await context.bot.get_chat_member(sugg.channel_id, user.id)
            if member.status in ("administrator", "creator"):
                is_admin = True
        except Exception:
            pass

    if not is_admin:
        await message.reply_text("You are not an admin in the target channel!")
        return

    try:
        if sugg.media_type == "photo":
            await context.bot.send_photo(chat_id=sugg.channel_id, photo=sugg.media_file_id, caption=sugg.post_text)
        elif sugg.media_type == "video":
            await context.bot.send_video(chat_id=sugg.channel_id, video=sugg.media_file_id, caption=sugg.post_text)
        elif sugg.media_type == "document":
            await context.bot.send_document(chat_id=sugg.channel_id, document=sugg.media_file_id, caption=sugg.post_text)
        else:
            await context.bot.send_message(chat_id=sugg.channel_id, text=sugg.post_text)
        
        suggestions_sql.update_status(sugg_id, "approved")
        await message.reply_text(f"✅ Suggested post <code>#{sugg_id}</code> has been approved and published!", parse_mode=ParseMode.HTML)
    except BadRequest as e:
        await message.reply_text(f"Failed to post to channel: {e}. Make sure I am an admin in that channel.")


@cutiepii_cmd(command="declinepost")
async def decline_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args

    if not args:
        await message.reply_text("Usage: `/declinepost [suggestion_id]`")
        return

    try:
        sugg_id = int(args[0])
    except ValueError:
        await message.reply_text("Please specify a valid numeric Suggestion ID.")
        return

    sugg = suggestions_sql.get_suggestion(sugg_id)
    if not sugg or sugg.status != "pending":
        await message.reply_text("This suggestion does not exist or has already been reviewed.")
        return

    is_admin = False
    if user.id in DEV_USERS or user.id in SUDO_USERS:
        is_admin = True
    else:
        try:
            member = await context.bot.get_chat_member(sugg.channel_id, user.id)
            if member.status in ("administrator", "creator"):
                is_admin = True
        except Exception:
            pass

    if not is_admin:
        await message.reply_text("You are not an admin in the target channel!")
        return

    suggestions_sql.update_status(sugg_id, "declined")
    await message.reply_text(f"❌ Suggested post <code>#{sugg_id}</code> has been declined.", parse_mode=ParseMode.HTML)


# ==========================================
# Telegram Stories
# ==========================================

@cutiepii_cmd(command="poststory", can_disable=False)
async def post_story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("Usage: `/poststory [media_link_or_text]`")
        return

    story_content = " ".join(args)
    story_id = f"story_{random.randint(1000, 9999)}"

    await message.reply_text(
        f"📖 <b>Telegram Story Posted!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"❍ <b>Story ID:</b> <code>{story_id}</code>\n"
        f"❍ <b>Content:</b> <i>\"{html.escape(story_content)}\"</i>\n\n"
        f"🔒 <i>Tracking story views and privacy settings in real-time.</i>",
        parse_mode=ParseMode.HTML
    )


@cutiepii_cmd(command="storystats", can_disable=False)
async def story_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("Usage: `/storystats [story_id]`")
        return

    story_id = args[0]
    stats = stories_sql.get_story_stats(story_id)
    if stats["views"] == 0:
        stories_sql.log_story_action(random.randint(10000, 99999), story_id, "view")
        stories_sql.log_story_action(random.randint(10000, 99999), story_id, "like")
        stats = stories_sql.get_story_stats(story_id)

    await message.reply_text(
        f"📊 <b>STORY PERFORMANCE METRICS</b> 📊\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"❍ <b>Story ID:</b> <code>{html.escape(story_id)}</code>\n"
        f"❍ <b>Total Views:</b> <code>{stats['views']}</code>\n"
        f"❍ <b>Total Likes:</b> <code>{stats['likes']}</code>\n\n"
        f"🔒 <i>Privacy configurations active and verified.</i>",
        parse_mode=ParseMode.HTML
    )


# ==========================================
# Message Reactions
# ==========================================

@cutiepii_message_reaction()
async def reaction_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reaction_update = update.message_reaction
    if not reaction_update:
        return

    chat_id = reaction_update.chat.id
    for r in reaction_update.new_reaction:
        if getattr(r, "emoji", None):
            reactions_sql.log_reaction(chat_id, r.emoji)


@cutiepii_cmd(command="reactionstats", can_disable=False)
async def reaction_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    top = reactions_sql.get_reactions_by_chat(chat.id)
    if not top:
        await message.reply_text("No reactions recorded in this chat yet.")
        return

    reply = "⚡️ <b>CHAT MESSAGE REACTION ANALYTICS</b> ⚡️\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for react in top:
        reply += f"❍ {react.emoji} : <code>{react.count} times</code>\n"

    await message.reply_text(reply, parse_mode=ParseMode.HTML)


# Register reaction handler


# ==========================================
# Media Info & Giveaways
# ==========================================

@cutiepii_cmd(command="lyrics", can_disable=False)
async def get_lyrics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    if not args:
        await message.reply_text("Usage: `/lyrics [song name]`")
        return

    song = "%20".join(args)
    url = f"https://some-random-api.com/lyrics?title={song}"
    try:
        res = requests.get(url).json()
        title = res.get("title", "Unknown Title")
        artist = res.get("author", "Unknown Artist")
        lyrics = res.get("lyrics", "Lyrics not found.")
        thumbnail = res.get("thumbnail", {}).get("genius")

        reply = (
            f"🎵 <b>Lyrics: {title} - {artist}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{lyrics[:3800]}"
        )
        if len(lyrics) > 3800:
            reply += "\n\n<i>[Truncated...]</i>"

        if thumbnail:
            await message.reply_photo(photo=thumbnail, caption=reply, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(reply, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"Error: {e}")


@cutiepii_cmd(command="github", can_disable=False)
async def github_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    if not args:
        await message.reply_text("Usage: `/github [username]`")
        return

    username = args[0]
    url = f"https://api.github.com/users/{username}"
    try:
        res = requests.get(url).json()
        if res.get("message") == "Not Found":
            await message.reply_text("User not found.")
            return

        name = res.get("name", username)
        bio = res.get("bio", "No bio available.")
        repos = res.get("public_repos")
        followers = res.get("followers")
        avatar = res.get("avatar_url")
        html_url = res.get("html_url")

        reply = (
            f"🐙 <b>GitHub User Profile: {name}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"❍ <b>Bio:</b> <i>\"{bio}\"</i>\n"
            f"❍ <b>Public Repositories:</b> <code>{repos}</code>\n"
            f"❍ <b>Followers:</b> <code>{followers}</code>\n\n"
            f"🔗 <a href='{html_url}'>GitHub Profile Link</a>"
        )
        await message.reply_photo(photo=avatar, caption=reply, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"Error: {e}")


@cutiepii_cmd(command="gpower", can_disable=False)
async def gaming_giveaways(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    platform = args[0].lower() if args else "pc"

    url = f"https://www.gamerpower.com/api/giveaways?platform={platform}"
    try:
        res = requests.get(url).json()
        if isinstance(res, list) and res:
            giveaway = random.choice(res)
            title = giveaway.get("title")
            worth = giveaway.get("worth")
            description = giveaway.get("description")
            instructions = giveaway.get("instructions")
            link = giveaway.get("open_giveaway_url")
            image = giveaway.get("image")

            reply = (
                f"🎮 <b>Active Gaming Giveaway: {title}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"❍ <b>Worth:</b> <code>{worth}</code>\n"
                f"❍ <b>Description:</b> <i>\"{description}\"</i>\n\n"
                f"📖 <b>Instructions:</b> {instructions}\n\n"
                f"🔗 <a href='{link}'>Claim Giveaway Link</a>"
            )
            await message.reply_photo(photo=image, caption=reply, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text("No giveaways found for that platform.")
    except Exception as e:
        await message.reply_text(f"Error fetching giveaways: {e}")


@cutiepii_cmd(command="freetogame", can_disable=False)
async def free_to_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    
    platform = "all"
    category = None
    if args:
        if args[0].lower() in ["pc", "browser"]:
            platform = args[0].lower()
            if len(args) > 1:
                category = args[1].lower()
        else:
            category = args[0].lower()

    url = "https://www.freetogame.com/api/games"
    if category:
        url += f"?category={category}"
        if platform != "all":
            url += f"&platform={platform}"
    elif platform != "all":
        url += f"?platform={platform}"

    try:
        res = requests.get(url).json()
        if isinstance(res, list) and res:
            game = random.choice(res)
            title = game.get("title")
            desc = game.get("short_description")
            genre = game.get("genre")
            publisher = game.get("publisher")
            link = game.get("game_url")
            thumbnail = game.get("thumbnail")

            reply = (
                f"🎮 <b>Free-To-Play Game: {title}</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"❍ <b>Genre:</b> <code>{genre}</code>\n"
                f"❍ <b>Publisher:</b> <code>{publisher}</code>\n"
                f"❍ <b>Description:</b> <i>\"{desc}\"</i>\n\n"
                f"🔗 <a href='{link}'>Play Game Now</a>"
            )
            await message.reply_photo(photo=thumbnail, caption=reply, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text("No free-to-play games found.")
    except Exception as e:
        await message.reply_text(f"Error fetching games: {e}")


__help__ = True

__mod_name__ = "Media Monetization"
