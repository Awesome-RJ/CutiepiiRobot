from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
import requests
from Cutiepii_Robot import dispatcher
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
CallbackContext = ContextTypes.DEFAULT_TYPE
from Cutiepii_Robot.modules.sql.clear_cmd_sql import get_clearcmd
from Cutiepii_Robot.modules.helper_funcs.misc import delete
from datetime import datetime
import re

@cutiepii_cmd(command="kernels")
async def linux_kernels(update: Update, context: CallbackContext):
    chat = update.effective_chat
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:10.0) Gecko/20100101 Firefox/10.0"}

    try:
        response = requests.get("https://www.kernel.org/releases.json", headers=headers)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        await update.effective_message.reply_text(f"Error fetching kernel data: {str(e)}")
        return

    releases = data.get("releases", [])
    if not releases:
        await update.effective_message.reply_text("No kernel releases found.")
        return

    message = "<b>Linux Kernel Versions</b>\n\n"
    for release in releases[:10]:
        version = release.get("version", "Unknown")
        moniker = release.get("moniker", "").lower()
        timestamp = release.get("released", {}).get("timestamp", 0)
        source_url = release.get("gitweb", "#")

        category = "MAINLINE"
        if release.get("iseol"):
            category = "EOL"
        elif "longterm" in moniker:
            category = "LTS"
        elif "stable" in moniker:
            category = "STABLE"
        elif "linux-next" in moniker:
            category = "NEXT"

        message += (
            f"- <a href='{source_url}'>{version}</a>\n"
            f"  └ <i>{category}</i> "
            f"({datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')})\n\n"
        )

    message += "<i>Source: kernel.org</i>"

    try:
        delmsg = await update.effective_message.reply_text(
            message,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    except Exception as e:
        await update.effective_message.reply_text(f"Error formatting message: {str(e)}")
        return

    cleartime = get_clearcmd(chat.id, "kernels")
    if cleartime:
        # Schedule delete task (run_async removed in v20+)
        import asyncio
        async def _delete_task():
            await asyncio.sleep(cleartime.time)
            try:
                await delmsg.delete()
            except:
                pass
        asyncio.create_task(_delete_task())

__help__ = True


__mod_name__ = "Linux"