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
from Cutiepii_Robot import dispatcher
from Cutiepii_Robot.modules.helper_funcs.admin_status import user_is_admin
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback

from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility

anonymous_data = {}

@cutiepii_callback(pattern="anonAdmin_")
async def anonymous_admin_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query:
        return
    
    # Extract message from anonymous_data or fallback
    data = query.data.split("_", 1)
    if not data[1] in anonymous_data:
        try:
            await query.message.edit_text("This button is expired!")
        except Exception:
            pass
        return

    d = anonymous_data[data[1]]
    message = d["message"]

    if not await user_is_admin(update, message.from_user.id):
        await query.answer("You need to be an admin to do this.", show_alert=True)
        return

    try:
        await query.message.delete()
    except Exception:
        pass

    try:
        context.__setattr__("args", message.text.split(None)[1:])
        update.__setattr__("_effective_message", message)
        update.__setattr__("callback_query", None)
        
        result = d["func"](update, context)
        if asyncio.iscoroutine(result):
            await result
            
        del anonymous_data[data[1]]
    except Exception as e:
        try:
            await context.bot.send_message(update.effective_chat.id, "Failed to authorize you!")
        except Exception:
            pass

# Callback handler is registered via cutiepii_callback decorator
