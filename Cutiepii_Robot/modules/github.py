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

import aiohttp
import html

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from Cutiepii_Robot import LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd


__mod_name__ = "Github"


@cutiepii_cmd(command=["github", "gitinfo", "gifinfo"])
async def github(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    
    if len(context.args) != 1:
        await message.reply_text("Usage: `/github <username>` or `/gitinfo <username>`")
        return
    
    username = context.args[0]
    URL = f"https://api.github.com/users/{username}"
    
    async with aiohttp.ClientSession() as session, session.get(URL) as request:
        if request.status == 404:
            return await message.reply_text("404 - User not found")

        result = await request.json()
        try:
            url = result.get("html_url", "")
            name = result.get("name") or username
            company = result.get("company") or "N/A"
            bio = result.get("bio") or "N/A"
            created_at = result.get("created_at", "N/A")
            avatar_url = result.get("avatar_url", "")
            blog = result.get("blog") or "N/A"
            location = result.get("location") or "N/A"
            repositories = result.get("public_repos", 0)
            followers = result.get("followers", 0)
            following = result.get("following", 0)
            
            caption = f"""👤 <b>Info Of {html.escape(str(name))}</b>
━━━━━━━━━━━━━━━━━━━━━━━

❍ <b>Username:</b> <code>{html.escape(str(username))}</code>
❍ <b>Bio:</b> <code>{html.escape(str(bio))}</code>
❍ <b>Profile Link:</b> <a href="{url}">Here</a>
❍ <b>Company:</b> <code>{html.escape(str(company))}</code>
❍ <b>Created On:</b> <code>{html.escape(str(created_at))}</code>
❍ <b>Repositories:</b> <code>{repositories}</code>
❍ <b>Blog:</b> <code>{html.escape(str(blog))}</code>
❍ <b>Location:</b> <code>{html.escape(str(location))}</code>
❍ <b>Followers:</b> <code>{followers}</code>
❍ <b>Following:</b> <code>{following}</code>"""
        except Exception as e:
            LOGGER.debug(e)
            return await message.reply_text("Failed to fetch GitHub data")
    
    await message.reply_photo(photo=avatar_url, caption=caption, parse_mode=ParseMode.HTML)
