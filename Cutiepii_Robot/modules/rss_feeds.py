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

from Cutiepii_Robot import dispatcher, updater, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    AdminPerms,
)
import Cutiepii_Robot.modules.sql.rss_sql as sql


def parse_feed_robust(xml_content: bytes):
    """
    Robustly parse standard RSS or ATOM feeds, bypassing all XML namespaces
    by matching local tag names. Returns a list of dictionaries with keys:
    'title', 'link', and 'guid'.
    """
    try:
        root = ET.fromstring(xml_content)
    except Exception as e:
        return None, f"Failed to parse XML: {e}"

    entries = []
    
    # Iterate through all elements to locate items (RSS) or entries (ATOM)
    for elem in root.iter():
        tag_local = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag_local in ["item", "entry"]:
            title = "No Title"
            link = ""
            guid = ""
            
            for child in elem:
                child_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if child_tag == "title":
                    title = child.text or "No Title"
                elif child_tag == "link":
                    # For ATOM links, URL is stored in 'href' attribute
                    link = child.attrib.get("href", "") if child.attrib else (child.text or "")
                elif child_tag in ["guid", "id"]:
                    guid = child.text or ""
            
            if not guid:
                guid = link or title
                
            entries.append({
                "title": title.strip(),
                "link": link.strip(),
                "guid": guid.strip()
            })
            
    return entries, None


# ========================================
# Command Handlers
# ========================================

@cutiepii_cmd(command="add_feed", group=440)
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def add_feed_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("Please provide a feed URL. Usage: `/add_feed [URL]`", parse_mode=ParseMode.MARKDOWN)
        return

    url = args[0].strip()
    await message.reply_chat_action("typing")

    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            await message.reply_text(f"Failed to reach URL (HTTP {r.status_code}). Please verify the link is correct.")
            return

        entries, err = parse_feed_robust(r.content)
        if err:
            await message.reply_text(f"Invalid feed. Only standard RSS and ATOM formats are supported. Error: {err}")
            return
        if not entries:
            await message.reply_text("The feed appears to be empty or has no entries.")
            return

        # Get latest entry ID
        latest_guid = entries[0]["guid"]
        
        # Save to database
        sql.add_feed(chat.id, url, latest_guid)
        await message.reply_text(
            f"✅ Successfully subscribed to feed in <b>{html.escape(chat.title)}</b>!\n\n"
            f"🔗 <b>URL:</b> {html.escape(url)}\n"
            f"⏱️ <b>Update Check Interval:</b> Every 5 minutes.",
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        await message.reply_text(f"An error occurred while validating the feed URL: {e}")


@cutiepii_cmd(command="rm_feed", group=441)
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def rm_feed_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message

    res = sql.remove_feed(chat.id)
    if res:
        await message.reply_text(
            f"✅ Successfully unsubscribed from feed in <b>{html.escape(chat.title)}</b>.",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text("There is no active feed subscription in this chat.")


@cutiepii_cmd(command="feeds", group=442)
@connection_status
async def feeds_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message

    feed = sql.get_feed(chat.id)
    if feed:
        await message.reply_text(
            f"This chat has <b>1</b> active RSS feed subscription:\n\n"
            f"❍ 🔗 <a href='{html.escape(feed.feed_url)}'>{html.escape(feed.feed_url)}</a>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    else:
        await message.reply_text(
            "This chat has <b>0</b> active RSS feed subscriptions.\n"
            "To add one, use <code>/add_feed [URL]</code>.",
            parse_mode=ParseMode.HTML
        )


# ========================================
# Repeating Job Callback
# ========================================

async def check_feeds(context: ContextTypes.DEFAULT_TYPE):
    feeds = sql.get_all_feeds()
    if not feeds:
        return

    for feed in feeds:
        chat_id = int(feed.chat_id)
        url = feed.feed_url
        last_entry_id = feed.last_entry_id

        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                continue

            entries, err = parse_feed_robust(r.content)
            if err or not entries:
                continue

            # The first item is usually the newest
            latest_entry = entries[0]
            latest_guid = latest_entry["guid"]

            # Store the latest entry ID if it is a new subscription
            if not last_entry_id:
                sql.update_last_entry(chat_id, latest_guid)
                continue

            # Check if there are new entries
            if latest_guid != last_entry_id:
                new_entries = []
                for entry in entries:
                    if entry["guid"] == last_entry_id:
                        break
                    new_entries.append(entry)

                # Broadcast new entries (limit to 3 to prevent spamming)
                for entry in reversed(new_entries[:3]):
                    msg = (
                        f"📰 <b>New Feed Update!</b>\n\n"
                        f"🔹 <b><a href='{entry['link']}'>{html.escape(entry['title'])}</a></b>"
                    )
                    try:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text=msg,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=False
                        )
                    except Exception as e:
                        LOGGER.warning(f"Failed to send RSS update to {chat_id}: {e}")

                # Update stored latest entry ID
                sql.update_last_entry(chat_id, latest_guid)

        except Exception as e:
            LOGGER.warning(f"Error checking feed {url} for chat {chat_id}: {e}")


# Initialize repeating check job (runs every 5 minutes / 300 seconds)
if updater and hasattr(updater, "job_queue") and updater.job_queue:
    updater.job_queue.run_repeating(callback=check_feeds, interval=300, first=30, name="rss_feed_check")


__help__ = True

__mod_name__ = "Feeds"
