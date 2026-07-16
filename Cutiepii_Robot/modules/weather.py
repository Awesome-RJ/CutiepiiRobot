"""
BSD 2-Clause License - Weather Module Enhanced v2.0

Improvements:
- Interactive inline keyboard buttons
- Smart caching for faster responses
- Better error handling with suggestions
- Help screen with examples
- Celsius/Fahrenheit toggle
- City suggestions
- Refresh button
- No API Key required (uses wttr.in JSON format)
"""

import io
import json
from typing import Optional
from datetime import datetime

import aiohttp
from pytz import country_timezones as c_tz, timezone as tz, country_names as c_n
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler
from telethon.tl import types, functions

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, register
from Cutiepii_Robot import telethn, REDIS, LOGGER, dispatcher

# ========================================
# Cache Helpers
# ========================================

def cache_set(key: str, value: str, ttl: int = 600) -> bool:
    """Cache weather data for 10 minutes"""
    try:
        REDIS.setex(f"weather:{key}", ttl, value)
        return True
    except Exception as e:
        LOGGER.warning(f"Weather cache set failed: {e}")
        return False

def cache_get(key: str) -> Optional[str]:
    """Get cached weather data"""
    try:
        return REDIS.get(f"weather:{key}")
    except Exception as e:
        LOGGER.warning(f"Weather cache get failed: {e}")
        return None

# ========================================
# Helper Functions
# ========================================

async def is_register_admin(chat, user):
    if isinstance(chat, (types.InputPeerChannel, types.InputChannel)):
        return isinstance(
            (await telethn(functions.channels.GetParticipantRequest(chat, user))).participant,
            (types.ChannelParticipantAdmin, types.ChannelParticipantCreator),
        )
    if isinstance(chat, types.InputPeerUser):
        return True

def get_country_code(country_name: str) -> Optional[str]:
    """Get 2-letter country code from full country name"""
    for code, name in c_n.items():
        if country_name.lower() == name.lower():
            return code
    return None

def _get_timezone_for_country(country_code: str):
    """Safely get a timezone object for a 2-letter country code."""
    try:
        zones = c_tz.get(country_code)
        if zones:
            return tz(zones[0])
    except Exception:
        pass
    return None

def get_icon(code: str) -> str:
    """Map wttr.in weatherCode to weather emoji"""
    try:
        code_val = int(code)
        if code_val == 113:
            return "☀️"
        elif code_val == 116:
            return "⛅️"
        elif code_val in (119, 122, 143, 248, 260):
            return "☁️"
        elif code_val in (176, 263, 266, 293, 296, 299, 302, 305, 308, 311, 314, 317, 353, 356, 359):
            return "🌧"
        elif code_val in (200, 386, 389):
            return "⛈"
        elif code_val in (179, 182, 185, 227, 230, 320, 323, 326, 329, 332, 335, 338, 350, 362, 365, 368, 371, 374, 377, 392, 395):
            return "❄️"
    except Exception:
        pass
    return "🌡"

def _build_weather_text(data: dict, unit: str = "C") -> str:
    """Build the formatted weather message string using wttr.in JSON data."""
    current = data['current_condition'][0]
    area = data['nearest_area'][0]
    weather_day = data['weather'][0]
    astronomy = weather_day['astronomy'][0]

    cityname = area['areaName'][0]['value']
    country_name = area['country'][0]['value']
    
    temp_c = current['temp_C']
    temp_f = current['temp_F']
    feels_c = current['FeelsLikeC']
    feels_f = current['FeelsLikeF']
    humidity = current['humidity']
    wind_kmh = current['windspeedKmph']
    condmain = current['weatherDesc'][0]['value']
    uv_index = current['uvIndex']
    
    sunrise = astronomy['sunrise']
    sunset = astronomy['sunset']

    country_code = get_country_code(country_name)
    ctimezone = None
    if country_code:
        ctimezone = _get_timezone_for_country(country_code)

    if ctimezone:
        current_time = datetime.now(ctimezone).strftime("%A %d %b, %H:%M")
    else:
        current_time = datetime.utcnow().strftime("%A %d %b, %H:%M UTC")

    if unit == "F":
        temp_str = f"{temp_f}°F"
        feels_str = f"{feels_f}°F"
    else:
        temp_str = f"{temp_c}°C"
        feels_str = f"{feels_c}°C"

    msg = f"<b>{cityname}, {country_name}</b>\n\n"
    msg += f"<b>Time:</b> {current_time}\n"
    msg += f"<b>Temperature:</b> {temp_str}\n"
    msg += f"<b>Feels like:</b> {feels_str}\n"
    msg += f"<b>Condition:</b> {condmain}\n"
    msg += f"<b>Humidity:</b> {humidity}%\n"
    msg += f"<b>Wind:</b> {wind_kmh} km/h\n"
    msg += f"<b>Sunrise:</b> {sunrise}\n"
    msg += f"<b>Sunset:</b> {sunset}\n"
    msg += f"<b>UV Index:</b> {uv_index}"
    return msg

async def _fetch_weather_data(city: str) -> Optional[dict]:
    """Async fetch of weather from wttr.in. Returns dict or None on error."""
    from urllib.parse import quote
    url = f"https://wttr.in/{quote(city)}?format=j1"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json(content_type=None)
                return data
    except Exception as e:
        LOGGER.error(f"Weather fetch error: {e}")
        return None

# ========================================
# Main Weather Command
# ========================================

@cutiepii_cmd(command="weather", can_disable=True, rate_limit_calls=10, rate_limit_window=60, add_error_handler=True)
async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced weather command with buttons"""
    message = update.effective_message
    city = " ".join(context.args) if context.args else ""

    # Show help if no city provided
    if not city:
        help_buttons = [
            [InlineKeyboardButton("London", callback_data="weather_search_London"),
             InlineKeyboardButton("New York", callback_data="weather_search_New York")],
            [InlineKeyboardButton("Tokyo", callback_data="weather_search_Tokyo"),
             InlineKeyboardButton("Paris", callback_data="weather_search_Paris")],
            [InlineKeyboardButton("Dubai", callback_data="weather_search_Dubai"),
             InlineKeyboardButton("Delhi", callback_data="weather_search_Delhi")],
            [InlineKeyboardButton("Close", callback_data="weather_close")]
        ]
        help_text = (
            "<b>Weather Information</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/weather London</code>\n"
            "<code>/weather New York</code>\n"
            "<code>/weather Tokyo</code>\n\n"
            "<i>Or try quick searches below!</i>"
        )
        await message.reply_text(
            help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(help_buttons)
        )
        return

    await _send_weather(message, city, edit_msg=None)


async def _send_weather(message, city: str, edit_msg=None, unit: str = "C"):
    """Core weather fetch+send logic, reusable from both command and callback."""
    # Normalise city string
    city = city.strip()
    cache_key = f"data_{city.lower()}_{unit}"
    cached = cache_get(cache_key)

    if cached:
        weather_data = json.loads(cached)
    else:
        # Show loading indicator
        if edit_msg:
            if hasattr(edit_msg, 'edit_message_text'):
                await edit_msg.edit_message_text("Fetching weather data...")
            else:
                await edit_msg.edit_text("Fetching weather data...")
            loading_msg = edit_msg
        else:
            loading_msg = await message.reply_text("Fetching weather data...")

        weather_data = await _fetch_weather_data(city)

        if not weather_data:
            error_buttons = [
                [InlineKeyboardButton("Search Again", callback_data="weather_help"),
                 InlineKeyboardButton("Close", callback_data="weather_close")]
            ]
            err_text = (
                "<b>City Not Found</b>\n\n"
                "The requested city was not found or the weather service is currently unavailable.\n\n"
                "<b>Tips:</b>\n"
                "- Check spelling\n"
                "- Use format: <code>City Name</code>\n"
                "- Try: <code>London</code>\n"
                "- Try: <code>New York</code>"
            )
            if hasattr(loading_msg, 'edit_message_text'):
                await loading_msg.edit_message_text(err_text, parse_mode=ParseMode.HTML,
                                            reply_markup=InlineKeyboardMarkup(error_buttons))
            else:
                await loading_msg.edit_text(err_text, parse_mode=ParseMode.HTML,
                                            reply_markup=InlineKeyboardMarkup(error_buttons))
            return

        cache_set(cache_key, json.dumps(weather_data), ttl=600)

        # Delete loading if it's a fresh message (not editing)
        if not edit_msg:
            await loading_msg.delete()

    result = weather_data
    area = result["nearest_area"][0]
    actual_city = area['areaName'][0]['value']

    msg_text = _build_weather_text(result, unit=unit)

    toggle_unit = "F" if unit == "C" else "C"
    toggle_label = "°F" if unit == "C" else "°C"
    buttons = [
        [InlineKeyboardButton("Refresh", callback_data=f"weather_search_{actual_city}"),
         InlineKeyboardButton(toggle_label, callback_data=f"weather_{toggle_unit}_{actual_city}")],
        [InlineKeyboardButton("Search Another", callback_data="weather_help"),
         InlineKeyboardButton("Close", callback_data="weather_close")]
    ]

    if edit_msg:
        if hasattr(edit_msg, 'edit_message_text'):
            await edit_msg.edit_message_text(msg_text, parse_mode=ParseMode.HTML,
                                     reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await edit_msg.edit_text(msg_text, parse_mode=ParseMode.HTML,
                                     reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await message.reply_text(msg_text, parse_mode=ParseMode.HTML,
                                 reply_markup=InlineKeyboardMarkup(buttons))


# ========================================
# Callback Handler
# ========================================

@cutiepii_callback(pattern=r"^weather_")
async def weather_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all weather button callbacks"""
    query = update.callback_query
    await query.answer()
    data = query.data

    try:
        if data == "weather_close":
            await query.message.delete()
            return

        if data == "weather_help":
            help_buttons = [
                [InlineKeyboardButton("London", callback_data="weather_search_London"),
                 InlineKeyboardButton("New York", callback_data="weather_search_New York")],
                [InlineKeyboardButton("Tokyo", callback_data="weather_search_Tokyo"),
                 InlineKeyboardButton("Paris", callback_data="weather_search_Paris")],
                [InlineKeyboardButton("Dubai", callback_data="weather_search_Dubai"),
                 InlineKeyboardButton("Delhi", callback_data="weather_search_Delhi")],
                [InlineKeyboardButton("Close", callback_data="weather_close")]
            ]
            await query.edit_message_text(
                "<b>Weather Information</b>\n\n"
                "<code>/weather City</code>\n\n"
                "Try quick searches below!",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(help_buttons)
            )
            return

        if data.startswith("weather_search_"):
            city = data[len("weather_search_"):]
            await _send_weather(query.message, city, edit_msg=query, unit="C")
            return

        if data.startswith("weather_F_"):
            city = data[len("weather_F_"):]
            await _send_weather(query.message, city, edit_msg=query, unit="F")
            return

        if data.startswith("weather_C_"):
            city = data[len("weather_C_"):]
            await _send_weather(query.message, city, edit_msg=query, unit="C")
            return

    except Exception as e:
        LOGGER.error(f"Weather callback error: {e}")
        await query.answer("An error occurred!", show_alert=True)


# ========================================
# Telethon Handler
# ========================================

@register(pattern="wttr")
async def wttr(event):
    """Alternative weather using wttr.in"""
    if event.fwd_from:
        return

    sample_url = "https://wttr.in/{}.png"
    input_str = event.pattern_match.group(2)
    if not input_str:
        await event.reply("<b>Invalid Command Usage</b>\nPlease specify a city. Example: <code>/wttr London</code>", parse_mode="html")
        return

    async with aiohttp.ClientSession() as session:
        from urllib.parse import quote
        response_api_zero = await session.get(sample_url.format(quote(input_str)))
        response_api = await response_api_zero.read()
        with io.BytesIO(response_api) as out_file:
            await event.reply(file=out_file)

# ========================================
# Help Text
# ========================================

__help__ = True

__mod_name__ = "Weather"

# ========================================
# Handlers
# ========================================

# Handles both weather_ prefixed callbacks and weather_close / weather_help
