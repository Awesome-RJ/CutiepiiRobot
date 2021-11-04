"""
MIT License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021 Awesome-RJ
Copyright (c) 2021, Yūki • Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

This file is part of @Cutiepii_Robot (Telegram Bot)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is

furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
import math
import os
import heroku3
import requests

from Cutiepii_Robot import telethn, HEROKU_APP_NAME, HEROKU_API_KEY, OWNER_ID
from Cutiepii_Robot.events import register

heroku_api = "https://api.heroku.com"
Heroku = heroku3.from_key(HEROKU_API_KEY)


@register(pattern=r"^/(set|see|del) var(?: |$)(.*)(?: |$)([\s\S]*)")
async def variable(var):
    if var.fwd_from:
        return
    if var.sender_id != OWNER_ID:
        return
    """
    Manage most of ConfigVars setting, set new var, get current var,
    or delete var...
    """
    if HEROKU_APP_NAME is not None:
        app = Heroku.app(HEROKU_APP_NAME)
    else:
        return await var.reply("`[HEROKU]:" f"\nPlease setup your` **{HEROKU_APP_NAME}**")
    exe = var.pattern_match.group(1)
    heroku_var = app.config()
    if exe == "see":
        k = await var.reply("`Getting information...`")
        await asyncio.sleep(1.5)
        try:
            variable = var.pattern_match.group(2).split()[0]
            if variable in heroku_var:
                return await k.edit(
                    "**ConfigVars**:" f"\n\n`{variable} = {heroku_var[variable]}`\n"
                )
            return await k.edit(
                "**ConfigVars**:" f"\n\n`Error:\n-> {variable} don't exists`"
            )
        except IndexError:
            configs = prettyjson(heroku_var.to_dict(), indent=2)
            with open("configs.json", "w") as fp:
                fp.write(configs)
            with open("configs.json", "r") as fp:
                result = fp.read()
                if len(result) >= 4096:
                    await var.client.send_file(
                        var.chat_id,
                        "configs.json",
                        reply_to=var.id,
                        caption="`Output too large, sending it as a file`",
                    )
                else:
                    await k.edit(
                        "`[HEROKU]` ConfigVars:\n\n"
                        "================================"
                        f"\n```{result}```\n"
                        "================================"
                    )
            os.remove("configs.json")
            return
    elif exe == "set":
        s = await var.reply("`Setting information...weit ser`")
        variable = var.pattern_match.group(2)
        if not variable:
            return await s.edit(">`.set var <ConfigVars-name> <value>`")
        value = var.pattern_match.group(3)
        if not value:
            variable = variable.split()[0]
            try:
                value = var.pattern_match.group(2).split()[1]
            except IndexError:
                return await s.edit(">`/set var <ConfigVars-name> <value>`")
        await asyncio.sleep(1.5)
        if variable in heroku_var:
            await s.edit(
                f"**{variable}**  `successfully changed to`  ->  **{value}**"
            )
        else:
            await s.edit(
                f"**{variable}**  `successfully added with value`  ->  **{value}**"
            )
        heroku_var[variable] = value
    elif exe == "del":
        m = await var.edit("`Getting information to deleting variable...`")
        try:
            variable = var.pattern_match.group(2).split()[0]
        except IndexError:
            return await m.edit("`Please specify ConfigVars you want to delete`")
        await asyncio.sleep(1.5)
        if variable not in heroku_var:
            return await m.edit(f"**{variable}**  `is not exists`")

        await m.edit(f"**{variable}**  `successfully deleted`")
        del heroku_var[variable]


@register(pattern="^/usage(?: |$)")
async def dyno_usage(dyno):
    if dyno.fwd_from:
        return
    if dyno.sender_id != OWNER_ID:
        return
    """
    Get your account Dyno Usage
    """
    die = await dyno.reply("**Processing...**")
    useragent = (
        "Mozilla/5.0 (Linux; Android 10; SM-G975F) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/80.0.3987.149 Mobile Safari/537.36"
    )
    user_id = Heroku.account().id
    headers = {
        "User-Agent": useragent,
        "Authorization": f"Bearer {HEROKU_API_KEY}",
        "Accept": "application/vnd.heroku+json; version=3.account-quotas",
    }
    path = "/accounts/" + user_id + "/actions/get-quota"
    r = requests.get(heroku_api + path, headers=headers)
    if r.status_code != 200:
        return await die.edit(
            "`Error: something bad happened`\n\n" f">.`{r.reason}`\n"
        )
    result = r.json()
    quota = result["account_quota"]
    quota_used = result["quota_used"]

    """ - Used - """
    remaining_quota = quota - quota_used
    percentage = math.floor(remaining_quota / quota * 100)
    minutes_remaining = remaining_quota / 60
    hours = math.floor(minutes_remaining / 60)
    minutes = math.floor(minutes_remaining % 60)

    """ - Current - """
    App = result["apps"]
    try:
        App[0]["quota_used"]
    except IndexError:
        AppQuotaUsed = 0
        AppPercentage = 0
    else:
        AppQuotaUsed = App[0]["quota_used"] / 60
        AppPercentage = math.floor(App[0]["quota_used"] * 100 / quota)
    AppHours = math.floor(AppQuotaUsed / 60)
    AppMinutes = math.floor(AppQuotaUsed % 60)

    await asyncio.sleep(1.5)

    return await die.edit(
        "**Dyno Usage**:\n\n"
        f" -> `Dyno usage for`  **{HEROKU_APP_NAME}**:\n"
        f"     ❍  `{AppHours}`**h**  `{AppMinutes}`**m**  "
        f"**|**  [`{AppPercentage}`**%**]"
        "\n\n"
        " -> `Dyno hours quota remaining this month`:\n"
        f"     ❍  `{hours}`**h**  `{minutes}`**m**  "
        f"**|**  [`{percentage}`**%**]"
    )


def prettyjson(obj, indent=2, maxlinelength=80):
    """Renders JSON content with indentation and line splits/concatenations to fit maxlinelength.
    Only dicts, lists and basic types are supported"""

    items, _ = getsubitems(
        obj,
        itemkey="",
        islast=True,
        maxlinelength=maxlinelength - indent,
        indent=indent,
    )
    return indentitems(items, indent, level=0)

def indentitems(items, indent, level):
    """Recursively traverses the list of json lines, adds indentation based on the current depth"""
    res = ""
    indentstr = " " * (indent * level)
    for (i, item) in enumerate(items):
        if isinstance(item, list):
            res += indentitems(item, indent, level + 1)
        else:
            islast = (i == len(items) - 1)
            # no new line character after the last rendered line
            if level == 0 and islast:
                res += indentstr + item
            else:
                res += indentstr + item + "\n"
    return res
