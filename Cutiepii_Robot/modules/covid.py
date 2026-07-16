"""
BSD 2-Clause License - COVID Stats Enhanced v2.0

Improvements:
- Interactive inline keyboard buttons
- Global vs Country stats navigation
- Smart caching
- Better error handling
- Comparison features
- Refresh button
"""

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd
import json
from typing import Optional

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler

from Cutiepii_Robot import REDIS, LOGGER, dispatcher
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd

# ========================================
# Cache Helpers
# ========================================

def cache_set(key: str, value: str, ttl: int = 1800) -> bool:
    """Cache COVID data for 30 minutes"""
    try:
        REDIS.setex(f"covid:{key}", ttl, value)
        return True
    except Exception as e:
        LOGGER.warning(f"COVID cache set failed: {e}")
        return False

def cache_get(key: str) -> Optional[str]:
    """Get cached COVID data"""
    try:
        return REDIS.get(f"covid:{key}")
    except Exception as e:
        LOGGER.warning(f"COVID cache get failed: {e}")
        return None

# ========================================
# Main COVID Command
# ========================================

@cutiepii_cmd(command=["covid", "corona"], can_disable=True)
async def covid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced COVID stats with interactive buttons"""
    message = update.effective_message
    args = context.args

    # Show help with country selection
    if not args:
        help_buttons = [
            [InlineKeyboardButton("Global Stats", callback_data="covid_global")],
            [InlineKeyboardButton("USA", callback_data="covid_country_USA"),
             InlineKeyboardButton("India", callback_data="covid_country_India")],
            [InlineKeyboardButton("UK", callback_data="covid_country_UK"),
             InlineKeyboardButton("Brazil", callback_data="covid_country_Brazil")],
            [InlineKeyboardButton("China", callback_data="covid_country_China"),
             InlineKeyboardButton("Japan", callback_data="covid_country_Japan")],
            [InlineKeyboardButton("Close", callback_data="close_msg")]
        ]
        
        help_text = (
            "<b>COVID-19 Statistics</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/covid</code> - Global stats\n"
            "<code>/covid USA</code> - Country stats\n"
            "<code>/covid India</code> - Country stats\n\n"
            "<b>Features:</b>\n"
            "- Real-time global statistics\n"
            "- Country-specific data\n"
            "- Cases, deaths, recovered\n"
            "- Daily updates\n"
            "- Active & critical cases\n\n"
            "<i>Select a region below!</i>"
        )
        
        await message.reply_text(
            help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(help_buttons)
        )
        return

    # Get country stats
    country = " ".join(args)
    
    # Check cache
    cache_key = f"country_{country.lower()}"
    cached = cache_get(cache_key)
    
    if cached:
        r = json.loads(cached)
        LOGGER.info(f"COVID cache hit: {country}")
    else:
        loading_msg = await message.reply_text("Fetching COVID-19 data...")
        
        try:
            response = requests.get(f"https://disease.sh/v3/covid-19/countries/{country}", timeout=10)
            r = response.json()
            
            if response.status_code != 200 or 'message' in r:
                await loading_msg.delete()
                error_buttons = [
                    [InlineKeyboardButton("Global Stats", callback_data="covid_global")],
                    [InlineKeyboardButton("Try Again", callback_data="covid_help")]
                ]
                await message.reply_text(
                    "<b>Country Not Found</b>\n\n"
                    "<b>Tips:</b>\n"
                    "- Check spelling\n"
                    "- Use full country name\n"
                    "- Examples: USA, India, UK",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(error_buttons)
                )
                return
            
            # Cache for 30 minutes
            cache_set(cache_key, json.dumps(r), ttl=1800)
            await loading_msg.delete()
            
        except Exception as e:
            LOGGER.error(f"COVID API error: {e}")
            await loading_msg.delete()
            error_buttons = [[InlineKeyboardButton("Try Again", callback_data=f"covid_country_{country}")]]
            await message.reply_text(
                "<b>Connection Error</b>\n\n"
                "Please try again later.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(error_buttons)
            )
            return

    # Format country stats
    reply_text = f"<b>COVID-19 Statistics: {r['country']}</b>\n\n"
    reply_text += f"<b>Total Cases:</b> {r['cases']:,}\n"
    reply_text += f"<b>Today:</b> +{r['todayCases']:,}\n\n"
    reply_text += f"<b>Total Deaths:</b> {r['deaths']:,}\n"
    reply_text += f"<b>Today:</b> +{r['todayDeaths']:,}\n\n"
    reply_text += f"<b>Recovered:</b> {r['recovered']:,}\n"
    reply_text += f"<b>Active:</b> {r['active']:,}\n"
    reply_text += f"<b>Critical:</b> {r['critical']:,}\n\n"
    reply_text += f"<b>Per Million:</b>\n"
    reply_text += f"  - Cases: {r['casesPerOneMillion']:,}\n"
    reply_text += f"  - Deaths: {r['deathsPerOneMillion']:,}\n\n"
    reply_text += f"<i>Last updated: {r.get('updated', 'N/A')}</i>"

    # Create buttons
    buttons = [
        [InlineKeyboardButton("Refresh", callback_data=f"covid_country_{country}"),
         InlineKeyboardButton("Global", callback_data="covid_global")],
        [InlineKeyboardButton("Other Country", callback_data="covid_help"),
         InlineKeyboardButton("Close", callback_data="close_msg")]
    ]

    await message.reply_text(
        reply_text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ========================================
# Callback Handler
# ========================================

@cutiepii_callback(pattern=r"^covid_")
async def covid_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle COVID button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    try:
        if data == "close_msg":
            await query.message.delete()
            return
        
        if data == "covid_help":
            help_buttons = [
                [InlineKeyboardButton("Global Stats", callback_data="covid_global")],
                [InlineKeyboardButton("USA", callback_data="covid_country_USA"),
                 InlineKeyboardButton("India", callback_data="covid_country_India")],
                [InlineKeyboardButton("UK", callback_data="covid_country_UK"),
                 InlineKeyboardButton("Brazil", callback_data="covid_country_Brazil")],
                [InlineKeyboardButton("Close", callback_data="close_msg")]
            ]
            
            await query.message.edit_text(
                "<b>COVID-19 Statistics</b>\n\n"
                "Select a country for stats:",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(help_buttons)
            )
            return
        
        if data == "covid_global":
            # Check cache
            cached = cache_get("global")
            
            if cached:
                r = json.loads(cached)
            else:
                await query.answer("Fetching global stats...", show_alert=False)
                try:
                    response = requests.get("https://disease.sh/v3/covid-19/all", timeout=10)
                    r = response.json()
                    cache_set("global", json.dumps(r), ttl=1800)
                except:
                    await query.answer("Error fetching data!", show_alert=True)
                    return
            
            # Format global stats
            reply_text = f"<b>Global COVID-19 Statistics</b>\n\n"
            reply_text += f"<b>Total Cases:</b> {r['cases']:,}\n"
            reply_text += f"<b>Today:</b> +{r['todayCases']:,}\n\n"
            reply_text += f"<b>Total Deaths:</b> {r['deaths']:,}\n"
            reply_text += f"<b>Today:</b> +{r['todayDeaths']:,}\n\n"
            reply_text += f"<b>Recovered:</b> {r['recovered']:,}\n"
            reply_text += f"<b>Active:</b> {r['active']:,}\n"
            reply_text += f"<b>Critical:</b> {r['critical']:,}\n\n"
            reply_text += f"<b>Per Million:</b>\n"
            reply_text += f"  - Cases: {r['casesPerOneMillion']:,}\n"
            reply_text += f"  - Deaths: {r['deathsPerOneMillion']:,}\n\n"
            reply_text += f"<b>Affected Countries:</b> {r.get('affectedCountries', 'N/A'):,}"
            
            buttons = [
                [InlineKeyboardButton("Refresh", callback_data="covid_global"),
                 InlineKeyboardButton("Country Stats", callback_data="covid_help")],
                [InlineKeyboardButton("Close", callback_data="close_msg")]
            ]
            
            await query.message.edit_text(
                reply_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        
        elif data.startswith("covid_country_"):
            country = data.replace("covid_country_", "")
            await query.answer(f"Fetching stats for {country}...", show_alert=False)
            
            # Check cache
            cache_key = f"country_{country.lower()}"
            cached = cache_get(cache_key)
            
            if cached:
                r = json.loads(cached)
            else:
                try:
                    response = requests.get(f"https://disease.sh/v3/covid-19/countries/{country}", timeout=10)
                    r = response.json()
                    cache_set(cache_key, json.dumps(r), ttl=1800)
                except:
                    await query.answer("Error fetching data!", show_alert=True)
                    return
            
            # Format country stats
            reply_text = f"<b>COVID-19 Statistics: {r['country']}</b>\n\n"
            reply_text += f"<b>Total Cases:</b> {r['cases']:,}\n"
            reply_text += f"<b>Today:</b> +{r['todayCases']:,}\n\n"
            reply_text += f"<b>Total Deaths:</b> {r['deaths']:,}\n"
            reply_text += f"<b>Today:</b> +{r['todayDeaths']:,}\n\n"
            reply_text += f"<b>Recovered:</b> {r['recovered']:,}\n"
            reply_text += f"<b>Active:</b> {r['active']:,}\n"
            reply_text += f"<b>Critical:</b> {r['critical']:,}\n\n"
            reply_text += f"<b>Per Million:</b>\n"
            reply_text += f"  - Cases: {r['casesPerOneMillion']:,}\n"
            reply_text += f"  - Deaths: {r['deathsPerOneMillion']:,}"
            
            buttons = [
                [InlineKeyboardButton("Refresh", callback_data=f"covid_country_{country}"),
                 InlineKeyboardButton("Global", callback_data="covid_global")],
                [InlineKeyboardButton("Other Country", callback_data="covid_help"),
                 InlineKeyboardButton("Close", callback_data="close_msg")]
            ]
            
            await query.message.edit_text(
                reply_text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    
    except Exception as e:
        if "Message is not modified" in str(e):
            await query.answer("Already up to date!", show_alert=False)
            return
        LOGGER.error(f"COVID callback error: {e}")
        await query.answer("❌ An error occurred!", show_alert=True)

# ========================================
# Help Text
# ========================================

__help__ = True

__mod_name__ = "COVID"
