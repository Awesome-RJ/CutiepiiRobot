import os
import math
import textwrap
from cloudscraper import CloudScraper
import urllib.request as urllib

from PIL import Image, ImageFont, ImageDraw
from html import escape
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import TelegramError
from telegram import Update
from telegram.ext import CallbackContext, CallbackQueryHandler
from telegram.constants import ParseMode
from telegram.helpers import mention_html
from urllib.parse import quote as urlquote
from bs4 import BeautifulSoup

from Cutiepii_Robot import REDIS, CUTIEPII_PTB, telethn, LOGGER
from Cutiepii_Robot.events import register as Cutiepii
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler

combot_stickers_url = "https://combot.org/telegram/stickers?q="
scraper = CloudScraper()


def get_cbs_data(query, page, user_id):
    # returns (text, buttons)
    text = scraper.get(
        f'{combot_stickers_url}{urlquote(query)}&page={page}').text
    soup = BeautifulSoup(text, 'lxml')
    div = soup.find('div', class_='page__container')
    packs = div.find_all('a', class_='sticker-pack__btn')
    titles = div.find_all('div', 'sticker-pack__title')
    has_prev_page = has_next_page = None
    highlighted_page = div.find('a', class_='pagination__link is-active')
    if highlighted_page is not None and user_id is not None:
        highlighted_page = highlighted_page.parent
        has_prev_page = highlighted_page.previous_sibling.previous_sibling is not None
        has_next_page = highlighted_page.next_sibling.next_sibling is not None
    buttons = []
    if has_prev_page:
        buttons.append(
            InlineKeyboardButton(text='⬅️',
                                 callback_data=f'cbs_{page - 1}_{user_id}'))
    if has_next_page:
        buttons.append(
            InlineKeyboardButton(text='➡️',
                                 callback_data=f'cbs_{page + 1}_{user_id}'))
    buttons = InlineKeyboardMarkup([buttons]) if buttons else None
    text = f'Stickers for <code>{escape(query)}</code>:\nPage: {page}'
    if packs and titles:
        for pack, title in zip(packs, titles):
            link = pack['href']
            text += f"\n➛ <a href='{link}'>{escape(title.get_text())}</a>"
    elif page == 1:
        text = 'No results found, try a different term'
    else:
        text += "\n\nInterestingly, there's nothing here."
    return text, buttons


async def stickerid(update: Update):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        await msg.reply_text(
            "Hello " +
            f"{mention_html(msg.from_user.id, msg.from_user.first_name)}" +
            ", The sticker id you are replying is :\n <code>" +
            escape(msg.reply_to_message.sticker.file_id) + "</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await msg.reply_text(
            "Hello " +
            f"{mention_html(msg.from_user.id, msg.from_user.first_name)}" +
            ", Please reply to sticker message to get id sticker",
            parse_mode=ParseMode.HTML,
        )


async def kang(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message
    user = update.effective_user
    args = context.args
    packnum = 0
    packname = "a" + str(user.id) + "_by_" + context.bot.username
    packname_found = 0
    max_stickers = 120

    while packname_found == 0:
        try:
            stickerset = context.bot.get_sticker_set(packname)
            if len(stickerset.stickers) >= max_stickers:
                packnum += 1
                packname = ("a" + str(packnum) + "_" + str(user.id) + "_by_" +
                            context.bot.username)
            else:
                packname_found = 1
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                packname_found = 1
    kangsticker = "kangsticker.png"
    is_animated = False
    is_video = False
    file_id = ""

    if msg.reply_to_message:
        if msg.reply_to_message.sticker:
            if msg.reply_to_message.sticker.is_animated:
                is_animated = True
            if msg.reply_to_message.sticker.is_video:
                is_video = True
            file_id = msg.reply_to_message.sticker.file_id

        elif msg.reply_to_message.photo:
            file_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            file_id = msg.reply_to_message.document.file_id
        elif msg.reply_to_message.video:
            file_id = msg.reply_to_message.video[-1].file_id
        else:
            await msg.reply_text("Yea, I can't kang that.")

        kang_file = await context.bot.get_file(file_id)

        if is_video:
            kang_file.download("kangsticker.webm")
        elif is_animated:
            kang_file.download("kangsticker.tgs")
        else:
            kang_file.download("kangsticker.png")

        if args:
            sticker_emoji = str(args[0])
        elif msg.reply_to_message.sticker and msg.reply_to_message.sticker.emoji:
            sticker_emoji = msg.reply_to_message.sticker.emoji
        else:
            sticker_emoji = "🙂"

        if not is_animated and not is_video:
            try:
                im = Image.open(kangsticker)
                maxsize = (512, 512)
                if (im.width and im.height) < 512:
                    size1 = im.width
                    size2 = im.height
                    if im.width > im.height:
                        scale = 512 / size1
                        size1new = 512
                        size2new = size2 * scale
                    else:
                        scale = 512 / size2
                        size1new = size1 * scale
                        size2new = 512
                    size1new = math.floor(size1new)
                    size2new = math.floor(size2new)
                    sizenew = (size1new, size2new)
                    im = im.resize(sizenew)
                else:
                    im.thumbnail(maxsize)
                if not msg.reply_to_message.sticker:
                    im.save(kangsticker, "PNG")
                context.bot.add_sticker_to_set(
                    user_id=user.id,
                    name=packname,
                    png_sticker=open("kangsticker.png", "rb"),
                    emojis=sticker_emoji,
                )
                edited_keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton(text="View Pack",
                                         url=f"t.me/addstickers/{packname}")
                ]])
                await msg.reply_text(
                    f"<b>Your sticker has been added!</b>"
                    f"\nEmoji Is : {sticker_emoji}",
                    reply_markup=edited_keyboard,
                    parse_mode=ParseMode.HTML,
                )

            except OSError as e:

                LOGGER.debug(e)
                return

            except TelegramError as e:
                if e.message == "Stickerset_invalid":
                    makepack_internal(
                        update,
                        context,
                        msg,
                        user,
                        sticker_emoji,
                        packname,
                        packnum,
                        png_sticker=open("kangsticker.png", "rb"),
                    )

                elif e.message == "Sticker_png_dimensions":
                    im.save(kangsticker, "PNG")
                    context.bot.add_sticker_to_set(
                        user_id=user.id,
                        name=packname,
                        png_sticker=open("kangsticker.png", "rb"),
                        emojis=sticker_emoji,
                    )
                    edited_keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            text="View Pack",
                            url=f"t.me/addstickers/{packname}")
                    ]])
                    await msg.reply_text(
                        f"<b>Your sticker has been added!</b>"
                        f"\nEmoji Is : {sticker_emoji}",
                        reply_markup=edited_keyboard,
                        parse_mode=ParseMode.HTML,
                    )
                elif e.message == "Invalid sticker emojis":
                    await msg.reply_text("Invalid emoji(s).")
                elif e.message == "Stickers_too_much":
                    await msg.reply_text(
                        "Max packsize reached. Press F to pay respecc.")
                elif e.message == "Internal Server Error: sticker set not found (500)":
                    edited_keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            text="View Pack",
                            url=f"t.me/addstickers/{packname}")
                    ]])
                    await msg.reply_text(
                        f"<b>Your sticker has been added!</b>"
                        f"\nEmoji Is : {sticker_emoji}",
                        reply_markup=edited_keyboard,
                        parse_mode=ParseMode.HTML,
                    )
                LOGGER.debug(e)

        elif is_animated:
            packname = "animated" + str(
                user.id) + "_by_" + context.bot.username
            packname_found = 0
            max_stickers = 50
            while packname_found == 0:
                try:
                    stickerset = context.bot.get_sticker_set(packname)
                    if len(stickerset.stickers) >= max_stickers:
                        packnum += 1
                        packname = ("animated" + str(packnum) + "_" +
                                    str(user.id) + "_by_" +
                                    context.bot.username)
                    else:
                        packname_found = 1
                except TelegramError as e:
                    if e.message == "Stickerset_invalid":
                        packname_found = 1
            try:
                context.bot.add_sticker_to_set(
                    user_id=user.id,
                    name=packname,
                    tgs_sticker=open("kangsticker.tgs", "rb"),
                    emojis=sticker_emoji,
                )
                edited_keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton(text="View Pack",
                                         url=f"t.me/addstickers/{packname}")
                ]])
                await msg.reply_text(
                    f"<b>Your sticker has been added!</b>"
                    f"\nEmoji Is : {sticker_emoji}",
                    reply_markup=edited_keyboard,
                    parse_mode=ParseMode.HTML,
                )
            except TelegramError as e:
                if e.message == "Stickerset_invalid":
                    makepack_internal(
                        update,
                        context,
                        msg,
                        user,
                        sticker_emoji,
                        packname,
                        packnum,
                        tgs_sticker=open("kangsticker.tgs", "rb"),
                    )

                elif e.message == "Invalid sticker emojis":
                    await msg.reply_text("Invalid emoji(s).")
                elif e.message == "Internal Server Error: sticker set not found (500)":
                    edited_keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            text="View Pack",
                            url=f"t.me/addstickers/{packname}")
                    ]])
                    await msg.reply_text(
                        f"<b>Your sticker has been added!</b>"
                        f"\nEmoji Is : {sticker_emoji}",
                        reply_markup=edited_keyboard,
                        parse_mode=ParseMode.HTML,
                    )
                LOGGER.debug(e)
        else:
            packname = "video" + str(user.id) + "_by_" + context.bot.username
            packname_found = 0
            max_stickers = 50
            while packname_found == 0:
                try:
                    stickerset = context.bot.get_sticker_set(packname)
                    if len(stickerset.stickers) >= max_stickers:
                        packnum += 1
                        packname = ("video" + str(packnum) + "_" +
                                    str(user.id) + "_by_" +
                                    context.bot.username)
                    else:
                        packname_found = 1
                except TelegramError as e:
                    if e.message == "Stickerset_invalid":
                        packname_found = 1
            try:
                context.bot.add_sticker_to_set(
                    user_id=user.id,
                    name=packname,
                    webm_sticker=open("kangsticker.webm", "rb"),
                    emojis=sticker_emoji,
                )
                edited_keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton(text="View Pack",
                                         url=f"t.me/addstickers/{packname}")
                ]])
                await msg.reply_text(
                    f"<b>Your sticker has been added!</b>"
                    f"\nEmoji Is : {sticker_emoji}",
                    reply_markup=edited_keyboard,
                    parse_mode=ParseMode.HTML,
                )
            except TelegramError as e:
                if e.message == "Stickerset_invalid":
                    makepack_internal(
                        update,
                        context,
                        msg,
                        user,
                        sticker_emoji,
                        packname,
                        packnum,
                        webm_sticker=open("kangsticker.webm", "rb"),
                    )

                elif e.message == "Invalid sticker emojis":
                    await msg.reply_text("Invalid emoji(s).")
                elif e.message == "Internal Server Error: sticker set not found (500)":
                    edited_keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton(
                            text="View Pack",
                            url=f"t.me/addstickers/{packname}")
                    ]])
                    await msg.reply_text(
                        f"<b>Your sticker has been added!</b>"
                        f"\nEmoji Is : {sticker_emoji}",
                        reply_markup=edited_keyboard,
                        parse_mode=ParseMode.HTML,
                    )
                LOGGER.debug(e)

    elif args:
        try:
            try:
                urlemoji = msg.text.split(" ")
                png_sticker = urlemoji[1]
                sticker_emoji = urlemoji[2]
            except IndexError:
                sticker_emoji = "🙃"
            urllib.urlretrieve(png_sticker, kangsticker)
            im = Image.open(kangsticker)
            maxsize = (512, 512)
            if (im.width and im.height) < 512:
                size1 = im.width
                size2 = im.height
                if im.width > im.height:
                    scale = 512 / size1
                    size1new = 512
                    size2new = size2 * scale
                else:
                    scale = 512 / size2
                    size1new = size1 * scale
                    size2new = 512
                size1new = math.floor(size1new)
                size2new = math.floor(size2new)
                sizenew = (size1new, size2new)
                im = im.resize(sizenew)
            else:
                im.thumbnail(maxsize)
            im.save(kangsticker, "PNG")
            await msg.reply_photo(photo=open("kangsticker.png", "rb"))
            context.bot.add_sticker_to_set(
                user_id=user.id,
                name=packname,
                png_sticker=open("kangsticker.png", "rb"),
                emojis=sticker_emoji,
            )
            edited_keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton(text="View Pack",
                                     url=f"t.me/addstickers/{packname}")
            ]])
            await msg.reply_text(
                f"<b>Your sticker has been added!</b>"
                f"\nEmoji Is : {sticker_emoji}",
                reply_markup=edited_keyboard,
                parse_mode=ParseMode.HTML,
            )
        except OSError as e:
            await msg.reply_text("I can only kang images m8.")
            LOGGER.debug(e)
            return
        except TelegramError as e:
            if e.message == "Stickerset_invalid":
                makepack_internal(
                    update,
                    context,
                    msg,
                    user,
                    sticker_emoji,
                    packname,
                    packnum,
                    png_sticker=open("kangsticker.png", "rb"),
                )

            elif e.message == "Sticker_png_dimensions":
                im.save(kangsticker, "PNG")
                context.bot.add_sticker_to_set(
                    user_id=user.id,
                    name=packname,
                    png_sticker=open("kangsticker.png", "rb"),
                    emojis=sticker_emoji,
                )
                edited_keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton(text="View Pack",
                                         url=f"t.me/addstickers/{packname}")
                ]])
                await msg.reply_text(
                    f"<b>Your sticker has been added!</b>"
                    f"\nEmoji Is : {sticker_emoji}",
                    reply_markup=edited_keyboard,
                    parse_mode=ParseMode.HTML,
                )
            elif e.message == "Invalid sticker emojis":
                await msg.reply_text("Invalid emoji(s).")
            elif e.message == "Stickers_too_much":
                await msg.reply_text(
                    "Max packsize reached. Press F to pay respecc.")
            elif e.message == "Internal Server Error: sticker set not found (500)":
                await msg.reply_text(
                    f"<b>Your sticker has been added!</b>"
                    f"\nEmoji Is : {sticker_emoji}",
                    reply_markup=edited_keyboard,
                    parse_mode=ParseMode.HTML,
                )
            LOGGER.debug(e)
    else:
        packs_text = "*Please reply to a sticker, or image to kang it!*\n"
        if packnum > 0:
            firstpackname = "a" + str(user.id) + "_by_" + context.bot.username
            for i in range(0, packnum + 1):
                if i == 0:
                    packs = f"t.me/addstickers/{firstpackname}"
                else:
                    packs = f"t.me/addstickers/{packname}"
        else:
            packs = f"t.me/addstickers/{packname}"

        edited_keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="View Pack", url=f"{packs}")]])
        await msg.reply_text(packs_text,
                             reply_markup=edited_keyboard,
                             parse_mode=ParseMode.MARKDOWN)
    try:
        if os.path.isfile("kangsticker.png"):
            os.remove("kangsticker.png")
        elif os.path.isfile("kangsticker.tgs"):
            os.remove("kangsticker.tgs")
        elif os.path.isfile("kangsticker.webm"):
            os.remove("kangsticker.webm")
    except:
        pass


async def makepack_internal(context,
                            msg,
                            user,
                            emoji,
                            packname,
                            packnum,
                            png_sticker=None,
                            tgs_sticker=None,
                            webm_sticker=None):
    name = user.first_name
    name = name[:50]
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(text="View Pack", url=f"{packname}")]])
    try:
        extra_version = ""
        if packnum > 0:
            extra_version = " " + str(packnum)
        if png_sticker:
            sticker_pack_name = (
                f"{name}'s stic-pack (@{context.bot.username})" +
                extra_version)
            success = context.bot.create_new_sticker_set(
                user.id,
                packname,
                sticker_pack_name,
                png_sticker=png_sticker,
                emojis=emoji,
            )
        if tgs_sticker:
            sticker_pack_name = (
                f"{name}'s ani-pack (@{context.bot.username})" + extra_version)
            success = context.bot.create_new_sticker_set(
                user.id,
                packname,
                sticker_pack_name,
                tgs_sticker=tgs_sticker,
                emojis=emoji,
            )
        if webm_sticker:
            sticker_pack_name = (
                f"{name}'s vid-pack (@{context.bot.username})" + extra_version)
            success = context.bot.create_new_sticker_set(
                user.id,
                packname,
                sticker_pack_name,
                webm_sticker=webm_sticker,
                emojis=emoji,
            )

    except TelegramError as e:
        LOGGER.debug(e)
        if e.message == "Sticker set name is already occupied":
            await msg.reply_text(
                "<b>Your Sticker Pack is already created!</b>"
                "\n\nYou can now reply to images, stickers and animated sticker with /steal to add them to your pack"
                "\n\n<b>Send /stickers to find any sticker pack.</b>",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        elif e.message == "Peer_id_invalid" or "bot was blocked by the user":
            await msg.reply_text(
                "Cutiepii Robot 愛 was blocked by you.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(text="Unblock",
                                         url=f"t.me/{context.bot.username}")
                ]]),
            )
        elif e.message == "Internal Server Error: created sticker set not found (500)":
            await msg.reply_text(
                "<b>Your Sticker Pack has been created!</b>"
                "\n\nYou can now reply to images, stickers and animated sticker with /steal to add them to your pack"
                "\n\n<b>Send /stickers to find sticker pack.</b>",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML,
            )
        return

    if success:
        await msg.reply_text(
            "<b>Your Sticker Pack has been created!</b>"
            "\n\nYou can now reply to images, stickers and animated sticker with /steal to add them to your pack"
            "\n\n<b>Send /stickers to find sticker pack.</b>",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
        )
    else:
        await msg.reply_text(
            "Failed to create sticker pack. Possibly due to blek mejik.")


async def getsticker(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message
    chat_id = update.effective_chat.id
    if msg.reply_to_message and msg.reply_to_message.sticker:
        await context.bot.sendChatAction(chat_id, "typing")
        await update.effective_message.reply_text(
            "Hello" +
            f"{mention_html(msg.from_user.id, msg.from_user.first_name)}" +
            ", Please check the file you requested below."
            "\nPlease use this feature wisely!",
            parse_mode=ParseMode.HTML,
        )
        await context.bot.sendChatAction(chat_id, "upload_document")
        file_id = msg.reply_to_message.sticker.file_id
        newFile = await context.bot.get_file(file_id)
        newFile.download("sticker.png")
        await context.bot.sendDocument(chat_id,
                                       document=open("sticker.png", "rb"))
        await context.bot.sendChatAction(chat_id, "upload_photo")
        await context.bot.send_photo(chat_id, photo=open("sticker.png", "rb"))

    else:
        await context.bot.sendChatAction(chat_id, "typing")
        await update.effective_message.reply_text(
            "Hello" +
            f"{mention_html(msg.from_user.id, msg.from_user.first_name)}" +
            ", Please reply to sticker message to get sticker image",
            parse_mode=ParseMode.HTML,
        )


async def cb_sticker(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message
    query = "".join(msg.text.split()[1:])
    if not query:
        await msg.reply_text("Provide some term to search for a sticker pack.")
        return
    if len(query) > 50:
        await msg.reply_text("Provide a search query under 50 characters")
        return
    if msg.from_user:
        user_id = msg.from_user.id
    else:
        user_id = None
    text, buttons = get_cbs_data(query, 1, user_id)
    await msg.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=buttons)


async def cbs_callback(update: Update):
    query = update.callback_query
    _, page, user_id = query.data.split("_", 2)
    if (user_id) != query.from_user.id:
        await query.answer("Not for you", cache_time=60 * 60)
        return
    search_query = query.message.text.split("\n",
                                            1)[0].split(maxsplit=2)[2][:-1]
    text, buttons = get_cbs_data(search_query, int(page), query.from_user.id)
    await query.edit_message_text(text,
                                  parse_mode=ParseMode.HTML,
                                  reply_markup=buttons)
    await query.answer()


async def getsticker(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    msg = update.effective_message
    chat_id = update.effective_chat.id

    if msg.reply_to_message and msg.reply_to_message.sticker:
        animated = msg.reply_to_message.sticker.is_animated is True
        videos = msg.reply_to_message.sticker.is_video is True

        if not animated and not videos:
            file_id = msg.reply_to_message.sticker.file_id
            new_file = await bot.get_file(file_id)
            new_file.download("sticker.png")
            await bot.sendDocument(chat_id, document=open("sticker.png", "rb"))
            await bot.sendChatAction(chat_id, "upload_photo")
            await bot.sendPhoto(chat_id, photo=open("sticker.png", "rb"))
            os.remove("sticker.png")
        elif animated:
            file_id = msg.reply_to_message.sticker.file_id
            new_file = await bot.get_file(file_id)
            new_file.download("sticker.tgs")
            new_files = await bot.get_file(file_id)
            new_files.download("sticker.tgs.rename_me")
            await bot.sendDocument(chat_id,
                                   document=open("sticker.tgs.rename_me",
                                                 "rb"))
            await bot.sendChatAction(chat_id, "upload_photo")
            await bot.sendDocument(chat_id, document=open("sticker.tgs", "rb"))
            os.remove("sticker.tgs")
            os.remove("sticker.tgs.rename_me")
        else:
            file_id = msg.reply_to_message.sticker.file_id
            new_file = await bot.get_file(file_id)
            new_file.download("sticker.webm")
            await bot.sendDocument(chat_id,
                                   document=open("sticker.webm", "rb"))
            await bot.sendChatAction(chat_id, "upload_video")
            await bot.sendVideo(chat_id, video=open("sticker.webm", "rb"))
            os.remove("sticker.webm")
        return
    await update.effective_message.reply_text(
        "Please reply to a sticker for me to upload its PNG or TGS or WEBM for video sticker."
    )


async def delsticker(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.sticker:
        file_id = msg.reply_to_message.sticker.file_id
        context.bot.delete_sticker_from_set(file_id)
        await msg.reply_text("Deleted!")
    else:
        await update.effective_message.reply_text(
            "Please reply to sticker message to del sticker")


async def add_fvrtsticker(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    user = update.effective_user
    args = context.args
    query = " ".join(args)
    if message.reply_to_message and message.reply_to_message.sticker:
        get_s_name = message.reply_to_message.sticker.set_name
        if not query:
            get_s_name_title = get_s_name
        else:
            get_s_name_title = query
        if get_s_name is None:
            await message.reply_text("Sticker is invalid!")
        sticker_url = f"https://t.me/addstickers/{get_s_name}"
        sticker_m = "<a href='{}'>{}</a>".format(sticker_url, get_s_name_title)
        check_pack = REDIS.hexists(f"fvrt_stickers2_{user.id}",
                                   get_s_name_title)
        if check_pack is False:
            REDIS.hset(f"fvrt_stickers2_{user.id}", get_s_name_title,
                       sticker_m)
            await message.reply_text(
                f"<code>{sticker_m}</code> has been succesfully added into your favorite sticker packs list!",
                parse_mode=ParseMode.HTML)
        else:
            await message.reply_text(
                f"<code>{sticker_m}</code> is already exist in your favorite sticker packs list!",
                parse_mode=ParseMode.HTML)

    else:
        await message.reply_text("Reply to any sticker!")


async def list_fvrtsticker(update: Update):
    message = update.effective_message
    user = update.effective_user
    fvrt_stickers_list = REDIS.hvals(f"fvrt_stickers2_{user.id}")
    fvrt_stickers_list.sort()
    fvrt_stickers_list = "\n• ".join(fvrt_stickers_list)
    if fvrt_stickers_list:
        await message.reply_text("{}'s favorite sticker packs:\n➛ {}".format(
            user.first_name, fvrt_stickers_list),
                                 parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("You haven't added any sticker yet.")


async def remove_fvrtsticker(update: Update, context: CallbackContext) -> None:
    message = update.effective_message
    user = update.effective_user
    args = context.args
    del_stick = " ".join(args)
    if not del_stick:
        await message.reply_text(
            "Please give a your favorite sticker pack name to remove from your list."
        )
        return
    del_check = REDIS.hexists(f"fvrt_stickers2_{user.id}", del_stick)
    if not del_check is False:
        REDIS.hdel(f"fvrt_stickers2_{user.id}", del_stick)
        await message.reply_text(
            f"<code>{del_stick}</code> has been succesfully deleted from your list.",
            parse_mode=ParseMode.HTML)
    else:
        await message.reply_text(
            f"<code>{del_stick}</code> doesn't exist in your favorite sticker pack list.",
            parse_mode=ParseMode.HTML)


Credit = "Yūki • Black Knights Union"


@Cutiepii(pattern="^/mmf ?(.*)")
async def handler(event):
    if event.fwd_from:
        return
    if not event.reply_to_msg_id:
        await event.reply(
            "Reply to an image or a sticker to memeify it Nigga!!")
        return
    reply_message = await event.get_reply_message()
    if not reply_message.media:
        await event.reply("Provide some Text please")
        return
    file = await telethn.download_media(reply_message)
    msg = await event.reply("Memifying this image! Please wait")
    text = str(event.pattern_match.group(1)).strip()

    if len(text) < 1:
        return await msg.edit("You might want to try `/mmf text`")
    meme = await drawText(file, text)
    await telethn.send_file(event.chat_id, file=meme, force_document=False)
    await msg.delete()
    os.remove(meme)


# Taken from https://github.com/UsergeTeam/Userge-Plugins/blob/master/plugins/memify.py#L64
# Maybe replyed to suit the needs of this module


async def drawText(image_path, text):
    img = Image.open(image_path)
    os.remove(image_path)
    i_width, i_height = img.size
    if os.name == "nt":
        fnt = "ariel.ttf"
    else:
        fnt = "./Cutiepii_Robot/resources/ArmWrestler.ttf"
    m_font = ImageFont.truetype(fnt, int((70 / 640) * i_width))
    if ";" in text:
        upper_text, lower_text = text.split(";")
    else:
        upper_text = text
        lower_text = ""
    draw = ImageDraw.Draw(img)
    current_h, pad = 10, 5
    if upper_text:
        for u_text in textwrap.wrap(upper_text, width=15):
            u_width, u_height = draw.textsize(u_text, font=m_font)
            draw.text(xy=(((i_width - u_width) / 2) - 2,
                          int((current_h / 640) * i_width)),
                      text=u_text,
                      font=m_font,
                      fill=(0, 0, 0))

            draw.text(xy=(((i_width - u_width) / 2) + 2,
                          int((current_h / 640) * i_width)),
                      text=u_text,
                      font=m_font,
                      fill=(0, 0, 0))
            draw.text(xy=((i_width - u_width) / 2,
                          int(((current_h / 640) * i_width)) - 2),
                      text=u_text,
                      font=m_font,
                      fill=(0, 0, 0))

            draw.text(xy=(((i_width - u_width) / 2),
                          int(((current_h / 640) * i_width)) + 2),
                      text=u_text,
                      font=m_font,
                      fill=(0, 0, 0))

            draw.text(xy=((i_width - u_width) / 2,
                          int((current_h / 640) * i_width)),
                      text=u_text,
                      font=m_font,
                      fill=(255, 255, 255))

            current_h += u_height + pad

    if lower_text:
        for l_text in textwrap.wrap(lower_text, width=15):
            u_width, u_height = draw.textsize(l_text, font=m_font)
            draw.text(
                xy=(
                    ((i_width - u_width) / 2) - 2,
                    i_height - u_height - int((20 / 640) * i_width),
                ),
                text=l_text,
                font=m_font,
                fill=(0, 0, 0),
            )
            draw.text(
                xy=(
                    ((i_width - u_width) / 2) + 2,
                    i_height - u_height - int((20 / 640) * i_width),
                ),
                text=l_text,
                font=m_font,
                fill=(0, 0, 0),
            )
            draw.text(
                xy=(
                    (i_width - u_width) / 2,
                    (i_height - u_height - int((20 / 640) * i_width)) - 2,
                ),
                text=l_text,
                font=m_font,
                fill=(0, 0, 0),
            )

            draw.text(
                xy=(
                    (i_width - u_width) / 2,
                    (i_height - u_height - int((20 / 640) * i_width)) + 2,
                ),
                text=l_text,
                font=m_font,
                fill=(0, 0, 0),
            )

            draw.text(
                xy=(
                    (i_width - u_width) / 2,
                    i_height - u_height - int((20 / 640) * i_width),
                ),
                text=l_text,
                font=m_font,
                fill=(255, 255, 255),
            )
            current_h += u_height + pad
    image_name = "memify.webp"
    webp_file = os.path.join(image_name)
    img.save(webp_file, "webp")
    return webp_file


__help__ = """
Stickers made easy with stickers module!

➛ /stickers`: Find stickers for given term on combot sticker catalogue 
➛ /addsticker` or `/kang` or `/steal`: Reply to a sticker to add it to your pack.
➛ /delkang`: Reply to your anime exist sticker to your pack to delete it.
➛ /stickerid`: Reply to a sticker to me to tell you its file ID.
➛ /getsticker`: Reply to a sticker to me to upload its raw PNG file.
➛ /addfsticker` or `/afs <custom name>`: Reply to a sticker to add it into your favorite pack list.
➛ /myfsticker` or `/mfs`: Get list of your favorite packs.
➛ /removefsticke`r or `/rfs <custom name>`: Reply to a sticker to remove it into your favorite pack list.

*Example:* `/addfsticker` my cool pack`
"""

__mod_name__ = "Stickers"

CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("stickerid", stickerid))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("getsticker", getsticker))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("kang", kang))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("delsticker", delsticker))
CUTIEPII_PTB.add_handler(
    DisableAbleCommandHandler(["addfsticker", "afs"], add_fvrtsticker))
CUTIEPII_PTB.add_handler(
    DisableAbleCommandHandler(["removefsticker", "rfs"], remove_fvrtsticker))
CUTIEPII_PTB.add_handler(
    DisableAbleCommandHandler(["myfsticker", "mfs"], list_fvrtsticker))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("stickers", cb_sticker))
CUTIEPII_PTB.add_handler(CallbackQueryHandler(cbs_callback, pattern="cbs_"))
