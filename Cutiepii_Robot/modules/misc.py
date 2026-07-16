"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd
import random
import requests
import codecs
import json
import html
import os
import re
import subprocess
import time

import sys
import traceback
import psutil
import platform
import sqlalchemy
import Cutiepii_Robot.modules.helper_funcs.git_api as git


from Cutiepii_Robot.modules.helper_funcs.chat_status import user_admin, sudo_plus  
from Cutiepii_Robot import dispatcher, StartTime, BOT_USERNAME, BOT_NAME
from Cutiepii_Robot.modules.helper_funcs.alternate import typing_action, send_action

from datetime import datetime
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Chat, User
from telegram.constants import ParseMode, ChatAction
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from telegram.ext import filters, CommandHandler, CallbackQueryHandler
from platform import python_version, uname
from telethon import version as tlthn
# Pyrogram imports removed
from requests import get

FORMATTING_HELP = """
<b>Markdown Formatting & Fillings Help</b>

Cutiepii Robot supports formatting your messages using Markdown, adding inline buttons, and customizing responses with dynamic fillings (like the user's name or ID) or random replies.

Choose one of the options below to learn more:
"""
MARKDOWN_HELP = f"""
Markdown is a very powerful formatting tool supported by telegram. {BOT_NAME} has some enhancements, to make sure that \
saved messages are correctly parsed, and to allow you to create buttons.

- <code>_italic_</code>: wrapping text with '_' will produce italic text
- <code>*bold*</code>: wrapping text with "*' will produce bold text
- <code>`code`</code>: wrapping text with "`' will produce monospaced text, also known as 'code'
- <code>[sometext](someURL)</code>: this will create a link - the message will just show <code>sometext</code>, \
and tapping on it will open the page at <code>someURL</code>.
<b>Example:</b><code>[test](example.com)</code>

- <code>[buttontext](buttonurl:someURL)</code>: this is a special enhancement to allow users to have telegram \
buttons in their markdown. <code>buttontext</code> will be what is displayed on the button, and <code>someurl</code> \
will be the url which is opened.
<b>Example:</b> <code>[This is a button](buttonurl:example.com)</code>

If you want multiple buttons on the same line, use :same, as such:
<code>[one](buttonurl://example.com)
[two](buttonurl://google.com:same)</code>
This will create two buttons on a single line, instead of one button per line.

Keep in mind that your message <b>MUST</b> contain some text other than just a button!
"""

FILLINGS_HELP = """
<b>Fillings</b>

You can also customise the contents of your message with contextual data. For example, you could mention a user by name in the welcome message, or mention them in a filter!

<b>Supported fillings</b>:
- <code>{first}</code>: The user's first name.
- <code>{last}</code>: The user's last name.
- <code>{fullname}</code>: The user's full name.
- <code>{username}</code>: The user's username. If they don't have one, mentions the user instead.
- <code>{mention}</code>: Mentions the user with their firstname.
- <code>{id}</code>: The user's ID.
- <code>{chatname}</code>: The chat's name.
- <code>{rules}</code>: Create a button to the chat's rules.
- <code>{preview}</code>: Enables link previews for this message. Useful when using links to Instant View pages.
- <code>{random}</code>: You can use this filling for a random greeting in welcome message.
"""

RANDOM_HELP = f"""
<b>Random Content</b>

Another thing that can be fun, is to randomise the contents of a message. Make things a little more personal by changing welcome messages, or changing notes!

<b>How to use random contents</b>:
- <code>%%%</code>: This separator can be used to add "random" replies to the bot.
For example:
<code>hello
%%%
how are you</code>
This will randomly choose between sending the first message, "hello", or the second message, "how are you". Use this to make {BOT_NAME} feel a bit more customised! (only works in notes/filters/greetings)

<b>Example welcome message</b>:
- Every time a new user joins, they'll be presented with one of the three messages shown here.
-> <code>/setwelcome hello there""" + "{first}! %%% Ooooh, {first} is in the house! %%% Welcome to the group, {first}!</code>"


# Pyrogram slcheck command removed

@user_admin
@cutiepii_cmd(command="echo", can_disable=True, filters=filters.ChatType.GROUPS)
async def echo(update, _):
    args = update.effective_message.text.split(None, 1)
    if len(args) < 2:
        return
    message = update.effective_message

    if update.effective_message.reply_to_message:
        await message.reply_to_message.reply_text(
            args[1], parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )
    else:
        await message.reply_text(
            args[1],
            do_quote=False,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
    try:
        await message.delete()
    except BadRequest:
        pass

      
def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        if count < 3:
            remainder, result = divmod(seconds, 60)
        else:
            remainder, result = divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time
      
   
def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor
   
def get_network_speed():
     old = psutil.net_io_counters()
 
     time.sleep(1)
 
     new = psutil.net_io_counters()
 
     upload = (new.bytes_sent - old.bytes_sent)
     download = (new.bytes_recv - old.bytes_recv)
     return upload, download

async def markdown_help_sender(update: Update):
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="Markdown formatting", callback_data="mkhelp_markdownformat"), InlineKeyboardButton(text="Fillings", callback_data="mkhelp_fillings")],
        [InlineKeyboardButton(text="Random Content", callback_data="mkhelp_randomcontent")],
    ])
    if update.callback_query:
        await update.effective_message.edit_text(FORMATTING_HELP, parse_mode=ParseMode.HTML, reply_markup=markup)
    else:
        await update.effective_message.reply_text(FORMATTING_HELP, parse_mode=ParseMode.HTML, reply_markup=markup)
    
@cutiepii_cmd(command="markdownhelp")
async def markdown_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        await update.effective_message.reply_text(
            "Contact me in pm",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "Markdown help",
                            url=f"t.me/{BOT_USERNAME}?start=markdownhelp",
                        ),
                    ],
                ],
            ),
        )
        return
    await markdown_help_sender(update)


@cutiepii_callback(pattern=r"mkhelp_")
async def mkdown_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    query = update.callback_query
    match = query.data.split("_")[1]

    if match == "fillings":
        await update.effective_message.edit_text(
            FILLINGS_HELP, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Back", callback_data="mkhelp_main")]],
            ),
        )

    elif match == "markdownformat":
        await update.effective_message.edit_text(
            MARKDOWN_HELP, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Back", callback_data="mkhelp_main")]],
            ),
        )

    elif match == "randomcontent":
        await update.effective_message.edit_text(
            RANDOM_HELP, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton(text="Back", callback_data="mkhelp_main")]],
            ),
        )

    else:
        await markdown_help_sender(update)

    await query.answer()


@typing_action
@cutiepii_cmd(command="source", filters=filters.ChatType.PRIVATE)
async def src(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "old Unmaintained Source Code Are Public. Click Below For The Source.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="[► Click Here ◄]",
                        url="https://github.com/Awesome-RJ/CutiepiiRobot",
                    ),
                ],
            ]
        ),
        disable_web_page_preview=True,
    )
    
@send_action(ChatAction.UPLOAD_PHOTO)
@cutiepii_cmd(command="rmeme", can_disable=True)
async def rmemes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat

    SUBREDS = [
        "meirl",
        "dankmemes",
        "AdviceAnimals",
        "memes",
        "meme",
        "memes_of_the_dank",
        "PornhubComments",
        "teenagers",
        "memesIRL",
        "insanepeoplefacebook",
        "terriblefacebookmemes",
    ]

    subreddit = random.choice(SUBREDS)
    res = requests.get(f"https://meme-api.com/gimme/{subreddit}")

    if res.status_code != 200:  # Like if api is down?
        await msg.reply_text("Sorry some error occurred :(")
        return
    res = res.json()

    rpage = res.get(str("subreddit"))  # Subreddit
    title = res.get(str("title"))  # Post title
    memeu = res.get(str("url"))  # meme pic url
    plink = res.get(str("postLink"))

    caps = f"- <b>Title</b>: {title}\n"
    caps += f"- <b>Subreddit:</b> <pre>r/{rpage}</pre>"

    keyb = [[InlineKeyboardButton(text="Subreddit Postlink 🔗", url=plink)]]
    try:
        await context.bot.send_photo(
            chat.id,
            photo=memeu,
            caption=caps,
            reply_markup=InlineKeyboardMarkup(keyb),
            parse_mode=ParseMode.HTML,
        )

    except BadRequest as excp:
        await msg.reply_text(f"Error! {excp.message}")

   
@sudo_plus
@cutiepii_cmd(command="status", can_disable=True)
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    query = update.callback_query

    msg = "*╔═══「Bot information: 」*\n"
    msg += f"╠ Python: `{python_version()}`\n"
    msg += f"╠ Python Tg Bot: `{telegram.__version__}`\n"
    msg += f"╠ Telethon: `{tlthn.__version__}`\n"
    msg += f"╠ SQLAlchemy: `{sqlalchemy.__version__}`\n"
    msg += f"╠ GitHub API: `{str(git.vercheck())}`\n"
    uptime = get_readable_time((time.time() - StartTime))
    msg += f"╠ Uptime: `{uptime}`\n\n"
    uname = platform.uname()
    msg += "*╠═══「System information: 」*\n"
    msg += f"╠ OS: `{uname.system}`\n"
    msg += f"╠ Version: `{uname.version}`\n"
    msg += f"╠ Release: `{uname.release}`\n"
    msg += f"╠ Processor: `{uname.processor}`\n"
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    msg += f"╠ Boot time: `{bt.day}/{bt.month}/{bt.year} - {bt.hour}:{bt.minute}:{bt.second}`\n"
    msg += f"╠ CPU cores: `{psutil.cpu_count(logical=False)} physical, {psutil.cpu_count()} logical`\n"
    msg += f"╠ CPU freq: `{psutil.cpu_freq().current:.2f}Mhz`\n" if psutil.cpu_freq() else ""
    msg += f"╠ CPU usage: `{psutil.cpu_percent()}%`\n"
    ram = psutil.virtual_memory()
    msg += f"╠ RAM: `{get_size(ram.total)} - {get_size(ram.used)} used ({ram.percent}%)`\n"
    disk = psutil.disk_usage('/')
    msg += f"╠ Disk usage: `{get_size(disk.total)} total - {get_size(disk.used)} used ({disk.percent}%)`\n"
    swap = psutil.swap_memory()
    msg += f"╠ SWAP: `{get_size(swap.total)} - {get_size(swap.used)} used ({swap.percent}%)`\n"
    upload, download = get_network_speed()
    msg += f"Network: `⬇ {get_size(download)}/s | ⬆ {get_size(upload)}/s`\n"
    msg += f"*╚═══「 @{BOT_USERNAME} 」*\n"
    await message.reply_text(
        text = msg,
        parse_mode = ParseMode.MARKDOWN,
        disable_web_page_preview = True,
    )

__help__ = True


@cutiepii_cmd(command="id", can_disable=True)
async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get ID of user, chat, or replied-to user/forward."""
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    # Build reply text
    if msg.reply_to_message:
        replied = msg.reply_to_message
        reply_user = replied.from_user
        # Check if message is a forward
        origin = getattr(replied, 'forward_origin', None)
        if origin and getattr(origin, 'sender_user', None):
            orig_user = origin.sender_user
            text = (
                f"Original sender ID: <code>{orig_user.id}</code>\n"
                f"Forwarded by: <code>{reply_user.id}</code>\n" if reply_user else
                f"Original sender ID: <code>{orig_user.id}</code>\n"
            )
        elif replied.sender_chat:
            # Replied to a channel/anonymous admin message
            text = f"Channel/Chat ID: <code>{replied.sender_chat.id}</code>\n"
        elif reply_user:
            text = f"User ID: <code>{reply_user.id}</code>\n"
        else:
            text = "Could not determine the user ID.\n"
    elif chat.type == 'private':
        text = f"Your ID: <code>{user.id}</code>\n"
    else:
        text = (
            f"Your ID: <code>{user.id}</code>\n"
            f"This group's ID: <code>{chat.id}</code>\n"
        )

    # Message ID logic
    msg_id = msg.reply_to_message.message_id if msg.reply_to_message else msg.message_id
    if chat.type in ('supergroup', 'channel'):
        if chat.username:
            msg_link = f"https://t.me/{chat.username}/{msg_id}"
        else:
            chat_id_str = str(chat.id)
            if chat_id_str.startswith("-100"):
                chat_id_str = chat_id_str[4:]
            elif chat_id_str.startswith("-"):
                chat_id_str = chat_id_str[1:]
            msg_link = f"https://t.me/c/{chat_id_str}/{msg_id}"
        msg_id_text = f"<a href=\"{msg_link}\">{msg_id}</a>"
    else:
        msg_id_text = f"<code>{msg_id}</code>"

    text += f"Message ID: {msg_id_text}"

    await msg.reply_text(text, parse_mode=ParseMode.HTML)


async def get_user_info(chat: Chat, user: User, bot) -> str:
    import contextlib
    import Cutiepii_Robot.modules.sql.users_sql as sql
    from telegram.helpers import mention_html
    from Cutiepii_Robot import SUDO_USERS, DEV_USERS, SUPPORT_USERS, TIGER_USERS, WHITELIST_USERS, OWNER_ID

    text = (
        f"<b>General:</b>\n"
        f"ID: <code>{user.id}</code>\n"
        f"First Name: {html.escape(user.first_name)}"
    )
    if user.last_name:
        text += f"\nLast Name: {html.escape(user.last_name)}"
    if user.username:
        text += f"\nUsername: @{html.escape(user.username)}"
    text += f"\nPermanent user link: {mention_html(user.id, 'link')}"
    
    status_list = []
    if user.id == OWNER_ID:
        status_list.append("Owner (Global)")
    elif user.id in DEV_USERS:
        status_list.append("Developer")
    elif user.id in SUDO_USERS:
        status_list.append("Sudo")
    elif user.id in SUPPORT_USERS:
        status_list.append("Support")
    elif user.id in TIGER_USERS:
        status_list.append("Tiger")
    elif user.id in WHITELIST_USERS:
        status_list.append("Whitelist")
        
    with contextlib.suppress(Exception):
        user_member = await chat.get_member(user.id)
        if user_member.status == "creator":
            status_list.append("Creator (Group)")
        elif user_member.status == "administrator":
            status_list.append("Admin (Group)")
            
    import Cutiepii_Robot.modules.sql.approve_sql as approve_sql
    if approve_sql.is_approved(chat.id, user.id):
        status_list.append("Approved")
        
    import Cutiepii_Robot.modules.sql.afk_sql as afk_sql
    if afk_sql.is_afk(user.id):
        afk_status = afk_sql.check_afk_status(user.id)
        if afk_status:
            import humanize
            from datetime import timezone
            time_diff = datetime.now(timezone.utc) - afk_status.time.replace(tzinfo=timezone.utc)
            time_away = humanize.naturaldelta(time_diff)
            status_list.append(f"AFK (away for {time_away})")
        else:
            status_list.append("AFK")

    if status_list:
        text += f"\nStatus: <b>{', '.join(status_list)}</b>"
    else:
        text += f"\nStatus: <b>Member</b>"
    
    dc_text = "Unknown"
    try:
        from Cutiepii_Robot import telethn
        t_user = await telethn.get_entity(user.id)
        if t_user and t_user.photo and hasattr(t_user.photo, 'dc_id'):
            dc_id = t_user.photo.dc_id
            dc_locations = {
                1: "Miami, FL, USA",
                2: "Amsterdam, Netherlands",
                3: "Miami, FL, USA",
                4: "Singapore",
                5: "Helsinki, Finland"
            }
            location = dc_locations.get(dc_id, "Unknown Location")
            dc_text = f"<code>{dc_id}</code> ({location})"
    except Exception:
        pass
    text += f"\nDatacenter: {dc_text}"
    
    pfp_count = 0
    try:
        photos = await bot.get_user_profile_photos(user.id)
        if photos:
            pfp_count = photos.total_count
    except Exception:
        pass
    text += f"\nProfile pictures count: <code>{pfp_count}</code>"
    
    Nation_level_present = False
    num_chats = sql.get_user_num_chats(user.id)
    text += f"\n<b>Chat count</b>: <code>{num_chats}</code>"
    
    with contextlib.suppress(BadRequest):
        user_member = await chat.get_member(user.id)
        if user_member.status == "administrator":
            result = await bot.get_chat_member(chat.id, user.id)
            if result.custom_title:
                text += f"\nThis user holds the title <b>{result.custom_title}</b> here."
                
    if user.id == OWNER_ID:
        text += '\nThis person is my owner'
        Nation_level_present = True
    elif user.id in DEV_USERS:
        text += '\nThis person is a Developer'
        Nation_level_present = True
    elif user.id in SUDO_USERS:
        text += '\nThe Nation level of this person is Sudo'
        Nation_level_present = True
    elif user.id in SUPPORT_USERS:
        text += '\nThe Nation level of this person is Support'
        Nation_level_present = True
    elif user.id in TIGER_USERS:
        text += '\nThe Nation level of this person is Tiger'
        Nation_level_present = True
    elif user.id in WHITELIST_USERS:
        text += '\nThe Nation level of this person is Whitelist'
        Nation_level_present = True
        
    if Nation_level_present:
        text += f' [<a href="https://t.me/{bot.username}?start=nations">?</a>]'
    text += "\n"
    
    import asyncio
    from Cutiepii_Robot.__main__ import USER_INFO
    for mod in USER_INFO:
        if mod.__mod_name__ == "Users":
            continue
        try:
            mod_info = mod.__user_info__(user.id)
            if asyncio.iscoroutine(mod_info):
                mod_info = await mod_info
        except TypeError:
            try:
                mod_info = mod.__user_info__(user.id, chat.id)
                if asyncio.iscoroutine(mod_info):
                    mod_info = await mod_info
            except Exception:
                mod_info = None
        except Exception:
            mod_info = None
            
        if mod_info:
            text += "\n" + mod_info
            
    return text


def get_chat_info(chat: Chat) -> str:
    from Cutiepii_Robot.modules.users import __user_info__ as chat_count
    text = (
        f"<b>Chat Info:</b>\n"
        f"<b>Title:</b> {chat.title}"
    )
    if chat.username:
        text += f"\n<b>Username:</b> @{html.escape(chat.username)}"
    text += f"\n<b>Chat ID:</b> <code>{chat.id}</code>"
    text += f"\n<b>Chat Type:</b> {chat.type.capitalize()}"
    text += "\n" + chat_count(chat.id)
    return text


@cutiepii_cmd(command="info", can_disable=True)
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from io import BytesIO
    from telegram import MessageEntity
    from Cutiepii_Robot import INFOPIC
    from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user

    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    
    user_id = await extract_user(update.effective_message, args)
    if user_id:
        try:
            user = await bot.get_chat(user_id)
        except Exception as e:
            await message.reply_text(f"Error fetching user: {e}")
            return
    elif not message.reply_to_message and not args:
        user = (
            message.sender_chat
            if message.sender_chat is not None
            else message.from_user
        )
    elif not message.reply_to_message and (
        not args
        or (
            len(args) >= 1
            and not args[0].startswith("@")
            and not args[0].lstrip("-").isdigit()
            and not message.parse_entities([MessageEntity.TEXT_MENTION])
        )
    ):
        await message.reply_text("I can't extract a user from this.")
        return
    else:
        return

    # Check if user is a chat/channel
    if hasattr(user, 'type') and user.type != "private":
        text = get_chat_info(user)
        is_chat = True
    else:
        text = await get_user_info(chat, user, bot)
        is_chat = False

    if INFOPIC:
        if is_chat:
            try:
                pic = user.photo.big_file_id
                pfp_file = await bot.get_file(pic)
                pfp = BytesIO()
                await pfp_file.download_to_memory(pfp)
                pfp.seek(0)
                await message.reply_document(
                    document=pfp,
                    filename=f'{user.id}.jpg',
                    caption=text,
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                await message.reply_text(
                    text,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
        else:
            try:
                photos = await bot.get_user_profile_photos(user.id)
                if photos.photos:
                    profile = photos.photos[0][-1]
                    _file = await bot.get_file(profile.file_id)
                    pfp = BytesIO()
                    await _file.download_to_memory(pfp)
                    pfp.seek(0)
                    await message.reply_document(
                        document=pfp,
                        filename=f'{user.id}.jpg',
                        caption=text,
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    await message.reply_text(
                        text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
                    )
            except Exception:
                await message.reply_text(
                    text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
                )
    else:
        await message.reply_text(
            text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )


@sudo_plus
@cutiepii_cmd(command="ginfo", can_disable=True)
async def ginfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from io import BytesIO
    from telegram.helpers import escape_markdown
    from Cutiepii_Robot import INFOPIC
    from Cutiepii_Robot.modules.users import __user_info__ as chat_count

    bot = context.bot
    args = context.args
    message = update.effective_message
    chat = update.effective_chat
    
    if len(args) == 0:
        if chat.type == "private":
            await message.reply_text("Please specify a chat ID or username (e.g. <code>/ginfo -100xxx</code> or <code>/ginfo @username</code>)", parse_mode=ParseMode.HTML)
            return
        chat_id = chat.id
    else:
        chat_id = args[0]
        try:
            chat_id = int(chat_id)
        except ValueError:
            if not chat_id.startswith("@"):
                chat_id = f"@{chat_id}"
                
    try:
        chat_obj = await bot.get_chat(chat_id)
    except Exception as e:
        await message.reply_text(f"Error fetching chat: {e}")
        return
        
    try:
        member_count = await bot.get_chat_member_count(chat_obj.id)
    except Exception:
        member_count = "Unknown"
        
    text = (
        f"<b>Group Information:</b>\n"
        f"<b>Title:</b> {html.escape(chat_obj.title or '')}\n"
        f"<b>Chat ID:</b> <code>{chat_obj.id}</code>\n"
        f"<b>Type:</b> {chat_obj.type.capitalize()}\n"
    )
    if chat_obj.username:
        text += f"<b>Username:</b> @{html.escape(chat_obj.username)}\n"
    text += f"<b>Members:</b> <code>{member_count}</code>\n"
    
    if chat_obj.description:
        text += f"<b>Description:</b>\n{html.escape(chat_obj.description)}\n"
        
    if chat_obj.invite_link:
        text += f"<b>Invite Link:</b> {chat_obj.invite_link}\n"
        
    db_info = chat_count(chat_obj.id)
    if db_info:
        text += f"\n{db_info}"
        
    try:
        from telegram.helpers import mention_html
        admins = await bot.get_chat_administrators(chat_obj.id)
        creator = None
        admin_list = []
        for member in admins:
            user_obj = member.user
            try:
                from Cutiepii_Robot.modules.sql import users_sql as sql
                sql.update_user(user_obj.id, user_obj.username, chat_obj.id, chat_obj.title)
            except Exception as e:
                LOGGER.error(f"Error saving admin {user_obj.id} to database in ginfo: {e}")
            mention = mention_html(user_obj.id, html.escape(user_obj.first_name or "User"))
            if user_obj.username:
                mention = f"{mention} (@{html.escape(user_obj.username)})"
            
            entry = f"{mention} (<code>{user_obj.id}</code>)"
            if member.status == "creator":
                creator = entry
            else:
                admin_list.append(entry)
                
        text += "\n\n<b>Administrators:</b>"
        if creator:
            text += f"\n<b>Creator:</b>\n➛ {creator}"
        if admin_list:
            text += f"\n<b>Admins ({len(admin_list)}):</b>"
            for adm in admin_list:
                text += f"\n➛ {adm}"
    except Exception as e:
        text += f"\n\n<b>Administrators:</b> Error fetching admins: {e}"
        
    if INFOPIC and chat_obj.photo:
        try:
            pic = chat_obj.photo.big_file_id
            pfp_file = await bot.get_file(pic)
            pfp = BytesIO()
            await pfp_file.download_to_memory(pfp)
            pfp.seek(0)
            await message.reply_document(
                document=pfp,
                filename=f'{chat_obj.id}.jpg',
                caption=text,
                parse_mode=ParseMode.HTML,
            )
            return
        except Exception:
            pass

    await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@cutiepii_cmd(command="gifid", can_disable=True)
async def gifid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.animation:
        await update.effective_message.reply_text(
            f"Gif ID:\n<code>{msg.reply_to_message.animation.file_id}</code>",
            parse_mode=ParseMode.HTML,
        )
    else:
        await update.effective_message.reply_text("Please reply to a gif to get its ID.")


@cutiepii_cmd(command=["botlist", "bots"], can_disable=True)
async def botlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from telethon.tl.types import ChannelParticipantsBots
    from telegram.helpers import mention_html
    from Cutiepii_Robot import telethn
    
    chat = update.effective_chat
    message = update.effective_message
    
    if chat.type == "private":
        await message.reply_text("This command can only be used in groups.")
        return
        
    try:
        chat_ent = await telethn.get_entity(chat.id)
        bots = await telethn.get_participants(chat_ent, filter=ChannelParticipantsBots)
    except Exception:
        try:
            chat_ent = await telethn.get_entity(chat.id)
            bots = [u for u in await telethn.get_participants(chat_ent) if u.bot]
        except Exception as e:
            await message.reply_text(f"Error fetching bots list: {e}")
            return

    if not bots:
        await message.reply_text("No bots found in this group.")
        return
        
    text = f"<b>Bots in {html.escape(chat.title)}:</b>\n"
    for i, bot_user in enumerate(bots, 1):
        mention = mention_html(bot_user.id, html.escape(bot_user.first_name or "Bot"))
        if bot_user.username:
            mention = f"{mention} (@{html.escape(bot_user.username)})"
        text += f"{i}. {mention} (<code>{bot_user.id}</code>)\n"
        
        # Save bot in database
        try:
            from Cutiepii_Robot.modules.sql import users_sql as sql
            sql.update_user(bot_user.id, bot_user.username, chat.id, chat.title)
        except Exception as e:
            LOGGER.error(f"Error saving bot {bot_user.id} to database: {e}")
        
    await message.reply_text(text, parse_mode=ParseMode.HTML)





__mod_name__ = "Extras"
__command_list__ = ["id", "echo", "source", "rmeme", "status", "info", "gifid", "ginfo", "botlist"]
__handlers__ = [
]
