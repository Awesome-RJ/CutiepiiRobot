from gpytranslate import Translator
from telegram.ext import CommandHandler, CallbackContext
from telegram import (
    Message,
    Chat,
    User,
    ParseMode,
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from Cutiepii_Robot import dispatcher
from Cutiepii_Robot import pgram, BOT_USERNAME
from pyrogram import filters
from pyrogram.types import Message
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler


trans = Translator()


@pgram.on_message(filters.command(["tr", f"tr@{BOT_USERNAME}"]))
async def translate(_, message: Message) -> None:
    reply_msg = message.reply_to_message
    if not reply_msg:
        await message.reply_text("Reply to a message to translate it!")
        return
    if reply_msg.caption:
        to_translate = reply_msg.caption
    elif reply_msg.text:
        to_translate = reply_msg.text
    try:
        args = message.text.split()[1].lower()
        if "//" in args:
            source = args.split("//")[0]
            dest = args.split("//")[1]
        else:
            source = await trans.detect(to_translate)
            dest = args
    except IndexError:
        source = await trans.detect(to_translate)
        dest = "en"
    translation = await trans(to_translate, sourcelang=source, targetlang=dest)
    reply = (
        f"<b>Translated from {source} to {dest}</b>:\n"
        f"<code>{translation.text}</code>"
    )

    await message.reply_text(reply, parse_mode="html")

__help__ = """ 
Use this module to translate stuff!
*Commands:*
   ➢ `/tl` (or `/tr`): as a reply to a message, translates it to English.
   ➢ `/tl <lang>`: translates to <lang>
eg: `/tl ja`: translates to Japanese.
   ➢ `/tl <source>//<dest>`: translates from <source> to <lang>.
eg: `/tl ja//en`: translates from Japanese to English.
• [List of supported languages for translation](https://telegra.ph/Lang-Codes-03-19-3)
"""

__mod_name__ = "Translator"
__command_list__ = ["tr", "tl"]
