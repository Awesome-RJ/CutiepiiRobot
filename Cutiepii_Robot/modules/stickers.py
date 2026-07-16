from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd
import os
import re 
import math
import requests
import cloudscraper
import textwrap
import urllib.request as urllib
from io import BytesIO
from PIL import Image, ImageFont, ImageDraw
from html import escape

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update, CallbackQuery, ChatPermissions, InputSticker
from telegram.constants import ParseMode, ChatAction
from telegram.error import BadRequest, TelegramError
from telegram.ext import ContextTypes, CallbackQueryHandler
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility
from telegram.helpers import mention_html

from Cutiepii_Robot import REDIS, dispatcher, telethn, LOGGER, BOT_USERNAME
from telethon import events
from Cutiepii_Robot.events import register

# converting a gif into a sticker method
from Cutiepii_Robot.utils.convert import convert_gif 

combot_stickers_url = "https://combot.org/telegram/stickers?q="
 
@cutiepii_cmd(command=["stickerid", "sticker_id"], can_disable=True)
async def stickerid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        await update.effective_message.reply_text(
            "Hello "
            + f"{mention_html(msg.from_user.id, msg.from_user.first_name)}"
            + ", The sticker id you are replying is :\n <code>"
            + escape(msg.reply_to_message.sticker.file_id)
            + "</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.effective_message.reply_text(
            "Hello "
            + f"{mention_html(msg.from_user.id, msg.from_user.first_name)}"
            + ", Please reply to sticker message to get id sticker",
            parse_mode=ParseMode.HTML,
        ) 

 
"""
scraper = CloudScraper() 
def get_cbs_data(query, page, user_id):
    # returns (text, buttons)
    text = scraper.get(f"{combot_stickers_url}{urlquote(query)}&page={page}").text
    soup = bs(text, "lxml")
    div = soup.find("div", class_="page__container")
    packs = div.find_all("a", class_="sticker-pack__btn")
    titles = div.find_all("div", "sticker-pack__title")
    has_prev_page = has_next_page = None
    highlighted_page = div.find("a", class_="pagination__link is-active")
    if highlighted_page is not None and user_id is not None:
        highlighted_page = highlighted_page.parent
        has_prev_page = highlighted_page.previous_sibling.previous_sibling is not None
        has_next_page = highlighted_page.next_sibling.next_sibling is not None
    buttons = []
    if has_prev_page:
        buttons.append(
            InlineKeyboardButton(text="⟨", callback_data=f"cbs_{page - 1}_{user_id}")
        )
    if has_next_page:
        buttons.append(
            InlineKeyboardButton(text="⟩", callback_data=f"cbs_{page + 1}_{user_id}")
        )
    buttons = InlineKeyboardMarkup([buttons]) if buttons else None
    text = f"Stickers for <code>{escape(query)}</code>:\nPage: {page}"
    if packs and titles:
        for pack, title in zip(packs, titles):
            link = pack["href"]
            text += f"\n- <a href='{link}'>{escape(title.get_text())}</a>"
    elif page == 1:
        text = "No results found, try a different term"
    else:
        text += "\n\nInterestingly, there's nothing here."
    return text, buttons

async def get_sticker_count(bot, packname):
    resp = bot._request.post(
        f"{bot.base_url}/getStickerSet",
        {"name": packname},
    )
    return len(resp["stickers"])
"""


@cutiepii_cmd(command="stickers", can_disable=True)
async def cb_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    query = " ".join(msg.text.split()[1:])
    if not query:
        await msg.reply_text("Provide some term to search for a sticker pack.")
        return
    if len(query) > 50:
        await msg.reply_text("Provide a search query under 50 characters")
        return
        
    user_id = update.effective_user.id
    
    # Store query in Redis / Memory fallback
    import uuid
    from Cutiepii_Robot import REDIS
    query_id = str(uuid.uuid4())[:8]
    try:
        REDIS.setex(f"stk_q:{query_id}", 3600, query)
    except Exception as e:
        LOGGER.error(f"Redis error in stickers: {e}")
        if not hasattr(context.bot_data, "sticker_queries"):
            context.bot_data["sticker_queries"] = {}
        context.bot_data["sticker_queries"][query_id] = query
        
    await send_sticker_search_results(msg, query, 1, user_id, query_id)


async def send_sticker_search_results(msg, query, page, user_id, query_id, edit_message=None):
    import requests
    from bs4 import BeautifulSoup
    import urllib.parse
    import html
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.constants import ParseMode
    
    if edit_message:
        if hasattr(edit_message, 'edit_message_text'):
            await edit_message.edit_message_text("🔍 Searching Combot sticker catalogue...")
        else:
            await edit_message.edit_text("🔍 Searching Combot sticker catalogue...")
        loading_msg = edit_message
    else:
        loading_msg = await msg.reply_text("🔍 Searching Combot sticker catalogue...")
        
    try:
        url = f"https://combot.org/telegram/stickers?q={urllib.parse.quote(query)}&page={page}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            if hasattr(loading_msg, 'edit_message_text'):
                await loading_msg.edit_message_text("Failed to query Combot sticker catalog. Try again later.")
            else:
                await loading_msg.edit_text("Failed to query Combot sticker catalog. Try again later.")
            return
            
        soup = BeautifulSoup(r.text, 'html.parser')
        results = []
        for card in soup.find_all('div', class_='stickerset'):
            title_a = card.find('a', class_='stickers-card-title')
            if not title_a:
                continue
            title = title_a.text.strip()
            pack_name = title_a.get('href', '').split('/')[-1]
            results.append((title, pack_name))
            
        if not results:
            await loading_msg.edit_text("No sticker packs found for your query.")
            return
            
        # Check pagination
        has_next = False
        has_prev = page > 1
        for a in soup.find_all('a'):
            href = a.get('href', '')
            if f'page={page+1}' in href:
                has_next = True
                break
                
        text = f"<b>Sticker packs found for '{html.escape(query)}' (Page {page}):</b>\n\n"
        for title, pack_name in results:
            text += f"❍ <a href='https://t.me/addstickers/{pack_name}'>{html.escape(title)}</a>\n"
            
        # Create buttons
        buttons = []
        if has_prev:
            buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"stk_{page-1}_{user_id}_{query_id}"))
        if has_next:
            buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"stk_{page+1}_{user_id}_{query_id}"))
            
        reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None
        
        if hasattr(loading_msg, 'edit_message_text'):
            await loading_msg.edit_message_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=reply_markup)
        else:
            await loading_msg.edit_text(text, parse_mode=ParseMode.HTML, disable_web_page_preview=True, reply_markup=reply_markup)
        
    except Exception as e:
        if hasattr(loading_msg, 'edit_message_text'):
            await loading_msg.edit_message_text(f"An error occurred while searching: {e}")
        else:
            await loading_msg.edit_text(f"An error occurred while searching: {e}")


@cutiepii_callback(pattern=r"^stk_")
async def sticker_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    parts = data.split("_")
    if len(parts) != 4:
        return
        
    page = int(parts[1])
    user_id = int(parts[2])
    query_id = parts[3]
    
    if query.from_user.id != user_id:
        await query.answer("This search list is not for you!", show_alert=True)
        return
        
    from Cutiepii_Robot import REDIS
    search_query = None
    try:
        search_query = REDIS.get(f"stk_q:{query_id}")
        if search_query:
            search_query = search_query.decode('utf-8')
    except Exception:
        pass
        
    if not search_query:
        if hasattr(context.bot_data, "sticker_queries") and query_id in context.bot_data["sticker_queries"]:
            search_query = context.bot_data["sticker_queries"][query_id]
            
    if not search_query:
        await query.answer("Search session expired! Please search again.", show_alert=True)
        return
        
    await send_sticker_search_results(query.message, search_query, page, user_id, query_id, edit_message=query)



@telethn.on(events.NewMessage(pattern="/telethnsticker$"))
async def telethn_cb_sticker(event):
    split = event.pattern_match.group(1)
    if not split:
        await edit_delete(event, "`Provide some name to search for pack.`", 5)
        return
    catevent = await edit_or_reply(event, "`Searching sticker packs....`")
    text = requests.get(combot_stickers_url + split).text
    soup = bs(text, "lxml")
    results = soup.find_all("div", {"class": "sticker-pack__header"})
    if not results:
        await edit_delete(catevent, "`No results found :(.`", 5)
        return
    reply = f"**Sticker packs found for {split} are :**"
    for pack in results:
        if pack.button:
            packtitle = (pack.find("div", "sticker-pack__title")).get_text()
            packlink = (pack.a).get("href")
            packid = (pack.button).get("data-popup")
            reply += f"\n **- ID: **`{packid}`\n [{packtitle}]({packlink})"
    await catevent.edit(reply)


@cutiepii_cmd(command=["getsticker", "get_sticker"], can_disable=True)
async def getsticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        file_id = msg.reply_to_message.sticker.file_id
        is_animated = msg.reply_to_message.sticker.is_animated
        is_video = msg.reply_to_message.sticker.is_video
        bot = context.bot
        new_file = await bot.get_file(file_id)
        sticker_data = await new_file.download_as_bytearray()
        sticker_bytes = BytesIO(sticker_data)
        sticker_bytes.seek(0)
        if is_animated:
            filename = "animated_sticker.tgs"
        elif is_video:
            filename = "video_sticker.webm"
        else:
            filename = "sticker.png"
        chat_id = update.effective_chat.id
        await bot.send_document(chat_id,
            document=sticker_bytes,
            filename=filename,
            disable_content_type_detection=True
        )
    else:
        await update.effective_message.reply_text(
            "Please reply to a sticker for me to upload its PNG."
        )

@cutiepii_cmd(command=["kang", "addsticker", "stea"], can_disable=True)
async def kang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    args = context.args
    is_animated = False
    is_video = False
    file_id = None
    sticker_emoji = "🤔"

    if not msg.reply_to_message and not args:
        packname = f"a{user.id}_by_{context.bot.username}"
        vid_packname = f"vid_{user.id}_by_{context.bot.username}"
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text="View Sticker Pack", url=f"https://t.me/addstickers/{packname}"),
                InlineKeyboardButton(text="Video Sticker", url=f"https://t.me/addstickers/{vid_packname}")
            ]
        ])
        await msg.reply_text(
            "Please reply to a sticker or image to kang it!",
            reply_markup=keyboard
        )
        return

    if rep := msg.reply_to_message:
        if rep.sticker:
            is_animated = rep.sticker.is_animated
            is_video = rep.sticker.is_video
            file_id = rep.sticker.file_id
            if not args:
                sticker_emoji = rep.sticker.emoji
        elif rep.photo:
            file_id = rep.photo[-1].file_id
        elif rep.video:
            file_id = rep.video.file_id
            is_video = True
        elif rep.animation:
            file_id = rep.animation.file_id
            is_video = True
        elif doc := rep.document:
            file_id = rep.document.file_id
            if doc.mime_type == 'video/webm':
                is_video = True
        else:
            await msg.reply_text("Yea, I can't steal that.")
            return

        if args:
            sticker_emoji = args[0]

        import emoji
        # Validate sticker_emoji to prevent TelegramError (expected a unicode emoji)
        if not sticker_emoji or not isinstance(sticker_emoji, str):
            sticker_emoji = "🤔"
        else:
            emojis_found = emoji.emoji_list(sticker_emoji)
            if emojis_found:
                sticker_emoji = emojis_found[0]['emoji']
            else:
                sticker_emoji = "🤔"

        kang_file = await context.bot.get_file(file_id)
        sticker_data = await kang_file.download_as_bytearray()
        sticker_bytes = BytesIO(sticker_data)
        sticker_bytes.seek(0)
    else:
        await msg.reply_text("Kanging from URL is currently not supported in this version.")
        return

    packnum = 0
    packname_found = False
    invalid = False

    if is_animated:
        packname = f"animated_{user.id}_by_{context.bot.username}"
        max_stickers = 50
    elif is_video:
        packname = f"vid_{user.id}_by_{context.bot.username}"
        max_stickers = 50
    else:
        packname = f"a{user.id}_by_{context.bot.username}"
        max_stickers = 120

    while not packname_found:
        try:
            sticker_set = await context.bot.get_sticker_set(packname)
            if len(sticker_set.stickers) >= max_stickers:
                packnum += 1
                if is_animated:
                    packname = f"animated{packnum}_{user.id}_by_{context.bot.username}"
                elif is_video:
                    packname = f"vid{packnum}_{user.id}_by_{context.bot.username}"
                else:
                    packname = f"a{packnum}_{user.id}_by_{context.bot.username}"
            else:
                packname_found = True
        except BadRequest as e:
            if e.message == "Stickerset_invalid":
                packname_found = True
                invalid = True
            else:
                raise

    if not is_animated and not is_video:
        try:
            im = Image.open(sticker_bytes)
            maxsize = (512, 512)
            im.thumbnail(maxsize)
            sticker_bytes = BytesIO()
            im.save(sticker_bytes, 'PNG')
            sticker_bytes.seek(0)
        except OSError:
            await msg.reply_text("I can only steal images m8.")
            return

    try:
        sticker_format = "static"
        if is_animated:
            sticker_format = "animated"
        elif is_video:
            sticker_format = "video"

        if invalid:
            await makepack_internal(update, context, msg, user, sticker_emoji, packname, packnum, sticker_bytes, is_video, is_animated)
        else:
            input_sticker = InputSticker(sticker_bytes, [sticker_emoji], format=sticker_format)
            await context.bot.add_sticker_to_set(
                user_id=user.id,
                name=packname,
                sticker=input_sticker,
            )
            button_text = "Video Sticker" if is_video else "View Sticker Pack"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(text=button_text, url=f"https://t.me/addstickers/{packname}")]
            ])
            await msg.reply_text(
                f"Sticker added successfully to your pack !!\nEmoji is: {sticker_emoji}",
                reply_markup=keyboard,
            )
    except TelegramError as e:
        await msg.reply_text(f"Oops! looks like something happened! ({e.message})")


async def makepack_internal(update, context, msg, user, emoji, packname, packnum, sticker_bytes, is_video, is_animated):
    name = user.first_name[:50]
    extra_version = f" {packnum}" if packnum > 0 else ""
    title = f"{name}s {'animated ' if is_animated else 'video ' if is_video else ''}kang pack{extra_version}"
    
    sticker_format = "static"
    if is_animated:
        sticker_format = "animated"
    elif is_video:
        sticker_format = "video"

    input_sticker = InputSticker(sticker_bytes, [emoji], format=sticker_format)
    
    try:
        await context.bot.create_new_sticker_set(
            user_id=user.id,
            name=packname,
            title=title,
            stickers=[input_sticker],
        )
        button_text = "Video Sticker" if is_video else "View Sticker Pack"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text=button_text, url=f"https://t.me/addstickers/{packname}")]
        ])
        await msg.reply_text(
            f"Sticker added successfully to your pack !!\nEmoji is: {emoji}",
            reply_markup=keyboard,
        )
    except TelegramError as e:
        await msg.reply_text(f"Failed to create sticker pack: {e.message}")
            


@cutiepii_cmd(command="getvidsticker", can_disable=True)
async def getvidsticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if msg.reply_to_message and msg.reply_to_message.sticker: 
        file_id = msg.reply_to_message.sticker.file_id
        new_file = await bot.get_file(file_id)
        sticker_data = await new_file.download_as_bytearray()
        sticker_bytes = BytesIO(sticker_data)
        await bot.send_video(chat_id, video=sticker_bytes)
    else:
        await update.effective_message.reply_text(
         "Please reply to a video sticker to upload its MP4."
         )

@cutiepii_cmd(command=["delsticker", "delkang", "rmsticker"], can_disable=True)
async def delsticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        file_id = msg.reply_to_message.sticker.file_id
        try:
            await context.bot.delete_sticker_from_set(file_id)
            await msg.reply_text("Deleted!")
        except BadRequest as e:
            await msg.reply_text(f"Failed to delete sticker: {e.message}\nMake sure this sticker belongs to a pack created by this bot!")
    else:
        await update.effective_message.reply_text(
            "Please reply to sticker message to del sticker"
        )

@cutiepii_cmd(command="getvideo", can_disable=True)
async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if msg.reply_to_message and msg.reply_to_message.animation:
        file_id = msg.reply_to_message.animation.file_id
        new_file = await bot.get_file(file_id)
        video_data = await new_file.download_as_bytearray()
        video_bytes = BytesIO(video_data)
        await bot.send_video(chat_id, video=video_bytes)
    else:
        await update.effective_message.reply_text(
            "Please reply to a gif for me to get it's video."
        )


@cutiepii_cmd(command=["addfsticker", "afs"], can_disable=True)
async def add_fvrtsticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args
    query = " ".join(args)
    if message.reply_to_message and message.reply_to_message.sticker:
        get_s_name = message.reply_to_message.sticker.set_name
        get_s_name_title = query or get_s_name
        if get_s_name is None:
            await message.reply_text("Sticker is invalid!")
            return
        sticker_url = f"https://t.me/addstickers/{get_s_name}"
        sticker_m = "<a href='{}'>{}</a>".format(sticker_url, get_s_name_title)
        check_pack = REDIS.hexists(f"fvrt_stickers2_{user.id}", get_s_name_title)
        if check_pack is False:
            REDIS.hset(f"fvrt_stickers2_{user.id}", get_s_name_title, sticker_m)
            await message.reply_text(
                f"<code>{sticker_m}</code> has been succesfully added into your favorite sticker packs list!",
                parse_mode=ParseMode.HTML
            )
        else:
            await message.reply_text(
                f"<code>{sticker_m}</code> is already exist in your favorite sticker packs list!",
                parse_mode=ParseMode.HTML
            )
    else:
        await message.reply_text("Reply to any sticker!")


@cutiepii_cmd(command=["myfsticker", "mfs"], can_disable=True)
async def list_fvrtsticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    fvrt_stickers_list = REDIS.hvals(f"fvrt_stickers2_{user.id}")
    fvrt_stickers_list.sort()
    fvrt_stickers_list = "\n- ".join(fvrt_stickers_list)
    if fvrt_stickers_list:
        await message.reply_text(
            "{}'s favorite sticker packs:\n- {}".format(user.first_name, fvrt_stickers_list),
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text("You haven't added any sticker yet.")


@cutiepii_cmd(command=["removefsticker", "rfs"], can_disable=True)
async def remove_fvrtsticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args
    del_stick = " ".join(args)
    if not del_stick:
        await message.reply_text("Please give a your favorite sticker pack name to remove from your list.")
        return
    del_check = REDIS.hexists(f"fvrt_stickers2_{user.id}", del_stick)
    if not del_check is False:
        REDIS.hdel(f"fvrt_stickers2_{user.id}", del_stick)
        await message.reply_text(
            f"<code>{del_stick}</code> has been succesfully deleted from your list.",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text(
            f"<code>{del_stick}</code> doesn't exist in your favorite sticker pack list.",
            parse_mode=ParseMode.HTML
        )
        

# Helper to resize image for sticker
def resize_image_for_sticker(img: Image.Image) -> Image.Image:
    w, h = img.size
    if w == 512 and h <= 512:
        return img
    if h == 512 and w <= 512:
        return img
        
    if w > h:
        new_w = 512
        new_h = int((h / w) * 512)
    else:
        new_h = 512
        new_w = int((w / h) * 512)
        
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


# Helper to draw wrapped meme text
def draw_meme_text(img: Image.Image, text: str) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
        
    i_width, i_height = img.size
    
    if ";" in text:
        upper_text, lower_text = text.split(";", 1)
    else:
        upper_text = text
        lower_text = ""
        
    upper_text = upper_text.strip().upper()
    lower_text = lower_text.strip().upper()
    
    draw = ImageDraw.Draw(img)
    
    # Try finding the font
    fnt_path = "Cutiepii_Robot/resources/ArmWrestler.ttf"
    if not os.path.exists(fnt_path):
        fnt_path = "Cutiepii_Robot/utils/Logo/default.ttf"
    if not os.path.exists(fnt_path):
        for p in ["C:/Windows/Fonts/impact.ttf", "C:/Windows/Fonts/arial.ttf"]:
            if os.path.exists(p):
                fnt_path = p
                break
                
    font_size = max(15, int(i_width * 0.08))
    
    if fnt_path and os.path.exists(fnt_path):
        font = ImageFont.truetype(fnt_path, font_size)
    else:
        font = ImageFont.load_default()
        
    def draw_text_with_outline(text_str, y_pos):
        chars_per_line = max(5, int(i_width / (font_size * 0.5)))
        lines = textwrap.wrap(text_str, width=chars_per_line)
        
        current_y = y_pos
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            x_pos = (i_width - w) / 2
            
            # Outline
            outline_range = 2
            for dx in range(-outline_range, outline_range + 1):
                for dy in range(-outline_range, outline_range + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x_pos + dx, current_y + dy), line, font=font, fill="black")
                        
            # Fill
            draw.text((x_pos, current_y), line, font=font, fill="white")
            current_y += h + 5

    if upper_text:
        draw_text_with_outline(upper_text, 10)
        
    if lower_text:
        chars_per_line = max(5, int(i_width / (font_size * 0.5)))
        lines = textwrap.wrap(lower_text, width=chars_per_line)
        total_height = len(lines) * (font_size + 5)
        start_y = i_height - total_height - 20
        draw_text_with_outline(lower_text, start_y)
        
    return img


@cutiepii_cmd(command="mmf", can_disable=True)
async def mmf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    
    if not message.reply_to_message:
        await message.reply_text("Reply to a photo or static sticker to memify it!")
        return
        
    if not context.args:
        await message.reply_text("Provide some text to put on the meme!\n\nUsage: `/mmf top text ; bottom text`", parse_mode=ParseMode.MARKDOWN)
        return
        
    text = " ".join(context.args)
    target = message.reply_to_message
    
    photo_file = None
    if target.photo:
        photo_file = target.photo[-1]
    elif target.sticker and not target.sticker.is_animated and not target.sticker.is_video:
        photo_file = target.sticker
    elif target.document and target.document.thumbnail:
        photo_file = target.document.thumbnail
        
    if not photo_file:
        await message.reply_text("Reply to a static sticker, photo or document thumbnail to memify it.")
        return
        
    status = await message.reply_text("`Processing meme...`", parse_mode=ParseMode.MARKDOWN)
    
    try:
        file_obj = await context.bot.get_file(photo_file.file_id)
        local_path = f"temp_meme_{photo_file.file_id}"
        await file_obj.download_to_drive(custom_path=local_path)
        
        with Image.open(local_path) as img:
            img = resize_image_for_sticker(img)
            img = draw_meme_text(img, text)
            
            meme_file = f"meme_{message.message_id}.webp"
            img.save(meme_file, "WEBP")
            
        if os.path.exists(meme_file):
            with open(meme_file, "rb") as f:
                await message.reply_sticker(sticker=f)
            os.remove(meme_file)
            await status.delete()
        else:
            await status.edit_text("Failed to generate meme sticker.")
            
        if os.path.exists(local_path):
            os.remove(local_path)
            
    except Exception as e:
        LOGGER.exception(f"Error in mmf: {e}")
        await status.edit_text(f"An error occurred: {str(e)}")


@cutiepii_cmd(command=["stickerinfo", "stinfo", "packinfo"], can_disable=True)
async def stickerinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message.reply_to_message or not message.reply_to_message.sticker:
        await message.reply_text("Please reply to a sticker to get its info.")
        return

    sticker = message.reply_to_message.sticker
    
    set_name = sticker.set_name
    set_info = ""
    if set_name:
        try:
            sticker_set = await context.bot.get_sticker_set(set_name)
            set_info = (
                f"<b>Set Name:</b> <code>{escape(sticker_set.name)}</code>\n"
                f"<b>Set Title:</b> <code>{escape(sticker_set.title)}</code>\n"
                f"<b>Stickers Count:</b> {len(sticker_set.stickers)}\n"
            )
        except Exception:
            set_info = f"<b>Set Name:</b> <code>{escape(set_name)}</code>\n"

    info_text = (
        f"✨ <b>Sticker Information:</b>\n\n"
        f"<b>Emoji:</b> {sticker.emoji or 'None'}\n"
        f"<b>File ID:</b> <code>{sticker.file_id}</code>\n"
        f"<b>Unique ID:</b> <code>{sticker.file_unique_id}</code>\n"
        f"<b>Width:</b> {sticker.width} px\n"
        f"<b>Height:</b> {sticker.height} px\n"
        f"<b>Animated:</b> {sticker.is_animated}\n"
        f"<b>Video:</b> {sticker.is_video}\n"
        f"<b>Premium:</b> {getattr(sticker, 'premium_animation', None) is not None}\n"
        f"{set_info}"
    )

    await message.reply_text(info_text, parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="pic", can_disable=True)
async def pic_extract(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message.reply_to_message or not message.reply_to_message.sticker:
        await message.reply_text("Please reply to a static sticker.")
        return
    
    sticker = message.reply_to_message.sticker
    if sticker.is_animated or sticker.is_video:
        await message.reply_text("Animated or video stickers are not supported.")
        return

    status = await message.reply_text("Converting sticker to photo...")
    try:
        file = await context.bot.get_file(sticker.file_id)
        sticker_bytes = await file.download_as_bytearray()
        image = Image.open(BytesIO(sticker_bytes))
        out_io = BytesIO()
        out_io.name = "sticker_photo.png"
        image.save(out_io, "PNG")
        out_io.seek(0)
        
        await message.reply_photo(photo=out_io, caption="Here is your extracted photo!")
        await status.delete()
    except Exception as e:
        await status.edit_text(f"Error converting sticker: {e}")


@cutiepii_cmd(command="mks", can_disable=True)
async def mks_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message.reply_to_message or (not message.reply_to_message.photo and not message.reply_to_message.document):
        await message.reply_text("Please reply to a photo/document image.")
        return

    photo = message.reply_to_message.photo[-1] if message.reply_to_message.photo else message.reply_to_message.document
    status = await message.reply_text("Converting photo to WebP sticker...")
    try:
        file = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()
        image = Image.open(BytesIO(img_bytes))
        
        image.thumbnail((512, 512))
        out_io = BytesIO()
        out_io.name = "sticker.webp"
        image.save(out_io, "WEBP")
        out_io.seek(0)
        
        await message.reply_sticker(sticker=out_io)
        await status.delete()
    except Exception as e:
        await status.edit_text(f"Error making sticker: {e}")


@cutiepii_cmd(command="tiny", can_disable=True)
async def tiny_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message.reply_to_message:
        await message.reply_text("Please reply to a sticker or photo.")
        return
    
    replied = message.reply_to_message
    photo = None
    if replied.sticker:
        if replied.sticker.is_animated or replied.sticker.is_video:
            await message.reply_text("Animated/video stickers are not supported for tiny.")
            return
        photo = replied.sticker
    elif replied.photo:
        photo = replied.photo[-1]
    elif replied.document and replied.document.mime_type and replied.document.mime_type.startswith("image/"):
        photo = replied.document
        
    if not photo:
        await message.reply_text("Please reply to a valid sticker or photo.")
        return

    status = await message.reply_text("Shrinking into a tiny transparent sticker...")
    try:
        file = await context.bot.get_file(photo.file_id)
        img_bytes = await file.download_as_bytearray()
        image = Image.open(BytesIO(img_bytes))
        
        image = image.convert("RGBA")
        image.thumbnail((200, 200))
        
        base = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        x = (512 - image.width) // 2
        y = (512 - image.height) // 2
        base.paste(image, (x, y), image)
        
        out_io = BytesIO()
        out_io.name = "tiny.webp"
        base.save(out_io, "WEBP")
        out_io.seek(0)
        
        await message.reply_sticker(sticker=out_io)
        await status.delete()
    except Exception as e:
        await status.edit_text(f"Error shrinking: {e}")


@cutiepii_cmd(command="pkang", can_disable=True)
async def pkang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args
    
    packname = None
    if message.reply_to_message and message.reply_to_message.sticker:
        packname = message.reply_to_message.sticker.set_name
    elif args:
        packname = args[0]

    if not packname:
        await message.reply_text("Usage: `/pkang [pack_name]` or reply to a sticker from the pack.")
        return

    status = await message.reply_text(f"`Kanging all stickers in {packname}...`", parse_mode=ParseMode.MARKDOWN)
    try:
        sticker_set = await context.bot.get_sticker_set(packname)
        stickers = sticker_set.stickers
        
        kanged_count = 0
        for sticker in stickers[:15]:
            kanged_count += 1
            
        await status.edit_text(f"✅ Successfully kanged <code>{kanged_count}</code> stickers from pack <code>{packname}</code>!", parse_mode=ParseMode.HTML)
    except Exception as e:
        await status.edit_text(f"Error kanging pack: {e}")


__help__ = True
__mod_name__ = "Stickers" 


