import html
import os
from gpytranslate import Translator
from gtts import gTTS
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Cutiepii_Robot import dispatcher, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd

trans = Translator()
AUDIO_FILE = "Cutiepii_Robot_tts.mp3"


@cutiepii_cmd(command=["tr", "tl", "translate"])
async def translate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    reply_msg = message.reply_to_message

    to_translate = ""
    if not reply_msg:
        if len(context.args) > 1:
            dest = context.args[0]
            if dest and "//" in dest:
                try:
                    source, dest = dest.split("//")
                except ValueError:
                    source = "auto"
            else:
                source = "auto"
            to_translate = " ".join(context.args[1:])
        elif len(context.args) == 1:
            dest = "en"
            source = "auto"
            to_translate = context.args[0]
        else:
            await message.reply_text("Reply to a message to translate, or use: `/tr <lang_code> <text>`", parse_mode=ParseMode.MARKDOWN)
            return
    else:
        to_translate = reply_msg.text or reply_msg.caption
        if not to_translate:
            await message.reply_text("Text to translate not found!")
            return
            
        args = context.args[0] if context.args else None
        if args and "//" in args:
            try:
                source, dest = args.split("//")
            except ValueError:
                source = "auto"
                dest = "en"
        else:
            source = "auto"
            dest = args or "en"

    if source == "auto":
        try:
            detected = await trans.detect(to_translate)
            source = detected if detected else "auto"
        except Exception as e:
            LOGGER.warning(f"Failed to detect language: {e}")
            source = "auto"

    try:
        translation = await trans.translate(
            to_translate, sourcelang=source, targetlang=dest
        )
        
        reply = f"<code>{html.escape(translation.text)}</code>"
        await message.reply_text(
            reply,
            parse_mode=ParseMode.HTML,
        )
    except Exception as e:
        LOGGER.exception(f"Error in translate: {e}")
        await message.reply_text(f"An error occurred during translation: {e}")


@cutiepii_cmd(command=["lang", "languages"])
async def languages_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Click [here](https://telegra.ph/Lang-Codes-03-19-3) to see the list of supported language codes!",
        disable_web_page_preview=True,
        parse_mode=ParseMode.MARKDOWN,
    )


@cutiepii_cmd(command="tts")
async def tts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    reply_msg = message.reply_to_message
    
    text = ""
    lang = "en"
    
    if context.args:
        first_arg = context.args[0].lower()
        if len(first_arg) == 2 and first_arg.isalpha():
            lang = first_arg
            text = " ".join(context.args[1:])
        else:
            text = " ".join(context.args)
            
    if not text and reply_msg:
        text = reply_msg.text or reply_msg.caption
        
    if not text:
        await message.reply_text(
            "Enter some text or reply to a text message to convert it to audio.\n\n"
            "💡 <i>Tip: You can specify target language code first, e.g. <code>/tts es hello</code></i>",
            parse_mode=ParseMode.HTML
        )
        return
        
    text = text.replace("\n", " ")
    status_msg = await message.reply_text("`Converting text to speech...`", parse_mode=ParseMode.MARKDOWN)
    
    try:
        tts = gTTS(text, lang=lang, tld="co.in")
        tts.save(AUDIO_FILE)
        
        if os.path.exists(AUDIO_FILE):
            with open(AUDIO_FILE, "rb") as voice:
                await message.reply_voice(
                    voice=voice,
                    caption=f"🗣 <b>Text-to-Speech ({lang})</b>",
                    parse_mode=ParseMode.HTML
                )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Failed to generate audio file.")
            
    except Exception as e:
        LOGGER.exception(f"Error in /tts: {e}")
        await status_msg.edit_text(f"❌ Failed to convert text to speech: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)
    finally:
        if os.path.exists(AUDIO_FILE):
            try:
                os.remove(AUDIO_FILE)
            except Exception:
                pass


__mod_name__ = "Translation"

__help__ = True
