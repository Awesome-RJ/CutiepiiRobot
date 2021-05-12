import html

import bs4
import requests
from Cutiepii_Robot import dispatcher
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ParseMode,
                      Update)
from telegram.ext import CallbackContext, run_async

info_btn = "More Information"
animetm_btn = "Animetm ☠️"
prequel_btn = "⬅️ Prequel"
sequel_btn = "Sequel ➡️"
close_btn = "Close ❌"


def site_search(update: Update, context: CallbackContext, site: str):
    message = update.effective_message
    args = message.text.strip().split(" ", 1)
    more_results = True

    try:
        search_query = args[1]
    except IndexError:
        message.reply_text("Give something to search")
        return

    if site == "animerocks":
        search_url = f"https://animerocks.ml/search?text={search_query}"
        html_text = requests.get(search_url).text
        soup = bs4.BeautifulSoup(html_text, "html.parser")
        search_result = soup.find_all("h2", {'class': "title"}) 
        
        result = f"<b>Search results for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>Anime Rocks</code>: \n"
        for entry in search_result:
                 
           if entry.text.strip() == "Nothing Found":
                result = f"<b>No result found for</b> <code>{html.escape(search_query)}</code> <b>on</b> <code>AnimeKayo </code>"
                more_results = False
                break
                
           post_link = entry.a['href']
           post_name = html.escape(entry.text.strip())
           result += f"• <a href='{post_link}'>{post_name}</a>\n"
           
    buttons = [[InlineKeyboardButton("See all results", url=search_url)]]

    if more_results:
        message.reply_text(
            result,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True)
    else:
        message.reply_text(
            result, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


@run_async
def animerocks(update: Update, context: CallbackContext):
    site_search(update, context, "animerocks")
    
ANIMEROCKS_SEARCH_HANDLER = DisableAbleCommandHandler("animerocks", animerocks)

dispatcher.add_handler(ANIMEROCKS_SEARCH_HANDLER)

__handlers__ = [ANIMEROCKS_SEARCH_HANDLER]
