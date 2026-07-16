from enum import IntEnum, unique

from Cutiepii_Robot.modules.helper_funcs.string_handling import button_markdown_parser, button_markdown_parser_v2, reply_button_parser_v2
from telegram import Message


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

async def get_note_type(msg: Message):  # sourcery no-metrics
    data_type = None
    content = None
    text = ""
    raw_text = msg.text or msg.caption
    args = raw_text.split(None, 2)  # use python's maxsplit to separate cmd and args
    note_name = args[1]

    buttons = []
    # determine what the contents of the filter are - text, image, sticker, etc
    if len(args) >= 3:
        offset = len(args[2]) - len(
            raw_text
        )  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser_v2(
            args[2],
            entities=msg.parse_entities() or msg.parse_caption_entities(),
            offset=offset,
        )
        if not text: text = f"Click the button below to view '{note_name}'"
        data_type = Types.BUTTON_TEXT if buttons else Types.TEXT
    elif msg.reply_to_message:
        entities = msg.reply_to_message.parse_entities()
        msgtext = msg.reply_to_message.text or msg.reply_to_message.caption
        if len(args) >= 2 and msg.reply_to_message.text:  # not caption, text
            text, buttons = reply_button_parser_v2(msgtext, entities=entities, replymarkup=msg.reply_to_message.reply_markup)
            data_type = Types.BUTTON_TEXT if buttons else Types.TEXT
        elif msg.reply_to_message.sticker:
            content = msg.reply_to_message.sticker.file_id
            data_type = Types.STICKER

        elif msg.reply_to_message.document:
            content = msg.reply_to_message.document.file_id
            text, buttons = button_markdown_parser_v2(msgtext, entities=entities)
            data_type = Types.DOCUMENT

        elif msg.reply_to_message.photo:
            content = msg.reply_to_message.photo[-1].file_id  # last elem = best quality
            text, buttons = button_markdown_parser_v2(msgtext, entities=entities)
            data_type = Types.PHOTO

        elif msg.reply_to_message.audio:
            content = msg.reply_to_message.audio.file_id
            text, buttons = button_markdown_parser_v2(msgtext, entities=entities)
            data_type = Types.AUDIO

        elif msg.reply_to_message.voice:
            content = msg.reply_to_message.voice.file_id
            text, buttons = button_markdown_parser_v2(msgtext, entities=entities)
            data_type = Types.VOICE

        elif msg.reply_to_message.video:
            content = msg.reply_to_message.video.file_id
            text, buttons = button_markdown_parser_v2(msgtext, entities=entities)
            data_type = Types.VIDEO

    return note_name, text, data_type, content, buttons


# note: add own args?
async def get_welcome_type(msg: Message):  # sourcery no-metrics
    data_type = None
    content = None
    text = ""
    raw_text = msg.text or msg.caption
    args = raw_text.split(None, 1) if raw_text else []

    buttons = []
    argumen = None
    # determine what the contents of the welcome message are - text, image, sticker, etc
    if msg.reply_to_message:
        argumen = msg.reply_to_message.caption or msg.reply_to_message.text or ""
        offset = 0  # offset is no need since target was in reply
        entities = msg.reply_to_message.parse_entities()
    elif args and len(args) > 1:
        argumen = args[1]
        offset = len(argumen) - len(raw_text)  # set correct offset relative to command
        entities = msg.parse_entities() or msg.parse_caption_entities()

    # Determine media source (from message itself or reply_to_message)
    media_source = msg.reply_to_message if msg.reply_to_message else msg

    if argumen:
        text, buttons = button_markdown_parser(
            argumen,
            entities=entities,
            offset=offset,
        )
        # Determine media type if present
        if media_source.sticker:
            content = media_source.sticker.file_id
            data_type = Types.STICKER
        elif media_source.animation:
            content = media_source.animation.file_id
            data_type = Types.DOCUMENT
        elif media_source.document:
            content = media_source.document.file_id
            data_type = Types.DOCUMENT
        elif media_source.photo:
            content = media_source.photo[-1].file_id
            data_type = Types.PHOTO
        elif media_source.audio:
            content = media_source.audio.file_id
            data_type = Types.AUDIO
        elif media_source.voice:
            content = media_source.voice.file_id
            data_type = Types.VOICE
        elif media_source.video:
            content = media_source.video.file_id
            data_type = Types.VIDEO
        elif media_source.video_note:
            content = media_source.video_note.file_id
            data_type = Types.VIDEO_NOTE
        else:
            data_type = Types.BUTTON_TEXT if buttons else Types.TEXT
            
    elif msg.reply_to_message:
        # If there is no argumen (e.g. empty command replying to a media)
        entities = msg.reply_to_message.parse_entities() or msg.reply_to_message.parse_caption_entities()
        msgtext = msg.reply_to_message.text or msg.reply_to_message.caption or ""
        text, buttons = button_markdown_parser(msgtext, entities=entities)
        
        if msg.reply_to_message.sticker:
            content = msg.reply_to_message.sticker.file_id
            data_type = Types.STICKER
        elif msg.reply_to_message.animation:
            content = msg.reply_to_message.animation.file_id
            data_type = Types.DOCUMENT
        elif msg.reply_to_message.document:
            content = msg.reply_to_message.document.file_id
            data_type = Types.DOCUMENT
        elif msg.reply_to_message.photo:
            content = msg.reply_to_message.photo[-1].file_id
            data_type = Types.PHOTO
        elif msg.reply_to_message.audio:
            content = msg.reply_to_message.audio.file_id
            data_type = Types.AUDIO
        elif msg.reply_to_message.voice:
            content = msg.reply_to_message.voice.file_id
            data_type = Types.VOICE
        elif msg.reply_to_message.video:
            content = msg.reply_to_message.video.file_id
            data_type = Types.VIDEO
        elif msg.reply_to_message.video_note:
            content = msg.reply_to_message.video_note.file_id
            data_type = Types.VIDEO_NOTE
        else:
            data_type = Types.BUTTON_TEXT if buttons else Types.TEXT

    return text, data_type, content, buttons


def get_filter_type(msg: Message):

    if not msg.reply_to_message and msg.text and len(msg.text.split()) >= 3:
        content = None
        text = msg.text.split(None, 2)[2]
        data_type = Types.TEXT

    elif (
        msg.reply_to_message
        and msg.reply_to_message.text
        and len(msg.text.split()) >= 2
    ):
        content = None
        text = msg.reply_to_message.text
        data_type = Types.TEXT

    elif msg.reply_to_message and msg.reply_to_message.sticker:
        content = msg.reply_to_message.sticker.file_id
        text = None
        data_type = Types.STICKER

    elif msg.reply_to_message and msg.reply_to_message.document:
        content = msg.reply_to_message.document.file_id
        text = msg.reply_to_message.caption
        data_type = Types.DOCUMENT

    elif msg.reply_to_message and msg.reply_to_message.photo:
        content = msg.reply_to_message.photo[-1].file_id  # last elem = best quality
        text = msg.reply_to_message.caption
        data_type = Types.PHOTO

    elif msg.reply_to_message and msg.reply_to_message.audio:
        content = msg.reply_to_message.audio.file_id
        text = msg.reply_to_message.caption
        data_type = Types.AUDIO

    elif msg.reply_to_message and msg.reply_to_message.voice:
        content = msg.reply_to_message.voice.file_id
        text = msg.reply_to_message.caption
        data_type = Types.VOICE

    elif msg.reply_to_message and msg.reply_to_message.video:
        content = msg.reply_to_message.video.file_id
        text = msg.reply_to_message.caption
        data_type = Types.VIDEO

    elif msg.reply_to_message and msg.reply_to_message.video_note:
        content = msg.reply_to_message.video_note.file_id
        text = None
        data_type = Types.VIDEO_NOTE

    else:
        text = None
        data_type = None
        content = None

    return text, data_type, content


def get_message_type(msg: Message):
    data_type = None
    content = None
    text = ""
    raw_text = msg.text or msg.caption
    args = raw_text.split(None, 1)  # use python's maxsplit to separate cmd and args

    buttons = []
    # determine what the contents of the filter are - text, image, sticker, etc
    if len(args) >= 2:
        offset = len(args[1]) - len(raw_text)  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(args[1], entities=msg.parse_entities() or msg.parse_caption_entities(),
                                               offset=offset)
        if buttons:
            data_type = Types.BUTTON_TEXT
        else:
            data_type = Types.TEXT

    elif msg.reply_to_message:
        entities = msg.reply_to_message.parse_entities()
        msgtext = msg.reply_to_message.text or msg.reply_to_message.caption
        if len(args) >= 1 and msg.reply_to_message.text:  # not caption, text
            text, buttons = button_markdown_parser(msgtext,
                                                   entities=entities)
            if buttons:
                data_type = Types.BUTTON_TEXT
            else:
                data_type = Types.TEXT

        elif msg.reply_to_message.sticker:
            content = msg.reply_to_message.sticker.file_id
            data_type = Types.STICKER

        elif msg.reply_to_message.document:
            content = msg.reply_to_message.document.file_id
            text, buttons = button_markdown_parser(msgtext, entities=entities)
            data_type = Types.DOCUMENT

        elif msg.reply_to_message.photo:
            content = msg.reply_to_message.photo[-1].file_id  # last elem = best quality
            text, buttons = button_markdown_parser(msgtext, entities=entities)
            data_type = Types.PHOTO

        elif msg.reply_to_message.audio:
            content = msg.reply_to_message.audio.file_id
            text, buttons = button_markdown_parser(msgtext, entities=entities)
            data_type = Types.AUDIO

        elif msg.reply_to_message.voice:
            content = msg.reply_to_message.voice.file_id
            text, buttons = button_markdown_parser(msgtext, entities=entities)
            data_type = Types.VOICE

        elif msg.reply_to_message.video:
            content = msg.reply_to_message.video.file_id
            text, buttons = button_markdown_parser(msgtext, entities=entities)
            data_type = Types.VIDEO

        elif msg.reply_to_message.video_note:
            content = msg.reply_to_message.video_note.file_id
            text, buttons = button_markdown_parser(msgtext, entities=entities)
            data_type = Types.VIDEO_NOTE

    return text, data_type, content, buttons