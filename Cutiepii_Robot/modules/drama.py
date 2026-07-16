from html import escape
import cloudscraper

scraper = cloudscraper.create_scraper()

from telegram.error import BadRequest
from telegram.ext import ContextTypes
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd

url = "https://mydramalist.com/"
    
# Text Shorter
def shorten(des: str = '', short: int = 500):
    msg = des
    if len(des) > int(short):
        msg = des[0:int(short)]
    return escape(msg)

# Drama
@cutiepii_cmd(command="drama")
async def drama(update: Update, context: CallbackContext):
    message = update.effective_message
    search = message.text.split(" ", 1)
    if len(search) == 1:
        await message.reply_text('Format: `/drama <query>`', parse_mode=ParseMode.MARKDOWN)
        return

    Dramas = {}
    buttons = []
    try:
        r = scraper.get(f'{url}/search/q/{search[1]}', timeout=10)
        if r.status_code != 200:
            await message.reply_text("Could not connect to MyDramaList.")
            return
        res = r.json()
        data = res.get('results', {}).get('dramas') or []
    except Exception:
        await message.reply_text("No Results Found!")
        return

    for x in data:
       Dramas[x.get('slug')] = x.get('title')
       if len(Dramas) > 4:
           break

    for slug, title in Dramas.items():
       buttons.append([InlineKeyboardButton(text=title, callback_data=f"drama-detail {message.from_user.id} {slug}")])
       if len(buttons) > 4:
           break

    if len(buttons) < 1:
        await message.reply_text("No Results Found!")
        return

    await message.reply_text(
        f"Results Of <b>{search[1]}</b>:",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# Callback Data
@cutiepii_callback(pattern=r"drama-detail.*")
async def drama_button(update: Update, context: CallbackContext):
    chat = update.effective_chat
    query = update.callback_query
    message = update.effective_message

    # Split data from query
    splitter = query.data.split()
    query_match = splitter[0]
    user_id = splitter[1]
    slug = splitter[2]

    if query_match == "drama-detail":
        if int(query.from_user.id) != int(user_id):
            query.answer("You Aren't Allowed!")
            return

        try:
            r = scraper.get(f'{url}/id/{slug}', timeout=10)
            if r.status_code != 200:
                await query.answer("Could not fetch drama details from MyDramaList.")
                return
            res = r.json()
        except Exception:
            await query.answer("Could not fetch drama details.")
            return

        type = res['data']['details'].get('type')
        country = res['data']['details'].get('country')
        episodes = res['data']['details'].get('episodes') or 'N/A'
        duration = res['data']['details'].get('duration')
        aired = res['data']['details'].get('aired') or res['data']['details'].get('release_date')
        content_rating = res['data']['details'].get('content_rating') or 'N/A'
        title = res['data'].get('title')
        native = res['data']['others'].get('native_title')
        also_known_as = res['data']['others'].get('also_known_as')
        genres = res['data']['others'].get('genres')
        description = shorten(res['data'].get('synopsis'))


        txt = f"<b>{title} - ({native})</b>\n"
        txt += f"\n<b>Type</b>: {type} ({content_rating.split(None, 1)[0] if content_rating != ('Not Yet Rated', '', None) else 'N/A'})"
        txt += f"\n<b>Country</b>: {country}"
        txt += f"\n<b>Also Known As</b>: {also_known_as if also_known_as != ('', None) else 'N/A'}\n"
        txt += f"\n<b>Episodes</b>: {episodes} ({duration})" if type == 'Drama' else f"\n<b>Duration</b>: {duration}"
        txt += f"\n<b>Aired</b>: {aired}" if type == 'Drama' else f"\n<b>Release Date</b>: {aired}"
        txt += f"\n<b>Genres</b>: {genres}"
        txt += f"\n\n<i>{description}....</i>"

        await query.message.edit_text(
            text=txt,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('More', url=f"https://mydramalist.com/{slug}")], [InlineKeyboardButton("Casts", callback_data=f"drama-cast-detail {user_id} {slug}")]]),
        )
        await query.answer()



@cutiepii_callback(pattern=r"drama-cast-detail.*")
async def casts_button(update: Update, context: CallbackContext):
    chat = update.effective_chat
    query = update.callback_query
    message = update.effective_message

    # Split data from query
    splitter = query.data.split()
    query_match = splitter[0]
    user_id = splitter[1]
    slug = splitter[2]

    if query_match == "drama-cast-detail":
        if int(query.from_user.id) != int(user_id):
            query.answer("You Aren't Allowed!")
            return

        try:
            r = scraper.get(f'{url}/id/{slug}/cast', timeout=10)
            if r.status_code != 200:
                await query.answer("Could not fetch cast details from MyDramaList.")
                return
            res = r.json()
        except Exception:
            await query.answer("Could not fetch cast details.")
            return

        title = res['data'].get('title')
        casts = res['data']['casts']
        mainroles = casts.get('Main Role')
        supportroles = casts.get('Support Role')

        txt = f"List Casts Of <a href='https://mydramalist.com/{slug}'>{title}</a>\n"
        if mainroles:
          txt += "\n\n● <u><b>Main</b></u>"
          for cast in mainroles:
             txt += f"\n⚬ {cast['role']['name'].replace('[', '').replace(']', '')}\n   (<a href='{cast['link']}'>{cast['name']}</a>)"

        if supportroles:
          txt += "\n\n● <u><b>Support</b></u>"
          for cast in supportroles:
             txt += f"\n⚬ {cast['role']['name'].replace('[', '').replace(']', '')}\n   (<a href='{cast['link']}'>{cast['name']}</a>)"

        await query.message.edit_text(
            text=txt,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data=f"drama-detail {user_id} {slug}")]]),
        )
        await query.answer()
