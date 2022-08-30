"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, [ https://github.com/Awesome-RJ ]
Copyright (c) 2021-2022, Yūki • Black Knights Union, [ https://github.com/Awesome-RJ/CutiepiiRobot ]

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
import json
import importlib
import time
import re
import traceback
import Cutiepii_Robot.modules.sql.users_sql as sql

from sys import argv
from typing import Optional

from Cutiepii_Robot import (
    DONATION_LINK,
    LOGGER,
    OWNER_ID,
    PORT,
    TOKEN,
    WEBHOOK,
    SUPPORT_CHAT,
    HELP_IMG,
    GROUP_START_IMG,
    CUTIEPII_PTB,
    StartTime,
    pgram,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from Cutiepii_Robot.modules import ALL_MODULES
from Cutiepii_Robot.modules.helper_funcs.chat_status import is_user_admin
from Cutiepii_Robot.modules.helper_funcs.misc import paginate_modules
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
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
from telegram.ext import (CallbackContext, CallbackContext, filters,
                          CallbackQueryHandler, MessageHandler)

from telegram.helpers import escape_markdown
from pyrogram import idle


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(
            seconds, 24)
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


HELP_MSG = "Click the button below to get help manu in your pm."
START_MSG = "I'm awake already!\n<b>Haven't slept since:</b> <code>{}</code>"

PM_START_TEXT = """
────「 [{}](https://telegra.ph/file/85581d42f2b95ff65fc06.jpg) 」────

*Hola! {},*
*I am an Anime themed advance group management bot with a lot of Cool Features.*
➖➖➖➖➖➖➖➖➖➖➖➖➖
❍ *Uptime:* `{}`
❍ `{}` *users, across* `{}` *chats.*
➖➖➖➖➖➖➖➖➖➖➖➖➖
➛ Try The Help Buttons Below To Know My Abilities ××
"""

buttons = [
    [
        InlineKeyboardButton(
            text="Add Cutiepii To Your Group",
            url="https://telegram.dog/Cutiepii_Robot?startgroup=true")
    ],
    [
        InlineKeyboardButton(text="[► Help ◄]", callback_data="help_back"),
        InlineKeyboardButton(text="❔ Chit Chat",
                             url="https://telegram.dog/GIrlsBoysXD"),
        InlineKeyboardButton(text="[► Inline ◄]",
                             switch_inline_query_current_chat=""),
    ],
    [
        InlineKeyboardButton(text="🚑 Support",
                             url=f"https://telegram.dog/{SUPPORT_CHAT}"),
        InlineKeyboardButton(text="📢 Updates",
                             url="https://telegram.dog/Black_Knights_Union")
    ],
]

HELP_STRINGS = """
*Main* commands available:
➛ /help: PM's you this message.
➛ /help <module name>: PM's you info about that module.
➛ /donate: information on how to donate!
➛ /settings:
   ➛ in PM: will send you your settings for all supported modules.
   ➛ in a group: will redirect you to pm, with all that chat's settings.
"""

DONATE_STRING = """❂ I'm Free for Everyone ❂"""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}
GDPR = []

for module_name in ALL_MODULES:
    imported_module = importlib.import_module(
        f"Cutiepii_Robot.modules.{module_name}")

    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception(
            "Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__gdpr__"):
        GDPR.append(imported_module)

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
async def send_help(context: CallbackContext, chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


async def test(update: Update):
    # pLOGGER.debug(eval(str(update)))
    # await update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    await update.effective_message.reply_text("This person edited a message")
    LOGGER.debug(update.effective_message)


async def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup([[
                        InlineKeyboardButton(text="[► Back ◄]",
                                             callback_data="help_back")
                    ]]),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = await CUTIEPII_PTB.bot.getChat(match[1])

                if await is_user_admin(update, update.effective_user.id):
                    send_settings(match[1], update.effective_user.id, False)
                else:
                    send_settings(match[1], update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            await update.effective_message.reply_text(
                PM_START_TEXT.format(escape_markdown(context.bot.first_name),
                                     escape_markdown(first_name),
                                     escape_markdown(uptime), sql.num_users(),
                                     sql.num_chats()),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
            )
    else:
        update.effective_message.reply_animation(
            GROUP_START_IMG,
            caption=
            f"<b>Yes, Darling I'm alive!\nHaven't sleep since</b>: <code>{uptime}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    text="🚑 Support",
                    url=f"https://telegram.dog/{SUPPORT_CHAT}",
                ),
                InlineKeyboardButton(
                    text="📢 Updates",
                    url="https://telegram.dog/Black_Knights_Union",
                ),
            ]]),
        )


async def error_handler(update: Update, context: CallbackContext):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:",
                 exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error,
                                         context.error.__traceback__)
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = f"An exception was raised while handling an update\n<pre>update = {html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False))}</pre>\n\n<pre>{html.escape(tb)}</pre>"

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    await context.bot.send_message(chat_id=OWNER_ID,
                                   text=message,
                                   parse_mode=ParseMode.HTML)


# for test purposes
async def error_callback(_, context: CallbackContext):
    try:
        raise context.error
    except (BadRequest):
        pass
        # remove update.message.chat_id from conversation list
    except TimedOut:
        pass
        # handle slow connection problems
    except NetworkError:
        pass
        # handle other connection problems
    except ChatMigrated:
        pass
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        pass
        # handle all other telegram related errors


async def help_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    with contextlib.suppress(BadRequest):
        if mod_match:
            module = mod_match[1]
            text = (f"╔═━「 *{HELPABLE[module].__mod_name__}* module: 」\n" +
                    HELPABLE[module].__help__)

            await query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(text="[► Back ◄]",
                                         callback_data="help_back"),
                    InlineKeyboardButton(
                        text="[► Support ◄]",
                        url="https://t.me/Black_Knights_Union_Support")
                ]]),
            )

        elif prev_match:
            curr_page = int(prev_match[1])
            await query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")),
            )

        elif next_match:
            next_page = int(next_match[1])
            await query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")),
            )

        elif back_match:
            await query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")),
            )

        # ensure no spinny white circle
        await context.bot.answer_callback_query(query.id)
        # await query.message.delete()


async def cutiepii_callback_data(update: Update,
                                 context: CallbackContext) -> None:
    query = update.callback_query
    uptime = get_readable_time((time.time() - StartTime))
    if query.data == "cutiepii_":
        await query.message.edit_text(
            text="""CallBackQueriesData Here""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(text="[► Back ◄]",
                                     callback_data="cutiepii_back")
            ]]),
        )
    elif query.data == "cutiepii_back":
        first_name = update.effective_user.first_name
        await query.message.edit_text(
            PM_START_TEXT.format(escape_markdown(context.bot.first_name),
                                 escape_markdown(first_name),
                                 escape_markdown(uptime), sql.num_users(),
                                 sql.num_chats()),
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode=ParseMode.MARKDOWN,
            timeout=60,
            disable_web_page_preview=False,
        )


async def get_help(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:

        update.effective_message.reply_photo(
            HELP_IMG,
            HELP_MSG,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    text="Open In Private Chat",
                    url=f"t.me/{context.bot.username}?start=help",
                )
            ]]),
        )

        return

    if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (f" 〔 *{HELPABLE[module].__mod_name__}* 〕\n" +
                HELPABLE[module].__help__)

        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup([[
                InlineKeyboardButton(text="[► Back ◄]",
                                     callback_data="help_back")
            ]]),
        )

    else:
        send_help(chat.id, HELP_STRINGS)


async def send_settings(context: CallbackContext,
                        chat_id,
                        user_id,
                        user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                f"*{mod.__mod_name__}*:\n{mod.__user_settings__(user_id)}"
                for mod in USER_SETTINGS.values())

            await context.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            await context.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    elif CHAT_SETTINGS:
        chat_name = await CUTIEPII_PTB.bot.getChat(chat_id).title
        await context.bot.send_message(
            user_id,
            text=
            f"Which module would you like to check {chat_name}'s settings for?",
            reply_markup=InlineKeyboardMarkup(
                paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)),
        )
    else:
        await context.bot.send_message(
            user_id,
            "Seems like there aren't any chat settings available :'(\nSend this "
            "in a group chat you're admin in to find its current settings!",
            parse_mode=ParseMode.MARKDOWN,
        )


async def settings_button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match[1]
            module = mod_match[2]
            chat = await bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            try:
                keyboard = CHAT_SETTINGS[module].__chat_settings_buttons__(
                    chat_id, user.id)
            except AttributeError:
                keyboard = []
            kbrd = InlineKeyboardMarkup(
                InlineKeyboardButton(text="Back",
                                     callback_data=f"stngs_back({chat_id}"))
            keyboard.append(kbrd)
            await query.message.edit_text(text=text,
                                          parse_mode=ParseMode.MARKDOWN,
                                          reply_markup=keyboard)
        elif prev_match:
            chat_id = prev_match[1]
            curr_page = int(prev_match[2])
            chat = await bot.get_chat(chat_id)
            await query.message.reply_text(
                f"Hi there! There are quite a few settings for {chat.title} - go ahead and pick what you're interested in.",
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1,
                                     CHAT_SETTINGS,
                                     "stngs",
                                     chat=chat_id)),
            )

        elif next_match:
            chat_id = next_match[1]
            next_page = int(next_match[2])
            chat = await bot.get_chat(chat_id)
            await query.message.edit_text(
                f"Hi there! There are quite a few settings for {chat.title} - go ahead and pick what you're interested in.",
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1,
                                     CHAT_SETTINGS,
                                     "stngs",
                                     chat=chat_id)),
            )

        elif back_match:
            chat_id = back_match[1]
            chat = await bot.get_chat(chat_id)
            await query.message.edit_text(
                text=
                f"Hi there! There are quite a few settings for {escape_markdown(chat.title)} - go ahead and pick what you're interested in.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)),
            )

        # ensure no spinny white circle
        await bot.answer_callback_query(query.id)
    except BadRequest as excp:
        if excp.message not in [
                "Message is not modified",
                "Query_id_invalid",
                "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s",
                             str(query.data))


async def get_settings(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type == chat.PRIVATE:
        send_settings(chat.id, user.id, True)

    elif await is_user_admin(update, user.id):
        text = "Click here to get this chat's settings, as well as yours."
        await msg.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    text="Settings",
                    url=
                    f"https://telegram.dog/{context.bot.username}?start=stngs_{chat.id}",
                )
            ]]),
        )

    else:
        text = "Click here to check your settings."


async def donate(update: Update, context: CallbackContext) -> None:
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    if chat.type == "private":
        await update.effective_message.reply_text(
            DONATE_STRING,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True)

        if OWNER_ID != 2131857711 and DONATION_LINK:
            await update.effective_message.reply_text(
                f"You can also donate to the person currently running me [here]({DONATION_LINK})",
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
                text=
                "I'm free for everyone❤️\njust donate by subs channel, Don't forget to join the support group.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        text="📢 Updates",
                        url="https://telegram.dog/Black_Knights_Union"),
                    InlineKeyboardButton(
                        text="🚑 Support",
                        url="https://telegram.dog/Black_Knights_Union_Support")
                ]]),
            )
        except Forbidden:
            await update.effective_message.reply_text(
                "Contact me in PM first to get donation information.")


async def migrate_chats(update: Update):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", old_chat, new_chat)
    for mod in MIGRATEABLE:
        with contextlib.suppress(KeyError, AttributeError):
            mod.__migrate__(old_chat, new_chat)
    LOGGER.info("Successfully migrated!")


def main():
    CUTIEPII_PTB.add_error_handler(error_callback)
    CUTIEPII_PTB.add_handler(
        DisableAbleCommandHandler("test", test, block=False))
    CUTIEPII_PTB.add_handler(
        DisableAbleCommandHandler("start", start, block=False))

    CUTIEPII_PTB.add_handler(
        DisableAbleCommandHandler("help", get_help, block=False))
    CUTIEPII_PTB.add_handler(
        CallbackQueryHandler(help_button, pattern=r"help_.*", block=False))

    CUTIEPII_PTB.add_handler(
        DisableAbleCommandHandler("settings", get_settings, block=False))
    CUTIEPII_PTB.add_handler(
        CallbackQueryHandler(settings_button, pattern=r"stngs_", block=False))

    CUTIEPII_PTB.add_handler(
        CallbackQueryHandler(cutiepii_callback_data,
                             pattern=r"cutiepii_",
                             block=False))
    CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("donate", donate))
    CUTIEPII_PTB.add_handler(
        MessageHandler(filters.StatusUpdate.MIGRATE,
                       migrate_chats,
                       block=False))

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        CUTIEPII_PTB.run_webhook(listen="127.0.0.1", port=PORT, url_path=TOKEN)

    else:
        CUTIEPII_PTB.run_polling(allowed_updates=Update.ALL_TYPES,
                                 stop_signals=None)
        LOGGER.info(
            "Cutiepii Robot started, Using long polling. | BOT: [@Cutiepii_Robot]"
        )


"""
try:
    ubot.start()
except BaseException:
    LOGGER.debug("Userbot Error! Have you added a STRING_SESSION in deploying??")
    sys.exit(1)
"""

if __name__ == "__main__":
    LOGGER.info(f"Successfully loaded modules: {str(ALL_MODULES)}")
    pgram.start()
    main()
    idle()
