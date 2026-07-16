import html
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.error import BadRequest

from Cutiepii_Robot import dispatcher, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd

CRICKET_API_URL = "https://sugoi-api.vercel.app/cricket"
FOOTBALL_API_URL = "https://sugoi-api.vercel.app/football"

class MatchManager:
    def __init__(self, api_url):
        self.api_url = api_url
        self.matches = []
        self.match_count = 0

    async def fetch_matches(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, timeout=10.0) as response:
                    if response.status == 200:
                        self.matches = await response.json()
                    else:
                        self.matches = []
        except Exception as e:
            LOGGER.warning(f"Failed to fetch matches from {self.api_url}: {e}")
            self.matches = []

    def get_next_matches(self, count):
        next_matches = self.matches[self.match_count : self.match_count + count]
        self.match_count += count
        return next_matches

    def reset_matches(self):
        self.matches = []
        self.match_count = 0


cricket_manager = MatchManager(CRICKET_API_URL)
football_manager = MatchManager(FOOTBALL_API_URL)


async def get_match_text(match, sport):
    match_text = f"{'🏏' if sport == 'cricket' else '⚽️'} <b>{html.escape(match.get('title', 'Unknown Match'))}</b>\n\n"
    match_text += f"🗓 <b>Date:</b> {html.escape(match.get('date', 'N/A'))}\n"
    match_text += f"🏆 <b>Team 1:</b> {html.escape(match.get('team1', 'N/A'))}\n"
    match_text += f"🏆 <b>Team 2:</b> {html.escape(match.get('team2', 'N/A'))}\n"
    match_text += f"🏟️ <b>Venue:</b> {html.escape(match.get('venue', 'N/A'))}"
    return match_text


def create_inline_keyboard(sport):
    inline_keyboard = [
        [
            InlineKeyboardButton(
                f"Next {sport.capitalize()} Match ➡️",
                callback_data=f"next_{sport}_match",
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard)


@cutiepii_cmd(command="cricket")
async def get_cricket_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    try:
        cricket_manager.reset_matches()
        await cricket_manager.fetch_matches()

        if not cricket_manager.matches:
            await message.reply_text("No upcoming cricket matches found or sports API is currently offline.")
            return

        next_matches = cricket_manager.get_next_matches(1)
        match = next_matches[0]

        match_text = await get_match_text(match, "cricket")
        reply_markup = create_inline_keyboard("cricket")

        await message.reply_text(
            match_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )

    except Exception as e:
        LOGGER.exception(f"Error in cricket command: {e}")
        await message.reply_text("No upcoming cricket matches found or sports API is currently offline.")


@cutiepii_cmd(command="football")
async def get_football_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    try:
        football_manager.reset_matches()
        await football_manager.fetch_matches()

        if not football_manager.matches:
            await message.reply_text("No upcoming football matches found or sports API is currently offline.")
            return

        next_matches = football_manager.get_next_matches(1)
        match = next_matches[0]

        match_text = await get_match_text(match, "football")
        reply_markup = create_inline_keyboard("football")

        await message.reply_text(
            match_text, reply_markup=reply_markup, parse_mode=ParseMode.HTML
        )

    except Exception as e:
        LOGGER.exception(f"Error in football command: {e}")
        await message.reply_text("No upcoming football matches found or sports API is currently offline.")


@cutiepii_callback(pattern=r"^next_(cricket|football)_match$")
async def show_next_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        sport = query.data.split("_")[1]
        manager = cricket_manager if sport == "cricket" else football_manager

        if not manager.matches:
            await query.answer(f"No more {sport} matches available.", show_alert=True)
            return

        next_matches = manager.get_next_matches(3)

        if not next_matches:
            await query.answer(f"No more {sport} matches available.", show_alert=True)
            return

        match_text = ""
        for match in next_matches:
            match_text += await get_match_text(match, sport) + "\n\n"

        reply_markup = create_inline_keyboard(sport)

        await query.message.edit_text(
            match_text.strip(),
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )
        await query.answer()

    except Exception as e:
        LOGGER.exception(f"Error in show_next_match callback: {e}")
        await query.answer("An error occurred.")


# Register callback query handler

__mod_name__ = "Sports"

__help__ = True
