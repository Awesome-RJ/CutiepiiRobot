# module to get anime info from AniList GraphQL API
# Ported to python-telegram-bot v22.5 and async HTTP requests.

import bs4
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Cutiepii_Robot import http, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, rate_limit

def shorten(description, info="anilist.co"):
    msg = ""
    if not description:
        description = "N/A"
    if len(description) > 700:
        description = f"{description[:500]}...."
        msg += f"\n*Description*: _{description}_[Read More]({info})"
    else:
        msg += f"\n*Description*: _{description}_"
    return (
        msg.replace("<br>", "")
        .replace("</br>", "")
        .replace("<i>", "")
        .replace("</i>", "")
    )


# time formatter from uniborg
def t(milliseconds: int) -> str:
    """Inputs time in milliseconds, to get beautified time, as string"""
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        (f"{str(days)} Days, " if days else "")
        + (f"{str(hours)} Hours, " if hours else "")
        + (f"{str(minutes)} Minutes, " if minutes else "")
        + (f"{str(seconds)} Seconds, " if seconds else "")
        + (f"{str(milliseconds)} ms, " if milliseconds else "")
    )

    return tmp[:-2]


airing_query = """
    query ($id: Int,$search: String) {
      Media (id: $id, type: ANIME,search: $search) {
        id
        episodes
        title {
          romaji
          english
          native
        }
        nextAiringEpisode {
           airingAt
           timeUntilAiring
           episode
        }
      }
    }
    """

fav_query = """
query ($id: Int) {
      Media (id: $id, type: ANIME) {
        id
        title {
          romaji
          english
          native
        }
     }
}
"""

anime_query = """
   query ($id: Int,$search: String) {
      Media (id: $id, type: ANIME,search: $search) {
        id
        title {
          romaji
          english
          native
        }
        description (asHtml: false)
        startDate{
            year
          }
          episodes
          season
          type
          format
          status
          duration
          siteUrl
          studios{
              nodes{
                   name
              }
          }
          trailer{
               id
               site
               thumbnail
          }
          averageScore
          genres
          bannerImage
      }
    }
"""

anime_search_query = """
query ($search: String) {
  Page(perPage: 10) {
    media(search: $search, type: ANIME) {
      id
      title {
        romaji
        english
        native
      }
      startDate {
        year
      }
      status
      averageScore
      format
    }
  }
}
"""
character_query = """
    query ($id: Int, $query: String) {
        Character (id: $id, search: $query) {
               id
               name {
                     first
                     last
                     full
               }
               siteUrl
               image {
                        large
               }
               description
        }
    }
"""

character_search_query = """
query ($query: String) {
  Page(perPage: 10) {
    characters(search: $query) {
      id
      name {
        first
        last
        full
      }
    }
  }
}
"""

manga_query = """
query ($id: Int,$search: String) {
      Media (id: $id, type: MANGA,search: $search) {
        id
        title {
          romaji
          english
          native
        }
        description (asHtml: false)
        startDate{
            year
          }
          type
          format
          status
          siteUrl
          averageScore
          genres
          bannerImage
      }
    }
"""

manga_search_query = """
query ($search: String) {
  Page(perPage: 10) {
    media(search: $search, type: MANGA) {
      id
      title {
        romaji
        english
        native
      }
      startDate {
        year
      }
      status
      averageScore
      format
    }
  }
}
"""


url = "https://graphql.anilist.co"

@cutiepii_cmd(command="airing")
@rate_limit(max_calls=5, time_window=60)
async def airing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    search_str = message.text.split(" ", 1)
    if len(search_str) == 1:
        await update.effective_message.reply_text(
            "Tell Anime Name :) ( /airing <anime name>)"
        )
        return
    variables = {"search": search_str[1]}
    try:
        response = await http.post(
            url, json={"query": airing_query, "variables": variables}
        )
        response_json = response.json()
        if "errors" in response_json:
            await update.effective_message.reply_text("Anime not found")
            return
        media = response_json.get("data", {}).get("Media")
        if not media:
            await update.effective_message.reply_text("Anime not found")
            return
    except Exception as e:
        LOGGER.error(f"Error in airing search: {e}")
        await update.effective_message.reply_text("An error occurred while connecting to AniList.")
        return

    msg = f"*Name*: *{media['title']['romaji']}*(`{media['title']['native']}`)\n*ID*: `{media['id']}`"
    if media.get("nextAiringEpisode"):
        time_left = media["nextAiringEpisode"]["timeUntilAiring"] * 1000
        time_left_str = t(time_left)
        msg += f"\n*Episode*: `{media['nextAiringEpisode']['episode']}`\n*Airing In*: `{time_left_str}`"
    else:
        msg += f"\n*Episode*: {media.get('episodes') or 'N/A'}\n*Status*: `N/A`"
    await update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


@cutiepii_cmd(command=["anilist", "alanime"])
@rate_limit(max_calls=40, time_window=60)
async def anime(update: Update, context: ContextTypes.DEFAULT_TYPE):  # sourcery no-metrics
    message = update.effective_message
    search = message.text.split(" ", 1)
    if len(search) == 1:
        await update.effective_message.reply_text("Format : /anilist < anime name >")
        return
    else:
        search = search[1]
    variables = {"search": search}
    try:
        response = await http.post(
            url, json={"query": anime_search_query, "variables": variables}
        )
        json_data = response.json()
        if "errors" in json_data.keys():
            await update.effective_message.reply_text("Anime not found")
            return
        media_list = json_data.get("data", {}).get("Page", {}).get("media", [])
        if not media_list:
            await update.effective_message.reply_text("No anime found")
            return
    except Exception as e:
        LOGGER.error(f"Error in AniList search: {e}")
        await update.effective_message.reply_text("An error occurred while connecting to AniList.")
        return

    if len(media_list) == 1:
        # directly show
        anime_id = media_list[0]["id"]
        variables = {"id": anime_id}
        try:
            response = await http.post(
                url, json={"query": anime_query, "variables": variables}
            )
            json_data = response.json()
            if "errors" in json_data.keys():
                await update.effective_message.reply_text("Anime not found")
                return
            json_data = json_data["data"]["Media"]
        except Exception as e:
            LOGGER.error(f"Error fetching media details: {e}")
            await update.effective_message.reply_text("An error occurred while fetching details.")
            return

        msg = f"*{json_data['title']['romaji']}*(`{json_data['title']['native']}`)\n*Type*: {json_data['format']}\n*Status*: {json_data['status']}\n*Episodes*: {json_data.get('episodes', 'N/A')}\n*Duration*: {json_data.get('duration', 'N/A')} Per Ep.\n*Score*: {json_data['averageScore']}\n*Genres*: `"
        for x in json_data["genres"]:
            msg += f"{x}, "
        msg = msg[:-2] + "`\n"
        msg += "*Studios*: `"
        for x in json_data["studios"]["nodes"]:
            msg += f"{x['name']}, "
        msg = msg[:-2] + "`\n"
        info = json_data.get("siteUrl")
        trailer = json_data.get("trailer", None)
        if trailer:
            trailer_id = trailer.get("id", None)
            site = trailer.get("site", None)
            if site == "youtube":
                trailer = f"https://youtu.be/{trailer_id}"
        description = (
           bs4.BeautifulSoup(json_data.get("description", "N/A"), features="html.parser").text
        )
        msg += shorten(description, info)
        image = json_data.get("bannerImage", None)
        if trailer:
            buttons = [
                [
                    InlineKeyboardButton("More Info", url=info),
                    InlineKeyboardButton("Trailer 🎬", url=trailer),
                ]
            ]
        else:
            buttons = [[InlineKeyboardButton("More Info", url=info)]]
        if image:
            try:
                await update.effective_message.reply_photo(
                    photo=image,
                    caption=msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            except Exception:
                msg += f" [〽️]({image})"
                await update.effective_message.reply_text(
                    msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        else:
            await update.effective_message.reply_text(
                msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons),
            )
    else:
        buttons = []
        for media in media_list:
            title = media["title"]["romaji"] or media["title"]["english"] or media["title"]["native"]
            year = media.get("startDate", {}).get("year", "N/A")
            status = media.get("status", "N/A")
            button_text = f"{title} ({year}) [{status}]"
            buttons.append([InlineKeyboardButton(button_text, callback_data=f"anilist_anime_{media['id']}_{update.effective_user.id}")])
        await update.effective_message.reply_text(
            "Select an anime:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )


@cutiepii_cmd(command="alcharacter")
@rate_limit(max_calls=40, time_window=60)
async def character(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    search = message.text.split(" ", 1)
    if len(search) == 1:
        await update.effective_message.reply_text("Format : /alcharacter < character name >")
        return
    search = search[1]
    variables = {"query": search}
    try:
        response = await http.post(
            url, json={"query": character_search_query, "variables": variables}
        )
        json_data = response.json()
        if "errors" in json_data.keys():
            await update.effective_message.reply_text("Character not found")
            return
        char_list = json_data.get("data", {}).get("Page", {}).get("characters", [])
        if not char_list:
            await update.effective_message.reply_text("No character found")
            return
    except Exception as e:
        LOGGER.error(f"Error in AniList character search: {e}")
        await update.effective_message.reply_text("An error occurred while connecting to AniList.")
        return

    if len(char_list) == 1:
        # directly show
        char_id = char_list[0]["id"]
        variables = {"id": char_id}
        try:
            response = await http.post(
                url, json={"query": character_query, "variables": variables}
            )
            json_data = response.json()
            if "errors" in json_data.keys():
                await update.effective_message.reply_text("Character not found")
                return
            json_data = json_data["data"]["Character"]
        except Exception as e:
            LOGGER.error(f"Error fetching character details: {e}")
            await update.effective_message.reply_text("An error occurred while fetching details.")
            return

        msg = f"*{json_data.get('name').get('full')}*(`{json_data.get('name').get('native')}`)\n"
        description = bs4.BeautifulSoup(f"{json_data['description']}", features="html.parser").text
        site_url = json_data.get("siteUrl")
        msg += shorten(description, site_url)
        if image := json_data.get("image", None):
            image = image.get("large")
            await update.effective_message.reply_photo(
                photo=image,
                caption=msg.replace("<b>", "</b>"),
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            await update.effective_message.reply_text(
                msg.replace("<b>", "</b>"), parse_mode=ParseMode.MARKDOWN
            )
    else:
        buttons = []
        for char in char_list:
            name = char["name"]["full"] or f"{char['name']['first']} {char['name']['last']}"
            buttons.append([InlineKeyboardButton(name, callback_data=f"anilist_char_{char['id']}_{update.effective_user.id}")])
        await update.effective_message.reply_text(
            "Select a character:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )


@cutiepii_cmd(command="almanga")
@rate_limit(max_calls=40, time_window=60)
async def manga(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    search = message.text.split(" ", 1)
    if len(search) == 1:
        await update.effective_message.reply_text("Format : /almanga < manga name >")
        return
    search = search[1]
    variables = {"search": search}
    try:
        response = await http.post(
            url, json={"query": manga_search_query, "variables": variables}
        )
        json_data = response.json()
        if "errors" in json_data.keys():
            await update.effective_message.reply_text("Manga not found")
            return
        media_list = json_data.get("data", {}).get("Page", {}).get("media", [])
        if not media_list:
            await update.effective_message.reply_text("No manga found")
            return
    except Exception as e:
        LOGGER.error(f"Error in AniList manga search: {e}")
        await update.effective_message.reply_text("An error occurred while connecting to AniList.")
        return

    if len(media_list) == 1:
        # directly show
        manga_id = media_list[0]["id"]
        variables = {"id": manga_id}
        try:
            response = await http.post(
                url, json={"query": manga_query, "variables": variables}
            )
            json_data = response.json()
            if "errors" in json_data.keys():
                await update.effective_message.reply_text("Manga not found")
                return
            json_data = json_data["data"]["Media"]
        except Exception as e:
            LOGGER.error(f"Error fetching manga details: {e}")
            await update.effective_message.reply_text("An error occurred while fetching details.")
            return

        msg = ""
        title, title_native = json_data["title"].get("romaji", False), json_data["title"].get(
            "native", False
        )
        start_date, status, score = (
            json_data["startDate"].get("year", False),
            json_data.get("status", False),
            json_data.get("averageScore", False),
        )
        if title:
            msg += f"*{title}*"
            if title_native:
                msg += f"(`{title_native}`)"
        if start_date:
            msg += f"\n*Start Date* - `{start_date}`"
        if status:
            msg += f"\n*Status* - `{status}`"
        if score:
            msg += f"\n*Score* - `{score}`"
        msg += "\n*Genres* - "
        for x in json_data.get("genres", []):
            msg += f"{x}, "
        msg = msg[:-2]
        info = json_data["siteUrl"]
        buttons = [[InlineKeyboardButton("More Info", url=info)]]
        image = json_data.get("bannerImage", False)
        desc_text = bs4.BeautifulSoup(json_data.get('description', 'N/A') or 'N/A', features="html.parser").text
        msg += f"_{desc_text}_"
        if image:
            try:
                await update.effective_message.reply_photo(
                    photo=image,
                    caption=msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
            except Exception:
                msg += f" [〽️]({image})"
                await update.effective_message.reply_text(
                    msg,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(buttons),
                )
        else:
            await update.effective_message.reply_text(
                msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons),
            )
    else:
        buttons = []
        for media in media_list:
            title = media["title"]["romaji"] or media["title"]["english"] or media["title"]["native"]
            year = media.get("startDate", {}).get("year", "N/A")
            status = media.get("status", "N/A")
            button_text = f"{title} ({year}) [{status}]"
            buttons.append([InlineKeyboardButton(button_text, callback_data=f"anilist_manga_{media['id']}_{update.effective_user.id}")])
        await update.effective_message.reply_text(
            "Select a manga:",
            reply_markup=InlineKeyboardMarkup(buttons),
        )


@cutiepii_callback(pattern=r"anilist_anime_(\d+)_(\d+)")
async def anime_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    anime_id = int(parts[2])
    user_id = int(parts[3])
    if query.from_user.id != user_id:
        await query.answer("This selection is not for you!", show_alert=True)
        return
    variables = {"id": anime_id}
    try:
        response = await http.post(
            url, json={"query": anime_query, "variables": variables}
        )
        json_data = response.json()
        if "errors" in json_data.keys():
            await query.edit_message_text("Anime not found")
            return
        json_data = json_data["data"]["Media"]
    except Exception as e:
        LOGGER.error(f"Error fetching media details in callback: {e}")
        await query.edit_message_text("An error occurred while fetching details.")
        return

    msg = f"*{json_data['title']['romaji']}*(`{json_data['title']['native']}`)\n*Type*: {json_data['format']}\n*Status*: {json_data['status']}\n*Episodes*: {json_data.get('episodes', 'N/A')}\n*Duration*: {json_data.get('duration', 'N/A')} Per Ep.\n*Score*: {json_data['averageScore']}\n*Genres*: `"
    for x in json_data["genres"]:
        msg += f"{x}, "
    msg = msg[:-2] + "`\n"
    msg += "*Studios*: `"
    for x in json_data["studios"]["nodes"]:
        msg += f"{x['name']}, "
    msg = msg[:-2] + "`\n"
    info = json_data.get("siteUrl")
    trailer = json_data.get("trailer", None)
    if trailer:
        trailer_id = trailer.get("id", None)
        site = trailer.get("site", None)
        if site == "youtube":
            trailer = f"https://youtu.be/{trailer_id}"
    description = (
       bs4.BeautifulSoup(json_data.get("description", "N/A"), features="html.parser").text
    )
    msg += shorten(description, info)
    image = json_data.get("bannerImage", None)
    if trailer:
        buttons = [
            [
                InlineKeyboardButton("More Info", url=info),
                InlineKeyboardButton("Trailer 🎬", url=trailer),
            ]
        ]
    else:
        buttons = [[InlineKeyboardButton("More Info", url=info)]]
    if image:
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(image, caption=msg, parse_mode=ParseMode.MARKDOWN),
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        except Exception:
            msg += f" [〽️]({image})"
            await query.edit_message_text(
                msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons),
            )
    else:
        await query.edit_message_text(
            msg,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons),
        )


@cutiepii_callback(pattern=r"anilist_char_(\d+)_(\d+)")
async def character_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    char_id = int(parts[2])
    user_id = int(parts[3])
    if query.from_user.id != user_id:
        await query.answer("This selection is not for you!", show_alert=True)
        return
    variables = {"id": char_id}
    try:
        response = await http.post(
            url, json={"query": character_query, "variables": variables}
        )
        json_data = response.json()
        if "errors" in json_data.keys():
            await query.edit_message_text("Character not found")
            return
        json_data = json_data["data"]["Character"]
    except Exception as e:
        LOGGER.error(f"Error fetching character details in callback: {e}")
        await query.edit_message_text("An error occurred while fetching details.")
        return

    msg = f"*{json_data.get('name').get('full')}*(`{json_data.get('name').get('native')}`)\n"
    description = bs4.BeautifulSoup(f"{json_data['description']}", features="html.parser").text
    site_url = json_data.get("siteUrl")
    msg += shorten(description, site_url)
    image = json_data.get("image", None)
    if image:
        image = image.get("large")
        await query.edit_message_media(
            media=InputMediaPhoto(image, caption=msg.replace("<b>", "</b>"), parse_mode=ParseMode.MARKDOWN),
        )
    else:
        await query.edit_message_text(
            msg.replace("<b>", "</b>"), parse_mode=ParseMode.MARKDOWN
        )


@cutiepii_callback(pattern=r"anilist_manga_(\d+)_(\d+)")
async def manga_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    parts = data.split("_")
    manga_id = int(parts[2])
    user_id = int(parts[3])
    if query.from_user.id != user_id:
        await query.answer("This selection is not for you!", show_alert=True)
        return
    variables = {"id": manga_id}
    try:
        response = await http.post(
            url, json={"query": manga_query, "variables": variables}
        )
        json_data = response.json()
        if "errors" in json_data.keys():
            await query.edit_message_text("Manga not found")
            return
        json_data = json_data["data"]["Media"]
    except Exception as e:
        LOGGER.error(f"Error fetching manga details in callback: {e}")
        await query.edit_message_text("An error occurred while fetching details.")
        return

    msg = ""
    title, title_native = json_data["title"].get("romaji", False), json_data["title"].get(
        "native", False
    )
    start_date, status, score = (
        json_data["startDate"].get("year", False),
        json_data.get("status", False),
        json_data.get("averageScore", False),
    )
    if title:
        msg += f"*{title}*"
        if title_native:
            msg += f"(`{title_native}`)"
    if start_date:
        msg += f"\n*Start Date* - `{start_date}`"
    if status:
        msg += f"\n*Status* - `{status}`"
    if score:
        msg += f"\n*Score* - `{score}`"
    msg += "\n*Genres* - "
    for x in json_data.get("genres", []):
        msg += f"{x}, "
    msg = msg[:-2]
    info = json_data["siteUrl"]
    buttons = [[InlineKeyboardButton("More Info", url=info)]]
    image = json_data.get("bannerImage", False)
    desc_text = bs4.BeautifulSoup(json_data.get('description', 'N/A') or 'N/A', features="html.parser").text
    msg += f"_{desc_text}_"
    if image:
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(image, caption=msg, parse_mode=ParseMode.MARKDOWN),
                reply_markup=InlineKeyboardMarkup(buttons),
            )
        except Exception:
            msg += f" [〽️]({image})"
            await query.edit_message_text(
                msg,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(buttons),
            )
    else:
        await query.edit_message_text(
            msg,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(buttons),
        )


__mod_name__ = "AniList"

__help__ = True
