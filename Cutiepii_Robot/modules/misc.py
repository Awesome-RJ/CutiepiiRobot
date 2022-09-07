"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (C) 2021-2022, Awesome-RJ, [ https://github.com/Awesome-RJ ]
Copyright (c) 2021-2022, Yūki • Black Knights Union, [ https://github.com/Awesome-RJ/CutiepiiRobot ]

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

import contextlib
import random
import requests
import time
import re
import psutil
import platform
import sqlalchemy
import Cutiepii_Robot.modules.helper_funcs.git_api as git

from Cutiepii_Robot.modules.helper_funcs.anonymous import user_admin
from Cutiepii_Robot.modules.helper_funcs.chat_status import sudo_plus
from Cutiepii_Robot.modules.helper_funcs.alternate import send_action
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot import CUTIEPII_PTB, pgram, StartTime
from Cutiepii_Robot.__main__ import GDPR

from bs4 import BeautifulSoup
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, __version__ as ptbver
from telegram.constants import ParseMode, ChatAction
from telegram.error import BadRequest
from telegram.ext import filters as PTB_Cutiepii_Filters, CommandHandler, CallbackQueryHandler, CallbackContext
from platform import python_version
from telethon import version as tlthn
from pyrogram import filters
from pyrogram import __version__ as __pyro__
from requests import get

FORMATTING_HELP = """
Main Help Here
"""
MARKDOWN_HELP = """

Markdown is a very powerful formatting tool supported by telegram. Cutiepii Robot 愛 has some enhancements, to make sure that \
saved messages are correctly parsed, and to allow you to create buttons.

➛ <code>_italic_</code>: wrapping text with '_' will produce italic text
➛ <code>*bold*</code>: wrapping text with "*' will produce bold text
➛ <code>`code`</code>: wrapping text with "`' will produce monospaced text, also known as 'code'
➛ <code>[sometext](someURL)</code>: this will create a link - the message will just show <code>sometext</code>, \
and tapping on it will open the page at <code>someURL</code>.
<b>Example:</b><code>[test](example.com)</code>

➛ <code>[buttontext](buttonurl:someURL)</code>: this is a special enhancement to allow users to have telegram \
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

RANDOM_HELP = """
<b>Random Content</b>

Another thing that can be fun, is to randomise the contents of a message. Make things a little more personal by changing welcome messages, or changing notes!

<b>How to use random contents</b>:
- <code>%%%</code>: This separator can be used to add "random" replies to the bot.
For example:
<code>hello
%%%
how are you</code>
This will randomly choose between sending the first message, "hello", or the second message, "how are you". Use this to make Cutiepii Robot 愛 feel a bit more customised! (only works in notes/filters/greetings)

<b>Example welcome message</b>:
- Every time a new user joins, they'll be presented with one of the three messages shown here.
-> <code>/setwelcome hello there""" + "{first}! %%% Ooooh, {first} is in the house! %%% Welcome to the group, {first}!</code>"


@pgram.on_message(filters.command("slcheck"))
async def slcheck(_, message):
    message = Update.effective_message
    user = message.text.split(" ")[1]
    res = get(f"https://sylviorus.up.railway.app/user/{user}")
    if res["blacklisted"]:
        enf = res["enforcer"]
        reason = res["reason"]
        await message.reply_text(
            f"**Enforcer**: {enf}\n**User** : {user}\n**Reason**: {reason}")


async def gdpr(update: Update):
    await update.effective_message.reply_text("Deleting identifiable data...")
    for mod in GDPR:
        mod.__gdpr__(update.effective_user.id)

    await update.effective_message.reply_text(
        "Your personal data has been deleted.\n\nNote that this will not unban "
        "you from any chats, as that is telegram data, not Priscia data. "
        "Flooding, warns, and gbans are also preserved, as of "
        "[this](https://ico.org.uk/for-organisations/guide-to-the-general-data-protection-regulation-gdpr/individual-rights/right-to-erasure/), "
        "which clearly states that the right to erasure does not apply "
        '"for the performance of a task carried out in the public interest", as is '
        "the case for the aforementioned pieces of data.",
        parse_mode=ParseMode.MARKDOWN,
    )


@user_admin
async def echo(update: Update):
    message = update.effective_message
    args = message.text.split(" " or None, 1)

    if update.effective_message.reply_to_message:
        message.reply_to_message.reply_text(args[1],
                                            parse_mode=ParseMode.MARKDOWN,
                                            disable_web_page_preview=True)
    else:
        await message.reply_text(
            args[1],
            quote=False,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
    with contextlib.suppress(BadRequest):
        await message.delete()


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(
            seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += f"{time_list.pop()}, "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


def get_size(bytes, suffix="B"):
    factor = 1024
    for unit in ["", "K", "M", "G", "T", "P"]:
        if bytes < factor:
            return f"{bytes:.2f}{unit}{suffix}"
        bytes /= factor


async def markdown_help_sender(update: Update):
    markup = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(text="Markdown formatting",
                                 callback_data="mkhelp_markdownformat"),
            InlineKeyboardButton(text="Fillings",
                                 callback_data="mkhelp_fillings")
        ],
        [
            InlineKeyboardButton(text="Random Content",
                                 callback_data="mkhelp_randomcontent")
        ],
    ])
    if update.callback_query:
        await update.effective_message.edit_text(FORMATTING_HELP,
                                                 parse_mode=ParseMode.MARKDOWN,
                                                 reply_markup=markup)
    else:
        await update.effective_message.reply_text(
            FORMATTING_HELP,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=markup)


async def markdown_help(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type != "private":
        await update.effective_message.reply_text(
            "Contact me in pm",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "Markdown help",
                        url=f"t.me/{context.bot.username}?start=markdownhelp",
                    ),
                ],
            ], ),
        )
        return
    markdown_help_sender(update)


async def mkdown_btn(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    query = update.callback_query
    match = query.data.split("_")[1]

    if match == "fillings":
        await update.effective_message.edit_text(
            FILLINGS_HELP,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(text="Back", callback_data="mkhelp_main")
            ]], ),
        )

    elif match == "markdownformat":
        await update.effective_message.edit_text(
            MARKDOWN_HELP,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(text="Back", callback_data="mkhelp_main")
            ]], ),
        )

    elif match == "randomcontent":
        await update.effective_message.edit_text(
            RANDOM_HELP,
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(text="Back", callback_data="mkhelp_main")
            ]], ),
        )

    else:
        markdown_help_sender(update)

    await bot.answer_callback_query(query.id)


async def src(update: Update) -> None:
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
            ],
            disable_web_page_preview=True,
        ),
    )


@send_action(ChatAction.UPLOAD_PHOTO)
async def rmemes(update: Update, context: CallbackContext) -> None:
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
    res = requests.get(f"https://meme-api.herokuapp.com/gimme/{subreddit}")

    if res.status_code != 200:  # Like if api is down?
        await msg.reply_text("Sorry some error occurred :(")
        return
    res = res.json()

    rpage = res.get("subreddit")
    title = res.get("title")
    memeu = res.get("url")
    plink = res.get("postLink")

    caps = f"× <b>Title</b>: {title}\n"
    caps += f"× <b>Subreddit:</b> <pre>r/{rpage}</pre>"

    keyb = [[InlineKeyboardButton(text="Subreddit Postlink 🔗", url=plink)]]
    try:
        await context.bot.send_photo(
            chat.id,
            photo=memeu,
            caption=caps,
            reply_markup=InlineKeyboardMarkup(keyb),
            timeout=60,
            parse_mode=ParseMode.HTML,
        )

    except BadRequest as excp:
        return await msg.reply_text(f"Error! {excp.message}")


async def markdown_help(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type != "private":
        await update.effective_message.reply_text(
            "Contact me in pm",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "Markdown help",
                        url=
                        f"https://telegram.dog/{context.bot.username}?start=markdownhelp",
                    ),
                ],
            ], ),
        )
        return
    markdown_help_sender(update)


async def imdb(update: Update, context: CallbackContext) -> None:
    try:
        args = context.args
        movie_name = " ".join(args)
        remove_space = movie_name.split(" ")
        final_name = "+".join(remove_space)
        page = requests.get(
            f"https://www.imdb.com/find?ref_=nv_sr_fn&q={final_name}&s=all")

        str(page.status_code)
        soup = BeautifulSoup(page.content, "lxml")
        odds = soup.findAll("tr", "odd")
        mov_title = odds[0].findNext("td").findNext("td").text
        mov_link = ("http://www.imdb.com/" +
                    odds[0].findNext("td").findNext("td").a["href"])
        page1 = requests.get(mov_link)
        soup = BeautifulSoup(page1.content, "lxml")
        if soup.find("div", "poster"):
            poster = soup.find("div", "poster").img["src"]
        else:
            poster = ""
        if soup.find("div", "title_wrapper"):
            pg = soup.find("div", "title_wrapper").findNext("div").text
            mov_details = re.sub(r"\s+", " ", pg)
        else:
            mov_details = ""
        credit = soup.findAll("div", "credit_summary_item")
        director = credit[0].a.text
        if len(credit) == 1:
            writer = "Not available"
            stars = "Not available"
        elif len(credit) > 2:
            writer = credit[1].a.text
            actors = [x.text for x in credit[2].findAll("a")]
            actors.pop()
            stars = f"{actors[0]},{actors[1]},{actors[2]}"
        else:
            writer = "Not available"
            actors = [x.text for x in credit[1].findAll("a")]
            actors.pop()
            stars = f"{actors[0]},{actors[1]},{actors[2]}"
        if soup.find("div", "inline canwrap"):
            story_line = soup.find("div",
                                   "inline canwrap").findAll("p")[0].text
        else:
            story_line = "Not available"
        if info := soup.findAll("div", "txt-block"):
            mov_country = []
            mov_language = []
            for node in info:
                a = node.findAll("a")
                for i in a:
                    if "country_of_origin" in i["href"]:
                        mov_country.append(i.text)
                    elif "primary_language" in i["href"]:
                        mov_language.append(i.text)
        if soup.findAll("div", "ratingValue"):
            for r in soup.findAll("div", "ratingValue"):
                mov_rating = r.strong["title"]
        else:
            mov_rating = "Not available"
        msg = f"*Title :* {mov_title}\n{mov_details}\n*Rating :* {mov_rating} \n*Country :*  {mov_country}\n*Language :* {mov_language}\n*Director :* {director}\n*Writer :* {writer}\n*Stars :* {stars}\n*IMDB Url :* {mov_link}\n*Story Line :* {story_line}"
        await update.effective_message.reply_photo(
            photo=poster, caption=msg, parse_mode=ParseMode.MARKDOWN)
    except IndexError:
        await update.effective_message.reply_text(
            "Plox enter **Valid movie name** kthx")


@sudo_plus
async def status(update: Update):
    message = update.effective_message
    chat = update.effective_chat
    query = update.callback_query

    msg = "*Bot information*\n"
    msg += f"Python: `{python_version()}`\n"
    msg += f"Python Tg Bot: `{ptbver}`\n"
    msg += f"Telethon: `{tlthn.__version__}`\n"
    msg += f"Pyrogram: `{__pyro__}`\n"
    msg += f"SQLAlchemy: `{sqlalchemy.__version__}`\n"
    msg += f"GitHub API: `{str(git.vercheck())}`\n"
    uptime = get_readable_time((time.time() - StartTime))
    msg += f"Uptime: `{uptime}`\n\n"
    uname = platform.uname()
    msg += "*System information*\n"
    msg += f"OS: `{uname.system}`\n"
    msg += f"Version: `{uname.version}`\n"
    msg += f"Release: `{uname.release}`\n"
    msg += f"Processor: `{uname.processor}`\n"
    boot_time_timestamp = psutil.boot_time()
    bt = datetime.fromtimestamp(boot_time_timestamp)
    msg += f"Boot time: `{bt.day}/{bt.month}/{bt.year} - {bt.hour}:{bt.minute}:{bt.second}`\n"
    msg += f"CPU cores: `{psutil.cpu_count(logical=False)} physical, {psutil.cpu_count()} logical`\n"
    msg += f"CPU freq: `{psutil.cpu_freq().current:.2f}Mhz`\n"
    msg += f"CPU usage: `{psutil.cpu_percent()}%`\n"
    ram = psutil.virtual_memory()
    msg += f"RAM: `{get_size(ram.total)} - {get_size(ram.used)} used ({ram.percent}%)`\n"
    disk = psutil.disk_usage('/')
    msg += f"Disk usage: `{get_size(disk.total)} total - {get_size(disk.used)} used ({disk.percent}%)`\n"
    swap = psutil.swap_memory()
    msg += f"SWAP: `{get_size(swap.total)} - {get_size(swap.used)} used ({swap.percent}%)`\n"

    await message.reply_text(
        text=msg,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


__help__ = """
Available commands:
📐 Markdown:
➛ /markdownhelp`: quick summary of how markdown works in telegram - can only be called in private chats

💴 Currency converter:
➛ /cash`: currency converter.

Example:
 `/cash 1 USD INR`
      OR
 `/cash 1 usd inr`

Output: `1.0 USD = 75.505 INR`

🗣 Translator:
Translate some text by give a text or reply that text/caption.
Translate by Google Translate
➛ `/tr (lang) (""text)`
Give a target language and text as args for translate to that target.
Reply a message to translate that.
"" = Not used when replied to a message.

🕐 Timezones:
➛ /time <query>`: Gives information about a timezone.
Available queries: Country Code/Country Name/Timezone Name
 ➛ [Timezones list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

🖌️ Quotly:
➛ /q` : To quote a message.
➛ /q <Number>` : To quote more than 1 messages.
➛ /q r` : to quote a message with it's reply

🗜️ Compress And Decompress:
➛ /zip*:* reply to a telegram file to compress it in .zip format
➛ /unzip*:* reply to a telegram file to decompress it from the .zip format

👤 Fake Info:
➛ /fakegen*:* Generates Fake Information
➛ /picgen➛ / generate a fake pic

🎛️ Encryprion:
➛ /encrypt*:* Encrypts The Given Text
➛ /decrypt*:* Decrypts Previously Ecrypted Text

📙 English:
➛ /define <text>*:* Type the word or expression you want to search\nFor example /define kill
➛ /spell*:* while replying to a message, will reply with a grammar corrected version
➛ /synonyms <word>*:* Find the synonyms of a word
➛ /antonyms <word>*:* Find the antonyms of a word

📙 Encryprion:
➛ /antonyms <Word>*:* Get antonyms from Dictionary.
➛ /synonyms <Word>*:* Get synonyms from Dictionary.
➛ /define <Word>*:* Get definition from Dictionary.
➛ /spell <Word>*:* Get definition from Dictionary.

💳 CC Checker:
➛ /au [cc]*:* Stripe Auth given CC
➛ /pp [cc]*:* Paypal 1$ Guest Charge
➛ /ss [cc]*:* Speedy Stripe Auth
➛ /ch [cc]*:* Check If CC is Live
➛ /bin [bin]*:* Gather's Info About the bin
➛ /gen [bin]*:* Generates CC with given bin
➛ /key [sk]*:* Checks if Stripe key is Live


🗳  Other Commands:
Paste:
➛ /paste*:* Saves replied content to nekobin.com and replies with a url
React:
➛ /react*:* Reacts with a random reaction
Urban Dictonary:
➛ /ud <word>*:* Type the word or expression you want to search use
Wikipedia:
➛ /wiki <query>*:* wikipedia your query
Wallpapers:
➛ /wall <query>*:* get a wallpaper from alphacoders
Text To Speech:
➛ /texttospeech <text>*:* Converts a text message to a voice message.
Books:
➛ /book <book name>*:* Gets Instant Download Link Of Given Book.
Cricket Score:
➛ /cs*:* get a Cricket Score.
Phone Info
➛ /phone [phone no]*:* Gathers no info.

Bass Boosting
➛ /bassboost*:* Reply To Music Bass Boost.
"""

CUTIEPII_PTB.add_handler(
    DisableAbleCommandHandler(
        "echo",
        echo,
        filters=PTB_Cutiepii_Filters.ChatType.GROUPS,
    ))
CUTIEPII_PTB.add_handler(CommandHandler("markdownhelp", markdown_help))
CUTIEPII_PTB.add_handler(
    CommandHandler(
        "gdpr",
        gdpr,
        filters=PTB_Cutiepii_Filters.ChatType.PRIVATE,
    ))
CUTIEPII_PTB.add_handler(CallbackQueryHandler(mkdown_btn, pattern=r"mkhelp_"))
CUTIEPII_PTB.add_handler(
    CommandHandler(
        "source",
        src,
        filters=PTB_Cutiepii_Filters.ChatType.PRIVATE,
    ))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("rmeme", rmemes))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("status", status))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("imdb", imdb))

__mod_name__ = "Extras"
__command_list__ = ["id", "echo", "source", "rmeme", "status"]
