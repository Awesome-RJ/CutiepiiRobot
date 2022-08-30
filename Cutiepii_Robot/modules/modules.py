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

import importlib
import collections

from Cutiepii_Robot import CUTIEPII_PTB, telethn
from Cutiepii_Robot.__main__ import CHAT_SETTINGS, DATA_EXPORT, DATA_IMPORT, HELPABLE, IMPORTED, MIGRATEABLE, STATS, USER_INFO, USER_SETTINGS
from Cutiepii_Robot.modules.helper_funcs.chat_status import dev_plus, sudo_plus
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler


@dev_plus
async def load(update: Update):
    message = update.effective_message
    text = await message.text.split(" ", 1)[1]
    load_messasge = await message.reply_text(
        f"Attempting to load module : <b>{text}</b>",
        parse_mode=ParseMode.HTML,
    )

    try:
        imported_module = importlib.import_module(
            f"Cutiepii_Robot.modules.{text}")
    except Exception:
        await load_messasge.edit_text("Does that module even exist?")
        return

    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        await load_messasge.edit_text("Module already loaded.")
        return
    if "__handlers__" in dir(imported_module):
        handlers = imported_module.__handlers__
        for handler in handlers:
            if not isinstance(handler, tuple):
                CUTIEPII_PTB.add_handler(handler)
            elif isinstance(handler[0], collections.Callable):
                callback, telethon_event = handler
                telethn.add_event_handler(callback, telethon_event)
            else:
                handler_name, priority = handler
                CUTIEPII_PTB.add_handler(handler_name, priority)
    else:
        IMPORTED.pop(imported_module.__mod_name__.lower())
        await load_messasge.edit_text("The module cannot be loaded.")
        return

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

    await load_messasge.edit_text(
        f"Successfully loaded module : <b>{text}</b>",
        parse_mode=ParseMode.HTML,
    )


@dev_plus
async def unload(update: Update):
    message = update.effective_message
    text = await message.text.split(" ", 1)[1]
    unload_messasge = await message.reply_text(
        f"Attempting to unload module : <b>{text}</b>",
        parse_mode=ParseMode.HTML,
    )

    try:
        imported_module = importlib.import_module(
            f"Cutiepii_Robot.modules.{text}")
    except Exception:
        await unload_messasge.edit_text("Does that module even exist?")
        return

    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__
    if imported_module.__mod_name__.lower() in IMPORTED:
        IMPORTED.pop(imported_module.__mod_name__.lower())
    else:
        await unload_messasge.edit_text(
            "Can't unload something that isn't loaded.")
        return
    if "__handlers__" in dir(imported_module):
        handlers = imported_module.__handlers__
        for handler in handlers:
            if isinstance(handler, bool):
                await unload_messasge.edit_text(
                    "This module can't be unloaded!")
                return
            if not isinstance(handler, tuple):
                CUTIEPII_PTB.remove_handler(handler)
            elif isinstance(handler[0], collections.Callable):
                callback, telethon_event = handler
                telethn.remove_event_handler(callback, telethon_event)
            else:
                handler_name, priority = handler
                CUTIEPII_PTB.remove_handler(handler_name, priority)
    else:
        await unload_messasge.edit_text("The module cannot be unloaded.")
        return

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE.pop(imported_module.__mod_name__.lower())

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.remove(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.remove(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.remove(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.remove(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.remove(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS.pop(imported_module.__mod_name__.lower())

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS.pop(imported_module.__mod_name__.lower())

    await unload_messasge.edit_text(
        f"Successfully unloaded module : <b>{text}</b>",
        parse_mode=ParseMode.HTML,
    )


@sudo_plus
async def listmodules(update: Update):
    message = update.effective_message
    module_list = []

    for helpable_module in HELPABLE:
        helpable_module_info = IMPORTED[helpable_module]
        file_info = IMPORTED[helpable_module_info.__mod_name__.lower()]
        file_name = file_info.__name__.rsplit("Cutiepii_Robot.modules.", 1)[1]
        mod_name = file_info.__mod_name__
        module_list.append(f"- <code>{mod_name} ({file_name})</code>\n")
    module_list = "Following modules are loaded : \n\n" + "".join(module_list)
    await message.reply_text(module_list, parse_mode=ParseMode.HTML)


CUTIEPII_PTB.add_handler(CommandHandler("load", load, block=False))
CUTIEPII_PTB.add_handler(CommandHandler("unload", unload, block=False))
CUTIEPII_PTB.add_handler(
    CommandHandler("listmodules", listmodules, block=False))

__mod_name__ = "Modules"
