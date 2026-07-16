"""
BSD 2-Clause License
TMDB Search Module
"""

import html
from telegram import Update
from telegram.ext import ContextTypes, filters
from telegram.constants import ParseMode

from Cutiepii_Robot import dispatcher, arq
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd


@cutiepii_cmd(command="tmdb", filters=filters.ChatType.GROUPS | filters.ChatType.PRIVATE, can_disable=True)
async def tmdb_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    
    if not args:
        await message.reply_text("Usage: `/tmdb [movie_or_show_title]`", parse_mode=ParseMode.MARKDOWN)
        return
        
    query = " ".join(args).strip()
    
    if not arq:
        await message.reply_text("ARQ service is not initialized.")
        return
        
    msg = await message.reply_text("Searching TMDB...")
    
    try:
        res = await arq.tmdb(query)
        if not res.ok:
            await msg.edit_text(f"❌ No results found for <code>{html.escape(query)}</code> or API error.", parse_mode=ParseMode.HTML)
            return
            
        r = res.result
        if isinstance(r, list):
            if not r:
                await msg.edit_text(f"❌ No results found for <code>{html.escape(query)}</code>.", parse_mode=ParseMode.HTML)
                return
            media = r[0]
        else:
            media = r
            
        genres = ", ".join(media.genre) if media.genre else "N/A"
        
        reply = (
            f"🎬 <b>{html.escape(media.title)}</b> ({html.escape(media.releaseDate[:4]) if media.releaseDate else 'N/A'})\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎥 <b>Type:</b> <code>{html.escape(media.type.title())}</code>\n"
            f"⭐ <b>Rating:</b> <code>{media.rating}/10</code>\n"
            f"📅 <b>Release Date:</b> <code>{html.escape(media.releaseDate) if media.releaseDate else 'N/A'}</code>\n"
            f"🎭 <b>Genres:</b> <code>{html.escape(genres)}</code>\n\n"
            f"📖 <b>Overview:</b>\n<i>{html.escape(media.overview)}</i>"
        )
        
        if media.poster:
            try:
                await message.reply_photo(
                    photo=media.poster,
                    caption=reply,
                    parse_mode=ParseMode.HTML
                )
                await msg.delete()
            except Exception:
                await msg.edit_text(reply, parse_mode=ParseMode.HTML)
        else:
            await msg.edit_text(reply, parse_mode=ParseMode.HTML)
            
    except Exception as e:
        await msg.edit_text(f"❌ Error searching TMDB: {e}")


__help__ = True
__mod_name__ = "TMDB"
