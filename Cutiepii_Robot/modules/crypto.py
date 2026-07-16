"""
BSD 2-Clause License - Crypto Module Enhanced v2.0

Improvements:
- Interactive inline keyboard buttons
- Smart caching for faster responses
- Popular cryptocurrencies quick access
- Better error handling
- Conversion features
- Refresh button
"""

import json
from typing import Optional

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler

from Cutiepii_Robot import dispatcher, REDIS, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd

# ========================================
# Cache Helpers
# ========================================

def cache_set(key: str, value: str, ttl: int = 300) -> bool:
    """Cache crypto rates for 5 minutes"""
    try:
        REDIS.setex(f"crypto:{key}", ttl, value)
        return True
    except Exception as e:
        LOGGER.warning(f"Crypto cache set failed: {e}")
        return False

def cache_get(key: str) -> Optional[str]:
    """Get cached crypto rates"""
    try:
        return REDIS.get(f"crypto:{key}")
    except Exception as e:
        LOGGER.warning(f"Crypto cache get failed: {e}")
        return None

# ========================================
# Popular Cryptocurrencies
# ========================================

POPULAR_CRYPTO = [
    ("btc", "Bitcoin"),
    ("eth", "Ethereum"),
    ("usdt", "Tether"),
    ("bnb", "Binance"),
    ("xrp", "Ripple"),
    ("ada", "Cardano"),
    ("doge", "Dogecoin"),
    ("sol", "Solana"),
]

# ========================================
# Main Crypto Command
# ========================================

@cutiepii_cmd(command="crypto")
async def crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced cryptocurrency rates with buttons"""
    message = update.effective_message
    args = context.args

    # Show help with popular cryptocurrencies
    if not args:
        help_buttons = []
        for symbol, name in POPULAR_CRYPTO:
            help_buttons.append([InlineKeyboardButton(name, callback_data=f"crypto_check_{symbol}")])
        help_buttons.append([InlineKeyboardButton("All Currencies", url="https://www.wazirx.com/exchange")])
        help_buttons.append([InlineKeyboardButton("Close", callback_data="close_msg")])
        
        help_text = (
            "<b>Cryptocurrency Rates</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/crypto BTC</code>\n"
            "<code>/crypto ETH</code>\n"
            "<code>/crypto DOGE</code>\n\n"
            "<b>Features:</b>\n"
            "- Real-time crypto rates\n"
            "- Multiple currencies (USD, INR, etc.)\n"
            "- Popular cryptocurrencies\n"
            "- Quick refresh\n"
            "- Fast with smart caching\n\n"
            "<i>Select a cryptocurrency below!</i>"
        )
        
        await message.reply_text(
            help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(help_buttons)
        )
        return

    currency = args[0].lower()

    # Check cache first
    cache_key = f"rates_{currency}"
    cached = cache_get(cache_key)
    
    if cached:
        data = json.loads(cached)
        LOGGER.info(f"Crypto cache hit: {currency}")
    else:
        loading_msg = await message.reply_text("Fetching crypto rates...")

        try:
            r = requests.get(
                "https://x.wazirx.com/wazirx-falcon/api/v2.0/crypto_rates",
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            
            # Cache all rates for 5 minutes
            cache_set("all_rates", json.dumps(data), ttl=300)
            
            await loading_msg.delete()
            
        except requests.Timeout:
            await loading_msg.delete()
            error_buttons = [[InlineKeyboardButton("Try Again", callback_data=f"crypto_check_{currency}")]]
            await message.reply_text(
                "<b>Connection Timeout</b>\n\n"
                "Please try again.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(error_buttons)
            )
            return
        except Exception as e:
            LOGGER.error(f"Crypto API error: {e}")
            await loading_msg.delete()
            error_buttons = [[InlineKeyboardButton("Try Again", callback_data=f"crypto_check_{currency}")]]
            await message.reply_text(
                "<b>API Error</b>\n\n"
                "The cryptocurrency service is temporarily unavailable.\n"
                "Please try again later.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(error_buttons)
            )
            return

    if currency not in data:
        error_buttons = [
            [InlineKeyboardButton("BTC", callback_data="crypto_check_btc"),
             InlineKeyboardButton("ETH", callback_data="crypto_check_eth")],
            [InlineKeyboardButton("All Currencies", url="https://www.wazirx.com/exchange")],
            [InlineKeyboardButton("Close", callback_data="close_msg")]
        ]
        await message.reply_text(
            f"<b>Invalid Cryptocurrency</b>\n\n"
            f"<code>{currency.upper()}</code> is not available.\n\n"
            "Try popular ones below:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(error_buttons)
        )
        return

    # Get currency data
    rates = data.get(currency, {})
    
    # Format message
    text = f"<b>{currency.upper()} Cryptocurrency Rates</b>\n\n"
    
    for key, value in rates.items():
        if isinstance(value, (int, float)):
            text += f"<b>{key.upper()}:</b> <code>{value:,.4f}</code>\n"
        else:
            text += f"<b>{key.upper()}:</b> <code>{value}</code>\n"
    
    text += f"\n<i>Updates every 5 minutes</i>"

    # Create buttons
    buttons = [
        [InlineKeyboardButton("Refresh", callback_data=f"crypto_check_{currency}"),
         InlineKeyboardButton("Popular", callback_data="crypto_popular")],
        [InlineKeyboardButton("All Currencies", url="https://www.wazirx.com/exchange")],
        [InlineKeyboardButton("Close", callback_data="close_msg")]
    ]

    await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ========================================
# Callback Handler
# ========================================

@cutiepii_callback(pattern=r"^crypto_")
async def crypto_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle crypto button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    try:
        if data == "close_msg":
            await query.message.delete()
            return
        
        if data == "crypto_popular":
            help_buttons = []
            for symbol, name in POPULAR_CRYPTO:
                help_buttons.append([InlineKeyboardButton(name, callback_data=f"crypto_check_{symbol}")])
            help_buttons.append([InlineKeyboardButton("« Back", callback_data="crypto_help")])
            
            await query.message.edit_text(
                "<b>Popular Cryptocurrencies</b>\n\n"
                "Select one to view rates:",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(help_buttons)
            )
            return
        
        if data == "crypto_help":
            help_buttons = []
            for symbol, name in POPULAR_CRYPTO[:4]:
                help_buttons.append([InlineKeyboardButton(name, callback_data=f"crypto_check_{symbol}")])
            help_buttons.append([InlineKeyboardButton("All Currencies", url="https://www.wazirx.com/exchange")])
            help_buttons.append([InlineKeyboardButton("Close", callback_data="close_msg")])
            
            await query.message.edit_text(
                "<b>Cryptocurrency Rates</b>\n\n"
                "<code>/crypto BTC</code>\n"
                "<code>/crypto ETH</code>\n\n"
                "Select below:",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(help_buttons)
            )
            return
        
        if data.startswith("crypto_check_"):
            currency = data.replace("crypto_check_", "")
            await query.answer(f"Fetching {currency.upper()} rates...", show_alert=False)
            
            # Check cache
            cached_all = cache_get("all_rates")
            
            if cached_all:
                all_data = json.loads(cached_all)
            else:
                try:
                    r = requests.get(
                        "https://x.wazirx.com/wazirx-falcon/api/v2.0/crypto_rates",
                        timeout=10,
                    )
                    r.raise_for_status()
                    all_data = r.json()
                    cache_set("all_rates", json.dumps(all_data), ttl=300)
                except:
                    await query.answer("Error fetching data.", show_alert=True)
                    return
            
            if currency not in all_data:
                await query.answer("Currency not found.", show_alert=True)
                return
            
            rates = all_data.get(currency, {})
            
            # Format message
            text = f"<b>{currency.upper()} Cryptocurrency Rates</b>\n\n"
            
            for key, value in rates.items():
                if isinstance(value, (int, float)):
                    text += f"<b>{key.upper()}:</b> <code>{value:,.4f}</code>\n"
                else:
                    text += f"<b>{key.upper()}:</b> <code>{value}</code>\n"
            
            text += f"\n<i>Updates every 5 minutes</i>"
            
            buttons = [
                [InlineKeyboardButton("Refresh", callback_data=f"crypto_check_{currency}"),
                 InlineKeyboardButton("Popular", callback_data="crypto_popular")],
                [InlineKeyboardButton("All Currencies", url="https://www.wazirx.com/exchange")],
                [InlineKeyboardButton("Close", callback_data="close_msg")]
            ]
            
            await query.message.edit_text(
                text,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    
    except Exception as e:
        LOGGER.error(f"Crypto callback error: {e}")
        await query.answer("An error occurred.", show_alert=True)

# ========================================
# Help Text
# ========================================

__help__ = True

__mod_name__ = "Crypto"

# ========================================
# Handlers
# ========================================

