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

import contextlib
import html
import os
import json
import importlib
import threading
import time
import re
import sys
import traceback
import logging
import asyncio
import Cutiepii_Robot.modules.sql.users_sql as sql


from sys import argv
from aiohttp import web
from typing import Optional

from Cutiepii_Robot import (
    ALLOW_EXCL,
    CERT_PATH,
    DONATION_LINK,
    LOGGER,
    OWNER_ID,
    PORT,
    TOKEN,
    URL,
    WEBHOOK,
    BIND_ADDRESS,
    SUPPORT_CHAT,
    BOT_USERNAME,
    BOT_NAME,
    HELP_IMG,
    GROUP_START_IMG,
    UPDATES_CHANNEL,
    dispatcher,
    StartTime,
    telethn,
    updater,
    aiohttpsession,
    http,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from Cutiepii_Robot.events import register
from Cutiepii_Robot.modules import ALL_MODULES
from Cutiepii_Robot.modules.helper_funcs.alternate import typing_action
from Cutiepii_Robot.modules.helper_funcs.misc import paginate_modules
from Cutiepii_Robot.modules.helper_funcs.chat_status import user_is_admin
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.sql import lang_sql
from Cutiepii_Robot.langs import get_help_text, get_string
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Forbidden,
)
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler,
    filters,
    MessageHandler,
)

from telegram.ext import (
    ApplicationHandlerStop as DispatcherHandlerStop,
)
from telegram.helpers import escape_markdown
# Pyrogram imports removed
from telethon import Button, events


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += f"{time_list.pop()}, "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time

HELP_MSG = "Click the button below to open the help menu in your private chat."
PM_START_TEXT = """
<b>Hola! {1},</b><a href="https://files.catbox.moe/ekfmos.mp4">‎</a>
I am <b>{0}</b>, a premium, anime-themed group management bot designed to keep your chats safe, active, and fun.

<i>Use the buttons below to explore my commands and settings!</i>
"""

buttons = [
    [
        InlineKeyboardButton(
            text=f"Add {BOT_NAME} To Your Group",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=true"
        )
    ],
    [
        InlineKeyboardButton(text="Help and Commands", callback_data="help_back"),
        InlineKeyboardButton(text="Inline Search", switch_inline_query_current_chat="")
    ],
    [
        InlineKeyboardButton(text="Support Group", url=f"https://t.me/{SUPPORT_CHAT}"),
        InlineKeyboardButton(text="Channel Updates", url=f"https://t.me/{UPDATES_CHANNEL}")
    ]
]


def get_help_strings(lang_code: str = "en") -> str:
    """Get localized help strings."""
    try:
        help_text = get_string(lang_code, "help.main")
        if help_text and not help_text.startswith("String not found"):
            return help_text
    except:
        pass
    
    # Fallback to English default
    return """<b>Main</b> commands available:
➛ <code>/help</code>: PM's you this message.
➛ <code>/help &lt;module name&gt;</code>: PM's you info about that module.
➛ <code>/donate</code>: information on how to donate!
➛ <code>/settings</code>:
   ❍ in PM: will send you your settings for all supported modules.
   ❍ in a group: will redirect you to pm, with all that chat's settings.
"""

HELP_STRINGS = get_help_strings()  # Default English

DONATE_STRING = "❂ I'm Free for Everyone ❂"

NORMALIZE_MODULE_KEY = {
    "admins": "admin",
    "bans/mutes": "bans",
    "anti-flood": "antiflood",
    "blacklists": "blacklist",
    "language selection": "language",
    "raid mode": "raid",
    "disabling": "disable",
    "muting": "muting",
    "private notes": "privatenotes",
    "anime hub": "anime",
    "social fun": "fun",
    "games manager": "games",
    "media monetization": "media",
    "blacklist chats": "blacklist_chats",
    "dev utils": "devutils",
    "feeds": "rss_feeds",
    "force subscribe": "forcesubscribe",
    "greetings": "welcome",
    "confession": "confession",
    "anti-nsfw": "antinsfw",
}

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}



for module_name in ALL_MODULES:
    imported_module = importlib.import_module("Cutiepii_Robot.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__.split('.')[-1].title()

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module


# do not async
async def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    await dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    
    try:
        if update.effective_chat.type == "private":
            if len(args) >= 1:
                if args[0].lower() == "help":
                    # Get user's language
                    user_id = update.effective_user.id if update.effective_user else None
                    chat_id = update.effective_chat.id
                    lang_code = lang_sql.get_lang(chat_id=chat_id, user_id=user_id)
                    help_strings = get_help_strings(lang_code)
                    await send_help(update.effective_chat.id, help_strings)
                    
                elif args[0].lower().startswith("ghelp_"):
                    mod = args[0].lower().split("_", 1)[1]
                    if not HELPABLE.get(mod, False):
                        return
                    
                    # Get user's language
                    user_id = update.effective_user.id if update.effective_user else None
                    chat_id = update.effective_chat.id
                    lang_code = lang_sql.get_lang(chat_id=chat_id, user_id=user_id)
                    
                    # Try to get localized help text
                    help_text = get_help_text(lang_code, mod)
                    
                    # Fallback to __help__ if not found in language file
                    if not help_text or help_text.startswith("String not found"):
                        help_text = HELPABLE[mod].__help__
                    
                    from Cutiepii_Robot.modules.helper_funcs.help_formatter import format_help_menu
                    help_text = format_help_menu(HELPABLE[mod].__mod_name__, help_text)
                    
                    await send_help(
                        update.effective_chat.id,
                        help_text,
                        InlineKeyboardMarkup(
                            [[InlineKeyboardButton(text="Back", callback_data="help_back", style="primary")]]
                        )
                    )

                elif args[0].lower().startswith("stngs_"):
                    try:
                        match = re.match("stngs_(.*)", args[0].lower())
                        chat = await dispatcher.bot.get_chat(match.group(1))
                        
                        # Check if user is admin
                        member = await context.bot.get_chat_member(chat.id, update.effective_user.id)
                        is_admin = member.status in ['administrator', 'creator']
                        
                        await send_settings(match.group(1), update.effective_user.id, not is_admin)
                    except Exception as e:
                        LOGGER.error(f"Error in settings: {e}")
                        await update.effective_message.reply_text("Error accessing settings.")

                elif args[0].lower().startswith("report_"):
                    from Cutiepii_Robot.modules.confession import handle_report_deeplink
                    await handle_report_deeplink(update, context, args[0])
                    return

                elif args[0].lower().startswith("reveal_"):
                    from Cutiepii_Robot.modules.confession import handle_reveal_deeplink
                    await handle_reveal_deeplink(update, context, args[0])
                    return

                elif args[0].lower().startswith("addblacklist_"):
                    try:
                        match = re.match("addblacklist_(.*)", args[0].lower())
                        connect_chat = int(match.group(1))
                        chat = await dispatcher.bot.get_chat(connect_chat)
                        
                        # Check if user is admin
                        member = await context.bot.get_chat_member(chat.id, update.effective_user.id)
                        is_admin = member.status in ['administrator', 'creator']
                        
                        import Cutiepii_Robot.modules.sql.connection_sql as conn_sql
                        isallow = conn_sql.allow_connect_to_chat(connect_chat)
                        ismember = member.status == "member"
                        
                        if isadmin or (isallow and ismember) or (update.effective_user.id in SUDO_USERS):
                            connection_status = conn_sql.connect(
                                update.effective_user.id, connect_chat
                            )
                            if connection_status:
                                await update.effective_message.reply_text(
                                    f"Successfully connected to <b>{html.escape(chat.title)}</b>.\n"
                                    f"You can now add blacklist triggers using:\n"
                                    f"<code>/addblacklist trigger1, trigger2</code>",
                                    parse_mode=ParseMode.HTML
                                )
                            else:
                                await update.effective_message.reply_text("Failed to connect to the group.")
                        else:
                            await update.effective_message.reply_text("Connection failed! You must be an administrator in that chat, or connection settings must be set to allow members.")
                    except Exception as e:
                        LOGGER.error(f"Error in addblacklist start parameter: {e}")
                        await update.effective_message.reply_text("Error connecting to chat.")

                elif args[0][1:].isdigit() and "rules" in IMPORTED:
                    await IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

                elif args[0].lower() == "nations":
                    if "disasters" in IMPORTED:
                        await update.effective_message.reply_text(
                            IMPORTED["disasters"].nations_text,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True,
                        )

                elif args[0].lower().startswith("note_"):
                    if "notes" in IMPORTED:
                        try:
                            parts = args[0].split("_", 2)
                            if len(parts) >= 3:
                                chat_id = int(parts[1])
                                if chat_id > 0:
                                    chat_id = -chat_id
                                note_name = parts[2]
                                await IMPORTED["notes"].get(update, context, note_name, show_none=True, note_chat_id=chat_id)
                        except Exception as e:
                            LOGGER.error(f"Error resolving start note parameter: {e}")

                elif args[0].lower() == "markdownhelp":
                    import Cutiepii_Robot.modules.misc as misc
                    await misc.markdown_help_sender(update)

            else:
                first_name = update.effective_user.first_name
                try:
                    await update.effective_message.reply_text(
                        PM_START_TEXT.format(
                            html.escape(context.bot.first_name),
                            html.escape(first_name),
                            html.escape(uptime),
                            sql.num_users(),
                            sql.num_chats()
                        ),
                        reply_markup=InlineKeyboardMarkup(buttons),
                        parse_mode=ParseMode.HTML,
                    )
                except Exception as e:
                    LOGGER.error(f"Error sending start message: {e}")
        else:
            # Group start message
            try:
                keyboard = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="🚑 Support", url=f"https://t.me/{SUPPORT_CHAT}"),
                            InlineKeyboardButton(text="📢 Updates", url="https://t.me/Black_Knights_Union"),
                        ]
                    ]
                )
                caption = f"<b>Yes, Darling I'm alive!\n\nHaven't sleep since</b>: <code>{uptime}</code>"
                
                is_animation = any(str(GROUP_START_IMG).lower().endswith(x) for x in (".gif", ".mp4"))
                methods = [
                    update.effective_message.reply_animation if is_animation else update.effective_message.reply_photo,
                    update.effective_message.reply_photo if is_animation else update.effective_message.reply_animation,
                ]
                
                for method in methods:
                    try:
                        await method(
                            GROUP_START_IMG,
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                            reply_markup=keyboard,
                        )
                        break
                    except Exception:
                        pass
                else:
                    await update.effective_message.reply_text(
                        text=caption,
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard,
                    )
            except Exception as e:
                LOGGER.error(f"Error in group start: {e}")
    
    except Exception as e:
        LOGGER.error(f"Error in start handler: {e}")
        try:
            await update.effective_message.reply_text("An error occurred. Please try again later.")
        except:
            pass




async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    # Get user's language
    user_id = query.from_user.id if query.from_user else None
    chat_id = query.message.chat.id if query.message else None
    lang_code = lang_sql.get_lang(chat_id=chat_id, user_id=user_id)

    with contextlib.suppress(BadRequest):
        if mod_match:
            module = mod_match.group(1)
            module_name = HELPABLE[module].__mod_name__
            
            # Try to get localized help text
            module_key = NORMALIZE_MODULE_KEY.get(module.lower(), module.lower())
            help_text = get_help_text(lang_code, module_key)
            
            # Fallback to __help__ if not found in language file
            if not help_text or help_text.startswith("String not found"):
                help_text = HELPABLE[module].__help__
            
            from Cutiepii_Robot.modules.helper_funcs.help_formatter import format_help_menu
            help_text = format_help_menu(module_name, help_text)
            
            if not isinstance(help_text, str):
                help_text = "No help text available."
            
            text = (
                "<b>{} Module</b>\n\n".format(module_name)
                + help_text
            )
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="Back", callback_data="help_back", style="primary"),
                     InlineKeyboardButton(text="Support", url=f"https://t.me/{SUPPORT_CHAT}")]]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            help_strings = get_help_strings(lang_code)
            await query.message.edit_text(
                text=help_strings,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            help_strings = get_help_strings(lang_code)
            await query.message.edit_text(
                text=help_strings,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            help_strings = get_help_strings(lang_code)
            await query.message.edit_text(
                text=help_strings,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        pass
        # query.message.delete()



async def cutiepii_callback_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uptime = get_readable_time((time.time() - StartTime))
    if query.data == "cutiepii_":
        await query.message.edit_text(
            text="""CallBackQueriesData Here""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Back", callback_data="cutiepii_back")
                 ]
                ]
            ),
        )
    elif query.data == "cutiepii_back":
        first_name = update.effective_user.first_name
        await query.message.edit_text(
            PM_START_TEXT.format(
                html.escape(context.bot.first_name),
                html.escape(first_name),
                html.escape(uptime),
                sql.num_users(),
                sql.num_chats()),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.HTML,
        )


@typing_action
async def get_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user
    args = update.effective_message.text.split(None, 1)

    # Get user's language
    lang_code = lang_sql.get_lang(chat_id=chat.id, user_id=user.id if user else None)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Open In Private Chat",
                        url="https://t.me/{}?start=help".format(BOT_USERNAME),
                    )
                ]
            ]
        )
        try:
            await update.effective_message.reply_animation(
                animation="https://files.catbox.moe/nrgudj.mp4",
                caption=HELP_MSG,
                reply_markup=keyboard,
            )
        except Exception:
            try:
                await update.effective_message.reply_photo(
                    HELP_IMG,
                    caption=HELP_MSG,
                    reply_markup=keyboard,
                )
            except Exception:
                await update.effective_message.reply_text(
                    HELP_MSG,
                    reply_markup=keyboard,
                )
        return

    if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        module_name = HELPABLE[module].__mod_name__
        
        # Try to get localized help text
        module_key = NORMALIZE_MODULE_KEY.get(module.lower(), module.lower())
        help_text = get_help_text(lang_code, module_key)
        
        # Fallback to __help__ if not found in language file
        if not help_text or help_text.startswith("String not found"):
            help_text = HELPABLE[module].__help__
        
        from Cutiepii_Robot.modules.helper_funcs.help_formatter import format_help_menu
        help_text = format_help_menu(module_name, help_text)
        
        text = (
            "<b>{} Module</b>\n\n".format(module_name)
            + help_text
        )
        await send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="help_back", style="primary")]]
            ),
        )

    else:
        help_strings = get_help_strings(lang_code)
        await send_help(chat.id, help_strings)



async def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            await dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            await dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    elif CHAT_SETTINGS:
        chat = await dispatcher.bot.get_chat(chat_id)
        chat_name = chat.title
        await dispatcher.bot.send_message(
            user_id,
            text=f"Which module would you like to check {chat_name}'s settings for?",
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
            ),
        )
    else:
        await dispatcher.bot.send_message(
            user_id,
            "Seems like there aren't any chat settings available :'(\nSend this "
            "in a group chat you're admin in to find its current settings!",
            parse_mode=ParseMode.MARKDOWN,
        )


async def settings_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = await bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + await CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Back",
                                callback_data=f"stngs_back({chat_id})",
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = await bot.get_chat(chat_id)
            await query.message.edit_text(
                text=f"Hi there! There are quite a few settings for {chat.title} - go ahead and pick what you're interested in.",
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = await bot.get_chat(chat_id)
            await query.message.edit_text(
                text=f"Hi there! There are quite a few settings for {chat.title} - go ahead and pick what you're interested in.",
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = await bot.get_chat(chat_id)
            await query.message.edit_text(
                text=f"Hi there! There are quite a few settings for {escape_markdown(chat.title)} - go ahead and pick what you're interested in.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        pass
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


async def get_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type == chat.PRIVATE:
        await send_settings(chat.id, user.id, True)

    elif await user_is_admin(update, user.id):
        text = "Click here to get this chat's settings, as well as yours."
        await msg.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Settings",
                            url="https://t.me/{}?start=stngs_{}".format(
                                context.bot.username, chat.id
                            ),
                        )
                    ]
                ]
            ),
        )
    else:
        text = "Click here to check your settings."


async def donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    if chat.type == "private":
        await update.effective_message.reply_text(
            DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )

        if OWNER_ID != 2131857711 and DONATION_LINK:
            await update.effective_message.reply_text(
                "You can also donate to the person currently running me "
                "[here]({})".format(DONATION_LINK),
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        try:
            await bot.send_message(
                user.id,
                DONATE_STRING,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

            await update.effective_message.reply_text(
                text="I'm free for everyone❤️\njust donate by subs channel, Don't forget to join the support group.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(text="📢 Updates", url="https://t.me/Black_Knights_Union"),
                      InlineKeyboardButton(text="🚑 Support", url="https://t.me/Black_Knights_Union_Support")]]
                ),
            )       
        except Forbidden:
            await update.effective_message.reply_text(
                "Contact me in PM first to get donation information."
            )


async def migrate_chats(update: Update, _: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        with contextlib.suppress(KeyError, AttributeError):
            import inspect
            if inspect.iscoroutinefunction(mod.__migrate__):
                await mod.__migrate__(old_chat, new_chat)
            else:
                mod.__migrate__(old_chat, new_chat)


    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


async def main():
    """Main bot initialization and startup"""
    try:
        LOGGER.info("[CUTIEPII]: Registering handlers...")
        
        # Core handlers
        start_handler = DisableAbleCommandHandler("start", start)
        help_handler = DisableAbleCommandHandler("help", get_help)
        help_callback_handler = CallbackQueryHandler(help_button, pattern=r"help_.*")
        settings_handler = DisableAbleCommandHandler("settings", get_settings)
        settings_callback_handler = CallbackQueryHandler(settings_button, pattern=r"stngs_")
        data_callback_handler = CallbackQueryHandler(cutiepii_callback_data, pattern=r"cutiepii_")
        donate_handler = DisableAbleCommandHandler("donate", donate)
        migrate_handler = MessageHandler(filters.StatusUpdate.MIGRATE, migrate_chats)

        # Add handlers
        dispatcher.add_handler(start_handler)
        dispatcher.add_handler(help_handler)
        dispatcher.add_handler(data_callback_handler)
        dispatcher.add_handler(settings_handler)
        dispatcher.add_handler(help_callback_handler)
        dispatcher.add_handler(settings_callback_handler)
        dispatcher.add_handler(migrate_handler)
        dispatcher.add_handler(donate_handler)

        LOGGER.info("[CUTIEPII]: ✅ Handlers registered successfully")
        
        # Allowed update types
        allowed_updates = [
            'message', 'edited_message', 'callback_query', 'my_chat_member',
            'chat_member', 'chat_join_request', 'channel_post', 'edited_channel_post', 'inline_query'
        ]

        # Start bot
        if WEBHOOK:
            LOGGER.info("[CUTIEPII]: Starting bot with webhooks...")
            LOGGER.info(f"[CUTIEPII]: Webhook URL: {URL + TOKEN}")
            await updater.initialize()
            await updater.start()
            await updater.start_webhook(
                listen=BIND_ADDRESS,
                port=PORT,
                url_path=TOKEN,
                allowed_updates=allowed_updates,
                webhook_url=URL + TOKEN,
                cert=CERT_PATH
            )
            LOGGER.info("[CUTIEPII]: ✅ Webhook started successfully")
        else:
            LOGGER.info("[CUTIEPII]: Starting bot with long polling...")
            await updater.initialize()
            await updater.start()
            await updater.updater.start_polling(
                timeout=15,
                allowed_updates=allowed_updates,
                drop_pending_updates=True
            )
            LOGGER.info(f"[CUTIEPII]: ✅ Bot started successfully! | @{BOT_USERNAME}")

        # Notify owner
        try:
            await dispatcher.bot.send_message(
                OWNER_ID,
                f"🤖 <b>Bot Started Successfully!</b>\n\n"
                f"<b>Username:</b> @{BOT_USERNAME}\n"
                f"<b>Uptime:</b> Just started\n"
                f"<b>Modules Loaded:</b> {len(IMPORTED)}",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            LOGGER.warning(f"[CUTIEPII]: Could not send startup message to owner: {e}")

        # Register bot commands dynamically
        try:
            from telegram import BotCommand
            main_commands = [
                BotCommand("start", "Start the bot"),
                BotCommand("help", "Show help menu and list of modules"),
                BotCommand("settings", "Manage group settings"),
                BotCommand("rules", "View group rules"),
                BotCommand("id", "Get user or chat ID"),
                BotCommand("info", "Get user profile details"),
                BotCommand("hug", "Hug someone"),
                BotCommand("neko", "Get a random neko image/gif"),
                BotCommand("pat", "Pat someone"),
                BotCommand("slap", "Slap someone"),
                BotCommand("cuddle", "Cuddle someone"),
                BotCommand("kiss", "Kiss someone"),
                BotCommand("poke", "Poke someone"),
            ]
            await dispatcher.bot.set_my_commands(main_commands)
            LOGGER.info("[CUTIEPII]: ✅ Bot commands registered successfully on Telegram")
        except Exception as e:
            LOGGER.warning(f"[CUTIEPII]: Could not register bot commands: {e}")
        
        # Start nightmode scheduler if module is loaded
        try:
            # Check both lowercase and original case
            nightmode_module = None
            if "nightmode" in IMPORTED:
                nightmode_module = IMPORTED["nightmode"]
            elif "NightMode" in IMPORTED:
                nightmode_module = IMPORTED["NightMode"]
            
            if nightmode_module and hasattr(nightmode_module, "start_nightmode_scheduler"):
                nightmode_module.start_nightmode_scheduler()
        except Exception as e:
            LOGGER.warning(f"[CUTIEPII]: Could not start nightmode scheduler: {e}")
            
        # Start ranking scheduler if module is loaded
        try:
            ranking_module = IMPORTED.get("ranking")
            if ranking_module and hasattr(ranking_module, "start_ranking_scheduler"):
                ranking_module.start_ranking_scheduler()
        except Exception as e:
            LOGGER.warning(f"[CUTIEPII]: Could not start ranking scheduler: {e}")
    
    except Exception as e:
        LOGGER.error(f"[CUTIEPII ERROR]: Failed to start bot: {e}")
        raise    

async def start_services():
    """Start web server. Tries PORT, then PORT+1..PORT+9 if port is in use."""
    try:
        LOGGER.info("[CUTIEPII]: Starting web server...")
        app = web.Application()

        async def health_check(request):
            return web.Response(text="OK")

        app.router.add_get('/', health_check)
        app.router.add_get('/health', health_check)

        server = web.AppRunner(app)
        await server.setup()

        last_err = None
        for attempt in range(10):
            try_port = PORT + attempt
            try:
                await web.TCPSite(server, BIND_ADDRESS, try_port).start()
                LOGGER.info(f"[CUTIEPII]: ✅ Web server started on {BIND_ADDRESS}:{try_port}")
                return
            except OSError as e:
                last_err = e
                if e.errno == 98:  # Address already in use
                    if attempt == 0:
                        LOGGER.warning(
                            f"[CUTIEPII]: Port {try_port} in use, trying next..."
                        )
                    continue
                raise

        LOGGER.error(
            f"[CUTIEPII ERROR]: Ports {PORT}-{PORT + 9} are in use. "
            f"Stop the process using the port (e.g. previous bot) or set PORT (e.g. export PORT=8450)."
        )
        raise last_err
    except Exception as e:
        LOGGER.error(f"[CUTIEPII ERROR]: Failed to start web services: {e}")
        raise


if __name__ == "__main__":
    try:
        from Cutiepii_Robot.utils.configdoctor import run_doctor
        run_doctor()

        LOGGER.info("=" * 50)
        LOGGER.info("[CUTIEPII]: 🚀 Starting Cutiepii Robot...")
        LOGGER.info("=" * 50)
        LOGGER.info(f"[CUTIEPII]: 📦 Loaded {len(ALL_MODULES)} modules: {', '.join(ALL_MODULES[:10])}{'...' if len(ALL_MODULES) > 10 else ''}")
        
        # Install uvloop for faster event loop execution on non-Windows systems
        try:
            import sys
            if sys.platform != "win32":
                import uvloop
                uvloop.install()
                LOGGER.info("[CUTIEPII]: 🚀 uvloop installed successfully (using high-performance event loop)")
        except ImportError:
            pass

        # Get event loop
        loop = asyncio.get_event_loop()
        
        # Start web services
        loop.run_until_complete(start_services())
        
        # Start Telethon (v1.42.0+)
        LOGGER.info("[CUTIEPII]: Starting Telethon client...")
        try:
            # Start Telethon (works with both sync and async in v1.42.0+)
            if not telethn.is_connected():
                # Use run_until_complete for async start
                loop.run_until_complete(telethn.start(bot_token=TOKEN))
            LOGGER.info("[CUTIEPII]: ✅ Telethon started (v1.42.0+)")
        except Exception as e:
            LOGGER.error(f"[CUTIEPII]: ❌ Failed to start Telethon: {e}")
            # Fallback to sync start for backward compatibility
            try:
                telethn.start(bot_token=TOKEN)
                LOGGER.warning("[CUTIEPII]: ⚠️ Using fallback Telethon start method")
            except Exception as e2:
                LOGGER.error(f"[CUTIEPII]: ❌ Telethon start failed completely: {e2}. Proceeding without Telethon.")
        
        # Start main bot
        loop.run_until_complete(main())
        
        LOGGER.info("=" * 50)
        LOGGER.info("[CUTIEPII]: ✅ Bot is now running!")
        LOGGER.info("=" * 50)
        
        # Keep the event loop running
        loop.run_forever()
        
    except KeyboardInterrupt:
        LOGGER.info("[CUTIEPII]: 👋 Bot stopped by user")
    except Exception as e:
        LOGGER.error(f"[CUTIEPII ERROR]: Fatal error during startup: {e}")
        LOGGER.exception("Full traceback:")
        sys.exit(1)
    finally:
        # Cleanup
        try:
            LOGGER.info("[CUTIEPII]: Cleaning up...")
            if aiohttpsession and not aiohttpsession.closed:
                loop.run_until_complete(aiohttpsession.close())
            if http:
                loop.run_until_complete(http.aclose())
            LOGGER.info("[CUTIEPII]: ✅ Cleanup complete")
        except:
            pass
