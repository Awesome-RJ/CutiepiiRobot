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
from Cutiepii_Robot.modules.helper_funcs.decorators import register


import json
import requests
import os
import urllib.request

from telethon import *
from telethon.tl import functions, types

from typing import List
from typing import Optional

from telegram import Message

from Cutiepii_Robot import telethn
from Cutiepii_Robot.events import register


API_KEY = ""
URL = "https://services.gingersoftware.com/Ginger/correct/json/GingerTheText"


@register(pattern="^/spell(?: |$)(.*)")
async def _(event):
    msg = event.pattern_match.group(1).strip()
    if not msg:
        ctext = await event.get_reply_message()
        if ctext and ctext.text:
            msg = ctext.text

    if not msg:
        await event.reply("Reply to a message or provide text to check spelling. Usage: `/spell <text>`")
        return

    params = dict(lang="US", clientVersion="2.0", apiKey=API_KEY, text=msg)
    try:
        res = requests.get(URL, params=params, timeout=10)
        if res.status_code != 200:
            await event.reply("Ginger spelling service is currently unavailable.")
            return
        changes = res.json().get("LightGingerTheTextResult", [])
    except Exception as e:
        await event.reply(f"Ginger spelling service error: {e}")
        return

    if not changes:
        await event.reply("No spelling errors found!")
        return

    curr_string = ""
    prev_end = 0

    for change in changes:
        start = change.get("From")
        end = change.get("To") + 1
        if suggestions := change.get("Suggestions"):
            sugg_str = suggestions[0].get("Text")
            curr_string += msg[prev_end:start] + sugg_str
            prev_end = end

    curr_string += msg[prev_end:]
    await event.reply(curr_string)


class FreeDictionary:
    def meaning(self, word):
        try:
            r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=10)
            if r.status_code != 200:
                return None
            data = r.json()
            if not data or not isinstance(data, list):
                return None
            meanings = {}
            for entry in data:
                for m in entry.get("meanings", []):
                    pos = m.get("partOfSpeech")
                    defs = [d.get("definition") for d in m.get("definitions", []) if d.get("definition")]
                    if pos and defs:
                        meanings.setdefault(pos, []).extend(defs)
            return meanings
        except Exception:
            return None

    def synonym(self, word):
        try:
            r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=10)
            if r.status_code != 200:
                return None
            data = r.json()
            synonyms = []
            for entry in data:
                for m in entry.get("meanings", []):
                    for syn in m.get("synonyms", []):
                        if syn:
                            synonyms.append(syn)
                    for d in m.get("definitions", []):
                        for syn in d.get("synonyms", []):
                            if syn:
                                synonyms.append(syn)
            return list(set(synonyms)) if synonyms else None
        except Exception:
            return None

    def antonym(self, word):
        try:
            r = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}", timeout=10)
            if r.status_code != 200:
                return None
            data = r.json()
            antonyms = []
            for entry in data:
                for m in entry.get("meanings", []):
                    for ant in m.get("antonyms", []):
                        if ant:
                            antonyms.append(ant)
                    for d in m.get("definitions", []):
                        for ant in d.get("antonyms", []):
                            if ant:
                                antonyms.append(ant)
            return list(set(antonyms)) if antonyms else None
        except Exception:
            return None

dictionary = FreeDictionary()


@register(pattern="^/define")
async def _(event):
    text = event.text[len("/define ") :]
    word = f"{text}"
    let = dictionary.meaning(word)
    set = str(let)
    jet = set.replace("{", "")
    net = jet.replace("}", "")
    got = net.replace("", "")
    await event.reply(got)


@register(pattern="^/synonyms")
async def _(event):
    text = event.text[len("/synonyms ") :]
    word = f"{text}"
    let = dictionary.synonym(word)
    set = str(let)
    jet = set.replace("{", "")
    net = jet.replace("}", "")
    got = net.replace("", "")
    await event.reply(got)


@register(pattern="^/antonyms")
async def _(event):
    text = event.text[len("/antonyms ") :]
    word = f"{text}"
    let = dictionary.antonym(word)
    set = str(let)
    jet = set.replace("{", "")
    net = jet.replace("}", "")
    got = net.replace("", "")
    await event.reply(got)
