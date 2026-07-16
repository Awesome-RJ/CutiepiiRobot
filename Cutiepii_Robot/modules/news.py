"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.
"""

import html
import requests
import xml.etree.ElementTree as ET
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Cutiepii_Robot import dispatcher, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    AdminPerms,
)
import Cutiepii_Robot.modules.sql.news_sql as sql

# Google News RSS Gates
GATES = {
    "world": "https://news.google.com/news/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en",
    "tech": "https://news.google.com/news/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
    "science": "https://news.google.com/news/rss/headlines/section/topic/SCIENCE?hl=en-US&gl=US&ceid=US:en",
    "business": "https://news.google.com/news/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "sports": "https://news.google.com/news/rss/headlines/section/topic/SPORTS?hl=en-US&gl=US&ceid=US:en",
    "health": "https://news.google.com/news/rss/headlines/section/topic/HEALTH?hl=en-US&gl=US&ceid=US:en",
    "entertainment": "https://news.google.com/news/rss/headlines/section/topic/ENTERTAINMENT?hl=en-US&gl=US&ceid=US:en",
    "gaming": "https://news.google.com/rss/search?q=gaming&hl=en-US&gl=US&ceid=US:en",
    "anime": "https://news.google.com/rss/search?q=anime&hl=en-US&gl=US&ceid=US:en"
}


def parse_news(xml_content: bytes):
    """Parse item elements from Google News RSS feed."""
    try:
        root = ET.fromstring(xml_content)
    except Exception as e:
        LOGGER.error(f"[NEWS]: XML Parse Error: {e}")
        return []

    entries = []
    for elem in root.iter():
        tag_local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag_local == "item":
            title = "No Title"
            link = ""
            for child in elem:
                child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if child_tag == "title":
                    title = child.text or "No Title"
                elif child_tag == "link":
                    link = child.text or ""
            entries.append({"title": title.strip(), "link": link.strip()})
    return entries


def filter_news(entries, keywords_str: str):
    """Filters stories to match any keyword (case-insensitive substring check)."""
    if not keywords_str:
        return entries
    
    keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]
    if not keywords:
        return entries

    filtered = []
    for entry in entries:
        title_lower = entry["title"].lower()
        if any(k in title_lower for k in keywords):
            filtered.append(entry)
    return filtered


# ========================================
# Command Handlers
# ========================================

@cutiepii_cmd(command="news", group=460)
async def fetch_news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args

    setting = sql.get_news_settings(chat.id)
    category = args[0].lower() if args else setting.category

    if category not in GATES:
        available = ", ".join(f"<code>{g}</code>" for g in GATES.keys())
        await message.reply_text(
            f"Invalid news gate: <b>{html.escape(category)}</b>.\n\n"
            f"🧭 <b>Available Gates:</b>\n{available}",
            parse_mode=ParseMode.HTML
        )
        return

    await message.reply_chat_action("typing")

    try:
        r = requests.get(GATES[category], timeout=10)
        if r.status_code != 200:
            await message.reply_text("Could not fetch news headlines at the moment. Try again later.")
            return

        entries = parse_news(r.content)
        if not entries:
            await message.reply_text("No articles found in this news gate.")
            return

        # Apply keyword filtering if set
        filtered = filter_news(entries, setting.keywords)

        if not filtered:
            await message.reply_text(
                f"📰 No articles in <b>{category.capitalize()}</b> matched your topic filters: "
                f"<code>{html.escape(setting.keywords)}</code>",
                parse_mode=ParseMode.HTML
            )
            return

        reply_text = f"📰 <b>Latest Headlines: {category.capitalize()} Gate</b>\n\n"
        for idx, entry in enumerate(filtered[:5], 1):  # Top 5 headlines
            # Extract clean title by removing Google News source attribution (usually ending in " - Source")
            clean_title = entry["title"]
            if " - " in clean_title:
                clean_title = " - ".join(clean_title.split(" - ")[:-1])
            reply_text += f"{idx}. <b><a href='{entry['link']}'>{html.escape(clean_title)}</a></b>\n\n"

        await message.reply_text(reply_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    except Exception as e:
        await message.reply_text(f"An error occurred while fetching news: {e}")


@cutiepii_cmd(command="headlines", group=461)
async def quick_headlines_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat

    # Fetch headlines from the default configured category
    setting = sql.get_news_settings(chat.id)
    category = setting.category

    await message.reply_chat_action("typing")

    try:
        r = requests.get(GATES[category], timeout=10)
        if r.status_code != 200:
            await message.reply_text("Could not fetch headlines at the moment. Try again later.")
            return

        entries = parse_news(r.content)
        if not entries:
            await message.reply_text("No articles found in your preferred news gate.")
            return

        filtered = filter_news(entries, setting.keywords)

        if not filtered:
            await message.reply_text(
                f"📰 No articles in your preferred gate (<b>{category.capitalize()}</b>) matched your topic filters: "
                f"<code>{html.escape(setting.keywords)}</code>",
                parse_mode=ParseMode.HTML
            )
            return

        reply_text = f"📰 <b>Top Headlines: {category.capitalize()}</b>\n"
        if setting.keywords:
            reply_text += f"🔍 <b>Filters:</b> <code>{html.escape(setting.keywords)}</code>\n"
        reply_text += "\n"

        for idx, entry in enumerate(filtered[:5], 1):
            clean_title = entry["title"]
            if " - " in clean_title:
                clean_title = " - ".join(clean_title.split(" - ")[:-1])
            reply_text += f"▪️ <b><a href='{entry['link']}'>{html.escape(clean_title)}</a></b>\n\n"

        await message.reply_text(reply_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)

    except Exception as e:
        await message.reply_text(f"An error occurred while fetching headlines: {e}")


@cutiepii_cmd(command="newsset", group=462)
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def configure_news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if len(args) < 2:
        await message.reply_text(
            "⚙️ <b>News Configurations</b>\n\n"
            "<b>Usage:</b>\n"
            "❍ <code>/newsset category [name]</code> - Set default category.\n"
            "❍ <code>/newsset topics [keywords]</code> - Filter stories by comma-separated keywords (use <code>none</code> to clear).\n\n"
            "<i>Example: /newsset category tech</i>",
            parse_mode=ParseMode.HTML
        )
        return

    sub_command = args[0].lower()
    value = " ".join(args[1:]).strip()

    if sub_command == "category":
        value = value.lower()
        if value not in GATES:
            available = ", ".join(f"<code>{g}</code>" for g in GATES.keys())
            await message.reply_text(f"Invalid category: <b>{html.escape(value)}</b>.\n\n🧭 <b>Available:</b> {available}", parse_mode=ParseMode.HTML)
            return
        sql.set_news_category(chat.id, value)
        await message.reply_text(f"✅ Preferred news category set to <b>{value.capitalize()}</b> in {html.escape(chat.title)}.", parse_mode=ParseMode.HTML)

    elif sub_command == "topics":
        if value.lower() in ["none", "clear", "nil"]:
            sql.set_news_keywords(chat.id, "")
            await message.reply_text(f"✅ Topic filters cleared in {html.escape(chat.title)}.")
        else:
            sql.set_news_keywords(chat.id, value)
            await message.reply_text(f"✅ Topic filter keywords set to: <code>{html.escape(value)}</code> in {html.escape(chat.title)}.", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("Invalid sub-command. Use <code>category</code> or <code>topics</code>.", parse_mode=ParseMode.HTML)


# Module Help details
__help__ = True

__mod_name__ = "News"
