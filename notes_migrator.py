import re
import threading
from enum import IntEnum, unique
from typing import Optional, Union

from telegram import InlineKeyboardMarkup
import Cutiepii_Robot

from Cutiepii_Robot import LOGGER

from Cutiepii_Robot.modules.sql.notes_sql import SESSION, Notes

BTN_LINK_REGEX = re.compile(
    r"(?<!\\)\[(.+?)\]\(((?!b(?:utto|t)nurl:).+?)\)|(?m)^(\n?\[(.+?)\]\(b(?:utto|t)nurl:(?:/*)?(.+?)(:same)?\))$"
)


@unique
class Types(IntEnum):
    TEXT = 0
    BUTTON_TEXT = 1
    STICKER = 2
    DOCUMENT = 3
    PHOTO = 4
    AUDIO = 5
    VOICE = 6
    VIDEO = 7
    VIDEO_NOTE = 8


def replacer(text: str) -> str:
    text = text.replace("\\{first\\}", '{first}').replace("\\{last\\}", '{last}').replace("\\{fullname\\}", '{fullname}') \
     .replace("\\{username\\}", '{username}').replace("\\{id\\}", '{id}').replace("\\{chatname\\}", '{chatname}') \
     .replace("\\{mention\\}", '{mention}').replace("\\{user\\}", '{user}').replace("\\{admin\\}", '{admin}') \
     .replace("\\{preview\\}", '{preview}').replace("\\{protect\\}", '{protect}')

    text = text.replace("\*", "*").replace("\[", "[").replace("\]", "]").replace("\(", "(").replace("\)", ")") \
     .replace("\+", "+").replace("\|", "|").replace("\{", "{").replace("\}", "}").replace("\.", ".").replace("\-", "-") \
     .replace("\'", "'").replace("\_", "_").replace("\~", "~").replace("\`", "`").replace("\>", ">").replace("\#", "#") \
     .replace("\-", "-").replace("\=", "=").replace("\!", "!").replace("\\\\", "\\")

    return text


def parser(
    txt: str,
    reply_markup: InlineKeyboardMarkup = None
) -> tuple[str, Union[str, list[Optional[tuple[str, Optional[str], bool]]]]]:
    buttons: Union[str, list[Optional[tuple[str, Optional[str], bool]]]] = []
    prev = 0
    note_data = ""
    if reply_markup:
        for btn in reply_markup.inline_keyboard:
            buttons.append((btn[0].text, btn[0].url, False))
            if len(btn) >= 2:
                buttons.extend((a.text, a.url, True) for a in btn[1:])

    if txt:
        for match in BTN_LINK_REGEX.finditer(txt):
            if match.group(1):
                note_data += txt[prev:match.start(1) - 1]
                note_data += f"<a href=\"{match.group(2)}\">{match.group(1)}</a>"
                prev = match.end(2) + 1
            else:
                buttons.append(
                    (match.group(4), match.group(5), bool(match.group(6))))
                note_data += txt[prev:match.start(3)].rstrip()
                prev = match.end(3)
        note_data += txt[prev:]

    final_text = Md2HTML(note_data)

    return final_text, buttons


def Md2HTML(text: str) -> str:
    _whitespace_re = re.compile(
        r"(?<!<)(?P<t_b><[^></]*?>)(?P<str>[^<>](?:.*?\s*?)*?(?P<ws>\s*?))(?P<t_e></[^<>]*?>)(?!>)"
    )
    _pre_re = re.compile(r'`{3}(.*?[^\s].*?)(\s*?)`{3}', re.DOTALL)
    _code_re = re.compile(r'`(.*?[^\s].*?)(\s*?)`', re.DOTALL)
    _bold_re = re.compile(r'\*(.*?[^\s].*?)(\s*?)\*', re.DOTALL)
    _underline_re = re.compile(r'(?<!_)__(.*?[^\s].*?)(\s*?)__(?!_)',
                               re.DOTALL)
    _italic_re = re.compile(r'_(.*?[^\s].*?)(\s*?)_', re.DOTALL)
    _strike_re = re.compile(r'~(.*?[^\s].*?)(\s*?)~', re.DOTALL)
    _spoiler_re = re.compile(r'\|\|(.*?[^\s].*?)(\s*?)\|\|', re.DOTALL)

    def repl_whitespace(match):
        return f"{match.group('t_b')}{match.group('str')}{match.group('t_e')}{match.group('ws')}"

    def _pre_repl(match):
        return f'<pre>{match[1]}</pre>{match[2]}'

    def _code_repl(match):
        return f'<code>{match[1]}</code>{match[2]}'

    def _bold_repl(match):
        return f'<b>{match[1]}</b>{match[2]}'

    def _underline_repl(match):
        return f'<u>{match[1]}</u>{match[2]}'

    def _italic_repl(match):
        return f'<i>{match[1]}</i>{match[2]}'

    def _strike_repl(match):
        return f'<s>{match[1]}</s>{match[2]}'

    def _spoiler_repl(match):
        return f'<span class="tg-spoiler">{match[1]}</span>{match[2]}'

    text = _whitespace_re.sub(repl_whitespace, text)
    text = _pre_re.sub(_pre_repl, text)
    text = _code_re.sub(_code_repl, text)
    text = _bold_re.sub(_bold_repl, text)
    text = _underline_re.sub(_underline_repl, text)
    text = _italic_re.sub(_italic_repl, text)
    text = _strike_re.sub(_strike_repl, text)
    text = _spoiler_re.sub(_spoiler_repl, text)

    return text


def update_note(text: str) -> str:
    return parser(replacer(text))[0]


def migrate_notes():
    LOGGER.debug("starting notes migration")
    with threading.RLock():

        all_notes = SESSION.query(Notes).all()

        for note in all_notes:
            note.value = update_note(note.value)

        SESSION.commit()

    LOGGER.debug("finished notes migration")
