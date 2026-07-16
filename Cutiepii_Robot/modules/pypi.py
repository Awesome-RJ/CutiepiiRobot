"""
BSD 2-Clause License
PyPI Search Module
"""

import html
from telegram import Update
from telegram.ext import ContextTypes, filters
from telegram.constants import ParseMode

from Cutiepii_Robot import dispatcher, arq
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd


@cutiepii_cmd(command="pypi", filters=filters.ChatType.GROUPS | filters.ChatType.PRIVATE, can_disable=True)
async def pypi_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    
    if not args:
        await message.reply_text("Usage: `/pypi [package_name]`", parse_mode=ParseMode.MARKDOWN)
        return
        
    query = " ".join(args).strip()
    
    if not arq:
        await message.reply_text("ARQ service is not initialized.")
        return
        
    msg = await message.reply_text("Searching PyPI...")
    
    try:
        res = await arq.pypi(query)
        if not res.ok:
            await msg.edit_text(f"❌ Package <code>{html.escape(query)}</code> not found or API error.", parse_mode=ParseMode.HTML)
            return
            
        r = res.result
        
        reply = (
            f"📦 <b><a href='{r.pypiURL}'>{html.escape(r.name)}</a></b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷️ <b>Version:</b> <code>{html.escape(r.version)}</code>\n"
        )
        if r.license:
            reply += f"⚖️ <b>License:</b> <code>{html.escape(r.license)}</code>\n"
        if r.size:
            reply += f"🗄️ <b>Size:</b> <code>{html.escape(r.size)}</code>\n"
        if r.uploadTime:
            reply += f"📅 <b>Uploaded:</b> <code>{html.escape(r.uploadTime)}</code>\n"
        if r.author:
            reply += f"👤 <b>Author:</b> <code>{html.escape(r.author)}</code>"
            if r.authorEmail and r.authorEmail != "None":
                reply += f" (<code>{html.escape(r.authorEmail)}</code>)"
            reply += "\n"
        if r.minPyVersion:
            reply += f"🐍 <b>Min Python:</b> <code>{html.escape(r.minPyVersion)}</code>\n"
            
        if r.homepage:
            reply += f"🌐 <b>Homepage:</b> <a href='{r.homepage}'>Link</a>\n"
        elif r.releaseURL:
            reply += f"🌐 <b>Release URL:</b> <a href='{r.releaseURL}'>Link</a>\n"
            
        if r.description:
            # truncate description if too long
            desc = html.escape(r.description).strip()
            if len(desc) > 300:
                desc = desc[:300] + "..."
            reply += f"\n📖 <b>Description:</b>\n<i>{desc}</i>\n"
            
        await msg.edit_text(reply, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        
    except Exception as e:
        await msg.edit_text(f"❌ Error searching PyPI: {e}")


__help__ = True
__mod_name__ = "PyPI"
