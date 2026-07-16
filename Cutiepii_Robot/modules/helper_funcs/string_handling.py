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
import re
import time
import html
from typing import Dict, List

import bleach
import markdown2
import emoji

from telegram import MessageEntity
from telegram import InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

# NOTE: the url \ escape may cause double escapes
# match * (bold) (don't escape if in url)
# match _ (italics) (don't escape if in url)
# match ` (code)
# match []() (markdown link)
# else, escape *, _, `, and [
MATCH_MD = re.compile(
    r"\*(.*?)\*|"
    r"_(.*?)_|"
    r"`(.*?)`|"
    r"(?<!\\)(\[.*?\])(\(.*?\))|"
    r"(?P<esc>[*_`\[])"
)

MATCH_MD_v2 = re.compile(
    r"(?<!\\)(\[.*?\])(\(.*?\))|"
    r"(?P<esc>[\_\-~`>#=!\|\*\[\]\(\)\+\{\}\.\\])" # https://core.telegram.org/bots/api#markdownv2-style
)

# regex to find []() links -> hyperlinks/buttons
LINK_REGEX = re.compile(r"(?<!\\)\[.+?\]\((.*?)\)")
LINK_REGEX_v2 = re.compile(r"(?<!\\)\[(.+?)\]\((.*?)\)")
BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)\]\(buttonurl:(?:/{0,2})(.+?)(:same)?\))")


def _selective_escape_v2(to_parse: str) -> str:
    """
    Escape all invalid markdown
    :param to_parse: text to escape
    :return: valid markdown string
    """
    offset = 0  # offset to be used as adding a \ character causes the string to shift
    for match in MATCH_MD_v2.finditer(to_parse):
        if match.group("esc"):
            ent_start = match.start()
            to_parse = (
                to_parse[: ent_start + offset] + "\\" + to_parse[ent_start + offset :]
            )
            offset += 1
    return to_parse


def _calc_emoji_offset(to_calc) -> int:
    # Get all emoji in text.
    # Emoji 2.x compatibility
    try:
        # emoji >= 2.0
        import emoji as emoji_lib
        emoticons = [e['emoji'] for e in emoji_lib.emoji_list(to_calc)]
    except (AttributeError, ImportError):
        # emoji < 2.0 fallback
        emoticons = [e.group(0) for e in emoji.get_emoji_regexp().finditer(to_calc)]
    # Check the utf16 length of the emoji to determine the offset it caused.
    # Normal, 1 character emoji don't affect; hence sub 1.
    # special, eg with two emoji characters (eg face, and skin col) will have length 2, so by subbing one we
    # know we'll get one extra offset
    return sum(len(emoji_str.encode("utf-16-le")) // 2 - 1 for emoji_str in emoticons)


def markdown_parser_v2(
    txt: str, entities: Dict[MessageEntity, str] = None, offset: int = 0
) -> str:
    """
    Parse a string, escaping all invalid markdown entities.

    Escapes URL's so as to avoid URL mangling.
    Re-adds any telegram code entities obtained from the entities object.

    :param txt: text to parse
    :param entities: dict of message entities in text
    :param offset: message offset - command and notename length
    :return: valid markdown string
    """
    if not entities:
        entities = {}
    if not txt:
        return ""

    prev = 0
    res = ""
    # Loop over all message entities, and:
    # reinsert code
    # escape free-standing urls
    for ent, ent_text in entities.items():
        if ent.offset < -offset:
            continue

        start = ent.offset + offset  # start of entity
        end = ent.offset + offset + ent.length - 1  # end of entity

        # we only care about code, url, text links
        if ent.type in ("code", "url", "text_link", "bold", "italic", "underline", "strikethrough", "spoiler"):
            # count emoji to switch counter
            count = _calc_emoji_offset(txt[:start])
            start -= count
            end -= count

            match ent.type:
                case "url":
                    for match in LINK_REGEX_v2.finditer(txt):
                        if match.start(2) <= start and end <= match.end(2) and not match.group(2).startswith("buttonurl"):
                            mt = match.group(1).center(count)
                            res += _selective_escape_v2(txt[prev:start - (len(mt) + 3)] + '[{}]({})'.format(_selective_escape_v2(match.group(1)), match.group(2)))
                            end +=1
                            break
                        continue
                    else:
                        if txt[start - 10:start] or txt[start - 12:start] in ['buttonurl:', 'buttonurl://']:
                            continue
                        # TODO: investigate possible offset bug when lots of emoji are present
                        res += _selective_escape_v2(txt[prev:start] or "") + escape_markdown(
                            ent_text, version=2
                        )

                # code handling
                case "code":
                    res += _selective_escape_v2(txt[prev:start]) + "`" + ent_text + "`"

                # bold handling
                case "bold":
                    res += _selective_escape_v2(txt[prev:start]) + "*" + ent_text + "*"

                # italic handling
                case "italic":
                    res += _selective_escape_v2(txt[prev:start]) + "_" + ent_text + "_"

                # underline handling
                case "underline":
                    res += _selective_escape_v2(txt[prev:start]) + "__" + ent_text + "__"

                # strikethrough handling
                case "strikethrough":
                    res += _selective_escape_v2(txt[prev:start]) + "~" + ent_text + "~"

                # spoiler handling
                case "spoiler":
                    res += _selective_escape_v2(txt[prev:start]) + "||" + ent_text + "||"

                # handle markdown/html links
                case "text_link":
                    res += _selective_escape_v2(txt[prev:start]) + "[{}]({})".format(
                        _selective_escape_v2(ent_text), ent.url
                    )

            end += 1

        # anything else
        else:
            continue

        prev = end

    res += _selective_escape_v2(txt[prev:])  # add the rest of the text
    return res


def button_markdown_parser_v2(
    txt: str, entities: Dict[MessageEntity, str] = None, offset: int = 0
) -> tuple("str, List"):
    markdown_note = markdown_parser_v2(txt, entities, offset)
    prev = 0
    note_data = ""
    buttons = []
    for match in BTN_URL_REGEX.finditer(markdown_note):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and markdown_note[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            # create a thruple with button label, url, and newline status
            buttons.append((match.group(2), match.group(3), bool(match.group(4))))
            note_data += markdown_note[prev : match.start(1)]
            prev = match.end(1)
        # if odd, escaped -> move along
        else:
            note_data += markdown_note[prev:to_check]
            prev = match.start(1) - 1
    note_data += markdown_note[prev:]

    return note_data, buttons

def reply_button_parser_v2(
    txt: str, entities: Dict[MessageEntity, str] = None, offset: int = 0, replymarkup: InlineKeyboardMarkup = None) -> tuple("str, List"):
    markdown_note = markdown_parser_v2(txt, entities, offset)
    buttons = []
    prev = 0
    note_data = ""
    if replymarkup:
        for btn in replymarkup.inline_keyboard:
            buttons.append((btn[0].text, btn[0].url, False))
            if len(btn) >= 2:
                for a in btn[1:]:
                    buttons.append((a.text, a.url, True))
                    return note_data, buttons
    for match in BTN_URL_REGEX.finditer(markdown_note):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and markdown_note[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            # create a thruple with button label, url, and newline status
            buttons.append((match.group(2), match.group(3), bool(match.group(4))))
            note_data += markdown_note[prev : match.start(1)]
            prev = match.end(1)
        # if odd, escaped -> move along
        else:
            note_data += markdown_note[prev:to_check]
            prev = match.start(1) - 1
    note_data += markdown_note[prev:]
    return note_data, buttons

def _selective_escape(to_parse: str) -> str:
    """
    Escape all invalid markdown
    :param to_parse: text to escape
    :return: valid markdown string
    """
    offset = 0  # offset to be used as adding a \ character causes the string to shift
    for match in MATCH_MD.finditer(to_parse):
        if match.group("esc"):
            ent_start = match.start()
            to_parse = (
                to_parse[: ent_start + offset] + "\\" + to_parse[ent_start + offset :]
            )
            offset += 1
    return to_parse

def markdown_parser(
    txt: str, entities: Dict[MessageEntity, str] = None, offset: int = 0
) -> str:
    """
    Parse a string, escaping all invalid markdown entities.
    Escapes URL's so as to avoid URL mangling.
    Re-adds any telegram code entities obtained from the entities object.
    :param txt: text to parse
    :param entities: dict of message entities in text
    :param offset: message offset - command and notename length
    :return: valid markdown string
    """
    if not entities:
        entities = {}
    if not txt:
        return ""

    prev = 0
    res = ""
    # Loop over all message entities, and:
    # reinsert code
    # escape free-standing urls
    for ent, ent_text in entities.items():
        if ent.offset < -offset:
            continue

        start = ent.offset + offset  # start of entity
        end = ent.offset + offset + ent.length - 1  # end of entity

        # we only care about code, url, text links, bold, italic, underline, strikethrough, spoiler
        if ent.type in ("code", "url", "text_link", "bold", "italic", "underline", "strikethrough", "spoiler"):
            # count emoji to switch counter
            count = _calc_emoji_offset(txt[:start])
            start -= count
            end -= count

            # URL handling -> do not escape if in [](), escape otherwise.
            if ent.type == "url":
                if any(
                    match.start(1) <= start and end <= match.end(1)
                    for match in LINK_REGEX.finditer(txt)
                ):
                    continue
                # else, check the escapes between the prev and last and forcefully escape the url to avoid mangling
                else:
                    # TODO: investigate possible offset bug when lots of emoji are present
                    res += _selective_escape(txt[prev:start] or "") + escape_markdown(
                        ent_text
                    )

            # code handling
            elif ent.type == "code":
                res += _selective_escape(txt[prev:start]) + "`" + ent_text + "`"

            # bold handling
            elif ent.type == "bold":
                res += _selective_escape(txt[prev:start]) + "*" + ent_text + "*"

            # italic handling
            elif ent.type == "italic":
                res += _selective_escape(txt[prev:start]) + "_" + ent_text + "_"

            # underline handling
            elif ent.type == "underline":
                res += _selective_escape(txt[prev:start]) + "<u>" + ent_text + "</u>"

            # strikethrough handling
            elif ent.type == "strikethrough":
                res += _selective_escape(txt[prev:start]) + "~" + ent_text + "~"

            # spoiler handling
            elif ent.type == "spoiler":
                res += _selective_escape(txt[prev:start]) + "||" + ent_text + "||"

            # handle markdown/html links
            elif ent.type == "text_link":
                res += _selective_escape(txt[prev:start]) + "[{}]({})".format(
                    ent_text, ent.url
                )

            end += 1

        # anything else
        else:
            continue

        prev = end

    res += _selective_escape(txt[prev:])  # add the rest of the text
    return res

def button_markdown_parser(
    txt: str, entities: Dict[MessageEntity, str] = None, offset: int = 0
) -> tuple("str, List"):
    markdown_note = markdown_parser(txt, entities, offset)
    prev = 0
    note_data = ""
    buttons = []
    for match in BTN_URL_REGEX.finditer(markdown_note):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and markdown_note[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            # create a thruple with button label, url, and newline status
            buttons.append((match.group(2), match.group(3), bool(match.group(4))))
            note_data += markdown_note[prev : match.start(1)]
            prev = match.end(1)
        # if odd, escaped -> move along
        else:
            note_data += markdown_note[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += markdown_note[prev:]

    return note_data, buttons

def escape_invalid_curly_brackets(text: str, valids: List[str]) -> str:
    new_text = ""
    idx = 0
    while idx < len(text):
        if text[idx] == "{":
            if idx + 1 < len(text) and text[idx + 1] == "{":
                idx += 2
                new_text += "{{{{"
                continue
            else:
                success = False
                for v in valids:
                    if text[idx:].startswith("{" + v + "}"):
                        success = True
                        break
                if success:
                    new_text += text[idx : idx + len(v) + 2]
                    idx += len(v) + 2
                    continue
                else:
                    new_text += "{{"

        elif text[idx] == "}":
            if idx + 1 < len(text) and text[idx + 1] == "}":
                idx += 2
                new_text += "}}}}"
                continue
            else:
                new_text += "}}"

        else:
            new_text += text[idx]
        idx += 1

    return new_text


SMART_OPEN = "“"
SMART_CLOSE = "”"
START_CHAR = ("'", '"', SMART_OPEN)


def split_quotes(text: str) -> List:
    if any(text.startswith(char) for char in START_CHAR):
        counter = 1  # ignore first char -> is some kind of quote
        while counter < len(text):
            if text[counter] == "\\":
                counter += 1
            elif text[counter] == text[0] or (
                text[0] == SMART_OPEN and text[counter] == SMART_CLOSE
            ):
                break
            counter += 1
        else:
            return text.split(None, 1)

        # 1 to avoid starting quote, and counter is exclusive so avoids ending
        key = remove_escapes(text[1:counter].strip())
        # index will be in range, or `else` would have been executed and returned
        rest = text[counter + 1 :].strip()
        if not key:
            key = text[0] + text[0]
        return list(filter(None, [key, rest]))
    else:
        return text.split(None, 1)


def remove_escapes(text: str) -> str:
    counter = 0
    res = ""
    is_escaped = False
    while counter < len(text):
        if is_escaped:
            res += text[counter]
            is_escaped = False
        elif text[counter] == "\\":
            is_escaped = True
        else:
            res += text[counter]
        counter += 1
    return res


def escape_chars(text: str, to_escape: List[str]) -> str:
    to_escape.append("\\")
    new_text = ""
    for x in text:
        if x in to_escape:
            new_text += "\\"
        new_text += x
    return new_text

async def extract_time_seconds(message, time_val):
    if any(time_val.endswith(unit) for unit in ("m", "h", "d", "w", "s")):
        unit = time_val[-1]
        time_num = time_val[:-1]  # type: str
        if not time_num.isdigit():
            await message.reply_text("<b>Invalid Argument</b>\nInvalid time duration amount specified.", parse_mode=ParseMode.HTML)

async def extract_time(message, time_val):
    if any(time_val.endswith(unit) for unit in ("m", "h", "d")):
        unit = time_val[-1]
        time_num = time_val[:-1]  # type: str
        if not time_num.isdigit():
            await message.reply_text("<b>Invalid Argument</b>\nInvalid time duration amount specified.", parse_mode=ParseMode.HTML)
            return ""

        if unit == "m":
            bantime = int(time.time()) + int(time_num) * 60
        elif unit == "h":
            bantime = int(time.time()) + int(time_num) * 60 * 60
        elif unit == "d":
            bantime = int(time.time()) + int(time_num) * 24 * 60 * 60
        else:
            # how even...?
            return ""
        return bantime
    else:
        await message.reply_text(
            "<b>Invalid Time Format</b>\nExpected units: <code>m</code> (minutes), <code>h</code> (hours), or <code>d</code> (days). Received: <code>{}</code>".format(
                html.escape(time_val[-1])
            ),
            parse_mode=ParseMode.HTML
        )
        return ""


def markdown_to_html(text):
    text = text.replace("*", "**")
    text = text.replace("`", "```")
    text = text.replace("~", "~~")
    
    import re
    spoiler_re = re.compile(r'\|\|(.*?[^\s].*?)(\s*?)\|\|', re.DOTALL)
    text = spoiler_re.sub(r'<span class="tg-spoiler">\1</span>\2', text)
    
    _html = markdown2.markdown(text, extras=["strike", "underline"])
    return bleach.clean(
        _html,
        tags=["strong", "em", "a", "code", "pre", "strike", "u", "span"],
        attributes={"span": ["class"], "a": ["href"]},
        strip=True
    )[:-1]


def telegramify(text: str) -> str:
    """
    Converts standard Markdown to Telegram MarkdownV2 format with proper escaping.
    """
    if not text:
        return ""
    import telegramify_markdown
    return telegramify_markdown.markdownify(text)


def telegramify_to_entities(text: str):
    """
    Converts standard Markdown into plain text and a list of Telegram MessageEntity objects.
    Useful for passing directly to message.reply_text(text, entities=entities) without escaping.
    """
    if not text:
        return "", []
    import telegramify_markdown
    res = telegramify_markdown.convert(text)
    # convert returns (text, list of entities)
    if isinstance(res, tuple) and len(res) == 2:
        return res[0], res[1]
    return text, []
