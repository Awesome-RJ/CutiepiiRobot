"""
Language Selection Module
Allows users to change bot language
"""

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from Cutiepii_Robot.langs import AVAILABLE_LANGUAGES, get_string
from Cutiepii_Robot.modules.sql import lang_sql
from Cutiepii_Robot.modules.helper_funcs.chat_status import user_admin


async def get_user_lang(update: Update) -> str:
    """Get user's preferred language."""
    chat_id = update.effective_chat.id if update.effective_chat else None
    user_id = update.effective_user.id if update.effective_user else None
    return lang_sql.get_lang(chat_id, user_id)


@cutiepii_cmd(command=["language", "lang"], can_disable=True)
async def language_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection menu."""
    chat = update.effective_chat
    user = update.effective_user
    
    # Get current language
    current_lang = lang_sql.get_lang(chat.id, user.id)
    
    # Create keyboard with language options
    buttons = []
    for lang_code, lang_name in AVAILABLE_LANGUAGES.items():
        # Add checkmark for current language
        label = f"✅ {lang_name}" if lang_code == current_lang else lang_name
        buttons.append([InlineKeyboardButton(label, callback_data=f"setlang_{lang_code}")])
    
    # Add close button
    buttons.append([InlineKeyboardButton("❌ Close", callback_data="setlang_close")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    text = get_string(current_lang, "language.select")
    if text == "String not found: language.select":
        text = (
            "🌐 *Language Selection*\n\n"
            "Choose your preferred language for the bot.\n"
            "This will change all bot messages and help text to your selected language."
        )
    
    await update.effective_message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


@user_admin
@cutiepii_callback(pattern=r"^setlang_")
async def set_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection."""
    query = update.callback_query
    await query.answer()
    
    chat = update.effective_chat
    user = update.effective_user
    
    # Parse callback data
    data = query.data.split("_")
    
    if len(data) < 2:
        return
    
    if data[1] == "close":
        await query.message.delete()
        return
    
    lang_code = data[1]
    
    # Validate language code
    if lang_code not in AVAILABLE_LANGUAGES:
        await query.answer("❌ Invalid language!", show_alert=True)
        return
    
    # Set language (prefer chat language in groups)
    if chat.type in ["group", "supergroup"]:
        lang_sql.set_chat_lang(chat.id, lang_code)
    else:
        lang_sql.set_user_lang(user.id, lang_code)
    
    # Get success message in new language
    success_text = get_string(lang_code, "language.changed")
    if success_text == "String not found: language.changed":
        success_text = f"✅ Language changed to {AVAILABLE_LANGUAGES[lang_code]}!"
    
    await query.answer(success_text, show_alert=True)
    
    # Update the keyboard to show new selection
    buttons = []
    for code, name in AVAILABLE_LANGUAGES.items():
        label = f"✅ {name}" if code == lang_code else name
        buttons.append([InlineKeyboardButton(label, callback_data=f"setlang_{code}")])
    
    buttons.append([InlineKeyboardButton("❌ Close", callback_data="setlang_close")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    # Update message
    text = get_string(lang_code, "language.select")
    if text == "String not found: language.select":
        text = (
            "🌐 *Language Selection*\n\n"
            "Choose your preferred language for the bot.\n"
            "This will change all bot messages and help text to your selected language."
        )
    
    try:
        await query.message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        pass


@cutiepii_cmd(command="currentlang")
async def get_current_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show current language."""
    chat = update.effective_chat
    user = update.effective_user
    
    lang_code = lang_sql.get_lang(chat.id, user.id)
    lang_name = AVAILABLE_LANGUAGES.get(lang_code, "English 🇬🇧")
    
    text = f"🌐 *Current Language:* {lang_name}"
    
    await update.effective_message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


@cutiepii_callback(pattern=r"^change_lang$")
async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection menu callback."""
    query = update.callback_query
    await query.answer()
    
    chat = update.effective_chat
    user = update.effective_user
    current_lang = lang_sql.get_lang(chat.id, user.id)
    
    buttons = []
    for lang_code, lang_name in AVAILABLE_LANGUAGES.items():
        label = f"✅ {lang_name}" if lang_code == current_lang else lang_name
        buttons.append([InlineKeyboardButton(label, callback_data=f"setlang_{lang_code}")])
    
    buttons.append([InlineKeyboardButton("Back to Help", callback_data="help_back", style="primary")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    text = get_string(current_lang, "language.select")
    if text == "String not found: language.select":
        text = (
            "🌐 *Language Selection*\n\n"
            "Choose your preferred language for the bot.\n"
            "This will change all bot messages and help text to your selected language."
        )
        
    await query.message.edit_text(
        text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )


__help__ = True

__mod_name__ = "Language Selection"
