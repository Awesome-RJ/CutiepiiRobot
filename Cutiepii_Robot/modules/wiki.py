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

import asyncio
import functools
import warnings

# Suppress BeautifulSoup GuessedAtParserWarning globally for wikipedia lib
warnings.filterwarnings("ignore", category=UserWarning, module="bs4")

import wikipedia
from wikipedia.exceptions import DisambiguationError, PageError

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd


def _wiki_summary(query: str, sentences: int = 10) -> str:
    """Blocking wikipedia summary call — run in executor."""
    wikipedia.set_lang("en")
    # Auto-suggest helps avoid exact-match failures
    results = wikipedia.search(query, results=5)
    if not results:
        raise PageError(query)
    # Use the top result
    best = results[0]
    return wikipedia.summary(best, sentences=sentences, auto_suggest=False)


def _wiki_page_url(query: str) -> str:
    """Blocking wikipedia page URL — tries direct then top search result."""
    wikipedia.set_lang("en")
    try:
        return wikipedia.page(query, auto_suggest=False).url
    except (PageError, DisambiguationError):
        results = wikipedia.search(query, results=3)
        if results:
            return wikipedia.page(results[0], auto_suggest=False).url
        raise


@cutiepii_cmd(command="wiki", can_disable=True)
async def wiki(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    full_text = message.text or ""

    # Extract query: everything after /wiki (and optional @botusername)
    parts = full_text.split(None, 1)
    query = parts[1].strip() if len(parts) > 1 else ""

    if not query:
        await message.reply_text(
            "<b>Invalid Command Usage</b>\nPlease provide a search term. Usage: <code>/wiki &lt;query&gt;</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    loading_msg = await message.reply_text("<b>Wikipedia Search</b>\nSearching Wikipedia...")

    loop = asyncio.get_event_loop()
    try:
        # Run blocking calls in executor so they don't freeze the event loop
        summary = await loop.run_in_executor(
            None, functools.partial(_wiki_summary, query, 10)
        )
        page_url = await loop.run_in_executor(
            None, functools.partial(_wiki_page_url, query)
        )

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Read More", url=page_url)]]
        )

        # Telegram messages have a 4096 char limit
        if len(summary) > 4000:
            summary = summary[:4000] + "..."

        await loading_msg.edit_text(
            summary,
            reply_markup=keyboard,
        )

    except PageError:
        await loading_msg.edit_text(
            f"<b>No Results Found</b>\nNo Wikipedia page found for: <code>{query}</code>\n\n"
            f"Try a different spelling or a more specific search query.",
            parse_mode=ParseMode.HTML,
        )
    except DisambiguationError as e:
        # Show top 10 suggestions
        options = [opt.strip() for opt in str(e).split("\n") if opt.strip()][:10]
        options_text = "\n- ".join(options)
        await loading_msg.edit_text(
            f"<b>Ambiguous Query</b>\nPlease be more specific.\n\n"
            f"<b>Possible Matches:</b>\n- {options_text}",
            parse_mode=ParseMode.HTML,
        )
    except BadRequest as e:
        await loading_msg.edit_text(f"<b>Telegram Error</b>\nFailed to edit: <code>{e}</code>", parse_mode=ParseMode.HTML)
    except ValueError as e:
        # This catches "Expecting value: line 1 column 1 (char 0)" JSON decode errors
        # from the wikipedia library when the API returns an unexpected response
        await loading_msg.edit_text(
            f"<b>Unexpected API Response</b>\nWikipedia returned an unexpected response for <code>{query}</code>.\n"
            f"Please try again or use a different search term.",
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        await loading_msg.edit_text(
            f"<b>Error</b>\nAn error occurred: <code>{str(e)[:200]}</code>",
            parse_mode=ParseMode.HTML,
        )


__mod_name__ = "Wikipedia"
__help__ = True