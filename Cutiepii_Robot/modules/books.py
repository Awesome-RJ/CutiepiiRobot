"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.
"""

import html
import re
import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Cutiepii_Robot import dispatcher, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd


# ========================================
# Command: /book [query]
# ========================================

@cutiepii_cmd(command="book", group=490)
async def book_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("<b>Invalid Command Usage</b>\nPlease specify the name of the book you want to search. Usage: <code>/book [name]</code>", parse_mode=ParseMode.HTML)
        return

    query = " ".join(args).strip()
    await message.reply_chat_action("typing")

    # Use Google Books API
    url = f"https://www.googleapis.com/books/v1/volumes?q={requests.utils.quote(query)}"
    
    use_fallback = False
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            items = data.get("items", [])
            if not items:
                await message.reply_text(f"<b>No Results Found</b>\nCould not find any books matching the query: <b>{html.escape(query)}</b>", parse_mode=ParseMode.HTML)
                return

            reply = f"<b>Book Search Results</b>\nQuery: <i>{html.escape(query)}</i>\n\n"
            for item in items[:3]:  # Return top 3 matches
                info = item.get("volumeInfo", {})
                title = info.get("title", "Unknown Title")
                authors = ", ".join(info.get("authors", [])) or "Unknown Author"
                published = info.get("publishedDate", "Unknown Date")
                pages = info.get("pageCount", "N/A")
                desc = info.get("description", "No description available.")
                link = info.get("previewLink", "")

                # Truncate description length for Telegram compatibility
                if len(desc) > 200:
                    desc = desc[:200] + "..."

                reply += (
                    f"<b><a href='{link}'>{html.escape(title)}</a></b>\n"
                    f"<b>Author(s):</b> {html.escape(authors)}\n"
                    f"<b>Published:</b> {html.escape(published)} | <b>Pages:</b> {pages}\n"
                    f"<b>Summary:</b> <i>{html.escape(desc)}</i>\n\n"
                )

            await message.reply_text(reply.strip(), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
            return
        else:
            LOGGER.warning(f"Google Books API returned status {r.status_code}. Falling back to Open Library.")
            use_fallback = True
    except Exception as e:
        LOGGER.warning(f"Google Books API request failed: {e}. Falling back to Open Library.")
        use_fallback = True

    if use_fallback:
        # Fallback: Open Library API
        fallback_url = f"https://openlibrary.org/search.json?q={requests.utils.quote(query)}&limit=3"
        try:
            r = requests.get(fallback_url, timeout=10)
            if r.status_code != 200:
                await message.reply_text("<b>API Connection Error</b>\nFailed to connect to the books search service databases.", parse_mode=ParseMode.HTML)
                return

            data = r.json()
            docs = data.get("docs", [])
            if not docs:
                await message.reply_text(f"<b>No Results Found</b>\nCould not find any books matching the query: <b>{html.escape(query)}</b>", parse_mode=ParseMode.HTML)
                return

            reply = f"<b>Book Search Results (Open Library)</b>\nQuery: <i>{html.escape(query)}</i>\n\n"
            for doc in docs[:3]:
                title = doc.get("title", "Unknown Title")
                authors = ", ".join(doc.get("author_name", [])) or "Unknown Author"
                published = doc.get("first_publish_year", "Unknown Date")
                pages = doc.get("number_of_pages_median", "N/A")
                key = doc.get("key", "")
                link = f"https://openlibrary.org{key}" if key else ""

                reply += (
                    f"<b><a href='{link}'>{html.escape(title)}</a></b>\n"
                    f"<b>Author(s):</b> {html.escape(authors)}\n"
                    f"<b>Published:</b> {published} | <b>Pages:</b> {pages}\n\n"
                )

            await message.reply_text(reply.strip(), parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        except Exception as fallback_err:
            await message.reply_text(f"<b>Error</b>\nAn error occurred while searching books: <code>{html.escape(str(fallback_err))}</code>", parse_mode=ParseMode.HTML)


# ========================================
# Command: /wiktionary [word]
# ========================================

@cutiepii_cmd(command="wiktionary", group=491)
async def wiktionary_def(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("<b>Invalid Command Usage</b>\nPlease specify a word to search. Usage: <code>/wiktionary [word]</code>", parse_mode=ParseMode.HTML)
        return

    word = args[0].strip().lower()
    await message.reply_chat_action("typing")

    # Wiktionary REST API for detailed definitions
    url = f"https://en.wiktionary.org/api/rest_v1/page/definition/{word}"
    headers = {"User-Agent": "CutiepiiRobot/2.0 (https://github.com/Awesome-RJ/CutiepiiRobot)"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 404:
            await message.reply_text(f"<b>No Results Found</b>\nCould not find any definitions for the word: <b>{html.escape(word)}</b>", parse_mode=ParseMode.HTML)
            return
        if r.status_code != 200:
            await message.reply_text("<b>API Connection Error</b>\nWiktionary service is currently unavailable.", parse_mode=ParseMode.HTML)
            return

        data = r.json()
        definitions_list = data.get("en", [])
        if not definitions_list:
            await message.reply_text(f"<b>No Results Found</b>\nNo English definitions found for the word: <b>{html.escape(word)}</b>", parse_mode=ParseMode.HTML)
            return

        reply = f"<b>Wiktionary: {word.capitalize()}</b>\n\n"
        for idx, item in enumerate(definitions_list[:3], 1):
            pos = item.get("partOfSpeech", "Noun")
            defs = item.get("definitions", [])
            reply += f"<b>{idx}. Part of Speech:</b> <i>{html.escape(pos)}</i>\n"
            for d in defs[:2]:  # Top 2 definitions per POS
                # Strip raw HTML tags from the dictionary definition text
                definition_text = re.sub('<[^<]+?>', '', d.get("definition", ""))
                reply += f"- {html.escape(definition_text)}\n"
            reply += "\n"

        await message.reply_text(reply.strip(), parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"<b>Error</b>\nAn error occurred while fetching the definition: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)


# ========================================
# Command: /xkcd [id]
# ========================================

@cutiepii_cmd(command="xkcd", group=492)
async def xkcd_comic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    await message.reply_chat_action("upload_photo")

    try:
        if args:
            comic_id = args[0].strip()
            url = f"https://xkcd.com/{comic_id}/info.0.json"
        else:
            url = "https://xkcd.com/info.0.json"

        r = requests.get(url, timeout=10)
        if r.status_code == 404:
            await message.reply_text("<b>No Results Found</b>\nThe specified XKCD comic ID is invalid or does not exist.", parse_mode=ParseMode.HTML)
            return
        if r.status_code != 200:
            await message.reply_text("<b>API Connection Error</b>\nFailed to reach the XKCD comic service.", parse_mode=ParseMode.HTML)
            return

        data = r.json()
        num = data.get("num")
        title = data.get("title", "Unknown")
        img_url = data.get("img")
        alt_text = data.get("alt", "")

        caption = (
            f"<b>xkcd Comic #{num}: {title}</b>\n\n"
            f"<b>Alt Text:</b> <i>{html.escape(alt_text)}</i>"
        )

        if img_url:
            await message.reply_photo(photo=img_url, caption=caption, parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(caption, parse_mode=ParseMode.HTML)
    except Exception as e:
        await message.reply_text(f"<b>Error</b>\nAn error occurred while fetching the comic: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)


# ========================================
# Module Help and Stats
# ========================================

__help__ = True

__mod_name__ = "Knowledge"
