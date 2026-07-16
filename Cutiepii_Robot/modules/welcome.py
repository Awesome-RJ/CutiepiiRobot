import html
import random
import re
import time
import os
from contextlib import suppress
from functools import partial
from io import BytesIO
import asyncio

from telegram import (
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import BadRequest, TelegramError
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    CommandHandler,
    filters,
    MessageHandler,
)
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility
from telegram.helpers import escape_markdown, mention_html, mention_markdown

from Cutiepii_Robot import (
    DEV_USERS,
    LOGGER,
    OWNER_ID,
    SUDO_USERS,
    SUPPORT_USERS,
    WHITELIST_USERS,
    SUPPORT_CHAT,
    JOIN_LOGGER,
    BOT_USERNAME,
    dispatcher,
    REDIS,
)
import Cutiepii_Robot.modules.sql.welcome_sql as sql
import Cutiepii_Robot.modules.sql.ranking_sql as rank_sql
from Cutiepii_Robot.modules.helper_funcs.admin_status import user_admin_check, bot_admin_check, AdminPerms, bot_is_admin, user_is_admin
from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status
from Cutiepii_Robot.modules.disable import DisableAbleMessageHandler
from Cutiepii_Robot.modules.helper_funcs.misc import build_keyboard, build_keyboard_parser, revert_buttons, delete
from Cutiepii_Robot.modules.private_notes import getprivatenotes
from Cutiepii_Robot.modules.sql.clear_cmd_sql import get_clearcmd
from Cutiepii_Robot.modules.helper_funcs.msg_types import get_welcome_type
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_chatmember, cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot.modules.helper_funcs.string_handling import (
    escape_invalid_curly_brackets,
    markdown_parser,
)
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.sql.global_bans_sql import is_user_gbanned
import Cutiepii_Robot.modules.sql.log_channel_sql as logsql
from Cutiepii_Robot.modules.cron_jobs import j

VALID_WELCOME_FORMATTERS = [
    "first",
    "last",
    "fullname",
    "username",
    "id",
    "count",
    "chatname",
    "mention",
    "name",
    "first_name",
    "last_name",
    "user_handle",
    "user_id",
    "chat",
    "group_title",
    "guild",
    "rank",
]

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
    sql.Types.VIDEO_NOTE.value: dispatcher.bot.send_video_note,
}

VERIFIED_USER_WAITLIST = {}
CAPTCHA_ANS_DICT = {}
WELCOME_GROUP = -100

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

class FallbackFontManager:
    def __init__(self, primary_path, fallback_paths, size):
        from fontTools.ttLib import TTFont
        self.fonts = []
        self.cmaps = []
        
        # Load primary font
        try:
            self.fonts.append(ImageFont.truetype(primary_path, size))
            self.cmaps.append(TTFont(primary_path).getBestCmap())
        except Exception:
            self.fonts.append(ImageFont.load_default())
            self.cmaps.append(None)
            
        # Load fallback fonts
        for path in fallback_paths:
            if os.path.exists(path):
                try:
                    self.fonts.append(ImageFont.truetype(path, size))
                    self.cmaps.append(TTFont(path).getBestCmap())
                except Exception:
                    continue

    def get_font_for_char(self, char):
        if char.isspace():
            return self.fonts[0]
        char_code = ord(char)
        for idx, cmap in enumerate(self.cmaps):
            if cmap and char_code in cmap:
                return self.fonts[idx]
        return self.fonts[0]

def draw_text_with_fallback(draw, xy, text, font_manager, fill):
    x, y = xy
    for char in text:
        font = font_manager.get_font_for_char(char)
        draw.text((x, y), char, fill=fill, font=font)
        x += font.getlength(char)

def generate_welcome_card(user_name, user_id, group_name, total_msg, rank, user_avatar_bytes=None):
    # Canvas Size
    width, height = 1024, 576
    
    # 1. Base Gradient Background (Deep violet to dark blue-black)
    base = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(base)
    
    for y in range(height):
        # Diagonal gradient logic
        r = int(15 + (10 * (y / height)))
        g = int(12 + (8 * (y / height)))
        b = int(35 + (15 * (y / height)))
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
        
    # 2. Add soft glowing neon blobs in background
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Glow 1: Top-Right (Purple/Magenta)
    overlay_draw.ellipse([700, -100, 1100, 300], fill=(176, 38, 255, 60))
    # Glow 2: Bottom-Left (Cyan)
    overlay_draw.ellipse([-100, 300, 300, 700], fill=(0, 240, 255, 50))
    
    # Apply heavy blur to the glows
    glows = overlay.filter(ImageFilter.GaussianBlur(80))
    img = Image.alpha_composite(base, glows)
    draw = ImageDraw.Draw(img)
    
    # 3. Draw central glassmorphic card (900x450, centered)
    card_left = 62
    card_top = 63
    card_right = 962
    card_bottom = 513
    
    # Glass fill
    card_fill = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    card_fill_draw = ImageDraw.Draw(card_fill)
    card_fill_draw.rounded_rectangle(
        [card_left, card_top, card_right, card_bottom],
        radius=30,
        fill=(25, 23, 42, 160)
    )
    img = Image.alpha_composite(img, card_fill)
    draw = ImageDraw.Draw(img)
    
    # Card thin glowing border
    draw.rounded_rectangle(
        [card_left, card_top, card_right, card_bottom],
        radius=30,
        outline=(255, 255, 255, 35),
        width=2
    )
    
    # 4. Fonts setup
    module_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(module_dir, "..", ".."))
    font_path_bold = os.path.join(project_root, "Cutiepii_Robot", "resources", "Montserrat-Bold.ttf")
    font_path_medium = os.path.join(project_root, "Cutiepii_Robot", "resources", "Montserrat-Medium.ttf")
    
    # Cross-platform fallbacks (Windows + Linux)
    fallback_paths = [
        "C:\\Windows\\Fonts\\segoeuib.ttf",
        "C:\\Windows\\Fonts\\seguisym.ttf",
        "C:\\Windows\\Fonts\\Nirmala.ttc",
        "C:\\Windows\\Fonts\\msyh.ttc",
        "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    ]
    
    fm_welcome = FallbackFontManager(font_path_medium, fallback_paths, 20)
    fm_group = FallbackFontManager(font_path_bold, fallback_paths, 36)
    fm_name = FallbackFontManager(font_path_bold, fallback_paths, 54)
    fm_stat_val = FallbackFontManager(font_path_bold, fallback_paths, 26)
    fm_stat_lbl = FallbackFontManager(font_path_medium, fallback_paths, 18)
    fm_avatar = FallbackFontManager(font_path_bold, fallback_paths, 70)
    
    # 5. Avatar section (Left side: X=190, Y=288)
    avatar_center = (190, 288)
    avatar_radius = 95
    
    # Outer neon ring
    draw.ellipse(
        [avatar_center[0] - avatar_radius - 6, avatar_center[1] - avatar_radius - 6,
         avatar_center[0] + avatar_radius + 6, avatar_center[1] + avatar_radius + 6],
        outline=(0, 240, 255, 200),
        width=4
    )
    
    # Paste user avatar or fallback to initial circle
    avatar_pasted = False
    if user_avatar_bytes:
        try:
            avatar = Image.open(io.BytesIO(user_avatar_bytes)).convert("RGBA")
            avatar = avatar.resize((avatar_radius * 2, avatar_radius * 2))
            
            mask = Image.new("L", (avatar_radius * 2, avatar_radius * 2), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([0, 0, avatar_radius * 2, avatar_radius * 2], fill=255)
            
            img.paste(avatar, (avatar_center[0] - avatar_radius, avatar_center[1] - avatar_radius), mask)
            avatar_pasted = True
        except Exception as avatar_err:
            LOGGER.warning(f"Error pasting avatar image: {avatar_err}")
            
    if not avatar_pasted:
        # Fallback circle placeholder with initial letter
        draw.ellipse(
            [avatar_center[0] - avatar_radius, avatar_center[1] - avatar_radius,
             avatar_center[0] + avatar_radius, avatar_center[1] + avatar_radius],
            fill=(40, 42, 58, 255)
        )
        initials = user_name[0].upper() if user_name else "?"
        draw_text_with_fallback(draw, (avatar_center[0] - 25, avatar_center[1] - 45), initials, fm_avatar, (255, 255, 255, 255))
        
    # 6. Right side details (Start X=335)
    text_x = 335
    
    # Welcome To text
    draw_text_with_fallback(draw, (text_x, 105), "WELCOME TO", fm_welcome, (0, 240, 255, 255))
    
    # Group Name with overflow truncation
    display_group = group_name
    group_w = 0
    truncated_group = ""
    for char in display_group:
        font = fm_group.get_font_for_char(char)
        group_w += font.getlength(char)
        if group_w > 560:
            truncated_group += "..."
            break
        truncated_group += char
    display_group = truncated_group
    draw_text_with_fallback(draw, (text_x, 135), display_group, fm_group, (255, 255, 255, 255))
    
    # Separation Line
    draw.line([(text_x, 195), (920, 195)], fill=(255, 255, 255, 25), width=2)
    
    # User Name with overflow truncation
    display_name = user_name
    name_w = 0
    truncated_name = ""
    for char in display_name:
        font = fm_name.get_font_for_char(char)
        name_w += font.getlength(char)
        if name_w > 560:
            truncated_name += "..."
            break
        truncated_name += char
    display_name = truncated_name
    draw_text_with_fallback(draw, (text_x, 215), display_name, fm_name, (255, 255, 255, 255))
    
    # 7. Stats rows (User ID, Msg count, Rank)
    stats_y = 300
    
    stats_data = [
        {"label": "USER ID", "value": str(user_id)},
        {"label": "TOTAL MSG", "value": str(total_msg)},
        {"label": "RANK", "value": str(rank)}
    ]
    
    box_width = 185
    box_height = 85
    gap = 18
    
    for idx, stat in enumerate(stats_data):
        bx = text_x + idx * (box_width + gap)
        by = stats_y
        
        # Draw stats card background with higher contrast
        draw.rounded_rectangle(
            [bx, by, bx + box_width, by + box_height],
            radius=15,
            fill=(20, 18, 35, 200),
            outline=(255, 255, 255, 45),
            width=1
        )
        
        # Draw value centered
        val_font = fm_stat_val.fonts[0]
        val_w = val_font.getlength(stat["value"])
        val_x = bx + (box_width - val_w) / 2
        draw_text_with_fallback(draw, (val_x, by + 14), stat["value"], fm_stat_val, (255, 255, 255, 255))
        
        # Draw label centered with high-contrast color
        lbl_font = fm_stat_lbl.fonts[0]
        lbl_w = lbl_font.getlength(stat["label"])
        lbl_x = bx + (box_width - lbl_w) / 2
        draw_text_with_fallback(draw, (lbl_x, by + 48), stat["label"], fm_stat_lbl, (200, 205, 220, 255))
        
    bio = io.BytesIO()
    bio.name = "welcome_card.png"
    img.save(bio, "PNG")
    bio.seek(0)
    return bio

from multicolorcaptcha import CaptchaGenerator

WHITELISTED = [OWNER_ID] + DEV_USERS + SUDO_USERS + SUPPORT_USERS + WHITELIST_USERS


async def send(update, message, keyboard, backup_message, reply_to_message=None):
    if not message:
        return

    chat = update.effective_chat
    try:
        msg = await dispatcher.bot.send_message(chat.id,
            message,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard,
            disable_web_page_preview=True,
            allow_sending_without_reply=True,
        )
    except BadRequest as excp:
        if excp.message == "Reply message not found" or excp.message == "Message can't be deleted":
            msg = await dispatcher.bot.send_message(chat.id,
                 message,
                 parse_mode=ParseMode.HTML,
                 reply_markup=keyboard,
                 disable_web_page_preview=True,
                 allow_sending_without_reply=True,
            )
        elif excp.message == "Button_url_invalid":
            msg = await dispatcher.bot.send_message(chat.id,
                markdown_parser(
                    backup_message +
                    "\nNote: the current message has an invalid url "
                    "in one of its buttons. Please update.",
                ),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                allow_sending_without_reply=True,
            )
        elif excp.message == "Unsupported url protocol":
            msg = await dispatcher.bot.send_message(chat.id,
                markdown_parser(
                    backup_message +
                    "\nNote: the current message has buttons which "
                    "use url protocols that are unsupported by "
                    "telegram. Please update.",
                ),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                allow_sending_without_reply=True,
            )
        elif excp.message == "Wrong url host":
            msg = await dispatcher.bot.send_message(chat.id,
                markdown_parser(
                    backup_message +
                    "\nNote: the current message has some bad urls. "
                    "Please update.",
                ),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                allow_sending_without_reply=True,
            )
            LOGGER.warning(message)
            LOGGER.warning(keyboard)
            LOGGER.exception("Could not parse! got invalid url host errors")
        elif excp.message == "Have no rights to send a message" or excp.message == "Topic_closed":
            return
        else:
            msg = await dispatcher.bot.send_message(chat.id,
                markdown_parser(
                    backup_message +
                    "\nNote: An error occured when sending the "
                    "custom message. Please update.",
                ),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                allow_sending_without_reply=True,
            )
            LOGGER.exception(
                "An error occurred when sending a custom message to %s",
                chat.id,
            )
    return msg

@cutiepii_chatmember(group=WELCOME_GROUP)
@cutiepii_msg(filters.StatusUpdate.NEW_CHAT_MEMBERS, group=WELCOME_GROUP)
async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):  # sourcery no-metrics
    bot, job_queue = context.bot, context.job_queue
    chat = update.effective_chat
    chat_member = update.chat_member

    LOGGER.debug(f"[GREETINGS] new_member handler triggered in chat {chat.id if chat else None}. Update type: {'chat_member' if chat_member else 'status_update' if (update.effective_message and update.effective_message.new_chat_members) else 'unknown'}")

    if chat_member:
        old_status = chat_member.old_chat_member.status
        new_status = chat_member.new_chat_member.status

        was_in_chat = old_status in ("member", "restricted", "administrator", "creator")
        is_in_chat = new_status in ("member", "restricted")

        if was_in_chat or not is_in_chat:
            return

        new_members = [chat_member.new_chat_member.user]
        user = chat_member.from_user
    elif update.effective_message and update.effective_message.new_chat_members:
        new_members = update.effective_message.new_chat_members
        user = update.effective_user
    else:
        return

    # Deduplicate welcome events per user/chat using Redis
    non_duplicate_members = []
    for new_mem in new_members:
        dedup_key = f"welc_join:{chat.id}:{new_mem.id}"
        if REDIS.get(dedup_key):
            LOGGER.debug(f"[GREETINGS] Ignoring duplicate join for user {new_mem.id} in chat {chat.id}")
            continue
        REDIS.set(dedup_key, "true", ex=5)
        non_duplicate_members.append(new_mem)

    if not non_duplicate_members:
        return

    new_members = non_duplicate_members

    # Raid Mode check
    raidmode = REDIS.get(f"raidmode:{chat.id}")
    if raidmode and raidmode.decode("utf-8") == "true":
        for new_mem in new_members:
            try:
                # Skip bot itself
                if new_mem.id == bot.id:
                    continue
                # Kick (ban & unban)
                await chat.ban_member(user_id=new_mem.id)
                await chat.unban_member(user_id=new_mem.id)
            except Exception as e:
                LOGGER.error(f"Failed to kick user in Raid Mode: {e}")
        # Delete joining service message if it exists
        if update.effective_message:
            try:
                await update.effective_message.delete()
            except Exception:
                pass
        return

    msg = update.effective_message
    if msg is None:
        class MockMessage:
            def __init__(self, chat, bot):
                self.chat = chat
                self.bot = bot
                self.message_id = None
            async def reply_text(self, *args, **kwargs):
                kwargs.pop('reply_to_message_id', None)
                return await self.bot.send_message(self.chat.id, *args, **kwargs)
            async def reply_photo(self, *args, **kwargs):
                kwargs.pop('reply_to_message_id', None)
                return await self.bot.send_photo(self.chat.id, *args, **kwargs)
            async def reply_video(self, *args, **kwargs):
                kwargs.pop('reply_to_message_id', None)
                return await self.bot.send_video(self.chat.id, *args, **kwargs)
        msg = MockMessage(chat, bot)

    log_setting = logsql.get_chat_setting(chat.id)
    if not log_setting:
        logsql.set_chat_setting(chat.id, True, True, True, True, True)
        log_setting = logsql.get_chat_setting(chat.id)

    should_welc, cust_welcome, cust_content, welc_type = sql.get_welc_pref(chat.id)
    welc_mutes = sql.welcome_mutes(chat.id)
    human_checks = sql.get_human_checks(new_members[0].id, chat.id) if new_members else None
    raid, _, deftime = sql.getRaidStatus(str(chat.id))

    for new_mem in new_members:

        welcome_log = None
        should_mute = True
        welcome_bool = True
        media_wel = False

        if raid and new_mem.id not in WHITELISTED:
            bantime = deftime
            try:
                await chat.ban_member(new_mem.id, until_date=bantime)
            except BadRequest:
                pass
            return

        reply = update.message.message_id if (update.message and hasattr(update.message, 'message_id')) else None
        cleanserv = sql.clean_service(chat.id)
        if cleanserv and reply:
            try:
                await bot.delete_message(chat.id, reply)
            except BadRequest:
                pass
            reply = False

        if should_welc:

            if new_mem.id == OWNER_ID:
                await msg.reply_video(
                    "https://te.legra.ph/file/409bdbf03868cf6b2d755.gif",
                    caption=f"Behold!! My Owner is Here. Welcome to {html.escape(chat.title)} my darling.",
                    reply_to_message_id=reply,
                )
                welcome_log = (
                    f"{html.escape(chat.title)}\n"
                    f"#USER_JOINED\n"
                    f"My Darling has come to this group for make the child with me"
                )
                continue

            elif new_mem.id in DEV_USERS:
                await msg.reply_text(
                    "Whoa! A developer user just joined!",
                    reply_to_message_id=reply,
                )
                continue

            elif new_mem.id in SUDO_USERS:
                await msg.reply_text(
                    "Huh! A Sudo user just joined! Stay Alert!",
                    reply_to_message_id=reply,
                )
                continue

            elif new_mem.id in SUPPORT_USERS:
                await msg.reply_text(
                    "Huh! a Support user just joined!",
                    reply_to_message_id=reply,
                )
                continue

            elif new_mem.id in WHITELIST_USERS:
                await msg.reply_text(
                    "Oof! A Whitelist user just joined!", reply_to_message_id=reply
                )
                continue


            if new_mem.id == bot.id:
                profile_photos = await bot.get_user_profile_photos(bot.id)
                profile = profile_photos.photos[0][-1] if profile_photos.total_count > 0 else None
                chet_name = f"<a href='t.me/{chat.username}'>{html.escape(chat.title)}</a>" if chat.username else html.escape(chat.title)
                await msg.reply_photo(
                        profile,
                        caption= f"Hey {user.first_name}, I'm {bot.first_name}! Thank you for adding me to {chet_name}\n Join support and channel update with clicking button below!\n\n <b>Promote me as administrator of the group, to access all my commands.</b>",
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        text="Support",
                                        url=f"https://t.me/{SUPPORT_CHAT}"),
                                    InlineKeyboardButton(
                                        text="Updates",
                                        url="https://t.me/Black_Knights_Union",
                                    )
                                ]
                            ]
                        ),
                        parse_mode=ParseMode.HTML,
                        reply_to_message_id=reply,
                    )
                creator = None

                admins = await bot.get_chat_administrators(chat.id)
                for x in admins:
                    if x.status == ChatMemberStatus.OWNER:
                        creator = mention_html(x.user.id, html.escape(x.user.first_name) or "Creator") + f" (<code>{x.user.id}</code>)"
                        break

                await bot.send_message(
                     JOIN_LOGGER,
                     "#NEW_GROUP\n\n"
                     "<b>Group Members:</b> {}\n<b>Group Name:</b> {} (<code>{}</code>) {}\n<b>Bot Added By:</b> {} (<code>{}</code>)".
                     format(await chat.get_member_count(), chat.title, chat.id, ('\n<b>Group Founder:</b> ' + creator) if creator is not None else '', mention_html(user.id, html.escape(user.first_name) or "Adder"), user.id),
                     parse_mode=ParseMode.HTML, 
                     disable_web_page_preview=True,
                )
                continue

            else:
                buttons = sql.get_welc_buttons(chat.id)
                keyb = build_keyboard_parser(bot, chat.id, buttons)

                if welc_type not in (sql.Types.TEXT, sql.Types.BUTTON_TEXT):
                    media_wel = True

                first_name = (
                        new_mem.first_name or "PersonWithNoName"
                )

                if cust_welcome:
                    if cust_welcome == sql.DEFAULT_WELCOME:
                        cust_welcome = random.choice(
                            sql.DEFAULT_WELCOME_MESSAGES
                        ).format(first=html.escape(first_name))

                    if new_mem.last_name:
                        fullname = html.escape(f"{first_name} {new_mem.last_name}")
                    else:
                        fullname = html.escape(first_name)
                    count = await chat.get_member_count()
                    mention = mention_html(new_mem.id, html.escape(first_name))
                    if new_mem.username:
                        username = "@" + html.escape(new_mem.username)
                    else:
                        username = mention

                    valid_format = escape_invalid_curly_brackets(
                        cust_welcome, VALID_WELCOME_FORMATTERS
                    )
                    guild_val = REDIS.get(f"hunter_guild:{new_mem.id}")
                    guild_val = guild_val.decode("utf-8") if guild_val else "Shadow Guild"

                    rank_val = REDIS.get(f"hunter_rank:{new_mem.id}")
                    rank_val = rank_val.decode("utf-8") if rank_val else "E-Rank"

                    res = valid_format.format(
                        first=html.escape(first_name),
                        last=html.escape(new_mem.last_name or first_name),
                        fullname=html.escape(fullname),
                        username=username,
                        mention=mention,
                        count=count,
                        chatname=html.escape(chat.title),
                        id=new_mem.id,
                        name=mention,
                        first_name=html.escape(first_name),
                        last_name=html.escape(new_mem.last_name or ""),
                        user_handle=f"@{new_mem.username}" if new_mem.username else "",
                        user_id=new_mem.id,
                        chat=html.escape(chat.title),
                        group_title=html.escape(chat.title),
                        guild=html.escape(guild_val),
                        rank=html.escape(rank_val),
                    )

                else:
                    res = random.choice(sql.DEFAULT_WELCOME_MESSAGES).format(
                        first=html.escape(first_name)
                    )
                    keyb = []

                backup_message = random.choice(sql.DEFAULT_WELCOME_MESSAGES).format(
                    first=html.escape(first_name)
                )
                keyboard = InlineKeyboardMarkup(keyb)

        else:
            welcome_bool = False
            res = None
            keyboard = None
            backup_message = None
            reply = None

        member = await chat.get_member(new_mem.id)
        if (
                member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]
                or human_checks
        ):
            should_mute = False

        if new_mem.is_bot:
            should_mute = False

        if user.id == new_mem.id and should_mute:
            if welc_mutes == "soft":
                await bot.restrict_chat_member(
                    chat.id,
                    new_mem.id,
                    permissions=ChatPermissions(
                        can_send_messages=True,
                        can_send_audios=False,
                        can_send_documents=False,
                        can_send_photos=False,
                        can_send_videos=False,
                        can_send_video_notes=False,
                        can_send_voice_notes=False,
                        can_send_other_messages=False,
                        can_invite_users=False,
                        can_pin_messages=False,
                        can_send_polls=False,
                        can_change_info=False,
                        can_add_web_page_previews=False,
                    ),
                    until_date=(int(time.time() + 24 * 60 * 60)),
                )
                sql.set_human_checks(user.id, chat.id)
            if welc_mutes == "strong":
                welcome_bool = False
                if not media_wel:
                    VERIFIED_USER_WAITLIST.update(
                        {
                            (chat.id, new_mem.id): {
                                "should_welc": should_welc,
                                "media_wel": False,
                                "status": False,
                                "update": update,
                                "res": res,
                                "keyboard": keyboard,
                                "backup_message": backup_message,
                            }
                        }
                    )
                else:
                    VERIFIED_USER_WAITLIST.update(
                        {
                            (chat.id, new_mem.id): {
                                "should_welc": should_welc,
                                "chat_id": chat.id,
                                "status": False,
                                "media_wel": True,
                                "cust_content": cust_content,
                                "welc_type": welc_type,
                                "res": res,
                                "keyboard": keyboard,
                            }
                        }
                    )
                new_join_mem = f"<a href=\"tg://user?id={new_mem.id}\">{html.escape(new_mem.first_name)}</a>"
                message = await msg.reply_text(
                    f"{new_join_mem}, click the button below to prove you're human.\nYou have 120 seconds.",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    text="Yes, I'm human.",
                                    callback_data=f"user_join_({new_mem.id})",
                                )
                            ]
                        ]
                    ),
                    parse_mode=ParseMode.HTML,
                    reply_to_message_id=reply,
                    allow_sending_without_reply=True,
                )
                await bot.restrict_chat_member(
                    chat.id,
                    new_mem.id,
                    permissions=ChatPermissions(
                        can_send_messages=False,
                        can_invite_users=False,
                        can_pin_messages=False,
                        can_send_polls=False,
                        can_change_info=False,
                        can_send_audios=False,
                        can_send_documents=False,
                        can_send_photos=False,
                        can_send_videos=False,
                        can_send_video_notes=False,
                        can_send_voice_notes=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False,
                    ),
                )
                job_data = {
                    'member': new_mem,
                    'id': chat.id,
                    'message_id': message.message_id,
                }

                job_queue.run_once(
                    callback = check_not_bot,
                    when = 120,
                    data = job_data,
                )
            if welc_mutes == "captcha":
                btn = []
                CAPCTHA_SIZE_NUM = 4
                generator = CaptchaGenerator(CAPCTHA_SIZE_NUM)

                captcha = generator.gen_captcha_image(difficult_level=2, multicolor=True)
                image = captcha["image"]
                characters = str(captcha["characters"])
                fileobj = BytesIO()
                fileobj.name = f'captcha_{new_mem.id}.png'
                image.save(fp=fileobj)
                fileobj.seek(0)
                CAPTCHA_ANS_DICT[(chat.id, new_mem.id)] = characters
                welcome_bool = False
                if not media_wel:
                    VERIFIED_USER_WAITLIST.update(
                        {
                            (chat.id, new_mem.id): {
                                "should_welc": should_welc,
                                "media_wel": False,
                                "status": False,
                                "update": update,
                                "res": res,
                                "keyboard": keyboard,
                                "backup_message": backup_message,
                                "captcha_correct": characters,
                            }
                        }
                    )
                else:
                    VERIFIED_USER_WAITLIST.update(
                        {
                            (chat.id, new_mem.id): {
                                "should_welc": should_welc,
                                "chat_id": chat.id,
                                "status": False,
                                "media_wel": True,
                                "cust_content": cust_content,
                                "welc_type": welc_type,
                                "res": res,
                                "keyboard": keyboard,
                                "captcha_correct": characters,
                            }
                        }
                    )

                min_val = 10 ** (CAPCTHA_SIZE_NUM - 1)
                max_val = (10 ** CAPCTHA_SIZE_NUM) - 1
                nums = [str(random.randint(min_val, max_val)) for _ in range(7)]
                nums.append(characters)
                random.shuffle(nums)
                to_append = []
                for a in nums:
                    to_append.append(InlineKeyboardButton(text=str(a),
                                                          callback_data=f"user_captchajoin_({chat.id},{new_mem.id})_({a})"))
                    if len(to_append) > 2:
                        btn.append(to_append)
                        to_append = []
                if to_append:
                    btn.append(to_append)

                message = await msg.reply_photo(fileobj,
                                          caption=f'Welcome <a href="tg://user?id={new_mem.id}">{html.escape(new_mem.first_name)}</a>. Click the correct button to get unmuted!\n'
                                                  f'You got 120 seconds for this.',
                                          reply_markup=InlineKeyboardMarkup(btn),
                                          parse_mode=ParseMode.HTML,
                                          reply_to_message_id=reply,
                                          allow_sending_without_reply=True,
                                          )
                await bot.restrict_chat_member(
                    chat.id,
                    new_mem.id,
                    permissions=ChatPermissions(
                        can_send_messages=False,
                        can_invite_users=False,
                        can_pin_messages=False,
                        can_send_polls=False,
                        can_change_info=False,
                        can_send_audios=False,
                        can_send_documents=False,
                        can_send_photos=False,
                        can_send_videos=False,
                        can_send_video_notes=False,
                        can_send_voice_notes=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False,
                    ),
                )
                job_data = {
                    'member': new_mem,
                    'id': chat.id,
                    'message_id': message.message_id,
                }
                job_queue.run_once(
                    callback = check_not_bot,
                    when = 120,
                    data = job_data,
                    name="welcomemute",
                )

        if welcome_bool:
            if media_wel:
                func = ENUM_FUNC_MAP[welc_type]
                if welc_type == sql.Types.STICKER:
                    sent = await func(
                        chat.id,
                        cust_content,
                        reply_markup=keyboard,
                        reply_to_message_id=reply,
                    )
                else:
                    if welc_type == sql.Types.DOCUMENT:
                        try:
                            sent = await bot.send_animation(
                                chat.id,
                                cust_content,
                                caption=res,
                                reply_markup=keyboard,
                                reply_to_message_id=reply,
                                parse_mode=ParseMode.HTML,
                            )
                        except Exception:
                            sent = await func(
                                chat.id,
                                cust_content,
                                caption=res,
                                reply_markup=keyboard,
                                reply_to_message_id=reply,
                                parse_mode=ParseMode.HTML,
                            )
                    else:
                        sent = await func(
                            chat.id,
                            cust_content,
                            caption=res,
                            reply_markup=keyboard,
                            reply_to_message_id=reply,
                            parse_mode=ParseMode.HTML,
                        )
            else:
                welcome_mode = REDIS.get(f"welcome_mode:{chat.id}")
                welcome_mode = welcome_mode.decode("utf-8") if welcome_mode else "text"
                
                if welcome_mode == "image":
                    try:
                        avatar_bytes = None
                        try:
                            photos = await bot.get_user_profile_photos(user_id=new_mem.id, limit=1)
                            if photos and photos.photos:
                                file_id = photos.photos[0][-1].file_id
                                file_obj = await bot.get_file(file_id)
                                buf = io.BytesIO()
                                await file_obj.download_to_memory(out=buf)
                                buf.seek(0)
                                avatar_bytes = buf.getvalue()
                        except Exception as avatar_err:
                            LOGGER.warning(f"Error fetching user avatar: {avatar_err}")

                        stats = rank_sql.get_user_stats(new_mem.id, chat.id)
                        total_msg = stats.all_time_messages if stats else 0
                        rank_num = rank_sql.get_chat_rank(chat.id, new_mem.id)
                        rank_val = f"#{rank_num}" if rank_num > 0 else "N/A"

                        welcome_image_bio = await asyncio.to_thread(
                            generate_welcome_card,
                            user_name=first_name,
                            user_id=new_mem.id,
                            group_name=chat.title,
                            total_msg=total_msg,
                            rank=rank_val,
                            user_avatar_bytes=avatar_bytes
                        )
                        
                        sent = await bot.send_photo(
                            chat_id=chat.id,
                            photo=welcome_image_bio,
                            caption=res,
                            reply_markup=keyboard,
                            parse_mode=ParseMode.HTML,
                            reply_to_message_id=reply,
                            allow_sending_without_reply=True
                        )
                    except Exception as img_err:
                        LOGGER.error(f"Failed to generate/send welcome card image: {img_err}")
                        sent = await send(update, res, keyboard, backup_message)
                else:
                    sent = await send(update, res, keyboard, backup_message)
            clean_pref = sql.get_clean_pref(chat.id)
            if clean_pref:
                if clean_pref > 1:
                    try:
                        await bot.delete_message(chat.id, clean_pref)
                    except BadRequest:
                        pass

                if sent:
                    sql.set_clean_welcome(chat.id, sent.message_id)
                    async def clean_welc(context: ContextTypes.DEFAULT_TYPE):
                        try:
                            await bot.delete_message(chat.id, sent.message_id)
                        except:
                            pass

                    context.job_queue.run_once(clean_welc, 300)


        if not log_setting.log_joins:
            return ""
        if welcome_log:
            return welcome_log

    return ""


async def check_not_bot(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.data['id']
    member = job.data['member']
    message_id = job.data['message_id']
    bot = context.bot
    member_dict = VERIFIED_USER_WAITLIST.pop((chat_id, member.id), None)
    CAPTCHA_ANS_DICT.pop((chat_id, member.id), None)
    if not member_dict:
        return
    member_status = member_dict.get("status")
    if not member_status:
        try:
            await bot.ban_chat_member(chat_id, member.id)
            await bot.unban_chat_member(chat_id, member.id)
        except TelegramError:
            pass

        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=message_id,
                                  text="*kicks user*\nThey can always rejoin and try.")
        except TelegramError:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
            except BadRequest:
                pass
            await bot.send_message(
                chat_id=chat_id, text=f'{mention_html(member.id, html.escape(member.first_name))} was kicked as they failed to verify themselves', parse_mode=ParseMode.HTML)


@cutiepii_chatmember(group=WELCOME_GROUP)
@cutiepii_msg(filters.StatusUpdate.LEFT_CHAT_MEMBER, group=WELCOME_GROUP)
async def left_member(update: Update, context: ContextTypes.DEFAULT_TYPE):  # sourcery no-metrics
    bot = context.bot
    chat = update.effective_chat
    chat_member = update.chat_member

    if chat_member:
        old_status = chat_member.old_chat_member.status
        new_status = chat_member.new_chat_member.status

        was_in_chat = old_status in ("member", "restricted", "administrator", "creator")
        is_in_chat = new_status in ("member", "restricted", "administrator", "creator")

        if was_in_chat and not is_in_chat:
            left_mem = chat_member.old_chat_member.user
            sql.remove_human_check(left_mem.id, chat.id)
        else:
            return
    elif update.effective_message and update.effective_message.left_chat_member:
        left_mem = update.effective_message.left_chat_member
        sql.remove_human_check(left_mem.id, chat.id)
    else:
        return

    # Deduplicate leave events per user/chat using Redis
    dedup_key = f"welc_leave:{chat.id}:{left_mem.id}"
    if REDIS.get(dedup_key):
        LOGGER.debug(f"[GREETINGS] Ignoring duplicate leave for user {left_mem.id} in chat {chat.id}")
        return
    REDIS.set(dedup_key, "true", ex=5)

    # Autoban check (auto-ban members who leave the group)
    autoban_status = REDIS.get(f"autoban:{chat.id}")
    if autoban_status and autoban_status.decode("utf-8") == "true":
        is_immune = (
            left_mem.id == bot.id
            or left_mem.id in DEV_USERS
            or left_mem.id in SUDO_USERS
            or left_mem.id == OWNER_ID
        )
        if not is_immune:
            is_staff = False
            if chat_member:
                is_staff = old_status in ("administrator", "creator")
            
            if not is_staff:
                try:
                    await chat.ban_member(left_mem.id)
                    LOGGER.info(f"[AUTOBAN]: Auto-banned {left_mem.id} on leave from {chat.id}")
                except Exception as ban_err:
                    LOGGER.error(f"Failed to auto-ban {left_mem.id} on leave: {ban_err}")

    # Check and mock update.effective_message if it's None
    msg = update.effective_message
    if msg is None:
        class MockMessage:
            def __init__(self, chat, bot):
                self.chat = chat
                self.bot = bot
                self.message_id = None
            async def reply_text(self, *args, **kwargs):
                kwargs.pop('reply_to_message_id', None)
                return await self.bot.send_message(self.chat.id, *args, **kwargs)
            async def reply_photo(self, *args, **kwargs):
                kwargs.pop('reply_to_message_id', None)
                return await self.bot.send_photo(self.chat.id, *args, **kwargs)
            async def reply_video(self, *args, **kwargs):
                kwargs.pop('reply_to_message_id', None)
                return await self.bot.send_video(self.chat.id, *args, **kwargs)
        msg = MockMessage(chat, bot)

    should_goodbye, cust_goodbye, goodbye_type = sql.get_gdbye_pref(chat.id)

    reply = update.message.message_id if (update.message and hasattr(update.message, 'message_id')) else None
    cleanserv = sql.clean_service(chat.id)
    if cleanserv and reply:
        try:
            await bot.delete_message(chat.id, reply)
        except BadRequest:
            pass
        reply = False

    if should_goodbye:
        if is_user_gbanned(left_mem.id):
            return

        if left_mem.id == bot.id:
            return

        if left_mem.id == OWNER_ID:
            await msg.reply_text(
                "Sorry to see you leave :(", reply_to_message_id=reply
            )
            return

        if left_mem.id == 1826542418:
            await msg.reply_text(
                "<i>You can rest now...</i>", reply_to_message_id=reply, parse_mode=ParseMode.HTML
            )
            return

        elif left_mem.id in DEV_USERS:
            await msg.reply_text(
                "See you later Dev!",
                reply_to_message_id=reply,
            )
            return

        # Clean old goodbye message if enabled
        cleangoodbye = REDIS.get(f"cleangoodbye_pref:{chat.id}")
        if cleangoodbye and cleangoodbye.decode("utf-8") == "true":
            last_id = REDIS.get(f"last_goodbye_message_id:{chat.id}")
            if last_id:
                try:
                    await bot.delete_message(chat.id, int(last_id))
                except Exception:
                    pass

        if goodbye_type not in [sql.Types.TEXT, sql.Types.BUTTON_TEXT]:
            func = ENUM_FUNC_MAP[goodbye_type]
            if goodbye_type == sql.Types.DOCUMENT:
                try:
                    sent = await bot.send_animation(chat.id, cust_goodbye)
                except Exception:
                    sent = await func(chat.id, cust_goodbye)
            else:
                sent = await func(chat.id, cust_goodbye)
            if sent and cleangoodbye and cleangoodbye.decode("utf-8") == "true":
                REDIS.set(f"last_goodbye_message_id:{chat.id}", sent.message_id)
            return

        first_name = (
            left_mem.first_name or "Person_With_No_Name"
        )
        if cust_goodbye:
            if cust_goodbye == sql.DEFAULT_GOODBYE:
                cust_goodbye = random.choice(sql.DEFAULT_GOODBYE_MESSAGES).format(
                    first=html.escape(first_name)
                )
            if left_mem.last_name:
                fullname = html.escape(f"{first_name} {left_mem.last_name}")
            else:
                fullname = html.escape(first_name)
            count = await chat.get_member_count()
            mention = mention_html(left_mem.id, html.escape(first_name))
            if left_mem.username:
                username = "@" + html.escape(left_mem.username)
            else:
                username = mention

            if "%%%" in cust_goodbye:
                split = cust_goodbye.split("%%%")
                if all(split):
                    cust_bye = random.choice(split)
                else:
                    cust_bye = cust_goodbye
            else:
                cust_bye = cust_goodbye

            valid_format = escape_invalid_curly_brackets(
                cust_bye, VALID_WELCOME_FORMATTERS
            )
            guild_val = REDIS.get(f"hunter_guild:{left_mem.id}")
            guild_val = guild_val.decode("utf-8") if guild_val else "Shadow Guild"

            rank_val = REDIS.get(f"hunter_rank:{left_mem.id}")
            rank_val = rank_val.decode("utf-8") if rank_val else "E-Rank"

            res = valid_format.format(
                first=html.escape(first_name),
                last=html.escape(left_mem.last_name or first_name),
                fullname=html.escape(fullname),
                username=username,
                mention=mention,
                count=count,
                chatname=html.escape(chat.title),
                id=left_mem.id,
                name=mention,
                first_name=html.escape(first_name),
                last_name=html.escape(left_mem.last_name or ""),
                user_handle=f"@{left_mem.username}" if left_mem.username else "",
                user_id=left_mem.id,
                chat=html.escape(chat.title),
                group_title=html.escape(chat.title),
                guild=html.escape(guild_val),
                rank=html.escape(rank_val),
            )
            buttons = sql.get_gdbye_buttons(chat.id)
            keyb = build_keyboard_parser(bot, chat.id, buttons)

        else:
            res = random.choice(sql.DEFAULT_GOODBYE_MESSAGES).format(
                first=html.escape(first_name)
            )
            keyb = []

        keyboard = InlineKeyboardMarkup(keyb)

        sent = await send(
            update,
            res,
            keyboard,
            random.choice(sql.DEFAULT_GOODBYE_MESSAGES).format(first=first_name),
        )
        if sent and cleangoodbye and cleangoodbye.decode("utf-8") == "true":
            REDIS.set(f"last_goodbye_message_id:{chat.id}", sent.message_id)


@cutiepii_cmd(command='welcome', filters=filters.ChatType.GROUPS, rate_limit_calls=30, rate_limit_window=60, add_error_handler=True)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if not args or args[0].lower() == "noformat":
        noformat = bool(args and args[0].lower() == "noformat")
        pref, welcome_m, cust_content, welcome_type = sql.get_welc_pref(chat.id)
        
        # Create interactive buttons
        action_buttons = [
            [InlineKeyboardButton("✅ Enable" if not pref else "❌ Disable", 
                                 callback_data=f"welcome_toggle_{'off' if pref else 'on'}"),
             InlineKeyboardButton("📝 Set Message", callback_data="welcome_set")],
            [InlineKeyboardButton("🔄 Reset", callback_data="welcome_reset"),
             InlineKeyboardButton("🧹 Clean Welcome", callback_data="welcome_clean")],
            [InlineKeyboardButton("🔇 Mute Settings", callback_data="welcome_mute_settings"),
             InlineKeyboardButton("ℹ️ Help", callback_data="welcome_help")],
            [InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
        ]
        
        status_text = "✅ Enabled" if pref else "❌ Disabled"
        await update.effective_message.reply_text(
            f"👋 <b>Welcome Settings</b>\n\n"
            f"<b>Status:</b> {status_text}\n"
            f"<b>Current welcome message:</b>\n\n"
            f"<i>Use buttons below to manage settings.</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(action_buttons)
        )

        if welcome_type in [sql.Types.BUTTON_TEXT, sql.Types.TEXT]:
            buttons = sql.get_welc_buttons(chat.id)
            if noformat:
                welcome_m += revert_buttons(buttons)
                await update.effective_message.reply_text(welcome_m)

            else:
                keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                await send(update, welcome_m, keyboard, random.choice(sql.DEFAULT_WELCOME_MESSAGES))
        else:
            buttons = sql.get_welc_buttons(chat.id)
            if noformat:
                welcome_m += revert_buttons(buttons)
                if welcome_type == sql.Types.DOCUMENT:
                    try:
                        await bot.send_animation(chat.id, cust_content, caption=welcome_m, parse_mode=ParseMode.HTML)
                    except Exception:
                        await ENUM_FUNC_MAP[welcome_type](chat.id, cust_content, caption=welcome_m, parse_mode=ParseMode.HTML)
                else:
                    await ENUM_FUNC_MAP[welcome_type](chat.id, cust_content, caption=welcome_m, parse_mode=ParseMode.HTML)


            else:
                if welcome_type in [sql.Types.TEXT, sql.Types.BUTTON_TEXT]:
                    kwargs = {'disable_web_page_preview': True}
                else:
                    kwargs = {}
                keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                keyboard = InlineKeyboardMarkup(keyb)
                if welcome_type == sql.Types.DOCUMENT:
                    try:
                        await bot.send_animation(
                            chat.id,
                            cust_content,
                            caption=welcome_m,
                            reply_markup=keyboard,
                            parse_mode=ParseMode.HTML,
                            **kwargs,
                        )
                    except Exception:
                        await ENUM_FUNC_MAP[welcome_type](
                            chat.id,
                            cust_content,
                            caption=welcome_m,
                            reply_markup=keyboard,
                            parse_mode=ParseMode.HTML,
                            **kwargs,
                        )
                else:
                    await ENUM_FUNC_MAP[welcome_type](
                        chat.id,
                        cust_content,
                        caption=welcome_m,
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML,
                        **kwargs,
                    )

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_welc_preference(str(chat.id), True)
            buttons = [
                [InlineKeyboardButton("🔙 Back to Settings", callback_data="welcome_settings"),
                 InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
            ]
            await update.effective_message.reply_text(
                "✅ <b>Welcome Enabled!</b>\n\n"
                "I'll greet members when they join.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        elif args[0].lower() in ("off", "no"):
            sql.set_welc_preference(str(chat.id), False)
            buttons = [
                [InlineKeyboardButton("🔙 Back to Settings", callback_data="welcome_settings"),
                 InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
            ]
            await update.effective_message.reply_text(
                "❌ <b>Welcome Disabled</b>\n\n"
                "I'll go loaf around and not welcome anyone then.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        else:
            await update.effective_message.reply_text(
                "I understand 'on/yes' or 'off/no' only!"
            )

@cutiepii_cmd(command='goodbye', filters=filters.ChatType.GROUPS, rate_limit_calls=30, rate_limit_window=60, add_error_handler=True)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
async def goodbye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message


    if not args or args[0] == "noformat":
        noformat = bool(args and args[0].lower() == "noformat")
        pref, goodbye_m, goodbye_type = sql.get_gdbye_pref(chat.id)
        await update.effective_message.reply_text(
            f"This chat has it's goodbye setting set to: `{pref}`.\n"
            f"*The goodbye  message (not filling the {{}}) is:*",
            parse_mode=ParseMode.MARKDOWN,
        )

        if goodbye_type == sql.Types.BUTTON_TEXT:
            buttons = sql.get_gdbye_buttons(chat.id)
            if noformat:
                goodbye_m += revert_buttons(buttons)
                await update.effective_message.reply_text(goodbye_m)

            else:
                keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                await send(update, goodbye_m, keyboard, random.choice(sql.DEFAULT_GOODBYE_MESSAGES))

        elif noformat:
            if goodbye_type == sql.Types.DOCUMENT:
                try:
                    await bot.send_animation(chat.id, goodbye_m)
                except Exception:
                    await ENUM_FUNC_MAP[goodbye_type](chat.id, goodbye_m)
            else:
                await ENUM_FUNC_MAP[goodbye_type](chat.id, goodbye_m)

        else:
            if goodbye_type == sql.Types.DOCUMENT:
                try:
                    await bot.send_animation(
                        chat.id, goodbye_m, parse_mode=ParseMode.HTML
                    )
                except Exception:
                    await ENUM_FUNC_MAP[goodbye_type](
                        chat.id, goodbye_m, parse_mode=ParseMode.HTML
                    )
            else:
                await ENUM_FUNC_MAP[goodbye_type](
                    chat.id, goodbye_m, parse_mode=ParseMode.HTML
                )

    elif len(args) >= 1:
        if args[0].lower() in ("on", "yes"):
            sql.set_gdbye_preference(str(chat.id), True)
            await update.effective_message.reply_text("Ok!")

        elif args[0].lower() in ("off", "no"):
            sql.set_gdbye_preference(str(chat.id), False)
            await update.effective_message.reply_text("Ok!")

        else:
            await update.effective_message.reply_text(
                "I understand 'on/yes' or 'off/no' only!"
            )

@cutiepii_cmd(command=['setwelcome', 'set_welcome'], filters=filters.ChatType.GROUPS, rate_limit_calls=5, rate_limit_window=60, add_error_handler=True)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def set_welcome(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message


    text, data_type, content, buttons = await get_welcome_type(msg)

    if data_type is None:
        await msg.reply_text("You didn't specify what to reply with!")
        return ""

    sql.set_custom_welcome(chat.id, content, text, data_type, buttons)
    await msg.reply_text("Successfully set custom welcome message!")

    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#SET_WELCOME\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"Set the welcome message."
    )


@cutiepii_cmd(command=['resetwelcome', 'del_welcome', 'rm_welcome'], filters=filters.ChatType.GROUPS, rate_limit_calls=5, rate_limit_window=60, add_error_handler=True)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def reset_welcome(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    sql.set_custom_welcome(chat.id, None, random.choice(sql.DEFAULT_WELCOME_MESSAGES), sql.Types.TEXT)
    await update.effective_message.reply_text(
        "Successfully reset welcome message to default!"
    )

    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#RESET_WELCOME\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"Reset the welcome message to default."
    )


@cutiepii_cmd(command='setgoodbye', filters=filters.ChatType.GROUPS, rate_limit_calls=5, rate_limit_window=60, add_error_handler=True)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def set_goodbye(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    text, data_type, content, buttons = await get_welcome_type(msg)

    if data_type is None:
        await msg.reply_text("You didn't specify what to reply with!")
        return ""

    sql.set_custom_gdbye(chat.id, content or text, data_type, buttons)
    await msg.reply_text("Successfully set custom goodbye message!")
    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#SET_GOODBYE\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"Set the goodbye message."
    )


@cutiepii_cmd(command='resetgoodbye', filters=filters.ChatType.GROUPS, rate_limit_calls=5, rate_limit_window=60, add_error_handler=True)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def reset_goodbye(update: Update, context: CallbackContext) -> str:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message


    sql.set_custom_gdbye(chat.id, sql.DEFAULT_GOODBYE, sql.Types.TEXT)
    await update.effective_message.reply_text(
        "Successfully reset goodbye message to default!"
    )

    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#RESET_GOODBYE\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"Reset the goodbye message."
    )


@cutiepii_cmd(command='welcomemute', filters=filters.ChatType.GROUPS, rate_limit_calls=5, rate_limit_window=60, add_error_handler=True)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def welcomemute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if len(args) >= 1:
        if args[0].lower() in ("off", "no"):
            sql.set_welcome_mutes(chat.id, False)
            buttons = [
                [InlineKeyboardButton("🔙 Back to Settings", callback_data="welcome_mute_settings"),
                 InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
            ]
            await msg.reply_text(
                "🔇 <b>Welcome Mute: OFF</b>\n\n"
                "I will no longer mute people on joining!",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#WELCOME_MUTE\n"
                f"<b>- Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"Has toggled welcome mute to <b>OFF</b>."
            )
        elif args[0].lower() in ["soft"]:
            sql.set_welcome_mutes(chat.id, "soft")
            buttons = [
                [InlineKeyboardButton("🔙 Back to Settings", callback_data="welcome_mute_settings"),
                 InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
            ]
            await msg.reply_text(
                "🔇 <b>Welcome Mute: SOFT</b>\n\n"
                "I will restrict users' permission to send media for 24 hours.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#WELCOME_MUTE\n"
                f"<b>- Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"Has toggled welcome mute to <b>SOFT</b>."
            )
        elif args[0].lower() in ["strong"]:
            sql.set_welcome_mutes(chat.id, "strong")
            buttons = [
                [InlineKeyboardButton("🔙 Back to Settings", callback_data="welcome_mute_settings"),
                 InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
            ]
            await msg.reply_text(
                "🔇 <b>Welcome Mute: STRONG</b>\n\n"
                "I will now mute people when they join until they prove they're not a bot.\n"
                "They will have 120 seconds before they get kicked.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#WELCOME_MUTE\n"
                f"<b>- Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"Has toggled welcome mute to <b>STRONG</b>."
            )
        elif args[0].lower() in ["captcha"]:
            sql.set_welcome_mutes(chat.id, "captcha")
            buttons = [
                [InlineKeyboardButton("🔙 Back to Settings", callback_data="welcome_mute_settings"),
                 InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
            ]
            await msg.reply_text(
                "🔇 <b>Welcome Mute: CAPTCHA</b>\n\n"
                "I will now mute people when they join until they prove they're not a bot.\n"
                "They have to solve a captcha to get unmuted.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#WELCOME_MUTE\n"
                f"<b>- Admin:</b> {mention_html(user.id, user.first_name)}\n"
                f"Has toggled welcome mute to <b>CAPTCHA</b>."
            )
        else:
            await msg.reply_text(
                "Please enter `off`/`no`/`soft`/`strong`/`captcha`!",
                parse_mode=ParseMode.MARKDOWN,
            )
            return ""
    else:
        curr_setting = sql.welcome_mutes(chat.id)
        buttons = [
            [InlineKeyboardButton("❌ Off", callback_data="welcome_mute_set_off"),
             InlineKeyboardButton("🔇 Soft", callback_data="welcome_mute_set_soft")],
            [InlineKeyboardButton("🔇 Strong", callback_data="welcome_mute_set_strong"),
             InlineKeyboardButton("🧩 Captcha", callback_data="welcome_mute_set_captcha")],
            [InlineKeyboardButton("🔙 Back", callback_data="welcome_settings"),
             InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
        ]
        await msg.reply_text(
            f"🔇 <b>Welcome Mute Settings</b>\n\n"
            f"<b>Current Setting:</b> <code>{curr_setting}</code>\n\n"
            f"<b>Options:</b>\n"
            f"- ❌ <b>Off</b> - No muting\n"
            f"- 🔇 <b>Soft</b> - Restrict media for 24h\n"
            f"- 🔇 <b>Strong</b> - Mute until verified (120s timeout)\n"
            f"- 🧩 <b>Captcha</b> - Mute until captcha solved\n\n"
            f"<i>Click a button to change setting.</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return ""


@cutiepii_cmd(command='cleanwelcome', filters=filters.ChatType.GROUPS, rate_limit_calls=10, rate_limit_window=60, add_error_handler=True)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
@loggable
async def clean_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if not args:
        clean_pref = sql.get_clean_pref(chat.id)
        buttons = [
            [InlineKeyboardButton("✅ Enable" if not clean_pref else "❌ Disable", 
                                 callback_data=f"welcome_clean_{'off' if clean_pref else 'on'}")],
            [InlineKeyboardButton("🔙 Back", callback_data="welcome_settings"),
             InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
        ]
        status = "✅ Enabled" if clean_pref else "❌ Disabled"
        message_text = (
            f"🧹 <b>Clean Welcome Settings</b>\n\n"
            f"<b>Status:</b> {status}\n\n"
        )
        if clean_pref:
            message_text += "I should be deleting welcome messages up to two days old.\n\n"
        else:
            message_text += "I'm currently not deleting old welcome messages!\n\n"
        message_text += "<i>This helps prevent spam from old welcome messages.</i>"
        await update.effective_message.reply_text(
            message_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return ""

    if args[0].lower() in ("on", "yes"):
        sql.set_clean_welcome(str(chat.id), True)
        buttons = [
            [InlineKeyboardButton("🔙 Back", callback_data="welcome_settings"),
             InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
        ]
        await update.effective_message.reply_text(
            "✅ <b>Clean Welcome Enabled!</b>\n\n"
            "I'll try to delete old welcome messages!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#CLEAN_WELCOME\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"Has toggled clean welcomes to <code>ON</code>."
        )
    elif args[0].lower() in ("off", "no"):
        sql.set_clean_welcome(str(chat.id), False)
        buttons = [
            [InlineKeyboardButton("🔙 Back", callback_data="welcome_settings"),
             InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
        ]
        await update.effective_message.reply_text(
            "❌ <b>Clean Welcome Disabled</b>\n\n"
            "I won't delete old welcome messages.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#CLEAN_WELCOME\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"Has toggled clean welcomes to <code>OFF</code>."
        )
    else:
        await update.effective_message.reply_text("I understand 'on/yes' or 'off/no' only!")
        return ""


@cutiepii_cmd(command='cleanservice', filters=filters.ChatType.GROUPS, rate_limit_calls=10, rate_limit_window=60, add_error_handler=True)
@bot_admin_check(AdminPerms.CAN_DELETE_MESSAGES)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods = True)
async def cleanservice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    args = context.args
    chat = update.effective_chat
    msg = update.effective_message
    
    if chat.type == chat.PRIVATE:
        service_clean = sql.clean_service(chat.id)
        status = "✅ Enabled" if service_clean else "❌ Disabled"
        await msg.reply_text(
            f"🧹 <b>Service Message Cleanup</b>\n\n"
            f"<b>Status:</b> {status}\n\n"
            f"{'I will delete Telegram service messages (user joined/left).' if service_clean else 'I will not delete service messages.'}",
            parse_mode=ParseMode.HTML
        )
        return ""

    if len(args) >= 1:
        var = args[0]
        if var in ("no", "off"):
            sql.set_clean_service(chat.id, False)
            buttons = [
                [InlineKeyboardButton("🔙 Back", callback_data="welcome_settings"),
                 InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
            ]
            await msg.reply_text(
                "❌ <b>Service Clean Disabled</b>\n\n"
                "I'll leave service messages.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        elif var in ("yes", "on"):
            sql.set_clean_service(chat.id, True)
            buttons = [
                [InlineKeyboardButton("🔙 Back", callback_data="welcome_settings"),
                 InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
            ]
            await msg.reply_text(
                "✅ <b>Service Clean Enabled!</b>\n\n"
                "I'll be deleting all service messages from now on!",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await msg.reply_text(
                "Invalid option. Use 'on/yes' or 'off/no'",
                parse_mode=ParseMode.MARKDOWN
            )
    else:
        service_clean = sql.clean_service(chat.id)
        buttons = [
            [InlineKeyboardButton("✅ Enable" if not service_clean else "❌ Disable", 
                                 callback_data=f"welcome_service_{'off' if service_clean else 'on'}")],
            [InlineKeyboardButton("🔙 Back", callback_data="welcome_settings"),
             InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
        ]
        status = "✅ Enabled" if service_clean else "❌ Disabled"
        await msg.reply_text(
            f"🧹 <b>Service Message Cleanup</b>\n\n"
            f"<b>Status:</b> {status}\n\n"
            f"{'I will delete Telegram service messages (user joined/left).' if service_clean else 'I am not currently deleting service messages when members join or leave.'}\n\n"
            f"<i>Examples: 'user joined chat', 'user left chat'</i>\n\n"
            f"<i>Click button to toggle or use command: /cleanservice on/off</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )


@cutiepii_callback(pattern=r"user_join_")
async def user_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    query = update.callback_query
    bot = context.bot
    match = re.match(r"user_join_\((.+?)\)", query.data)
    message = update.effective_message
    join_user = int(match.group(1))

    if join_user == user.id:
        sql.set_human_checks(user.id, chat.id)
        member_dict = VERIFIED_USER_WAITLIST.pop((chat.id, user.id), None)
        if not member_dict:
            return
        member_dict["status"] = True
        await query.answer(text="Yeet! You're a human, unmuted!")
        await bot.restrict_chat_member(
            chat.id,
            user.id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_send_polls=True,
                can_change_info=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        try:
            await bot.delete_message(chat.id, message.message_id)
        except BadRequest:
            pass
        if member_dict["should_welc"]:
            if member_dict.get("media_wel"):
                func = ENUM_FUNC_MAP[member_dict["welc_type"]]
                if member_dict["welc_type"] == sql.Types.STICKER:
                    sent = await func(
                        member_dict["chat_id"],
                        member_dict["cust_content"],
                        reply_markup=member_dict["keyboard"],
                    )
                else:
                    if member_dict["welc_type"] == sql.Types.DOCUMENT:
                        try:
                            sent = await bot.send_animation(
                                member_dict["chat_id"],
                                member_dict["cust_content"],
                                caption=member_dict["res"],
                                reply_markup=member_dict["keyboard"],
                                parse_mode=ParseMode.HTML,
                            )
                        except Exception:
                            sent = await func(
                                member_dict["chat_id"],
                                member_dict["cust_content"],
                                caption=member_dict["res"],
                                reply_markup=member_dict["keyboard"],
                                parse_mode=ParseMode.HTML,
                            )
                    else:
                        sent = await func(
                            member_dict["chat_id"],
                            member_dict["cust_content"],
                            caption=member_dict["res"],
                            reply_markup=member_dict["keyboard"],
                            parse_mode=ParseMode.HTML,
                        )
            else:
                sent = await send(
                    member_dict["update"],
                    member_dict["res"],
                    member_dict["keyboard"],
                    member_dict["backup_message"],
                )

            clean_pref = sql.get_clean_pref(chat.id)
            if clean_pref:
                if clean_pref > 1:
                    try:
                        await bot.delete_message(chat.id, clean_pref)
                    except BadRequest:
                        pass

                if sent:
                    sql.set_clean_welcome(chat.id, sent.message_id)

                    async def clean_welc(context: ContextTypes.DEFAULT_TYPE):
                        try:
                            await bot.delete_message(chat.id, sent.message_id)
                        except:
                            pass

                    context.job_queue.run_once(clean_welc, 300)

    else:
        await query.answer(text="You're not allowed to do this!")



@cutiepii_callback(pattern=r"user_captchajoin_")
async def user_captcha_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    query = update.callback_query
    bot = context.bot
    match = re.match(r"user_captchajoin_\(([\d\-]+),(\d+)\)_\((\d+)\)", query.data)
    message = update.effective_message
    join_chat = int(match.group(1))
    join_user = int(match.group(2))
    captcha_ans = str(match.group(3))
    join_usr_data = await bot.get_chat(join_user)

    if join_user == user.id:
        c_captcha_ans = CAPTCHA_ANS_DICT.pop((join_chat, join_user), None)
        if c_captcha_ans == captcha_ans:
            sql.set_human_checks(user.id, chat.id)
            member_dict = VERIFIED_USER_WAITLIST.pop((chat.id, user.id), None)
            if not member_dict:
                return
            member_dict["status"] = True
            await query.answer(text="Yeet! You're a human, unmuted!")
            await bot.restrict_chat_member(
                chat.id,
                user.id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_invite_users=True,
                    can_pin_messages=True,
                    can_send_polls=True,
                    can_change_info=True,
                    can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            try:
                await bot.delete_message(chat.id, message.message_id)
            except BadRequest:
                pass
            if member_dict["should_welc"]:
                if member_dict.get("media_wel"):
                    func = ENUM_FUNC_MAP[member_dict["welc_type"]]
                    if member_dict["welc_type"] == sql.Types.STICKER:
                        sent = await func(
                            member_dict["chat_id"],
                            member_dict["cust_content"],
                            reply_markup=member_dict["keyboard"],
                        )
                    else:
                        if member_dict["welc_type"] == sql.Types.DOCUMENT:
                            try:
                                sent = await bot.send_animation(
                                    member_dict["chat_id"],
                                    member_dict["cust_content"],
                                    caption=member_dict["res"],
                                    reply_markup=member_dict["keyboard"],
                                    parse_mode=ParseMode.HTML,
                                )
                            except Exception:
                                sent = await func(
                                    member_dict["chat_id"],
                                    member_dict["cust_content"],
                                    caption=member_dict["res"],
                                    reply_markup=member_dict["keyboard"],
                                    parse_mode=ParseMode.HTML,
                                )
                        else:
                            sent = await func(
                                member_dict["chat_id"],
                                member_dict["cust_content"],
                                caption=member_dict["res"],
                                reply_markup=member_dict["keyboard"],
                                parse_mode=ParseMode.HTML,
                            )
                else:
                    sent = await send(
                        member_dict["update"],
                        member_dict["res"],
                        member_dict["keyboard"],
                        member_dict["backup_message"],
                    )

                clean_pref = sql.get_clean_pref(chat.id)
                if clean_pref:
                    if clean_pref > 1:
                        try:
                            await bot.delete_message(chat.id, clean_pref)
                        except BadRequest:
                            pass

                    if sent:
                        sql.set_clean_welcome(chat.id, sent.message_id)

                        async def clean_welc(context: ContextTypes.DEFAULT_TYPE):
                            try:
                                await bot.delete_message(chat.id, sent.message_id)
                            except:
                                pass
                        context.job_queue.run_once(clean_welc, 300)
        else:
            try:
                await bot.delete_message(chat.id, message.message_id)
            except BadRequest:
                pass
            kicked_msg = f'''
            ❌ [{escape_markdown(join_usr_data.first_name)}](tg://user?id={join_user}) failed the captcha and was kicked.
            '''
            await query.answer(text="Wrong answer")
            await chat.ban_member(join_user)
            res = await chat.unban_member(join_user)
            if res:
                await bot.send_message(chat_id=chat.id, text=kicked_msg, parse_mode=ParseMode.MARKDOWN)


    else:
        await query.answer(text="You're not allowed to do this!")


WELC_HELP_TXT = (
    "Your group's welcome/goodbye messages can be personalised in multiple ways. If you want the messages"
    " to be individually generated, like the default welcome message is, you can use *these* variables:\n"
    "- `{first}`: this represents the user's *first* name\n"
    "- `{last}`: this represents the user's *last* name. Defaults to *first name* if user has no "
    "last name.\n"
    "- `{fullname}`: this represents the user's *full* name. Defaults to *first name* if user has no "
    "last name.\n"
    "- `{username}`: this represents the user's *username*. Defaults to a *mention* of the user's "
    "first name if has no username.\n"
    "- `{mention}`: this simply *mentions* a user - tagging them with their first name.\n"
    "- `{id}`: this represents the user's *id*\n"
    "- `{count}`: this represents the user's *member number*.\n"
    "- `{chatname}`: this represents the *current chat name*.\n"
    "\nEach variable MUST be surrounded by `{}` to be replaced.\n"
    "Welcome messages also support markdown, so you can make any elements bold/italic/code/links. "
    "Buttons are also supported, so you can make your welcomes look awesome with some nice intro "
    "buttons.\n"
    "To create a button automatically linking to your group rules, use the `{rules}` tag:\n"
    "  `[Rules](buttonurl:{rules})`\n"
    f"Or create a button linking to group rules manually using: `[Rules](buttonurl://t.me/{BOT_USERNAME}?start=group_id)`.\n"
    f"To link to any group note in PM, use: `[Note](buttonurl://t.me/{BOT_USERNAME}?start=note_groupid_notename)`.\n"
    "You can even set images/gifs/videos/voice messages as the welcome message by "
    "sending them directly with `/setwelcome` in the caption (or by replying to the desired media and calling `/setwelcome`)."
)

WELC_MUTE_HELP_TXT = (
    "You can get the bot to mute new people who join your group and hence prevent spambots from flooding your group. "
    "The following options are possible:\n"
    "- `/welcomemute soft*:* restricts new members from sending media for 24 hours.\n"
    "- `/welcomemute strong*:* mutes new members till they tap on a button thereby verifying they're human.\n"
    "- `/welcomemute captcha*:*  Mutes new members till they solve a button captcha thereby verifying they're human.\n"
    "- `/welcomemute off*:* Turns off welcomemute.\n"
    "*Note:* Strong mode kicks a user from the chat if they don't verify in 120 seconds. They can always rejoin though"
)

@cutiepii_cmd(command='welcomehelp', rate_limit_calls=30, rate_limit_window=60, add_error_handler=True)
@user_admin_check()
async def welcome_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(WELC_HELP_TXT, parse_mode=ParseMode.MARKDOWN)

@cutiepii_cmd(command='welcomemutehelp', rate_limit_calls=30, rate_limit_window=60, add_error_handler=True)
@user_admin_check()
async def welcome_mute_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        WELC_MUTE_HELP_TXT, parse_mode=ParseMode.MARKDOWN
    )


# TODO: get welcome data from group butler snap
# def __import_data__(chat_id, data):
#     welcome = data.get('info', {}).get('rules')
#     welcome = welcome.replace('$username', '{username}')
#     welcome = welcome.replace('$name', '{fullname}')
#     welcome = welcome.replace('$id', '{id}')
#     welcome = welcome.replace('$title', '{chatname}')
#     welcome = welcome.replace('$surname', '{lastname}')
#     welcome = welcome.replace('$rules', '{rules}')
#     sql.set_custom_welcome(chat_id, welcome, sql.Types.TEXT)


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)
    # Migrate Redis keys
    redis_keys = [
        "welcome_mode",
        "autoban",
        "cleangoodbye_pref",
        "raidmode",
        "last_goodbye_message_id"
    ]
    for key_prefix in redis_keys:
        old_key = f"{key_prefix}:{old_chat_id}"
        new_key = f"{key_prefix}:{new_chat_id}"
        if val := REDIS.get(old_key):
            REDIS.set(new_key, val)
            REDIS.delete(old_key)


async def __chat_settings__(chat_id, user_id):
    welcome_pref = sql.get_welc_pref(chat_id)[0]
    goodbye_pref = sql.get_gdbye_pref(chat_id)[0]
    return (
        "This chat has it's welcome preference set to `{}`.\n"
        "It's goodbye preference is `{}`.".format(welcome_pref, goodbye_pref)
    )

__help__ = True



# Callback handler for welcome module buttons
@cutiepii_callback(pattern=r"^welcome_")
async def welcome_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str = None):
    query = update.callback_query
    await query.answer()
    if data is None:
        data = query.data
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if user is admin
    if not await user_is_admin(chat, user.id):
        await query.answer("⚠️ You need to be an admin to use this!", show_alert=True)
        return
    
    if data == "welcome_close":
        await query.message.delete()
        return
    
    if data == "welcome_settings" or data == "welcome_help":
        if data == "welcome_help":
            help_text = """
<b>ℹ️ Welcome System Help</b>

<b>What is the welcome system?</b>
Automatically greets new members when they join your group.

<b>Features:</b>
- Custom welcome messages
- Welcome buttons
- Media support (photos, videos, stickers)
- Welcome mute (anti-bot protection)
- Clean old welcome messages
- Service message cleanup

<b>Quick Commands:</b>
❍ /welcome - View settings
❍ /welcome_mode - Set welcome mode (text/image)
❍ /setwelcome - Set custom message
❍ /welcomemute - Configure mute settings
❍ /cleanwelcome - Auto-delete old welcomes

<b>Formatting:</b>
- {first} - User's first name
- {last} - User's last name
- {fullname} - Full name
- {username} - Username
- {mention} - Mention user
- {id} - User ID
- {count} - Member count
- {chatname} - Chat name

<i>Use /welcomehelp for more formatting info!</i>
            """
            buttons = [
                [InlineKeyboardButton("« Back", callback_data="welcome_settings"),
                 InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
            ]
            await query.message.edit_text(help_text, parse_mode=ParseMode.HTML,
                                         reply_markup=InlineKeyboardMarkup(buttons))
            return
        
        # Settings view
        pref, welcome_m, cust_content, welcome_type = sql.get_welc_pref(chat.id)
        clean_pref = sql.get_clean_pref(chat.id)
        mute_setting = sql.welcome_mutes(chat.id)
        service_clean = sql.clean_service(chat.id)
        
        action_buttons = [
            [InlineKeyboardButton("✅ Enable" if not pref else "❌ Disable", 
                                 callback_data=f"welcome_toggle_{'off' if pref else 'on'}"),
             InlineKeyboardButton("📝 Set Message", callback_data="welcome_set")],
            [InlineKeyboardButton("🔄 Reset", callback_data="welcome_reset"),
             InlineKeyboardButton("🧹 Clean Welcome", callback_data="welcome_clean")],
            [InlineKeyboardButton("🔇 Mute Settings", callback_data="welcome_mute_settings"),
             InlineKeyboardButton("🧹 Service Clean", callback_data="welcome_service")],
            [InlineKeyboardButton("ℹ️ Help", callback_data="welcome_help"),
             InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
        ]
        
        status_text = "✅ Enabled" if pref else "❌ Disabled"
        clean_status = "✅ ON" if clean_pref else "❌ OFF"
        service_status = "✅ ON" if service_clean else "❌ OFF"
        
        try:
            await query.message.edit_text(
                f"👋 <b>Welcome Settings</b>\n\n"
                f"<b>Welcome Status:</b> {status_text}\n"
                f"<b>Clean Welcome:</b> {clean_status}\n"
                f"<b>Service Clean:</b> {service_status}\n"
                f"<b>Mute Setting:</b> <code>{mute_setting}</code>\n\n"
                f"<i>Use buttons below to manage settings.</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(action_buttons)
            )
        except BadRequest as excp:
            if "Message is not modified" not in excp.message:
                raise
        return
    
    if data.startswith("welcome_toggle_"):
        toggle = data.split("_")[-1]
        sql.set_welc_preference(str(chat.id), toggle == "on")
        status = "✅ Enabled" if toggle == "on" else "❌ Disabled"
        await query.answer(f"✅ Welcome {status.lower()}!", show_alert=True)
        await welcome_callback(update, context, data="welcome_settings")
        return
    
    if data == "welcome_mute_settings":
        curr_setting = sql.welcome_mutes(chat.id)
        buttons = [
            [InlineKeyboardButton("❌ Off", callback_data="welcome_mute_set_off"),
             InlineKeyboardButton("🔇 Soft", callback_data="welcome_mute_set_soft")],
            [InlineKeyboardButton("🔇 Strong", callback_data="welcome_mute_set_strong"),
             InlineKeyboardButton("🧩 Captcha", callback_data="welcome_mute_set_captcha")],
            [InlineKeyboardButton("« Back", callback_data="welcome_settings"),
             InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
        ]
        try:
            await query.message.edit_text(
                f"🔇 <b>Welcome Mute Settings</b>\n\n"
                f"<b>Current Setting:</b> <code>{curr_setting}</code>\n\n"
                f"<b>Options:</b>\n"
                f"- ❌ <b>Off</b> - No muting\n"
                f"- 🔇 <b>Soft</b> - Restrict media for 24h\n"
                f"- 🔇 <b>Strong</b> - Mute until verified (120s timeout)\n"
                f"- 🧩 <b>Captcha</b> - Mute until captcha solved\n\n"
                f"<i>Click a button to change setting.</i>",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except BadRequest as excp:
            if "Message is not modified" not in excp.message:
                raise
        return
    
    if data.startswith("welcome_mute_set_"):
        mute_type = data.split("_")[-1]
        if mute_type == "off":
            sql.set_welcome_mutes(chat.id, False)
            await query.answer("✅ Mute set to OFF", show_alert=True)
        elif mute_type == "soft":
            sql.set_welcome_mutes(chat.id, "soft")
            await query.answer("✅ Mute set to SOFT", show_alert=True)
        elif mute_type == "strong":
            sql.set_welcome_mutes(chat.id, "strong")
            await query.answer("✅ Mute set to STRONG", show_alert=True)
        elif mute_type == "captcha":
            sql.set_welcome_mutes(chat.id, "captcha")
            await query.answer("✅ Mute set to CAPTCHA", show_alert=True)
        
        await welcome_callback(update, context, data="welcome_mute_settings")
        return
    
    if data.startswith("welcome_clean_"):
        clean_toggle = data.split("_")[-1]
        sql.set_clean_welcome(str(chat.id), clean_toggle == "on")
        status = "✅ Enabled" if clean_toggle == "on" else "❌ Disabled"
        await query.answer(f"✅ Clean welcome {status.lower()}!", show_alert=True)
        await welcome_callback(update, context, data="welcome_settings")
        return
    
    if data == "welcome_clean":
        clean_pref = sql.get_clean_pref(chat.id)
        buttons = [
            [InlineKeyboardButton("✅ Enable" if not clean_pref else "❌ Disable", 
                                 callback_data=f"welcome_clean_{'off' if clean_pref else 'on'}")],
            [InlineKeyboardButton("« Back", callback_data="welcome_settings"),
             InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
        ]
        status = "✅ Enabled" if clean_pref else "❌ Disabled"
        message_text = (
            f"🧹 <b>Clean Welcome Settings</b>\n\n"
            f"<b>Status:</b> {status}\n\n"
        )
        if clean_pref:
            message_text += "I should be deleting welcome messages up to two days old.\n\n"
        else:
            message_text += "I'm currently not deleting old welcome messages!\n\n"
        message_text += "<i>This helps prevent spam from old welcome messages.</i>"
        await query.message.edit_text(
            message_text,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
    
    if data == "welcome_service":
        service_clean = sql.clean_service(chat.id)
        buttons = [
            [InlineKeyboardButton("✅ Enable" if not service_clean else "❌ Disable", 
                                 callback_data=f"welcome_service_{'off' if service_clean else 'on'}")],
            [InlineKeyboardButton("« Back", callback_data="welcome_settings"),
             InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
        ]
        status = "✅ Enabled" if service_clean else "❌ Disabled"
        await query.message.edit_text(
            f"🧹 <b>Service Message Cleanup</b>\n\n"
            f"<b>Status:</b> {status}\n\n"
            f"{'I will delete Telegram service messages (user joined/left).' if service_clean else 'I will not delete service messages.'}\n\n"
            f"<i>Examples: 'user joined chat', 'user left chat'</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
    
    if data.startswith("welcome_service_"):
        service_toggle = data.split("_")[-1]
        sql.set_clean_service(chat.id, service_toggle == "on")
        status = "✅ Enabled" if service_toggle == "on" else "❌ Disabled"
        await query.answer(f"✅ Service clean {status.lower()}!", show_alert=True)
        await welcome_callback(update, context, data="welcome_settings")
        return
    
    if data == "welcome_reset":
        sql.set_custom_welcome(chat.id, None, None, sql.Types.TEXT)
        await query.answer("✅ Welcome message reset to default!", show_alert=True)
        await welcome_callback(update, context, data="welcome_settings")
        return
    
    if data == "welcome_set":
        await query.answer("📝 Use /setwelcome <message> to set custom welcome message!", show_alert=True)
        return

    if data == "welcome_toggle_mode":
        welcome_mode = REDIS.get(f"welcome_mode:{chat.id}")
        welcome_mode = welcome_mode.decode("utf-8") if welcome_mode else "image"
        new_mode = "text" if welcome_mode == "image" else "image"
        REDIS.set(f"welcome_mode:{chat.id}", new_mode)
        await query.answer(f"✅ Welcome mode changed to {new_mode.upper()}!", show_alert=True)
        await welcome_callback(update, context, data="welcome_settings")
        return


# ========================================
# Command: /captcha [ENABLE|DISABLE]
# ========================================

@cutiepii_cmd(command="captcha", filters=filters.ChatType.GROUPS, can_disable=False)
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def captcha_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if not args:
        curr_setting = sql.welcome_mutes(chat.id)
        is_captcha = curr_setting == "captcha"
        status = "Enabled" if is_captcha else "Disabled"
        await message.reply_text(f"<b>Captcha Settings</b>\nCaptcha: <code>{status}</code>\nWelcome Mute: <code>{curr_setting}</code>", parse_mode=ParseMode.HTML)
        return

    action = args[0].upper().strip()
    if action in ["ENABLE", "ON", "YES"]:
        sql.set_welcome_mutes(chat.id, "captcha")
        await message.reply_text("<b>Captcha Settings Updated</b>\nCaptcha check has been enabled for new members.", parse_mode=ParseMode.HTML)
    elif action in ["DISABLE", "OFF", "NO"]:
        sql.set_welcome_mutes(chat.id, False)
        await message.reply_text("<b>Captcha Settings Updated</b>\nCaptcha check has been disabled.", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("<b>Usage</b>\n<code>/captcha [enable|disable]</code>", parse_mode=ParseMode.HTML)


# ========================================
# Command: /get_welcome
# ========================================

@cutiepii_cmd(command="get_welcome", filters=filters.ChatType.GROUPS, can_disable=False)
@connection_status
async def get_welcome_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    
    pref, welcome_m, cust_content, welcome_type = sql.get_welc_pref(chat.id)
    if welcome_m:
        await message.reply_text(
            f"👋 <b>Your Current Welcome Message Template:</b>\n\n<code>{html.escape(welcome_m)}</code>",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply_text("There is no custom welcome template set. Using default greeting.")


# ========================================
# Command: /welcome_mode [text|image]
# ========================================

@cutiepii_cmd(command="welcome_mode", filters=filters.ChatType.GROUPS, can_disable=False)
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def welcome_mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if not args:
        current_mode = REDIS.get(f"welcome_mode:{chat.id}")
        current_mode = current_mode.decode("utf-8") if current_mode else "image"
        await message.reply_text(f"Welcome mode is currently: <code>{current_mode.upper()}</code>", parse_mode=ParseMode.HTML)
        return

    mode = args[0].lower().strip()
    if mode in ["text", "image"]:
        REDIS.set(f"welcome_mode:{chat.id}", mode)
        await message.reply_text(f"✅ Welcome mode has been set to: <code>{mode.upper()}</code>", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("Invalid welcome mode. Use `text` or `image`.")


# ========================================
# Command: /welcome_settings
# ========================================

@cutiepii_cmd(command="welcome_settings", filters=filters.ChatType.GROUPS, can_disable=False)
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def welcome_settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    
    pref, _, _, _ = sql.get_welc_pref(chat.id)
    clean_pref = sql.get_clean_pref(chat.id)
    mute_setting = sql.welcome_mutes(chat.id)
    service_clean = sql.clean_service(chat.id)
    welcome_mode = REDIS.get(f"welcome_mode:{chat.id}")
    welcome_mode = welcome_mode.decode("utf-8") if welcome_mode else "image"
    
    action_buttons = [
        [InlineKeyboardButton("✅ Enable" if not pref else "❌ Disable", 
                             callback_data=f"welcome_toggle_{'off' if pref else 'on'}"),
         InlineKeyboardButton("📝 Set Message", callback_data="welcome_set")],
        [InlineKeyboardButton("🔄 Reset", callback_data="welcome_reset"),
         InlineKeyboardButton("🧹 Clean Welcome", callback_data="welcome_clean")],
        [InlineKeyboardButton("🔇 Mute Settings", callback_data="welcome_mute_settings"),
         InlineKeyboardButton("🧹 Service Clean", callback_data="welcome_service")],
        [InlineKeyboardButton(f"Mode: {welcome_mode.upper()}", callback_data="welcome_toggle_mode")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="welcome_help"),
         InlineKeyboardButton("❌ Close", callback_data="welcome_close")]
    ]
    
    status_text = "✅ Enabled" if pref else "❌ Disabled"
    clean_status = "✅ ON" if clean_pref else "❌ OFF"
    service_status = "✅ ON" if service_clean else "❌ OFF"
    
    await message.reply_text(
        f"👋 <b>Welcome Settings</b>\n\n"
        f"<b>Welcome Status:</b> {status_text}\n"
        f"<b>Clean Welcome:</b> {clean_status}\n"
        f"<b>Service Clean:</b> {service_status}\n"
        f"<b>Mute Setting:</b> <code>{mute_setting}</code>\n"
        f"<b>Welcome Mode:</b> <code>{welcome_mode.upper()}</code>\n\n"
        f"<i>Use buttons below to manage settings.</i>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(action_buttons)
    )


# ========================================
# Command: /autoban
# ========================================

@cutiepii_cmd(command="autoban", filters=filters.ChatType.GROUPS, can_disable=False)
@connection_status
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
async def autoban_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message

    autoban_status = REDIS.get(f"autoban:{chat.id}")
    autoban_status = autoban_status.decode("utf-8") if autoban_status else "false"

    if autoban_status == "true":
        REDIS.set(f"autoban:{chat.id}", "false")
        await message.reply_text("❌ <b>Autoban (Kazuto-style) has been disabled in this group.</b>", parse_mode=ParseMode.HTML)
    else:
        REDIS.set(f"autoban:{chat.id}", "true")
        await message.reply_text("🟢 <b>Autoban (Kazuto-style) has been enabled in this group.</b>\n\nAny non-staff members who leave will be auto-banned.", parse_mode=ParseMode.HTML)


# ========================================
# Command: /cleangoodbye [on|off]
# ========================================

@cutiepii_cmd(command="cleangoodbye", filters=filters.ChatType.GROUPS, can_disable=False)
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def cleangoodbye_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if not args:
        pref = REDIS.get(f"cleangoodbye_pref:{chat.id}")
        pref = pref.decode("utf-8") if pref else "false"
        status = "ON" if pref == "true" else "OFF"
        await message.reply_text(f"Clean goodbye messages setting is currently: <code>{status}</code>", parse_mode=ParseMode.HTML)
        return

    action = args[0].lower().strip()
    if action in ["on", "yes", "enable"]:
        REDIS.set(f"cleangoodbye_pref:{chat.id}", "true")
        await message.reply_text("🟢 Clean goodbye messages has been enabled. Old goodbye messages will be deleted when a new user leaves.")
    elif action in ["off", "no", "disable"]:
        REDIS.set(f"cleangoodbye_pref:{chat.id}", "false")
        REDIS.delete(f"last_goodbye_message_id:{chat.id}")
        await message.reply_text("❌ Clean goodbye messages has been disabled.")
    else:
        await message.reply_text("Usage: `/cleangoodbye [on|off]`")


from telegram.ext import CallbackQueryHandler



__mod_name__ = "Greetings"
