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
import requests
import json
import zlib
import base64
import base58
import typing
import contextlib

from typing import Dict, List
from urllib.parse import urlparse, urljoin, urlunparse
from Crypto import Random, Hash
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from math import ceil
from asyncio import sleep
from Cutiepii_Robot import NO_LOAD
from telegram import Bot, InlineKeyboardButton
from telegram.constants import ParseMode, MessageLimit
MAX_MESSAGE_LENGTH = MessageLimit.MAX_TEXT_LENGTH
from telegram.error import TelegramError


class EqInlineKeyboardButton(InlineKeyboardButton):
    def __eq__(self, other):
        return self.text == other.text

    def __lt__(self, other):
        return self.text < other.text

    def __gt__(self, other):
        return self.text > other.text

async def delete(delmsg, timer):
    await sleep(timer)
    try:
        await delmsg.delete()
    except Exception:
        return

def split_message(msg: str) -> List[str]:
    if len(msg) < MAX_MESSAGE_LENGTH:
        return [msg]

    lines = msg.splitlines(True)
    small_msg = ""
    result = []
    for line in lines:
        if len(small_msg) + len(line) < MAX_MESSAGE_LENGTH:
            small_msg += line
        else:
            result.append(small_msg)
            small_msg = line
    # Else statement at the end of the for loop, so append the leftover string.
    result.append(small_msg)

    return result


def paginate_modules(page_n: int, module_dict: Dict, prefix, chat=None) -> List:
    if not chat:
        modules = sorted(
            [InlineKeyboardButton(x.__mod_name__,
                                    callback_data="{}_module({})".format(prefix, x.__mod_name__.lower())) for x
             in module_dict.values()],
            key=lambda x: x.text
        )
    else:
        modules = sorted(
            [InlineKeyboardButton(x.__mod_name__,
                                    callback_data="{}_module({},{})".format(prefix, chat, x.__mod_name__.lower())) for x
             in module_dict.values()],
            key=lambda x: x.text
        )

    modules_per_page = 15
    max_pages = ceil(len(modules) / modules_per_page)
    
    if page_n < 0:
        page_n = 0
    elif page_n >= max_pages:
        page_n = max_pages - 1
        
    start_idx = page_n * modules_per_page
    end_idx = start_idx + modules_per_page
    page_modules = modules[start_idx:end_idx]
    
    pairs = [
        page_modules[i * 3:(i + 1) * 3]
        for i in range((len(page_modules) + 3 - 1) // 3)
    ]
    
    nav_row = []
    if page_n > 0:
        if not chat:
            nav_row.append(InlineKeyboardButton("◀ Prev", callback_data=f"{prefix}_prev({page_n})"))
        else:
            nav_row.append(InlineKeyboardButton("◀ Prev", callback_data=f"{prefix}_prev({chat},{page_n})"))
            
    if page_n < max_pages - 1:
        if not chat:
            nav_row.append(InlineKeyboardButton("Next ▶", callback_data=f"{prefix}_next({page_n})"))
        else:
            nav_row.append(InlineKeyboardButton("Next ▶", callback_data=f"{prefix}_next({chat},{page_n})"))
            
    if nav_row:
        pairs.append(nav_row)
        
    pairs.append([
        InlineKeyboardButton("Back", callback_data="cutiepii_back"),
        InlineKeyboardButton("Language", callback_data="change_lang")
    ])
    return pairs

async def send_to_list(
    bot: Bot, send_to: list, message: str, markdown=False, html=False
) -> None:
    if html and markdown:
        raise Exception("Can only send with either markdown or HTML!")
    for user_id in set(send_to):
        with contextlib.suppress(TelegramError):
            if markdown:
                await bot.send_message(user_id, message, parse_mode=ParseMode.MARKDOWN)
            elif html:
                await bot.send_message(user_id, message, parse_mode=ParseMode.HTML)
            else:
                await bot.send_message(user_id, message)


def build_keyboard(buttons):
    keyb = []
    for btn in buttons:
        if btn.same_line and keyb:
            keyb[-1].append(InlineKeyboardButton(btn.name, url=btn.url))
        else:
            keyb.append([InlineKeyboardButton(btn.name, url=btn.url)])

    return keyb


def revert_buttons(buttons):
    return "".join(
        "\n[{}](buttonurl://{}:same)".format(btn.name, btn.url)
        if btn.same_line
        else "\n[{}](buttonurl://{})".format(btn.name, btn.url)
        for btn in buttons
    )


def build_keyboard_parser(bot, chat_id, buttons):
    keyb = []
    for btn in buttons:
        if btn.url == "{rules}":
            btn.url = "https://t.me/{}?start={}".format(bot.username, chat_id)
        if btn.same_line and keyb:
            keyb[-1].append(InlineKeyboardButton(btn.name, url=btn.url))
        else:
            keyb.append([InlineKeyboardButton(btn.name, url=btn.url)])

    return keyb


def is_module_loaded(name):
    return name not in NO_LOAD

   
def upload_text(data: str) -> typing.Optional[str]:
    passphrase = Random.get_random_bytes(32)
    salt = Random.get_random_bytes(8)
    key = PBKDF2(passphrase, salt, 32, 100000, hmac_hash_module=Hash.SHA256)
    compress = zlib.compressobj(wbits=-15)
    paste_blob = compress.compress(json.dumps({'paste': data}, separators=(',', ':')).encode()) + compress.flush()
    cipher = AES.new(key, AES.MODE_GCM)
    paste_meta = [[base64.b64encode(cipher.nonce).decode(), base64.b64encode(salt).decode(), 100000, 256, 128, 'aes', 'gcm', 'zlib'], 'syntaxhighlighting', 0, 0]
    cipher.update(json.dumps(paste_meta, separators=(',', ':')).encode())
    ct, tag = cipher.encrypt_and_digest(paste_blob)
    resp = requests.post('https://bin.nixnet.services', headers={'X-Requested-With': 'JSONHttpRequest'}, data=json.dumps({'v': 2, 'adata': paste_meta, 'ct': base64.b64encode(ct + tag).decode(), 'meta': {'expire': '1week'}}, separators=(',', ':')))
    data = resp.json()
    url = list(urlparse(urljoin('https://bin.nixnet.services', data['url'])))
    url[5] = base58.b58encode(passphrase).decode()
    return urlunparse(url)
