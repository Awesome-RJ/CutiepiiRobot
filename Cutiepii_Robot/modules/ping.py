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

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd
import time
import requests
import html
import datetime
import platform
import aiohttp
from typing import List

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, __version__ as ptbver
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from Cutiepii_Robot import StartTime, dispatcher
from Cutiepii_Robot.modules.helper_funcs.chat_status import sudo_plus
from Cutiepii_Robot.__main__ import STATS
from Cutiepii_Robot.modules.sql import SESSION
from sqlalchemy import text
from psutil import cpu_percent, virtual_memory, disk_usage, boot_time
from platform import python_version

sites_list = {
    "Telegram": "https://api.telegram.org",
    "Jikan": "https://api.jikan.moe/v4",
}


from Cutiepii_Robot.modules.helper_funcs.readable_time import get_readable_time


def ping_func(to_ping: List[str]) -> List[str]:
    ping_result = []

    for each_ping in to_ping:
        start_time = time.time()
        site_to_ping = sites_list[each_ping]
        try:
            r = requests.get(site_to_ping, timeout=5)
            status = r.status_code
        except Exception:
            status = "Error"
        end_time = time.time()
        ping_time = str(round((end_time - start_time), 2)) + "s"

        ping_text = f"<b>{each_ping}</b>: <code>{ping_time} (Status: {status})</code>"
        ping_result.append(ping_text)

    return ping_result

@sudo_plus
@cutiepii_cmd(command="ping", can_disable=True)
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    start_time = time.time()
    message = await msg.reply_text("Pinging...")
    end_time = time.time()
    telegram_ping = str(round((end_time - start_time) * 1000, 3)) + " ms"
    uptime = get_readable_time((time.time() - StartTime))

    await message.edit_text(
        "PONG\n"
        "<b>Time Taken:</b> <code>{}</code>\n"
        "<b>Service Uptime:</b> <code>{}</code>".format(telegram_ping, uptime),
        parse_mode=ParseMode.HTML,
    )


@sudo_plus
@cutiepii_cmd(command="pingall", can_disable=True)
async def pingall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    to_ping = ["Telegram", "Jikan"]
    pinged_list = ping_func(to_ping)
    uptime = get_readable_time((time.time() - StartTime))

    reply_msg = "Ping results are:\n"
    reply_msg += "\n".join(pinged_list)
    reply_msg += "\n<b>Service Uptime:</b> <code>{}</code>".format(uptime)

    await update.effective_message.reply_text(
        reply_msg, parse_mode=ParseMode.HTML, disable_web_page_preview=True,
    )


@sudo_plus
@cutiepii_cmd(command=["uptime", "up"], can_disable=True)
async def uptime_func(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uptime = get_readable_time((time.time() - StartTime))
    await update.effective_message.reply_text(
        f"<b>Service uptime:</b> <code>{uptime}</code>",
        parse_mode=ParseMode.HTML,
    )


def get_progress_bar(percentage: float) -> str:
    filled_blocks = int(round(percentage / 10))
    empty_blocks = 10 - filled_blocks
    return "█" * filled_blocks + "░" * empty_blocks


@sudo_plus
@cutiepii_cmd(command=["stats", "statistics"], can_disable=True)
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    
    db_size = SESSION.execute(
        text("SELECT pg_size_pretty(pg_database_size(current_database()))")
    ).scalar_one_or_none()
    
    uptime = datetime.datetime.fromtimestamp(boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    botuptime = get_readable_time((time.time() - StartTime))
    uname = platform.uname()
    
    mem = virtual_memory()
    cpu = cpu_percent()
    disk = disk_usage("/")
    
    ram_used_gb = mem.used / (1024 ** 3)
    ram_total_gb = mem.total / (1024 ** 3)
    ram_pct = mem.percent
    
    disk_used_gb = disk.used / (1024 ** 3)
    disk_total_gb = disk.total / (1024 ** 3)
    disk_pct = disk.percent
    
    status = (
        "<b>╭── [ SYSTEM METRICS ] ──</b>\n"
        f"<b>├ System Start:</b> <code>{uptime}</code>\n"
        f"<b>├ Bot Uptime:</b> <code>{botuptime}</code>\n"
        f"<b>├ CPU Usage:</b> [ <code>{get_progress_bar(cpu)}</code> ] <code>{cpu}%</code>\n"
        f"<b>├ RAM Usage:</b> [ <code>{get_progress_bar(ram_pct)}</code> ] <code>{ram_pct}%</code> (<code>{ram_used_gb:.1f}GB / {ram_total_gb:.1f}GB</code>)\n"
        f"<b>├ Disk Space:</b> [ <code>{get_progress_bar(disk_pct)}</code> ] <code>{disk_pct}%</code> (<code>{disk_used_gb:.1f}GB / {disk_total_gb:.1f}GB</code>)\n"
        f"<b>├ Database Size:</b> <code>{db_size}</code>\n"
        f"<b>╰───────────────────────</b>\n\n"
        
        "<b>╭── [ SOFTWARE ENVIRONMENT ] ──</b>\n"
        f"<b>├ OS Platform:</b> <code>{html.escape(uname.system)} {html.escape(uname.release)} ({html.escape(uname.machine)})</code>\n"
        f"<b>├ Python Version:</b> <code>{python_version()}</code>\n"
        f"<b>├ PTB Version:</b> <code>{ptbver}</code>\n"
        f"<b>╰──────────────────────────</b>\n\n"
        
        "<b>╭── [ BOT STATISTICS ] ──</b>\n"
    )
    
    bot_stats = []
    for mod in STATS:
        try:
            stat_text = mod.__stats__()
            if stat_text:
                cleaned = stat_text.replace("•", "").strip()
                bot_stats.append(f"<b>├</b> {cleaned}")
        except Exception:
            pass
            
    if bot_stats:
        bot_stats[-1] = bot_stats[-1].replace("<b>├</b>", "<b>╰</b>")
        status += "\n".join(bot_stats)
    else:
        status += "<b>╰</b> No statistics available."
        
    status += (
        "\n\n<a href='https://t.me/Black_Knights_Union_Support'>Support</a> | "
        "<a href='https://t.me/Black_Knights_Union'>Updates</a>\n\n"
        "╘═━「 by <a href='https://github.com/Awesome-RJ'>Awesome-RJ</a> 」\n"
    )
    
    kb = [
        [
            InlineKeyboardButton("View Ping (Only Sudo)", callback_data="pingCB")
        ]
    ]
    
    await message.reply_text(
        status,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(kb),
        disable_web_page_preview=True,
        allow_sending_without_reply=True
    )


@cutiepii_callback(pattern=r"pingCB")
async def pingCallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    start_time = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.telegram.org", timeout=aiohttp.ClientTimeout(total=5)) as _:
                pass
    except Exception:
        pass
    end_time = time.time()
    ping_time = round((end_time - start_time) * 1000, 3)
    await query.answer(f'Pong! {ping_time}ms')



__help__ = True

__mod_name__ = "Ping"
