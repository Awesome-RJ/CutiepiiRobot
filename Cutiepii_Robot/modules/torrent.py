"""
BSD 2-Clause License
Torrent Search Module
"""

import html
from telegram import Update
from telegram.ext import ContextTypes, filters
from telegram.constants import ParseMode

from Cutiepii_Robot import dispatcher, arq
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd


@cutiepii_cmd(command="torrent", filters=filters.ChatType.GROUPS | filters.ChatType.PRIVATE, can_disable=True)
async def torrent_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    
    if not args:
        await message.reply_text("Usage: `/torrent [search_query]`", parse_mode=ParseMode.MARKDOWN)
        return
        
    query = " ".join(args).strip()
    
    if not arq:
        await message.reply_text("ARQ service is not initialized.")
        return
        
    msg = await message.reply_text("Searching for torrents...")
    
    try:
        res = await arq.torrent(query)
        if not res.ok:
            await msg.edit_text(f"❌ No torrents found for <code>{html.escape(query)}</code> or API error.", parse_mode=ParseMode.HTML)
            return
            
        r = res.result
        if not r or not isinstance(r, list):
            await msg.edit_text(f"❌ No torrents found for <code>{html.escape(query)}</code>.", parse_mode=ParseMode.HTML)
            return
            
        reply = f"🏴‍☠️ <b>Torrent Search Results for:</b> <code>{html.escape(query)}</code>\n\n"
        
        for idx, t in enumerate(r[:5], 1):
            reply += (
                f"{idx}. <b>{html.escape(t.name)}</b>\n"
                f"   🗄️ <b>Size:</b> <code>{html.escape(t.size)}</code> | "
                f"🧲 <a href='{t.magnet}'>Magnet Link</a>\n"
                f"   ⬆️ <b>Seeds:</b> <code>{t.seeds}</code> | ⬇️ <b>Leechers:</b> <code>{t.leechs}</code>\n"
                f"   📂 <b>Category:</b> <code>{html.escape(t.category)}</code>\n\n"
            )
            
        await msg.edit_text(reply, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        
    except Exception as e:
        await msg.edit_text(f"❌ Error searching torrents: {e}")


__help__ = True
__mod_name__ = "Torrent"
