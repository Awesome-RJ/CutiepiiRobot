"""
Inline Query Module for Cutiepii Robot
Provides inline search capabilities for Nekos, Wallpapers, Action GIFs, and AniList Anime search.
"""

import re
import uuid
import random
import httpx
from typing import List

import html
from telegram import (
    Update,
    InlineQueryResultPhoto,
    InlineQueryResultGif,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler

from Cutiepii_Robot import dispatcher, LOGGER, REDIS, arq
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_inline
from Cutiepii_Robot.modules.helper_funcs.hmtai import (
    sfwNeko,
    slapImages,
    lickImages,
    wallpaperDesktop,
    mobileWallpaper,
)


async def search_anime_inline(query: str) -> List[dict]:
    """Search for anime on AniList."""
    gql_query = """
    query ($search: String) {
      Page (perPage: 5) {
        media (search: $search, type: ANIME) {
          id
          title {
            romaji
            english
            native
          }
          description
          coverImage {
            large
          }
          averageScore
          status
          episodes
        }
      }
    }
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://graphql.anilist.co",
                json={"query": gql_query, "variables": {"search": query}},
                timeout=10,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("Page", {}).get("media", [])
        except Exception as e:
            LOGGER.error(f"Error in inline anime search: {e}")
    return []


async def safe_answer_query(update: Update, results, cache_time=5):
    from telegram.error import BadRequest
    try:
        await update.inline_query.answer(results, cache_time=cache_time)
    except BadRequest as e:
        if "Query is too old" in str(e) or "query id is invalid" in str(e):
            LOGGER.warning(f"Inline query expired: {e}")
        else:
            raise


@cutiepii_inline()
async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline queries."""
    query = update.inline_query.query.strip().lower()
    bot_username = context.bot.username
    results = []

    if not query:
        # Help list with descriptive titles, descriptions, and permanent Icons8 images
        results = [
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🐱 SFW Neko Images",
                description="Get random SFW cute neko images\nType: @{} neko".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/cat.png",
                input_message_content=InputTextMessageContent(
                    f"🐱 <b>SFW Neko Images</b>\n\nTo view neko images, type:\n<code>@{bot_username} neko</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🐱 Try Neko", switch_inline_query_current_chat="neko")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🖼️ Anime Wallpapers",
                description="Get desktop & mobile anime wallpapers\nType: @{} wallpaper".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/wallpaper.png",
                input_message_content=InputTextMessageContent(
                    f"🖼️ <b>Anime Wallpapers</b>\n\nTo view wallpapers, type:\n<code>@{bot_username} wallpaper</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🖼️ Try Wallpapers", switch_inline_query_current_chat="wallpaper")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="👋 Slap GIFs",
                description="Get random anime slap GIFs\nType: @{} slap".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/hand.png",
                input_message_content=InputTextMessageContent(
                    f"👋 <b>Slap GIFs</b>\n\nTo view slap GIFs, type:\n<code>@{bot_username} slap</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="👋 Try Slap", switch_inline_query_current_chat="slap")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="👅 Lick GIFs",
                description="Get random anime lick GIFs\nType: @{} lick".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/tongue.png",
                input_message_content=InputTextMessageContent(
                    f"👅 <b>Lick GIFs</b>\n\nTo view lick GIFs, type:\n<code>@{bot_username} lick</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="👅 Try Lick", switch_inline_query_current_chat="lick")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🤫 Secret Whisper",
                description="Send a private secret message to someone\nType: @{} wspr Username|Message".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/whisper.png",
                input_message_content=InputTextMessageContent(
                    f"🤫 <b>Secret Whisper</b>\n\nTo send a private message, type:\n<code>@{bot_username} wspr [Username/UserID]|[Message]</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🤫 Try Secret Whisper", switch_inline_query_current_chat="wspr ")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🎬 Anime Search",
                description="Search for any anime on AniList\nType: @{} anime <query>".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/anime.png",
                input_message_content=InputTextMessageContent(
                    f"🎬 <b>Anime Search</b>\n\nTo search for an anime, type:\n<code>@{bot_username} anime &lt;query&gt;</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🎬 Try Anime Search", switch_inline_query_current_chat="anime ")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🔍 Google Search",
                description="Search Google/DuckDuckGo\nType: @{} google <query>".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/google-logo.png",
                input_message_content=InputTextMessageContent(
                    f"🔍 <b>Google Search</b>\n\nTo search, type:\n<code>@{bot_username} google &lt;query&gt;</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🔍 Try Google Search", switch_inline_query_current_chat="google ")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🌐 Translator",
                description="Translate text to other languages\nType: @{} tr <lang> <text>".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/translate.png",
                input_message_content=InputTextMessageContent(
                    f"🌐 <b>Translator</b>\n\nTo translate, type:\n<code>@{bot_username} tr [language code] [text]</code>\n\nExample:\n<code>@{bot_username} tr es Hello</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🌐 Try Translator", switch_inline_query_current_chat="tr es Hello")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="📖 Urban Dictionary",
                description="Search word definitions\nType: @{} ud <word>".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/vocabulary.png",
                input_message_content=InputTextMessageContent(
                    f"📖 <b>Urban Dictionary</b>\n\nTo search word definitions, type:\n<code>@{bot_username} ud &lt;word&gt;</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="📖 Try Urban Dictionary", switch_inline_query_current_chat="ud ")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🎥 YouTube Search",
                description="Search YouTube videos\nType: @{} yt <query>".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/youtube-play.png",
                input_message_content=InputTextMessageContent(
                    f"🎥 <b>YouTube Search</b>\n\nTo search videos, type:\n<code>@{bot_username} yt &lt;query&gt;</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🎥 Try YouTube Search", switch_inline_query_current_chat="yt ")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🖼️ Wallpaper Search",
                description="Search high-res wallpapers\nType: @{} wall <query>".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/wallpaper.png",
                input_message_content=InputTextMessageContent(
                    f"🖼️ <b>Wallpaper Search</b>\n\nTo search, type:\n<code>@{bot_username} wall &lt;query&gt;</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🖼️ Try Wallpaper Search", switch_inline_query_current_chat="wall ")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="📥 Torrent Search",
                description="Search torrent database\nType: @{} torrent <query>".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/download-from-cloud.png",
                input_message_content=InputTextMessageContent(
                    f"📥 <b>Torrent Search</b>\n\nTo search, type:\n<code>@{bot_username} torrent &lt;query&gt;</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="📥 Try Torrent Search", switch_inline_query_current_chat="torrent ")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🎵 Lyrics Search",
                description="Search song lyrics\nType: @{} lyrics <song>".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/music.png",
                input_message_content=InputTextMessageContent(
                    f"🎵 <b>Lyrics Search</b>\n\nTo search, type:\n<code>@{bot_username} lyrics &lt;song&gt;</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🎵 Try Lyrics Search", switch_inline_query_current_chat="lyrics ")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="📚 Wikipedia Search",
                description="Search Wikipedia articles\nType: @{} wiki <query>".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/wikipedia.png",
                input_message_content=InputTextMessageContent(
                    f"📚 <b>Wikipedia Search</b>\n\nTo search, type:\n<code>@{bot_username} wiki &lt;query&gt;</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="📚 Try Wikipedia Search", switch_inline_query_current_chat="wiki ")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🎬 TMDB Movie Search",
                description="Search movies and series on TMDB\nType: @{} tmdb <query>".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/movie-projector.png",
                input_message_content=InputTextMessageContent(
                    f"🎬 <b>TMDB Search</b>\n\nTo search, type:\n<code>@{bot_username} tmdb &lt;query&gt;</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🎬 Try TMDB Search", switch_inline_query_current_chat="tmdb ")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🖼️ Google Image Search",
                description="Search images online\nType: @{} image <query>".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/search-in-list.png",
                input_message_content=InputTextMessageContent(
                    f"🖼️ <b>Google Image Search</b>\n\nTo search, type:\n<code>@{bot_username} image &lt;query&gt;</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🖼️ Try Image Search", switch_inline_query_current_chat="image ")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🏓 Ping Test",
                description="Check database response latency\nType: @{} ping".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/speed.png",
                input_message_content=InputTextMessageContent(
                    f"🏓 <b>Ping Test</b>\n\nTo run, type:\n<code>@{bot_username} ping</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🏓 Try Ping Test", switch_inline_query_current_chat="ping")]
                ])
            ),
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="🟢 Alive Status",
                description="Check bot online status\nType: @{} alive".format(bot_username),
                thumbnail_url="https://img.icons8.com/color/96/robot.png",
                input_message_content=InputTextMessageContent(
                    f"🟢 <b>Alive Status</b>\n\nTo check status, type:\n<code>@{bot_username} alive</code>",
                    parse_mode=ParseMode.HTML
                ),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(text="🟢 Try Alive Status", switch_inline_query_current_chat="alive")]
                ])
            ),
        ]
        await safe_answer_query(update, results, cache_time=5)
        return

    # 1. Neko Images
    if query == "neko":
        selected = random.sample(sfwNeko, min(len(sfwNeko), 10))
        for img_url in selected:
            results.append(
                InlineQueryResultPhoto(
                    id=str(uuid.uuid4()),
                    photo_url=img_url,
                    thumbnail_url=img_url,
                    title="Cute Neko",
                    description="SFW Neko Image",
                    caption="✨ <i>Cute Neko!</i>",
                    parse_mode=ParseMode.HTML,
                )
            )

    # 2. Wallpapers
    elif query in ["wallpaper", "wall", "wallpapers"]:
        selected_desktop = random.sample(wallpaperDesktop, min(len(wallpaperDesktop), 5))
        selected_mobile = random.sample(mobileWallpaper, min(len(mobileWallpaper), 5))
        
        for img_url in selected_desktop:
            results.append(
                InlineQueryResultPhoto(
                    id=str(uuid.uuid4()),
                    photo_url=img_url,
                    thumbnail_url=img_url,
                    title="Desktop Wallpaper",
                    description="Anime Desktop Wallpaper",
                    caption="💻 <i>Desktop Wallpaper</i>",
                    parse_mode=ParseMode.HTML,
                )
            )
        for img_url in selected_mobile:
            results.append(
                InlineQueryResultPhoto(
                    id=str(uuid.uuid4()),
                    photo_url=img_url,
                    thumbnail_url=img_url,
                    title="Mobile Wallpaper",
                    description="Anime Mobile Wallpaper",
                    caption="📱 <i>Mobile Wallpaper</i>",
                    parse_mode=ParseMode.HTML,
                )
            )

    # 3. Slap GIFs
    elif query == "slap":
        selected = random.sample(slapImages, min(len(slapImages), 10))
        for gif_url in selected:
            results.append(
                InlineQueryResultGif(
                    id=str(uuid.uuid4()),
                    gif_url=gif_url,
                    thumbnail_url=gif_url,
                    title="Slap!",
                    caption="👋 *Slap!*",
                    parse_mode=ParseMode.MARKDOWN,
                )
            )

    # 4. Lick GIFs
    elif query == "lick":
        selected = random.sample(lickImages, min(len(lickImages), 10))
        for gif_url in selected:
            results.append(
                InlineQueryResultGif(
                    id=str(uuid.uuid4()),
                    gif_url=gif_url,
                    thumbnail_url=gif_url,
                    title="Lick!",
                    caption="👅 *Lick!*",
                    parse_mode=ParseMode.MARKDOWN,
                )
            )

    # 5. Whisper Messages
    elif query.startswith("wspr"):
        inp_parts = query.split(None, 1)
        if len(inp_parts) < 2:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="🤫 Secret Whisper",
                    description="Send a private secret message to someone\nFormat: @BotUsername wspr [Username/UserID]|[Message]",
                    thumbnail_url="https://img.icons8.com/color/96/whisper.png",
                    input_message_content=InputTextMessageContent(
                        f"🤫 <b>How to send a whisper:</b>\n\n"
                        f"Type <code>@{bot_username} wspr [Username or UserID]|[Message]</code>\n\n"
                        f"Example:\n<code>@{bot_username} wspr @durov|Hello Pavel!</code>",
                        parse_mode=ParseMode.HTML
                    ),
                )
            )
        else:
            inp = inp_parts[1].strip()
            if "|" not in inp:
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid.uuid4()),
                        title="🤫 Secret Whisper",
                        description="Format error! Missing '|' separator\nUse: [Username/UserID]|[Message]",
                        thumbnail_url="https://img.icons8.com/color/96/whisper.png",
                        input_message_content=InputTextMessageContent(
                            f"⚠️ <b>Format error:</b>\n"
                            f"Please separate the recipient and message with a <code>|</code> character.\n\n"
                            f"Example:\n<code>@{bot_username} wspr @durov|Hello!</code>",
                            parse_mode=ParseMode.HTML
                        ),
                    )
                )
            else:
                target_user, whisper_msg = inp.split("|", 1)
                target_user = target_user.strip()
                whisper_msg = whisper_msg.strip()
                
                if not target_user or not whisper_msg:
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid.uuid4()),
                            title="🤫 Secret Whisper",
                            description="Recipient or message cannot be empty!",
                            thumbnail_url="https://img.icons8.com/color/96/whisper.png",
                            input_message_content=InputTextMessageContent(
                                f"⚠️ <b>Empty fields:</b>\n"
                                f"Ensure both recipient and message are filled.",
                                parse_mode=ParseMode.HTML
                            ),
                        )
                    )
                else:
                    target_id = None
                    target_name = target_user
                    
                    if target_user.isdigit():
                        target_id = int(target_user)
                    elif target_user.startswith("-") and target_user[1:].isdigit():
                        target_id = int(target_user)
                    
                    if not target_id:
                        try:
                            resolved_chat = await context.bot.get_chat(target_user)
                            target_id = resolved_chat.id
                            target_name = resolved_chat.first_name or resolved_chat.title
                        except Exception:
                            db_user = target_user
                            if db_user.startswith("@"):
                                db_user = db_user[1:]
                            from Cutiepii_Robot.modules.sql.users_sql import get_userid_by_name
                            res_users = get_userid_by_name(db_user)
                            if res_users:
                                target_id = res_users[0].user_id
                                target_name = res_users[0].username or target_user

                    if not target_id:
                        results.append(
                            InlineQueryResultArticle(
                                id=str(uuid.uuid4()),
                                title="🤫 Secret Whisper",
                                description=f"Could not resolve '{target_user}'. Make sure the username is correct.",
                                thumbnail_url="https://img.icons8.com/color/96/whisper.png",
                                input_message_content=InputTextMessageContent(
                                    f"❌ <b>Error:</b> Could not find user <code>{target_user}</code>.\n"
                                    f"The user must have interacted with this bot previously.",
                                    parse_mode=ParseMode.HTML
                                ),
                            )
                        )
                    else:
                        whisper_id = uuid.uuid4().hex[:12]
                        # Store whisper in Redis (expiry of 24h)
                        REDIS.hset(
                            f"whisper:{whisper_id}",
                            mapping={
                                "user_id": target_id,
                                "sender_id": update.effective_user.id,
                                "msg": whisper_msg
                            }
                        )
                        REDIS.expire(f"whisper:{whisper_id}", 86400)
                        
                        text = (
                            f"🤫 <b>Secret message sent!</b>\n\n"
                            f"👤 <b>To:</b> <a href='tg://user?id={target_id}'>{html.escape(target_name)}</a>\n"
                            f"👤 <b>From:</b> {update.effective_user.mention_html()}\n\n"
                            f"<i>Only the recipient and sender can open this message.</i>"
                        )
                        
                        keyboard = InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton("Show Message 🔐", callback_data=f"wspr_{whisper_id}")
                                ]
                            ]
                        )
                        
                        results.append(
                            InlineQueryResultArticle(
                                id=str(uuid.uuid4()),
                                title=f"🤫 Send Secret Message to {target_name}",
                                description="Only they will be able to read it",
                                thumbnail_url="https://img.icons8.com/color/96/whisper.png",
                                input_message_content=InputTextMessageContent(
                                    text,
                                    parse_mode=ParseMode.HTML,
                                    disable_web_page_preview=True
                                ),
                                reply_markup=keyboard
                            )
                        )


    # 7. Google Search (DuckDuckGo Search)
    elif query.startswith("google"):
        search_query = query[6:].strip()
        if not search_query:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Google Search",
                    description="Search Google\nFormat: @BotUsername google [QUERY]",
                    thumbnail_url="https://img.icons8.com/color/96/google-logo.png",
                    input_message_content=InputTextMessageContent(
                        f"🔍 <b>Google Search</b>\n\nType <code>@{bot_username} google [search query]</code>",
                        parse_mode=ParseMode.HTML
                    ),
                )
            )
        else:
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                async with httpx.AsyncClient() as client:
                    r = await client.get(f'https://html.duckduckgo.com/html/?q={search_query}', headers=headers, timeout=10)
                    from bs4 import BeautifulSoup
                    from urllib.parse import urlparse, parse_qs
                    soup = BeautifulSoup(r.text, 'html.parser')
                    for parent in soup.find_all('div', class_='result__body')[:10]:
                        title_a = parent.find('a', class_='result__a')
                        snippet_a = parent.find('a', class_='result__snippet')
                        if title_a:
                            title = title_a.text.strip()
                            raw_link = title_a['href']
                            if raw_link.startswith('//'):
                                raw_link = 'https:' + raw_link
                            parsed = urlparse(raw_link)
                            query_params = parse_qs(parsed.query)
                            link = query_params['uddg'][0] if 'uddg' in query_params else raw_link
                            snippet = snippet_a.text.strip() if snippet_a else ''
                            
                            results.append(
                                InlineQueryResultArticle(
                                    id=str(uuid.uuid4()),
                                    title=title,
                                    description=snippet,
                                    input_message_content=InputTextMessageContent(
                                        f"🔍 <b>Search Result:</b>\n"
                                        f"▪️ <a href='{link}'>{html.escape(title)}</a>\n\n"
                                        f"{html.escape(snippet)}",
                                        parse_mode=ParseMode.HTML,
                                        disable_web_page_preview=False
                                    )
                                )
                            )
            except Exception as e:
                LOGGER.error(f"Error in inline Google search: {e}")

    # 8. Translator
    elif query.startswith("tr"):
        inp_parts = query.split(None, 2)
        if len(inp_parts) < 3:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Translator",
                    description="Translate text to other language\nFormat: @BotUsername tr [LANG] [TEXT]",
                    thumbnail_url="https://img.icons8.com/color/96/translate.png",
                    input_message_content=InputTextMessageContent(
                        f"🌐 <b>Language Translator</b>\n\nType <code>@{bot_username} tr [LANG] [TEXT]</code>\n\nExample:\n<code>@{bot_username} tr fr Hello world</code>",
                        parse_mode=ParseMode.HTML
                    ),
                )
            )
        else:
            lang = inp_parts[1].strip()
            tex = inp_parts[2].strip()
            try:
                res_tr = await arq.translate(tex, lang)
                if res_tr.ok:
                    res_val = res_tr.result
                    msg = (
                        f"🌐 <b>Translated from {res_val.src.upper()} to {res_val.dest.upper()}</b>\n\n"
                        f"<b>INPUT:</b>\n<code>{html.escape(tex)}</code>\n\n"
                        f"<b>OUTPUT:</b>\n<code>{html.escape(res_val.translatedText)}</code>"
                    )
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid.uuid4()),
                            title=f"Translate: {res_val.translatedText[:50]}",
                            description=f"From {res_val.src} to {res_val.dest}",
                            input_message_content=InputTextMessageContent(msg, parse_mode=ParseMode.HTML)
                        )
                    )
                else:
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid.uuid4()),
                            title="Error",
                            description=str(res_tr.result),
                            input_message_content=InputTextMessageContent(f"Error: {res_tr.result}")
                        )
                    )
            except Exception as e:
                LOGGER.error(f"Error in inline translator: {e}")

    # 9. Urban Dictionary
    elif query.startswith("ud"):
        search_query = query[2:].strip()
        if not search_query:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Urban Dictionary",
                    description="Search word definitions\nFormat: @BotUsername ud [QUERY]",
                    thumbnail_url="https://img.icons8.com/color/96/vocabulary.png",
                    input_message_content=InputTextMessageContent(
                        f"📖 <b>Urban Dictionary Search</b>\n\nType <code>@{bot_username} ud [word]</code>",
                        parse_mode=ParseMode.HTML
                    ),
                )
            )
        else:
            try:
                res_ud = await arq.urbandict(search_query)
                if res_ud.ok:
                    results_list = res_ud.result[:10]
                    for i in results_list:
                        clean = lambda x: re.sub(r"[\[\]]", "", x)
                        msg = (
                            f"📖 <b>Word:</b> {html.escape(i.word)}\n\n"
                            f"🗣️ <b>Definition:</b>\n<i>{html.escape(clean(i.definition))}</i>\n\n"
                            f"💡 <b>Example:</b>\n<i>{html.escape(clean(i.example))}</i>"
                        )
                        results.append(
                            InlineQueryResultArticle(
                                id=str(uuid.uuid4()),
                                title=i.word,
                                description=clean(i.definition)[:100],
                                input_message_content=InputTextMessageContent(msg, parse_mode=ParseMode.HTML)
                            )
                        )
                else:
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid.uuid4()),
                            title="Error",
                            description=str(res_ud.result),
                            input_message_content=InputTextMessageContent(f"Error: {res_ud.result}")
                        )
                    )
            except Exception as e:
                LOGGER.error(f"Error in inline Urban Dictionary: {e}")

    # 10. YouTube Search
    elif query.startswith("yt"):
        search_query = query[2:].strip()
        if not search_query:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="YouTube Search",
                    description="Search YouTube videos\nFormat: @BotUsername yt [QUERY]",
                    thumbnail_url="https://img.icons8.com/color/96/youtube-play.png",
                    input_message_content=InputTextMessageContent(
                        f"🎥 <b>YouTube Search</b>\n\nType <code>@{bot_username} yt [video name]</code>",
                        parse_mode=ParseMode.HTML
                    ),
                )
            )
        else:
            try:
                res_yt = await arq.youtube(search_query)
                if res_yt.ok:
                    results_list = res_yt.result[:10]
                    for i in results_list:
                        video_url = f"https://youtube.com{i.url_suffix}"
                        caption = (
                            f"🎥 <b><a href='{video_url}'>{html.escape(i.title)}</a></b>\n\n"
                            f"👤 <b>Channel:</b> {html.escape(i.channel)}\n"
                            f"⏳ <b>Duration:</b> {html.escape(i.duration)}\n"
                            f"👁️ <b>Views:</b> {html.escape(i.views)}\n"
                            f"📅 <b>Uploaded:</b> {html.escape(i.publish_time)}"
                        )
                        results.append(
                            InlineQueryResultArticle(
                                id=str(uuid.uuid4()),
                                title=i.title,
                                description=f"{i.channel} | {i.duration} | {i.views} views",
                                thumbnail_url=i.thumbnails[0] if i.thumbnails else None,
                                input_message_content=InputTextMessageContent(caption, parse_mode=ParseMode.HTML, disable_web_page_preview=False),
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("Watch Video 🎥", url=video_url)]
                                    ])
                            )
                        )
                else:
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid.uuid4()),
                            title="Error",
                            description=str(res_yt.result),
                            input_message_content=InputTextMessageContent(f"Error: {res_yt.result}")
                        )
                    )
            except Exception as e:
                LOGGER.error(f"Error in inline YouTube search: {e}")

    # 11. Wallpaper Search
    elif query.startswith("wall "):
        search_query = query[5:].strip()
        try:
            res_wall = await arq.wall(search_query)
            if res_wall.ok:
                results_list = res_wall.result[:10]
                for i in results_list:
                    results.append(
                        InlineQueryResultPhoto(
                            id=str(uuid.uuid4()),
                            photo_url=i.url_image,
                            thumbnail_url=i.url_thumb,
                            title="Wallpaper",
                            description=f"Download Wallpaper",
                            caption=f"💻 <a href='{i.url_image}'>High-Res Wallpaper</a>",
                            parse_mode=ParseMode.HTML
                        )
                    )
            else:
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid.uuid4()),
                        title="Error",
                        description=str(res_wall.result),
                        input_message_content=InputTextMessageContent(f"Error: {res_wall.result}")
                    )
                )
        except Exception as e:
            LOGGER.error(f"Error in inline Wallpaper search: {e}")

    # 12. Torrent Search
    elif query.startswith("torrent"):
        search_query = query[7:].strip()
        if not search_query:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Torrent Search",
                    description="Search torrent database\nFormat: @BotUsername torrent [QUERY]",
                    thumbnail_url="https://img.icons8.com/color/96/download-from-cloud.png",
                    input_message_content=InputTextMessageContent(
                        f"📥 <b>Torrent Search</b>\n\nType <code>@{bot_username} torrent [query]</code>",
                        parse_mode=ParseMode.HTML
                    ),
                )
            )
        else:
            try:
                res_tor = await arq.torrent(search_query)
                if res_tor.ok:
                    results_list = res_tor.result[:10]
                    for i in results_list:
                        caption = (
                            f"📥 <b>{html.escape(i.name)}</b>\n\n"
                            f"⚖️ <b>Size:</b> {html.escape(i.size)}\n"
                            f"⬆️ <b>Seeds:</b> {html.escape(i.seeds)} | <b>Leechers:</b> {html.escape(i.leechs)}\n"
                            f"📅 <b>Uploaded:</b> {html.escape(i.uploaded)}\n\n"
                            f"🧲 <b>Magnet Link:</b>\n<code>{i.magnet}</code>"
                        )
                        results.append(
                            InlineQueryResultArticle(
                                id=str(uuid.uuid4()),
                                title=i.name,
                                description=f"Size: {i.size} | Seeds: {i.seeds} | L: {i.leechs}",
                                input_message_content=InputTextMessageContent(caption, parse_mode=ParseMode.HTML)
                            )
                        )
                else:
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid.uuid4()),
                            title="Error",
                            description=str(res_tor.result),
                            input_message_content=InputTextMessageContent(f"Error: {res_tor.result}")
                        )
                    )
            except Exception as e:
                LOGGER.error(f"Error in inline Torrent search: {e}")

    # 13. Lyrics Search
    elif query.startswith("lyrics"):
        search_query = query[6:].strip()
        if not search_query:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Lyrics Search",
                    description="Search song lyrics\nFormat: @BotUsername lyrics [SONG]",
                    thumbnail_url="https://img.icons8.com/color/96/music.png",
                    input_message_content=InputTextMessageContent(
                        f"🎵 <b>Lyrics Search</b>\n\nType <code>@{bot_username} lyrics [song name]</code>",
                        parse_mode=ParseMode.HTML
                    ),
                )
            )
        else:
            try:
                res_ly = await arq.lyrics(search_query)
                if res_ly.ok:
                    results_list = res_ly.result[:5]
                    for song in results_list:
                        lyrics_text = song.get("lyrics", "")
                        if len(lyrics_text) > 4000:
                            lyrics_text = lyrics_text[:4000] + "\n\n<i>Lyrics too long to display...</i>"
                        caption = (
                            f"🎵 <b>{html.escape(song.get('song', ''))}</b>\n"
                            f"👤 <b>Artist:</b> {html.escape(song.get('artist', ''))}\n\n"
                            f"{html.escape(lyrics_text)}"
                        )
                        results.append(
                            InlineQueryResultArticle(
                                id=str(uuid.uuid4()),
                                title=song.get("song"),
                                description=song.get("artist"),
                                input_message_content=InputTextMessageContent(caption, parse_mode=ParseMode.HTML)
                            )
                        )
                else:
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid.uuid4()),
                            title="Error",
                            description=str(res_ly.result),
                            input_message_content=InputTextMessageContent(f"Error: {res_ly.result}")
                        )
                    )
            except Exception as e:
                LOGGER.error(f"Error in inline Lyrics search: {e}")

    # 14. Wikipedia Search
    elif query.startswith("wiki"):
        search_query = query[4:].strip()
        if not search_query:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Wikipedia Search",
                    description="Search Wikipedia articles\nFormat: @BotUsername wiki [QUERY]",
                    thumbnail_url="https://img.icons8.com/color/96/wikipedia.png",
                    input_message_content=InputTextMessageContent(
                        f"📚 <b>Wikipedia Search</b>\n\nType <code>@{bot_username} wiki [search query]</code>",
                        parse_mode=ParseMode.HTML
                    ),
                )
            )
        else:
            try:
                res_wiki = await arq.wiki(search_query)
                if res_wiki.ok:
                    results_list = res_wiki.result[:5] if isinstance(res_wiki.result, list) else [res_wiki.result]
                    for item in results_list:
                        title = getattr(item, "title", search_query.capitalize())
                        summary = getattr(item, "summary", str(item))
                        url = getattr(item, "url", "https://wikipedia.org")
                        
                        if len(summary) > 800:
                            summary = summary[:800] + "..."
                        caption = (
                            f"📚 <b><a href='{url}'>{html.escape(title)}</a></b>\n\n"
                            f"{html.escape(summary)}"
                        )
                        results.append(
                            InlineQueryResultArticle(
                                id=str(uuid.uuid4()),
                                title=title,
                                description=summary[:100],
                                input_message_content=InputTextMessageContent(caption, parse_mode=ParseMode.HTML, disable_web_page_preview=False),
                                reply_markup=InlineKeyboardMarkup([
                                    [InlineKeyboardButton("Read Article 🌐", url=url)]
                                    ])
                            )
                        )
                else:
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid.uuid4()),
                            title="Error",
                            description=str(res_wiki.result),
                            input_message_content=InputTextMessageContent(f"Error: {res_wiki.result}")
                        )
                    )
            except Exception as e:
                LOGGER.error(f"Error in inline Wikipedia search: {e}")

    # 15. Movie Search (TMDB)
    elif query.startswith("tmdb"):
        search_query = query[4:].strip()
        if not search_query:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="TMDB Search",
                    description="Search movies and series on TMDB\nFormat: @BotUsername tmdb [QUERY]",
                    thumbnail_url="https://img.icons8.com/color/96/movie-projector.png",
                    input_message_content=InputTextMessageContent(
                        f"🎬 <b>TMDB Search</b>\n\nType <code>@{bot_username} tmdb [movie name]</code>",
                        parse_mode=ParseMode.HTML
                    ),
                )
            )
        else:
            try:
                res_tmdb = await arq.tmdb(search_query)
                if res_tmdb.ok:
                    results_list = res_tmdb.result[:10]
                    for result in results_list:
                        description = result.overview[:800] if result.overview else "No overview available."
                        genre = " | ".join(result.genre) if result.genre else "N/A"
                        caption = (
                            f"🎬 <b>{html.escape(result.title)}</b>\n"
                            f"🎭 <b>Type:</b> {html.escape(result.type or 'Movie')} | ⭐ <b>Rating:</b> {result.rating}\n"
                            f"📁 <b>Genre:</b> {html.escape(genre)}\n"
                            f"📅 <b>Release Date:</b> {html.escape(result.releaseDate or 'N/A')}\n\n"
                            f"📖 <b>Description:</b>\n<i>{html.escape(description)}</i>"
                        )
                        image_url = result.backdrop or result.poster
                        if image_url:
                            results.append(
                                InlineQueryResultPhoto(
                                    id=str(uuid.uuid4()),
                                    photo_url=image_url,
                                    thumbnail_url=image_url,
                                    title=result.title,
                                    description=f"Rating: {result.rating} | Release: {result.releaseDate}",
                                    caption=caption,
                                    parse_mode=ParseMode.HTML
                                )
                            )
                        else:
                            results.append(
                                InlineQueryResultArticle(
                                    id=str(uuid.uuid4()),
                                    title=result.title,
                                    description=f"Rating: {result.rating} | Release: {result.releaseDate}",
                                    input_message_content=InputTextMessageContent(caption, parse_mode=ParseMode.HTML)
                                )
                            )
                else:
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid.uuid4()),
                            title="Error",
                            description=str(res_tmdb.result),
                            input_message_content=InputTextMessageContent(f"Error: {res_tmdb.result}")
                        )
                    )
            except Exception as e:
                LOGGER.error(f"Error in inline TMDB search: {e}")

    # 16. Image Search
    elif query.startswith("image"):
        search_query = query[5:].strip()
        if not search_query:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Image Search",
                    description="Search Google Images\nFormat: @BotUsername image [QUERY]",
                    thumbnail_url="https://img.icons8.com/color/96/search-in-list.png",
                    input_message_content=InputTextMessageContent(
                        f"🖼️ <b>Google Image Search</b>\n\nType <code>@{bot_username} image [search query]</code>",
                        parse_mode=ParseMode.HTML
                    ),
                )
            )
        else:
            try:
                res_img = await arq.image(search_query)
                if res_img.ok:
                    results_list = res_img.result[:15]
                    for i in results_list:
                        results.append(
                            InlineQueryResultPhoto(
                                id=str(uuid.uuid4()),
                                photo_url=i.url,
                                thumbnail_url=i.url,
                                title=search_query.capitalize(),
                                caption=f"🖼️ <a href='{i.url}'>Source Link</a>",
                                parse_mode=ParseMode.HTML
                            )
                        )
                else:
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid.uuid4()),
                            title="Error",
                            description=str(res_img.result),
                            input_message_content=InputTextMessageContent(f"Error: {res_img.result}")
                        )
                    )
            except Exception as e:
                LOGGER.error(f"Error in inline Image search: {e}")

    # 17. Ping
    elif query == "ping":
        try:
            import time
            t1 = time.time()
            REDIS.ping()
            t2 = time.time()
            ping_time = f"{round((t2 - t1) * 1000, 2)} ms"
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Ping Test 🏓",
                    description="Check database response latency",
                    thumbnail_url="https://img.icons8.com/color/96/speed.png",
                    input_message_content=InputTextMessageContent(
                        f"🏓 <b>Pong!</b>\n\n⚡ <b>Database Latency:</b> <code>{ping_time}</code>",
                        parse_mode=ParseMode.HTML
                    ),
                )
            )
        except Exception as e:
            LOGGER.error(f"Error in inline ping: {e}")

    # 18. Alive
    elif query == "alive":
        try:
            bot_info = await context.bot.get_me()
            msg = (
                f"✨ <b>{bot_info.first_name} is Alive & Active!</b>\n\n"
                f"🟢 <b>Status:</b> Running\n"
                f"🐍 <b>Python Version:</b> <code>3.10</code>\n"
                f"📦 <b>PTB Version:</b> <code>22.5</code>\n"
                f"💾 <b>Databases:</b> PostgreSQL & Redis\n\n"
                f"💻 <b>Platform:</b> Windows Server"
            )
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Alive Status 🟢",
                    description="Check if bot is online and working",
                    thumbnail_url="https://img.icons8.com/color/96/robot.png",
                    input_message_content=InputTextMessageContent(msg, parse_mode=ParseMode.HTML),
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Go Inline!", switch_inline_query_current_chat="")]
                    ])
                )
            )
        except Exception as e:
            LOGGER.error(f"Error in inline alive: {e}")

    # 6. Anime Search (explicit prefix or fallback for general text queries)
    else:
        anime_query_str = query[6:].strip() if query.startswith("anime ") else query
        if anime_query_str:
            media_list = await search_anime_inline(anime_query_str)
            for item in media_list:
                romaji_title = item.get("title", {}).get("romaji") or "N/A"
                english_title = item.get("title", {}).get("english") or ""
                native_title = item.get("title", {}).get("native") or "N/A"
                score = item.get("averageScore") or "N/A"
                episodes = item.get("episodes") or "N/A"
                status = item.get("status") or "N/A"
                cover_img = item.get("coverImage", {}).get("large")
                
                desc = item.get("description") or "No description available."
                desc = re.sub(r'<br\s*/?>', '\n', desc)
                desc = re.sub(r'</?(?!(?:b|i|code|pre|u|s|a|span|blockquote)\b)[a-zA-Z0-9]+(?:\s[^>]*)?>', '', desc)
                if len(desc) > 500:
                    desc = desc[:500] + "..."

                title_to_show = romaji_title
                if english_title:
                    title_to_show += f" ({english_title})"

                caption = (
                    f"🎬 <b>{romaji_title}</b>\n"
                    f"🇯🇵 <i>Native: {native_title}</i>\n"
                    f"⭐ <b>Score:</b> {score}% | <b>Episodes:</b> {episodes}\n"
                    f"📊 <b>Status:</b> {status}\n\n"
                    f"{desc}"
                )

                if cover_img:
                    results.append(
                        InlineQueryResultPhoto(
                            id=str(uuid.uuid4()),
                            photo_url=cover_img,
                            thumbnail_url=cover_img,
                            title=title_to_show,
                            description=f"Score: {score}% | Episodes: {episodes}",
                            caption=caption,
                            parse_mode=ParseMode.HTML,
                        )
                    )
                else:
                    results.append(
                        InlineQueryResultArticle(
                            id=str(uuid.uuid4()),
                            title=title_to_show,
                            description=f"Score: {score}% | Episodes: {episodes}",
                            input_message_content=InputTextMessageContent(
                                caption, parse_mode=ParseMode.HTML
                            ),
                        )
                    )

    if not results:
        # Fallback when no match
        no_results_article = InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="🔍 No Results Found",
            description="Tap here to search again or see options",
            thumbnail_url="https://img.icons8.com/color/96/search.png",
            input_message_content=InputTextMessageContent(
                f"❌ <b>No results matched your query.</b>\n\n"
                f"Try typing SFW actions or an anime search:\n"
                f"❍ <code>@{bot_username} neko</code>\n"
                f"❍ <code>@{bot_username} wallpaper</code>\n"
                f"❍ <code>@{bot_username} anime &lt;search query&gt;</code>",
                parse_mode=ParseMode.HTML,
            ),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text="🔍 Try Search Again", switch_inline_query_current_chat="")]
            ])
        )
        results.append(no_results_article)

    await safe_answer_query(update, results, cache_time=5)


__help__ = True

__mod_name__ = "Inline"
__command_list__ = []

@cutiepii_callback(pattern=r"^wspr_")
async def whisper_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    
    cb_data = query.data
    whisper_id = cb_data.split("_")[1]
    
    whisper_data = REDIS.hgetall(f"whisper:{whisper_id}")
    if not whisper_data:
        await query.answer("Oops! This secret message has expired or was deleted.", show_alert=True)
        return
        
    sender_id = int(whisper_data.get(b"sender_id", 0))
    recipient_id = int(whisper_data.get(b"user_id", 0))
    msg = whisper_data.get(b"msg", b"").decode("utf-8")
    
    if user.id not in [sender_id, recipient_id]:
        await query.answer("🔐 This message is not for you!", show_alert=True)
        return
        
    await query.answer(msg, show_alert=True)


__handlers__ = [
]
