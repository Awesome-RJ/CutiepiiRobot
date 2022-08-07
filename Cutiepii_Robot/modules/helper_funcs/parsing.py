import re
from enum import IntEnum, unique
from typing import Optional, Union
from html import escape

from telegram import InlineKeyboardButton, Message, Update
from telegram import InlineKeyboardMarkup
from telegram.helpers import mention_html

from Cutiepii_Robot.modules.helper_funcs.admin_status import user_is_admin
from Cutiepii_Robot.modules.sql.notes_sql import Buttons
from Cutiepii_Robot import CUTIEPII_PTB

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


ENUM_FUNC_MAP = {
    Types.TEXT.value: CUTIEPII_PTB.bot.send_message,
    Types.BUTTON_TEXT.value: CUTIEPII_PTB.bot.send_message,
    Types.STICKER.value: CUTIEPII_PTB.bot.send_sticker,
    Types.DOCUMENT.value: CUTIEPII_PTB.bot.send_document,
    Types.PHOTO.value: CUTIEPII_PTB.bot.send_photo,
    Types.AUDIO.value: CUTIEPII_PTB.bot.send_audio,
    Types.VOICE.value: CUTIEPII_PTB.bot.send_voice,
    Types.VIDEO.value: CUTIEPII_PTB.bot.send_video,
}

VALID_FORMATTERS = [
    "first",
    "last",
    "fullname",
    "username",
    "id",
    "chatname",
    "mention",
    "user",
    "admin",
    "preview",
    "protect",
]


def get_data(
    msg: Message,
    welcome: bool = False
) -> tuple[str, str, Types, Optional[str], Union[str, list[Optional[tuple[
        str, Optional[str], bool]]]]]:
    data_type: Types = Types.TEXT
    content: Optional[str] = None
    text: str = ""
    raw_text: str = msg.text_html or msg.caption_html
    args: list[str] = raw_text.split(None, 1 if welcome else 2)
    note_name: str = "" if welcome else args[1]

    buttons: Union[str, list[Optional[tuple[str, Optional[str], bool]]]] = []
    # determine what the contents of the filter are - text, image, sticker, etc
    if len(args) >= 3:
        text, buttons = parser(args[2])

    elif len(args) >= 2 and welcome:
        text, buttons = parser(args[1])

        data_type = Types.BUTTON_TEXT if buttons else Types.TEXT

    elif rep := msg.reply_to_message:
        msgtext = msg.reply_to_message.text_html or msg.reply_to_message.caption_html
        if (len(args) >= (1 if welcome else 2)
                and msg.reply_to_message.text_html):  # not caption, text
            text, buttons = parser(
                msgtext, reply_markup=msg.reply_to_message.reply_markup)
            data_type = Types.BUTTON_TEXT if buttons else Types.TEXT
        elif rep.sticker:
            content = msg.reply_to_message.sticker.file_id
            data_type = Types.STICKER

        elif rep.document:
            content = msg.reply_to_message.document.file_id
            text, buttons = parser(msgtext)
            data_type = Types.DOCUMENT

        elif rep.photo:
            content = msg.reply_to_message.photo[
                -1].file_id  # last elem = best quality
            text, buttons = parser(msgtext)
            data_type = Types.PHOTO

        elif rep.audio:
            content = msg.reply_to_message.audio.file_id
            text, buttons = parser(msgtext)
            data_type = Types.AUDIO

        elif rep.voice:
            content = msg.reply_to_message.voice.file_id
            text, buttons = parser(msgtext)
            data_type = Types.VOICE

        elif rep.video:
            content = msg.reply_to_message.video.file_id
            text, buttons = parser(msgtext)
            data_type = Types.VIDEO

    if buttons and not text:
        text = note_name

    return note_name, text, data_type, content, buttons


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
            if match[1]:
                note_data += txt[prev:match.start(1) - 1]
                note_data += f"<a href=\"{match[2]}\">{match[1]}</a>"
                prev = match.end(2) + 1
            else:
                buttons.append((match[4], match[5], bool(match[6])))
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


def revertMd2HTML(text: str, buttons: Buttons) -> str:
    _pre_re = re.compile(r'<pre>(.*?[^\s].*?)(\s*?)</pre>', re.DOTALL)
    _code_re = re.compile(r'<code>(.*?[^\s].*?)(\s*?)</code>')
    _bold_re = re.compile(r'<b>(.*?[^\s].*?)(\s*?)</b>')
    _underline_re = re.compile(r'<u>(.*?[^\s].*?)(\s*?)</u>')
    _italic_re = re.compile(r'<i>(.*?[^\s].*?)(\s*?)</i>')
    _strike_re = re.compile(r'<s>(.*?[^\s].*?)(\s*?)</s>')
    _spoiler_re = re.compile(
        r'<span class="tg-spoiler">(.*?[^\s].*?)(\s*?)</span>')
    _link_re = re.compile(
        r'<a href=(?:"(.*?[^\s].*?)"|\'(.*?[^\s].*?)\')>(.*?[^\s].*?)</a>')

    def _pre_repl(match):
        return f'```{match[1]}```{match[2]}'

    def _code_repl(match):
        return f'`{match[1]}`{match[2]}'

    def _bold_repl(match):
        return f'*{match[1]}*{match[2]}'

    def _underline_repl(match):
        return f'__{match[1]}__{match[2]}'

    def _italic_repl(match):
        return f'_{match[1]}_{match[2]}'

    def _strike_repl(match):
        return f'~{match[1]}~{match[2]}'

    def _spoiler_repl(match):
        return f'||{match[1]}||{match[2]}'

    def _link_repl(match):
        return f"[{match[2]}]({match[1]})"

    def _buttons_repl(txt, btns):
        return txt + "".join(
            f"\n[{i.name}](buttonurl://{i.url}{':same' if i.same_line else ''})"
            for i in btns)

    text = _pre_re.sub(_pre_repl, text)
    text = _code_re.sub(_code_repl, text)
    text = _bold_re.sub(_bold_repl, text)
    text = _underline_re.sub(_underline_repl, text)
    text = _italic_re.sub(_italic_repl, text)
    text = _strike_re.sub(_strike_repl, text)
    text = _spoiler_re.sub(_spoiler_repl, text)
    text = _link_re.sub(_link_repl, text)

    if buttons:
        text = _buttons_repl(text, buttons)

    return text


def build_keyboard_from_list(buttons) -> list[list[InlineKeyboardButton]]:
    kb = []
    for btn in buttons:
        if btn[2] and kb:
            kb[-1].append(InlineKeyboardButton(btn[0], url=btn[1]))
        else:
            kb.append([InlineKeyboardButton(btn[0], url=btn[1])])

    return kb


def parse_filler(update: Update, user_id: int,
                 text: str) -> (bool, bool, bool, str):
    message = update.effective_message

    if "{admin}" in text and user_is_admin(update, user_id):
        return True, False, False, ""
    if "{user}" in text and not user_is_admin(update, user_id):
        return True, False, False, ""
    preview = "{preview}" not in text
    protect = "{protect}" in text
    text = text.format(
        first=escape(message.from_user.first_name),
        last=escape(
            message.from_user.last_name or message.from_user.first_name, ),
        fullname=escape(
            " ".join([
                message.from_user.first_name,
                message.from_user.last_name or "",
            ]), ),
        username=f'@{message.from_user.username}'
        if message.from_user.username else mention_html(
            message.from_user.id,
            message.from_user.first_name,
        ),
        mention=mention_html(
            message.from_user.id,
            message.from_user.first_name,
        ),
        chatname=escape(
            message.chat.title if message.chat.type != "private" else
            message.from_user.first_name, ),
        id=message.from_user.id,
        user="",
        admin="",
        preview="",
        protect="",
    )

    return (
        False,
        preview,
        protect,
    )
