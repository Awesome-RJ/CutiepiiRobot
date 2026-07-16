"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.
"""

import html
import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd

@cutiepii_cmd(command=["dict", "define", "meaning"], group=410)
async def dictionary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("<b>Invalid Command Usage</b>\nPlease specify a word to define. Usage: <code>/define [word]</code>", parse_mode=ParseMode.HTML)
        return

    word = args[0].strip()
    await message.reply_chat_action("typing")

    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        r = requests.get(url, timeout=10)
        
        if r.status_code == 404:
            await message.reply_text(f"<b>No Results Found</b>\nCould not find any definition for the word: <b>{html.escape(word)}</b>", parse_mode=ParseMode.HTML)
            return
            
        if r.status_code != 200:
            await message.reply_text("<b>API Connection Error</b>\nThe dictionary service is currently unavailable.", parse_mode=ParseMode.HTML)
            return

        data = r.json()
        if not isinstance(data, list) or len(data) == 0:
            await message.reply_text(f"<b>No Results Found</b>\nCould not find any definition for the word: <b>{html.escape(word)}</b>", parse_mode=ParseMode.HTML)
            return

        entry = data[0]
        word_name = entry.get("word", word)
        phonetic = entry.get("phonetic", "")
        origin = entry.get("origin", "")
        meanings = entry.get("meanings", [])

        reply_text = f"<b>Word:</b> {html.escape(word_name.capitalize())}\n"
        if phonetic:
            reply_text += f"<b>Phonetic:</b> {html.escape(phonetic)}\n"
        if origin:
            reply_text += f"<b>Origin:</b> {html.escape(origin)}\n"
        reply_text += "\n"

        for meaning in meanings[:3]:
            pos = meaning.get("partOfSpeech", "")
            reply_text += f"<i>{html.escape(pos.capitalize())}</i>\n"
            definitions = meaning.get("definitions", [])
            for idx, df in enumerate(definitions[:3], 1):
                definition = df.get("definition", "")
                example = df.get("example", "")
                reply_text += f"  {idx}. {html.escape(definition)}\n"
                if example:
                    reply_text += f"     <i>Example: \"{html.escape(example)}\"</i>\n"
            reply_text += "\n"

        await message.reply_text(reply_text.strip(), parse_mode=ParseMode.HTML)

    except Exception as e:
        await message.reply_text(f"<b>Error</b>\nAn error occurred while fetching dictionary details: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="synonym", group=418)
async def synonym_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("<b>Invalid Command Usage</b>\nPlease specify a word to search. Usage: <code>/synonym [word]</code>", parse_mode=ParseMode.HTML)
        return

    word = args[0].strip()
    await message.reply_chat_action("typing")

    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        r = requests.get(url, timeout=10)
        
        if r.status_code == 404:
            await message.reply_text(f"<b>No Results Found</b>\nCould not find any synonyms for the word: <b>{html.escape(word)}</b>", parse_mode=ParseMode.HTML)
            return
            
        if r.status_code != 200:
            await message.reply_text("<b>API Connection Error</b>\nThe dictionary service is currently unavailable.", parse_mode=ParseMode.HTML)
            return

        data = r.json()
        if not isinstance(data, list) or len(data) == 0:
            await message.reply_text(f"<b>No Results Found</b>\nCould not find any synonyms for the word: <b>{html.escape(word)}</b>", parse_mode=ParseMode.HTML)
            return

        synonyms = set()
        for entry in data:
            for meaning in entry.get("meanings", []):
                for syn in meaning.get("synonyms", []):
                    synonyms.add(syn)
                for df in meaning.get("definitions", []):
                    for syn in df.get("synonyms", []):
                        synonyms.add(syn)

        if not synonyms:
            await message.reply_text(f"<b>No Results Found</b>\nNo synonyms found for the word: <b>{html.escape(word)}</b>", parse_mode=ParseMode.HTML)
            return

        reply = f"<b>Synonyms for {html.escape(word.capitalize())}:</b>\n\n"
        reply += ", ".join(f"<code>{html.escape(s)}</code>" for s in sorted(synonyms))
        await message.reply_text(reply, parse_mode=ParseMode.HTML)

    except Exception as e:
        await message.reply_text(f"<b>Error</b>\nAn error occurred: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="antonym", group=419)
async def antonym_lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    args = context.args

    if not args:
        await message.reply_text("<b>Invalid Command Usage</b>\nPlease specify a word to search. Usage: <code>/antonym [word]</code>", parse_mode=ParseMode.HTML)
        return

    word = args[0].strip()
    await message.reply_chat_action("typing")

    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        r = requests.get(url, timeout=10)
        
        if r.status_code == 404:
            await message.reply_text(f"<b>No Results Found</b>\nCould not find any antonyms for the word: <b>{html.escape(word)}</b>", parse_mode=ParseMode.HTML)
            return
            
        if r.status_code != 200:
            await message.reply_text("<b>API Connection Error</b>\nThe dictionary service is currently unavailable.", parse_mode=ParseMode.HTML)
            return

        data = r.json()
        if not isinstance(data, list) or len(data) == 0:
            await message.reply_text(f"<b>No Results Found</b>\nCould not find any antonyms for the word: <b>{html.escape(word)}</b>", parse_mode=ParseMode.HTML)
            return

        antonyms = set()
        for entry in data:
            for meaning in entry.get("meanings", []):
                for ant in meaning.get("antonyms", []):
                    antonyms.add(ant)
                for df in meaning.get("definitions", []):
                    for ant in df.get("antonyms", []):
                        antonyms.add(ant)

        if not antonyms:
            await message.reply_text(f"<b>No Results Found</b>\nNo antonyms found for the word: <b>{html.escape(word)}</b>", parse_mode=ParseMode.HTML)
            return

        reply = f"<b>Antonyms for {html.escape(word.capitalize())}:</b>\n\n"
        reply += ", ".join(f"<code>{html.escape(a)}</code>" for a in sorted(antonyms))
        await message.reply_text(reply, parse_mode=ParseMode.HTML)

    except Exception as e:
        await message.reply_text(f"<b>Error</b>\nAn error occurred: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)


__help__ = True

__mod_name__ = "Dictionary"
