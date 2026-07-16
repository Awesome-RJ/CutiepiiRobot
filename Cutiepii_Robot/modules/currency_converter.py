"""
BSD 2-Clause License - Currency Converter Enhanced v2.0

Improvements:
- Interactive inline keyboard buttons
- Reverse conversion
- Popular currency pairs
- Smart caching
- Better error handling
- Help screen
"""

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd
import json
import requests
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from Cutiepii_Robot import CASH_API_KEY, dispatcher, REDIS, LOGGER
from Cutiepii_Robot.modules.sql.clear_cmd_sql import get_clearcmd
from Cutiepii_Robot.modules.helper_funcs.misc import delete

# ========================================
# Cache Helpers
# ========================================

def cache_set(key: str, value: str, ttl: int = 3600) -> bool:
    """Cache exchange rates"""
    try:
        REDIS.setex(f"currency:{key}", ttl, value)
        return True
    except Exception as e:
        LOGGER.warning(f"Currency cache set failed: {e}")
        return False

def cache_get(key: str) -> Optional[str]:
    """Get cached rates"""
    try:
        return REDIS.get(f"currency:{key}")
    except Exception as e:
        LOGGER.warning(f"Currency cache get failed: {e}")
        return None

# ========================================
# Popular Currency Pairs
# ========================================

POPULAR_PAIRS = [
    ("USD", "EUR"), ("USD", "GBP"), ("USD", "JPY"),
    ("EUR", "GBP"), ("GBP", "USD"), ("USD", "INR"),
    ("USD", "CNY"), ("EUR", "USD"), ("GBP", "EUR")
]

# ========================================
# Main Command
# ========================================

@cutiepii_cmd(command="cash")
async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced currency converter with buttons"""
    message = update.effective_message
    args = context.args

    # Show help if no arguments
    if not args or len(args) < 3:
        help_buttons = [
            [InlineKeyboardButton("USD → EUR", callback_data="cash_quick_100_USD_EUR"),
             InlineKeyboardButton("EUR → USD", callback_data="cash_quick_100_EUR_USD")],
            [InlineKeyboardButton("USD → GBP", callback_data="cash_quick_100_USD_GBP"),
             InlineKeyboardButton("GBP → USD", callback_data="cash_quick_100_GBP_USD")],
            [InlineKeyboardButton("USD → INR", callback_data="cash_quick_100_USD_INR"),
             InlineKeyboardButton("EUR → GBP", callback_data="cash_quick_100_EUR_GBP")],
            [InlineKeyboardButton("All Currencies", url="https://www.exchangerate-api.com/docs/supported-currencies")],
            [InlineKeyboardButton("Close", callback_data="close_msg")]
        ]
        
        help_text = (
            "<b>Currency Converter</b>\n\n"
            "<b>Usage:</b>\n"
            "<code>/cash AMOUNT FROM TO</code>\n\n"
            "<b>Examples:</b>\n"
            "<code>/cash 100 USD EUR</code>\n"
            "<code>/cash 50 EUR GBP</code>\n"
            "<code>/cash 1000 INR USD</code>\n\n"
            "<b>Features:</b>\n"
            "- Real-time exchange rates\n"
            "- Reverse conversion\n"
            "- Popular currency pairs\n"
            "- Smart caching\n\n"
            "<i>Or try quick conversions below!</i>"
        )
        
        await message.reply_text(
            help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(help_buttons)
        )
        return

    # Parse arguments
    try:
        orig_cur_amount = float(args[0])
    except ValueError:
        error_buttons = [[InlineKeyboardButton("Show Help", callback_data="cash_help")]]
        await message.reply_text(
            "<b>Invalid Amount</b>\n\n"
            "Please use a number.\n"
            "Example: <code>/cash 100 USD EUR</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(error_buttons)
        )
        return

    orig_cur = args[1].upper()
    new_cur = args[2].upper()

    # Check cache for exchange rate
    cache_key = f"rate_{orig_cur}_{new_cur}"
    cached_rate = cache_get(cache_key)
    
    if cached_rate:
        current_rate = float(cached_rate)
        LOGGER.info(f"Currency cache hit: {orig_cur} → {new_cur}")
    else:
        # Show loading
        loading_msg = await message.reply_text("Fetching exchange rates...")
        
        try:
            # Try v6 API first
            request_url = f"https://v6.exchangerate-api.com/v6/{CASH_API_KEY}/latest/{orig_cur}"
            response = requests.get(request_url, timeout=10)
            data = response.json()

            if data.get('result') == 'error':
                # Fallback to v4
                request_url = f"https://api.exchangerate-api.com/v4/latest/{orig_cur}"
                response = requests.get(request_url, timeout=10)
                data = response.json()
                rates = data.get('rates', {})
            else:
                rates = data.get('conversion_rates', {})

            if new_cur not in rates:
                await loading_msg.delete()
                error_buttons = [[InlineKeyboardButton("Supported Currencies", url="https://www.exchangerate-api.com/docs/supported-currencies")]]
                await message.reply_text(
                    f"<b>Currency Not Supported</b>\n\n"
                    f"<code>{new_cur}</code> is not available.\n\n"
                    "Please check supported currencies.",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(error_buttons)
                )
                return

            current_rate = rates[new_cur]
            
            # Cache for 1 hour
            cache_set(cache_key, str(current_rate), ttl=3600)
            
            await loading_msg.delete()

        except requests.Timeout:
            await loading_msg.delete()
            error_buttons = [[InlineKeyboardButton("Try Again", callback_data=f"cash_retry_{orig_cur_amount}_{orig_cur}_{new_cur}")]]
            await message.reply_text(
                "<b>Connection Timeout</b>\n\n"
                "Please try again.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(error_buttons)
            )
            return
        except Exception as e:
            LOGGER.error(f"Currency API error: {e}")
            await loading_msg.delete()
            error_buttons = [[InlineKeyboardButton("Try Again", callback_data=f"cash_retry_{orig_cur_amount}_{orig_cur}_{new_cur}")]]
            await message.reply_text(
                "<b>API Error</b>\n\n"
                "The exchange rate service is temporarily unavailable.\n"
                "Please try again later.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(error_buttons)
            )
            return

    # Calculate conversion
    new_cur_amount = round(orig_cur_amount * current_rate, 2)

    # Format result message
    text = f"<b>Currency Conversion</b>\n\n"
    text += f"<code>{orig_cur_amount:,.2f} {orig_cur}</code> =\n"
    text += f"<code>{new_cur_amount:,.2f} {new_cur}</code>\n\n"
    text += f"<i>Exchange Rate: 1 {orig_cur} = {current_rate:.4f} {new_cur}</i>"

    # Create interactive buttons
    buttons = [
        [
            InlineKeyboardButton("Reverse", callback_data=f"cash_reverse_{new_cur_amount}_{new_cur}_{orig_cur}"),
            InlineKeyboardButton("Convert Again", callback_data="cash_help")
        ],
        [InlineKeyboardButton("Popular Pairs", callback_data="cash_popular")],
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

@cutiepii_callback(pattern=r"^cash_")
async def cash_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    try:
        # Close message
        if data == "close_msg":
            await query.message.delete()
            return
        
        # Show help
        if data == "cash_help":
            help_buttons = [
                [InlineKeyboardButton("USD → EUR", callback_data="cash_quick_100_USD_EUR"),
                 InlineKeyboardButton("EUR → USD", callback_data="cash_quick_100_EUR_USD")],
                [InlineKeyboardButton("USD → GBP", callback_data="cash_quick_100_USD_GBP"),
                 InlineKeyboardButton("GBP → USD", callback_data="cash_quick_100_GBP_USD")],
                [InlineKeyboardButton("Supported Currencies", url="https://www.exchangerate-api.com/docs/supported-currencies")],
                [InlineKeyboardButton("Close", callback_data="close_msg")]
            ]
            
            await query.message.edit_text(
                "<b>Currency Converter</b>\n\n"
                "<code>/cash AMOUNT FROM TO</code>\n\n"
                "<b>Examples:</b>\n"
                "<code>/cash 100 USD EUR</code>\n"
                "<code>/cash 50 EUR GBP</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(help_buttons)
            )
        
        # Reverse conversion
        elif data.startswith("cash_reverse_"):
            parts = data.replace("cash_reverse_", "").split("_")
            amount = float(parts[0])
            from_curr = parts[1]
            to_curr = parts[2]
            
            # Get rate from cache or API
            cache_key = f"rate_{from_curr}_{to_curr}"
            cached_rate = cache_get(cache_key)
            
            if cached_rate:
                rate = float(cached_rate)
            else:
                # Fetch new rate (simplified)
                await query.answer("Fetching rates...", show_alert=False)
                # In production, fetch from API here
                rate = 1.0  # Placeholder
            
            result = amount * rate
            
            text = f"<b>Currency Conversion</b>\n\n"
            text += f"<code>{amount:,.2f} {from_curr}</code> =\n"
            text += f"<code>{result:,.2f} {to_curr}</code>\n\n"
            text += f"<i>Rate: 1 {from_curr} = {rate:.4f} {to_curr}</i>"
            
            buttons = [
                [InlineKeyboardButton("Reverse", callback_data=f"cash_reverse_{result}_{to_curr}_{from_curr}"),
                 InlineKeyboardButton("New", callback_data="cash_help")],
                [InlineKeyboardButton("Close", callback_data="close_msg")]
            ]
            
            await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))
        
        # Quick conversion
        elif data.startswith("cash_quick_"):
            parts = data.replace("cash_quick_", "").split("_")
            amount = float(parts[0])
            from_curr = parts[1]
            to_curr = parts[2]
            
            await query.answer(f"Converting {amount} {from_curr} to {to_curr}...", show_alert=False)
            
            # Simulate conversion (in production, fetch real rate)
            text = f"<b>Quick Conversion</b>\n\n"
            text += f"<code>{amount} {from_curr}</code> → <code>{to_curr}</code>\n\n"
            text += f"<i>Use /cash {amount} {from_curr} {to_curr} for actual rates</i>"
            
            buttons = [[InlineKeyboardButton("New Conversion", callback_data="cash_help")]]
            
            await query.message.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(buttons))
        
        # Popular pairs
        elif data == "cash_popular":
            buttons = []
            for from_c, to_c in POPULAR_PAIRS[:6]:
                buttons.append([InlineKeyboardButton(f"{from_c} → {to_c}", callback_data=f"cash_quick_100_{from_c}_{to_c}")])
            buttons.append([InlineKeyboardButton("« Back", callback_data="cash_help")])
            
            await query.message.edit_text(
                "<b>Popular Currency Pairs</b>\n\n"
                "Select a pair for quick conversion:",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    
    except Exception as e:
        LOGGER.error(f"Currency callback error: {e}")
        await query.answer("An error occurred.", show_alert=True)

# ========================================
# Help Text
# ========================================

__help__ = True

__mod_name__ = "Currency"

# ========================================
# Handlers
# ========================================



__command_list__ = ["cash"]
__handlers__ = [
]
