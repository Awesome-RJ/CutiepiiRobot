import re
from html import escape

import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.error import BadRequest
from telegram.constants import MessageLimit, ParseMode
from telegram.ext import (
    filters as PTB_Cutiepii_Filters,
    CallbackContext,
    CallbackQueryHandler,
    MessageHandler,
)
from telegram.helpers import escape_markdown, mention_html

from Cutiepii_Robot import CUTIEPII_PTB, SUDO_USERS, LOGGER
from Cutiepii_Robot.modules.helper_funcs.msg_types import get_filter_type
from Cutiepii_Robot.modules.helper_funcs.misc import build_keyboard_parser
from Cutiepii_Robot.modules.helper_funcs.string_handling import escape_invalid_curly_brackets
from Cutiepii_Robot.modules.helper_funcs.string_handling import (
    split_quotes,
    button_markdown_parser,
    markdown_to_html,
)
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.sql import cust_filters_sql as sql
from Cutiepii_Robot.modules.connection import connected
from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.helper_funcs.alternate import send_message
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_text
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    AdminPerms,
)

HANDLER_GROUP = 10

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: CUTIEPII_PTB.bot.send_message,
    sql.Types.BUTTON_TEXT.value: CUTIEPII_PTB.bot.send_message,
    sql.Types.STICKER.value: CUTIEPII_PTB.bot.send_sticker,
    sql.Types.DOCUMENT.value: CUTIEPII_PTB.bot.send_document,
    sql.Types.PHOTO.value: CUTIEPII_PTB.bot.send_photo,
    sql.Types.AUDIO.value: CUTIEPII_PTB.bot.send_audio,
    sql.Types.VOICE.value: CUTIEPII_PTB.bot.send_voice,
    sql.Types.VIDEO.value: CUTIEPII_PTB.bot.send_video,
    # sql.Types.VIDEO_NOTE.value: CUTIEPII_PTB.bot.send_video_note
}


async def list_handlers(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user

    conn = await connected(context.bot,
                           update,
                           chat,
                           user.id,
                           need_admin=False)
    if conn is not False:
        chat_id = conn
        chat_name = CUTIEPII_PTB.bot.getChat(conn).title
        filter_list = "*Filter in {}:*\n"
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "Local filters"
            filter_list = "*local filters:*\n"
        else:
            chat_name = chat.title
            filter_list = "*Filters in {}*:\n"

    all_handlers = sql.get_chat_triggers(chat_id)

    if not all_handlers:
        send_message(update.effective_message,
                     f"No filters saved in {chat_name}!")
        return

    for keyword in all_handlers:
        entry = f"➛ `{escape_markdown(keyword)}`\n"
        if len(entry) + len(filter_list) > MessageLimit.TEXT_LENGTH:
            send_message(
                update.effective_message,
                filter_list.format(chat_name),
                parse_mode=ParseMode.MARKDOWN,
            )
            filter_list = entry
        else:
            filter_list += entry

    send_message(
        update.effective_message,
        filter_list.format(chat_name),
        parse_mode=ParseMode.MARKDOWN,
    )


# NOT ASYNC BECAUSE CUTIEPII_PTB HANDLER RAISED


@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@loggable
async def filters(update, context) -> None:  # sourcery no-metrics
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = msg.text.split(
        None,
        1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    conn = await connected(context.bot, update, chat, user.id)
    if conn is not False:
        chat_id = conn
        chat_name = CUTIEPII_PTB.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        chat_name = "local filters" if chat.type == "private" else chat.title
    if not msg.reply_to_message and len(args) < 2:
        send_message(
            update.effective_message,
            "Please provide keyboard keyword for this filter to reply with!",
        )
        return

    if msg.reply_to_message:
        if len(args) < 2:
            send_message(
                update.effective_message,
                "Please provide keyword for this filter to reply with!",
            )
            return
        keyword = args[1]
    else:
        extracted = split_quotes(args[1])
        if len(extracted) < 1:
            return
        # set trigger -> lower, so as to avoid adding duplicate filters with different cases
        keyword = extracted[0].lower()

    # Add the filter
    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in CUTIEPII_PTB.handlers.get(HANDLER_GROUP, []):
        if handler.filters == (keyword, chat_id):
            CUTIEPII_PTB.remove_handler(handler, HANDLER_GROUP)

    text, file_type, file_id = get_filter_type(msg)
    if not msg.reply_to_message and len(extracted) >= 2:
        offset = len(extracted[1]) - len(
            msg.text)  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(extracted[1],
                                               entities=msg.parse_entities(),
                                               offset=offset)
        text = text.strip()
        if not text:
            send_message(
                update.effective_message,
                "There is no filter message - You can't JUST have buttons, you need a message to go with it!",
            )
            return

    elif msg.reply_to_message and len(args) >= 2:
        if msg.reply_to_message.text:
            text_to_parsing = msg.reply_to_message.text
        elif msg.reply_to_message.caption:
            text_to_parsing = msg.reply_to_message.caption
        else:
            text_to_parsing = ""
        offset = len(text_to_parsing
                     )  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(text_to_parsing,
                                               entities=msg.parse_entities(),
                                               offset=offset)
        text = text.strip()

    elif not text and not file_type:
        send_message(
            update.effective_message,
            "Please provide keyword for this filter reply with!",
        )
        return

    elif msg.reply_to_message:
        if msg.reply_to_message.text:
            text_to_parsing = msg.reply_to_message.text
        elif msg.reply_to_message.caption:
            text_to_parsing = msg.reply_to_message.caption
        else:
            text_to_parsing = ""
        offset = len(text_to_parsing
                     )  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(text_to_parsing,
                                               entities=msg.parse_entities(),
                                               offset=offset)
        text = text.strip()
        if (msg.reply_to_message.text
                or msg.reply_to_message.caption) and not text:
            send_message(
                update.effective_message,
                "There is no filter message - You can't JUST have buttons, you need a message to go with it!",
            )
            return

    else:
        send_message(update.effective_message, "Invalid filter!")
        return

    add = addnew_filter(update, chat_id, keyword, text, file_type, file_id,
                        buttons)
    # This is an old method
    # sql.add_filter(chat_id, keyword, content, is_sticker, is_document, is_image, is_audio, is_voice, is_video, buttons)

    if add is True:
        send_message(
            update.effective_message,
            f"Saved filter '{keyword}' in *{chat_name}*!",
            parse_mode=ParseMode.MARKDOWN,
        )

        return f"<b>{escape(chat.title or chat.id)}:</b>\n"


# NOT ASYNC BECAUSE CUTIEPII_PTB HANDLER RAISE
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@loggable
async def stop_filter(update, context) -> str:
    chat = update.effective_chat
    user = update.effective_user
    args = update.effective_message.text.split(None, 1)
    message = update.effective_message

    conn = await connected(context.bot, update, chat, user.id)
    if conn is not False:
        chat_id = conn
        chat_name = CUTIEPII_PTB.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        chat_name = "Local filters" if chat.type == "private" else chat.title
    if len(args) < 2:
        send_message(update.effective_message, "What should i stop?")
        return ''

    chat_filters = sql.get_chat_triggers(chat_id)

    if not chat_filters:
        send_message(update.effective_message, "No filters active here!")
        return ''

    for keyword in chat_filters:
        if keyword == args[1]:
            sql.remove_filter(chat_id, args[1])
            send_message(
                update.effective_message,
                f"Okay, I'll stop replying to that filter in *{chat_name}*.",
                parse_mode=ParseMode.MARKDOWN,
            )
            logmsg = (
                f"<b>{escape(chat.title or chat.id)}:</b>\n"
                f"#STOPFILTER\n"
                f"<b>Admin:</b> {mention_html(user.id, escape(user.first_name))}\n"
                f"<b>Filter:</b> {keyword}")
            return logmsg

    send_message(
        update.effective_message,
        "That's not a filter - Click: /filters to get currently active filters.",
    )


async def reply_filter(
        update: Update,
        context: CallbackContext) -> None:  # sourcery no-metrics
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]

    if not update.effective_user or update.effective_user.id == 777000:
        return
    to_match = extract_text(message)
    if not to_match:
        return

    chat_filters = sql.get_chat_triggers(chat.id)
    for keyword in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            filt = sql.get_filter(chat.id, keyword)
            if filt.reply == "there is should be a new reply":
                buttons = sql.get_buttons(chat.id, filt.keyword)
                keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                VALID_WELCOME_FORMATTERS = [
                    "first",
                    "last",
                    "fullname",
                    "username",
                    "id",
                    "chatname",
                    "mention",
                ]
                if filt.reply_text:
                    if valid_format := escape_invalid_curly_brackets(
                            markdown_to_html(filt.reply_text),
                            VALID_WELCOME_FORMATTERS):
                        filtext = valid_format.format(
                            first=escape(message.from_user.first_name),
                            last=escape(message.from_user.last_name
                                        or message.from_user.first_name),
                            fullname=" ".join(
                                [
                                    escape(message.from_user.first_name),
                                    escape(message.from_user.last_name),
                                ] if message.from_user.last_name else
                                [escape(message.from_user.first_name)]),
                            username=f"@{escape(message.from_user.username)}"
                            if message.from_user.username else mention_html(
                                message.from_user.id,
                                message.from_user.first_name),
                            mention=mention_html(message.from_user.id,
                                                 message.from_user.first_name),
                            chatname=escape(message.chat.title)
                            if message.chat.type != "private" else escape(
                                message.from_user.first_name),
                            id=message.from_user.id)

                    else:
                        filtext = ""
                else:
                    filtext = ""

                if filt.file_type in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    try:
                        await context.bot.send_message(
                            chat.id,
                            filtext,
                            reply_to_message_id=message.message_id,
                            parse_mode=ParseMode.HTML,
                            disable_web_page_preview=True,
                            reply_markup=keyboard,
                        )
                    except BadRequest as excp:
                        error_catch = get_exception(excp, filt, chat)
                        if error_catch == "noreply":
                            try:
                                await context.bot.send_message(
                                    chat.id,
                                    filtext,
                                    parse_mode=ParseMode.HTML,
                                    disable_web_page_preview=True,
                                    reply_markup=keyboard)

                            except BadRequest as excp:
                                LOGGER.exception(
                                    f"Error in filters: {excp.message}")
                                send_message(update.effective_message,
                                             get_exception(excp, filt, chat))
                        else:
                            try:
                                send_message(update.effective_message,
                                             get_exception(excp, filt, chat))
                            except BadRequest as excp:
                                LOGGER.exception(
                                    f"Failed to send message: {excp.message}")
                elif ENUM_FUNC_MAP[
                        filt.file_type] == CUTIEPII_PTB.bot.send_sticker:
                    ENUM_FUNC_MAP[filt.file_type](
                        chat.id,
                        filt.file_id,
                        reply_to_message_id=message.message_id,
                        reply_markup=keyboard,
                    )
                else:
                    ENUM_FUNC_MAP[filt.file_type](
                        chat.id,
                        filt.file_id,
                        caption=filtext,
                        reply_to_message_id=message.message_id,
                        parse_mode=ParseMode.HTML,
                        reply_markup=keyboard,
                    )
            elif filt.is_sticker:
                await message.reply_sticker(filt.reply)
            elif filt.is_document:
                await message.reply_document(filt.reply)
            elif filt.is_image:
                await message.reply_photo(filt.reply)
            elif filt.is_audio:
                await message.reply_audio(filt.reply)
            elif filt.is_voice:
                await message.reply_voice(filt.reply)
            elif filt.is_video:
                await message.reply_video(filt.reply)
            elif filt.has_markdown:
                buttons = sql.get_buttons(chat.id, filt.keyword)
                keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                try:
                    send_message(
                        update.effective_message,
                        filt.reply,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True,
                        reply_markup=keyboard,
                    )
                except BadRequest as excp:
                    if excp.message == "Unsupported url protocol":
                        try:
                            send_message(
                                update.effective_message,
                                "You seem to be trying to use an unsupported url protocol. Telegram doesn't support buttons for some protocols, such as tg://. Please try again..."
                            )

                        except BadRequest as excp:
                            LOGGER.exception(
                                f"Error in filters: {excp.message}")
                    elif excp.message == "Reply message not found":
                        try:
                            await context.bot.send_message(
                                chat.id,
                                filt.reply,
                                parse_mode=ParseMode.MARKDOWN,
                                disable_web_page_preview=True,
                                reply_markup=keyboard)

                        except BadRequest as excp:
                            LOGGER.exception(
                                f"Error in filters: {excp.message}")
                    else:
                        try:
                            send_message(
                                update.effective_message,
                                "This message couldn't be sent as it's incorrectly formatted."
                            )

                        except BadRequest as excp:
                            LOGGER.exception(
                                f"Error in filters: {excp.message}")
                        LOGGER.warning("Message %s could not be parsed",
                                       str(filt.reply))
                        LOGGER.exception(
                            "Could not parse filter %s in chat %s",
                            str(filt.keyword), str(chat.id))

            else:
                # LEGACY - all new filters will have has_markdown set to True.
                try:
                    send_message(update.effective_message, filt.reply)
                except BadRequest as excp:
                    LOGGER.exception(f"Error in filters: {excp.message}")
            break


async def rmall_filters(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    member = chat.get_member(user.id)
    if member.status != "creator" and user.id not in SUDO_USERS:
        await update.effective_message.reply_text(
            "Only the chat owner can clear all filters at once.")
    else:
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text="Stop all filters",
                                     callback_data="filters_rmall")
            ],
            [
                InlineKeyboardButton(text="Cancel",
                                     callback_data="filters_cancel")
            ],
        ])
        await update.effective_message.reply_text(
            f"Are you sure you would like to stop ALL filters in {chat.title}? This action cannot be undone.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


@loggable
async def rmall_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    chat = update.effective_chat
    msg = update.effective_message
    member = chat.get_member(query.from_user.id)
    if query.data == "filters_rmall":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            allfilters = sql.get_chat_triggers(chat.id)
            if not allfilters:
                msg.edit_text("No filters in this chat, nothing to stop!")
                return

            count = 0
            filterlist = []
            for x in allfilters:
                count += 1
                filterlist.append(x)

            for i in filterlist:
                sql.remove_filter(chat.id, i)

            msg.edit_text(f"Cleaned {count} filters in {chat.title}")

        if member.status == "administrator":
            await query.answer("Only owner of the chat can do this.")

        if member.status == "member":
            await query.answer("You need to be admin to do this.")
    elif query.data == "filters_cancel":
        if member.status == "creator" or query.from_user.id in SUDO_USERS:
            msg.edit_text("Clearing of all filters has been cancelled.")
            return
        if member.status == "administrator":
            await query.answer("Only owner of the chat can do this.")
        if member.status == "member":
            await query.answer("You need to be admin to do this.")


# NOT ASYNC NOT A HANDLER
def get_exception(excp, filt, chat):
    if excp.message == "Unsupported url protocol":
        return "You seem to be trying to use the URL protocol which is not supported. Telegram does not support key for multiple protocols, such as tg: //. Please try again!"
    if excp.message == "Reply message not found":
        return "noreply"
    LOGGER.warning("Message %s could not be parsed", str(filt.reply))
    LOGGER.exception("Could not parse filter %s in chat %s", str(filt.keyword),
                     str(chat.id))
    return "This data could not be sent because it is incorrectly formatted."


# NOT ASYNC NOT A HANDLER
async def addnew_filter(update, chat_id, keyword, text, file_type, file_id,
                        buttons):
    msg = update.effective_message
    totalfilt = sql.get_chat_triggers(chat_id)
    if len(totalfilt) >= 900:  # Idk why i made this like function....
        await msg.reply_text(
            "This group has reached its max filters limit of 900.")
        return False
    sql.new_add_filter(chat_id, keyword, text, file_type, file_id, buttons)
    return True


def __stats__():
    return f"➛ {sql.num_filters()} filters, across {sql.num_chats()} chats."


def __import_data__(chat_id, data):
    # set chat filters
    filters = data.get("filters", {})
    for trigger in filters:
        sql.add_to_blacklist(chat_id, trigger)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, _):
    cust_filters = sql.get_chat_triggers(chat_id)
    return f"There are `{len(cust_filters)}` custom filters here."


__help__ = """
➛ /filters*:* List all active filters saved in the chat.
*Admin only:*
➛ /filter <keyword> <reply message>*:* Add a filter to this chat. The bot will now reply that message whenever 'keyword'\
is mentioned. If you reply to a sticker with a keyword, the bot will reply with that sticker. NOTE: all filter \
keywords are in lowercase. If you want your keyword to be a sentence, use quotes. eg: /filter "hey there" How you \
doin?
 Separate diff replies by `%%%` to get random replies
 *Example:* 
 `/filter "filtername"
 Reply 1
 %%%
 Reply 2
 %%%
 Reply 3`
➛ /stop <filter keyword>*:* Stop that filter.
*Chat creator only:*
➛ /removeallfilters*:* Remove all chat filters at once.
*Note*: Filters also support markdown formatters like: {first}, {last} etc.. and buttons.
Check `/markdownhelp` to know more!
"""

CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("filter", filters))
CUTIEPII_PTB.add_handler(DisableAbleCommandHandler("stop", stop_filter))
CUTIEPII_PTB.add_handler(
    DisableAbleCommandHandler(["removeallfilters", "stopall"],
                              rmall_filters,
                              filters=PTB_Cutiepii_Filters.ChatType.GROUPS))
CUTIEPII_PTB.add_handler(
    CallbackQueryHandler(rmall_callback, pattern=r"filters_.*"))
CUTIEPII_PTB.add_handler(
    DisableAbleCommandHandler("filters", list_handlers, admin_ok=True))
CUTIEPII_PTB.add_handler(
    MessageHandler(
        PTB_Cutiepii_Filters.TEXT
        & ~PTB_Cutiepii_Filters.UpdateType.EDITED_MESSAGE, reply_filter))

__mod_name__ = "Filters"
