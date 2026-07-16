import re
import random
from html import escape
from typing import Optional

import telegram
from telegram import Chat, InlineKeyboardMarkup, Message, InlineKeyboardButton
from telegram.constants import ParseMode, MessageLimit
MAX_MESSAGE_LENGTH = MessageLimit.MAX_TEXT_LENGTH
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationHandlerStop as DispatcherHandlerStop,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
Filters = filters  # Alias for backward compatibility
from telegram.helpers import escape_markdown, mention_html

from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
from Cutiepii_Robot.modules.helper_funcs.filters import CustomFilters
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot import dispatcher, LOGGER, SUDO_USERS
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_text
from Cutiepii_Robot.modules.helper_funcs.misc import build_keyboard_parser, revert_buttons
from Cutiepii_Robot.modules.helper_funcs.msg_types import get_filter_type
from Cutiepii_Robot.modules.helper_funcs.string_handling import (
    split_quotes,
    button_markdown_parser,
    escape_invalid_curly_brackets,
    markdown_to_html,
)
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.sql import cust_filters_sql as sql
from Cutiepii_Robot.modules.connection import connected
from Cutiepii_Robot.modules.helper_funcs.alternate import send_message, typing_action
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    AdminPerms,
    user_is_admin,
)

HANDLER_GROUP = 10

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
    # sql.Types.VIDEO_NOTE.value: dispatcher.bot.send_video_note
}
CUSTFILTERS_GROUP = 50
PENDING_FILTERS = {}

@cutiepii_cmd(command='filters', admin_ok=True, rate_limit_calls=30, rate_limit_window=60, add_error_handler=True)
@typing_action
async def list_handlers(update, context):
    chat = update.effective_chat
    user = update.effective_user

    conn = await connected(context.bot, update, chat, user.id, need_admin=True)
    if conn is not False:
        chat_id = conn
        chat_obj = await dispatcher.bot.get_chat(conn)
        chat_name = escape_markdown(chat_obj.title)
        filter_list = "*Filter in {}:*\n"
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = "Local filters"
            filter_list = "*local filters:*\n"
        else:
            chat_name = escape_markdown(chat.title)
            filter_list = "*Filters in {}*:\n"

    all_handlers = sql.get_chat_triggers(chat_id)

    if not all_handlers:
        await send_message(
            update.effective_message, "No filters saved in {}!".format(chat_name)
        )
        return

    for keyword in all_handlers:
        entry = "- `{}`\n".format(keyword)
        if len(entry) + len(filter_list) > MAX_MESSAGE_LENGTH:
            await send_message(
                update.effective_message,
                filter_list.replace("{}", chat_name, 1),
                parse_mode=ParseMode.MARKDOWN,
            )
            filter_list = entry
        else:
            filter_list += entry

    await send_message(
        update.effective_message,
        filter_list.replace("{}", chat_name, 1),
        parse_mode=ParseMode.MARKDOWN,
    )


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@cutiepii_cmd(command='filter', group=55, rate_limit_calls=20, rate_limit_window=60, add_error_handler=True)
@typing_action
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@loggable
async def filters(update, context) -> None:  # sourcery no-metrics
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = msg.text.split(
        None, 1
    )  # use python's maxsplit to separate Cmd, keyword, and reply_text



    conn = await connected(context.bot, update, chat, user.id)
    if conn is not False:
        chat_id = conn
        chat_obj = await dispatcher.bot.get_chat(conn)
        chat_name = chat_obj.title
    else:
        chat_id = update.effective_chat.id
        chat_name = "local filters" if chat.type == "private" else chat.title
    if not msg.reply_to_message and len(args) < 2:
        await send_message(
            update.effective_message,
            "Please provide keyboard keyword for this filter to reply with!",
        )
        return

    if msg.reply_to_message:
        if len(args) < 2:
            await send_message(
                update.effective_message,
                "Please provide keyword for this filter to reply with!",
            )
            return
        else:
            keyword = args[1]
    else:
        extracted = split_quotes(args[1])
        if len(extracted) < 1:
            return
        # set trigger -> lower, so as to avoid adding duplicate filters with different cases
        keyword = extracted[0].lower()

    # Add the filter
    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(HANDLER_GROUP, []):
        if handler.filters == (keyword, chat_id):
            dispatcher.remove_handler(handler, HANDLER_GROUP)

    text, file_type, file_id = get_filter_type(msg)
    if not msg.reply_to_message and len(extracted) >= 2:
        offset = len(extracted[1]) - len(
            msg.text
        )  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(
            extracted[1], entities=msg.parse_entities(), offset=offset
        )
        text = text.strip()
        if not text:
            await send_message(
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
        offset = len(
            text_to_parsing
        )  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(
            text_to_parsing, entities=msg.parse_entities(), offset=offset
        )
        text = text.strip()

    elif not text and not file_type:
        await send_message(
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
        offset = len(
            text_to_parsing
        )  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(
            text_to_parsing, entities=msg.parse_entities(), offset=offset
        )
        text = text.strip()
        if (msg.reply_to_message.text or msg.reply_to_message.caption) and not text:
            await send_message(
                update.effective_message,
                "There is no filter message - You can't JUST have buttons, you need a message to go with it!",
            )
            return

    else:
        await send_message(update.effective_message, "Invalid filter!")
        return

    # Check if filter already exists
    existing_triggers = sql.get_chat_triggers(chat_id)
    if keyword in existing_triggers:
        pending_key = f"{chat_id}_{user.id}"
        PENDING_FILTERS[pending_key] = {
            'keyword': keyword,
            'text': text,
            'file_type': file_type,
            'file_id': file_id,
            'buttons': buttons,
            'chat_name': chat_name
        }
        
        buttons_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text="Yes", callback_data=f"filter_overwrite_yes_{chat_id}_{user.id}"),
                InlineKeyboardButton(text="No", callback_data=f"filter_overwrite_no_{chat_id}_{user.id}")
            ]
        ])
        await send_message(
            update.effective_message,
            "Filter already exists!\nDo you want to overwrite it?",
            reply_markup=buttons_markup
        )
        return None

    add = await addnew_filter(update, chat_id, keyword, text, file_type, file_id, buttons)
    # This is an old method
    # sql.add_filter(chat_id, keyword, content, is_sticker, is_document, is_image, is_audio, is_voice, is_video, buttons)

    if add is True:
        await send_message(
            update.effective_message,
            "Saved filter '{}' in *{}*!".format(escape_markdown(keyword), escape_markdown(chat_name)),
            parse_mode=ParseMode.MARKDOWN,
        )
        logmsg = (
        f"<b>{escape(chat.title or chat.id)}:</b>\n"
        f"#ADDFILTER\n"
        f"<b>Admin:</b> {mention_html(user.id, escape(user.first_name))}\n"
        f"<b>Note:</b> {keyword}"
        )
        return logmsg
    raise DispatcherHandlerStop


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISE
@cutiepii_cmd(command='stop', rate_limit_calls=20, rate_limit_window=60, add_error_handler=True)
@typing_action
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
        chat_obj = await dispatcher.bot.get_chat(conn)
        chat_name = chat_obj.title
    else:
        chat_id = update.effective_chat.id
        chat_name = "Local filters" if chat.type == "private" else chat.title
    if len(args) < 2:
        await send_message(update.effective_message, "What should i stop?")
        return ''

    chat_filters = sql.get_chat_triggers(chat_id)

    if not chat_filters:
        await send_message(update.effective_message, "No filters active here!")
        return ''

    for keyword in chat_filters:
        if keyword == args[1]:
            sql.remove_filter(chat_id, args[1])
            await send_message(
                update.effective_message,
                "Okay, I'll stop replying to that filter in *{}*.".format(escape_markdown(chat_name)),
                parse_mode=ParseMode.MARKDOWN,
            )
            logmsg = (
                    f"<b>{escape(chat.title or chat.id)}:</b>\n"
                    f"#STOPFILTER\n"
                    f"<b>Admin:</b> {mention_html(user.id, escape(user.first_name))}\n"
                    f"<b>Filter:</b> {keyword}"
                )
            return logmsg

    await send_message(
        update.effective_message,
        "That's not a filter - Click: /filters to get currently active filters.",
    )

def replace_dynamic_placeholders(text: str, message: Message, parse_mode: Optional[ParseMode]) -> str:
    if not text:
        return text

    user = message.from_user
    if not user:
        return text

    first_name = user.first_name or ""
    last_name = user.last_name or ""
    username = f"@{user.username}" if user.username else ""
    user_id = str(user.id)

    # Determine mention style based on parse_mode
    if parse_mode == ParseMode.HTML:
        mention = mention_html(user.id, escape(first_name))
    else:
        # Default to Markdown mention style
        mention = f"[{first_name}](tg://user?id={user_id})"

    # Handle (parentheses) placeholders
    text = text.replace("(username)", username)
    text = text.replace("(first_name)", first_name)
    text = text.replace("(last_name)", last_name)
    text = text.replace("(mention)", mention)
    text = text.replace("(user_id)", user_id)

    # Support {curly} placeholders too for maximum compatibility
    text = text.replace("{username}", username)
    text = text.replace("{first_name}", first_name)
    text = text.replace("{last_name}", last_name)
    text = text.replace("{mention}", mention)
    text = text.replace("{user_id}", user_id)

    return text

@cutiepii_msg((CustomFilters.has_text & ~telegram.ext.filters.UpdateType.EDITED_MESSAGE), group=CUSTFILTERS_GROUP)
async def reply_filter(update, context):  # sourcery no-metrics
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]
    user = update.effective_user

    if not update.effective_user or update.effective_user.id == 777000:
        return
    to_match = await extract_text(message)
    if not to_match:
        return

    chat_filters = sql.get_chat_triggers(chat.id)
    for keyword in chat_filters:
        # Support aliases separated by '|'
        aliases = keyword.split('|')
        matched = False
        for alias in aliases:
            alias = alias.strip()
            if not alias:
                continue
            pattern = r"( |^|[^\w])" + re.escape(alias) + r"( |$|[^\w])"
            if re.search(pattern, to_match, flags=re.IGNORECASE):
                matched = True
                break
        if matched:
            filt = sql.get_filter(chat.id, keyword)

            if to_match.endswith(("raw", "noformat")) and to_match.lower() == keyword + (" raw" or " noformat"):
                no_format = True
            else:
                no_format = False

            if filt.reply == "there is should be a new reply":
                buttons = sql.get_buttons(chat.id, filt.keyword)

                VALID_WELCOME_FORMATTERS = [
                    "first",
                    "last",
                    "fullname",
                    "username",
                    "id",
                    "chatname",
                    "mention",
                    "replytag",
                    "user",
                    "admin",
                ]
                if filt.reply_text:

                    if not no_format and "%%%" in filt.reply_text:
                        split = filt.reply_text.split("%%%")
                        if all(split):
                            text = random.choice(split)
                        else:
                            text = filt.reply_text
                    else:
                        text = filt.reply_text

                    text = replace_dynamic_placeholders(text, message, ParseMode.HTML)

                    if (text.startswith("~!") or text.startswith(" ~!")) and (text.endswith("!~") or text.endswith("!~ ")):
                        sticker_id = text.replace("~!", "").replace("!~", "").replace(" ", "") # replace space (' ') bcz, got error: Wrong remote file....
                        try:
                            await context.bot.send_sticker(
                                chat.id,
                                sticker_id,
                                reply_to_message_id=message.message_id,
                            )
                            return
                        except BadRequest as excp:
                            if (
                                excp.message
                                == "Wrong remote file identifier specified: wrong padding in the string"
                            ):
                                await context.bot.send_message(
                                    chat.id,
                                    "Message couldn't be sent, Is the sticker id valid?",
                                )
                                return
                            else:
                                LOGGER.exception("Error in filters: " + excp.message)
                                return

                    valid_format = escape_invalid_curly_brackets(
                        markdown_to_html(text), VALID_WELCOME_FORMATTERS
                    )
                    if valid_format:
                        filtext = valid_format.format(
                            first=escape(message.from_user.first_name),
                            last=escape(
                                message.from_user.last_name
                                or message.from_user.first_name
                            ),
                            fullname=" ".join(
                                [
                                    escape(message.from_user.first_name),
                                    escape(message.from_user.last_name),
                                ]
                                if message.from_user.last_name
                                else [escape(message.from_user.first_name)]
                            ),
                            username="@" + escape(message.from_user.username)
                            if message.from_user.username
                            else mention_html(
                                message.from_user.id, message.from_user.first_name
                            ),
                            mention=mention_html(
                                message.from_user.id, message.from_user.first_name
                            ),
                            chatname=escape(message.chat.title)
                            if message.chat.type == "private"
                            else escape(message.from_user.first_name),
                            id=message.from_user.id,
                            replytag=message.reply_to_message.from_user.id
                            if message.reply_to_message and message.reply_to_message.from_user
                            else message.from_user.id,
                            user="",
                            admin="",
                        )
                    else:
                        filtext = ""
                else:
                    filtext = ""

                if (
                    "{admin}" in filt.reply_text
                    and user_is_admin(chat, user.id)
                ):
                    return

                if (
                    "{user}" in filt.reply_text
                    and not user_is_admin(chat, user.id)
                ):
                    return

                keyb = []
                if no_format:
                    parse_mode = None
                    filtext += revert_buttons(buttons)
                    keyboard = InlineKeyboardMarkup(keyb)
                else:
                    parse_mode = ParseMode.HTML
                    keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                    keyboard = InlineKeyboardMarkup(keyb)

                if filt.file_type in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    try:
                        await message.reply_text(
                            filtext,
                            reply_to_message_id=message.message_id,
                            parse_mode=parse_mode,
                            disable_web_page_preview=True,
                            reply_markup=keyboard,
                            allow_sending_without_reply=True
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
                                    reply_markup=keyboard,
                                    allow_sending_without_reply=True
                                )
                            except BadRequest as excp:
                                LOGGER.exception("Error in filters: " + excp.message)
                                await send_message(
                                    update.effective_message,
                                    get_exception(excp, filt, chat),
                                )
                        else:
                            try:
                                await send_message(
                                    update.effective_message,
                                    get_exception(excp, filt, chat),
                                )
                            except BadRequest as excp:
                                LOGGER.exception(
                                    "Failed to send message: " + excp.message
                                )
                    return
                try:
                    if ENUM_FUNC_MAP[filt.file_type] == dispatcher.bot.send_sticker:
                        await ENUM_FUNC_MAP[filt.file_type](
                            chat.id,
                            filt.file_id,
                            reply_to_message_id=message.message_id,
                            reply_markup=keyboard,
                            allow_sending_without_reply=True
                        )
                    else:
                        await ENUM_FUNC_MAP[filt.file_type](
                            chat.id,
                            filt.file_id,
                            caption=filtext,
                            reply_to_message_id=message.message_id,
                            parse_mode=parse_mode,
                            reply_markup=keyboard,
                            allow_sending_without_reply=True
                        )
                except BadRequest as excp:
                    LOGGER.exception("Error in filters (sending media): " + excp.message)
                    await send_message(
                        update.effective_message,
                        await get_exception(excp, filt, chat),
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

                keyb = []
                buttons = sql.get_buttons(chat.id, filt.keyword)
                if no_format:
                    parse_mode = None
                    reply_text = filt.reply + revert_buttons(buttons)
                    keyboard = InlineKeyboardMarkup(keyb)
                else:
                    parse_mode = ParseMode.MARKDOWN
                    reply_text = replace_dynamic_placeholders(filt.reply, message, parse_mode)
                    keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                    keyboard = InlineKeyboardMarkup(keyb)


                try:
                    await send_message(
                        update.effective_message,
                        reply_text,
                        parse_mode=parse_mode,
                        disable_web_page_preview=True,
                        reply_markup=keyboard,
                        allow_sending_without_reply=True
                    )
                except BadRequest as excp:
                    if excp.message == "Unsupported url protocol":
                        try:
                            await send_message(
                                update.effective_message,
                                "You seem to be trying to use an unsupported url protocol. "
                                "Telegram doesn't support buttons for some protocols, such as tg://. Please try "
                                "again...",
                            )
                        except BadRequest as excp:
                            LOGGER.exception("Error in filters: " + excp.message)
                    elif excp.message == "Reply message not found" or excp.message == "Message can't be deleted":
                        try:
                            await context.bot.send_message(
                                chat.id,
                                reply_text,
                                parse_mode=parse_mode,
                                disable_web_page_preview=True,
                                reply_markup=keyboard,
                                allow_sending_without_reply=True
                            )
                        except BadRequest as excp:
                            LOGGER.exception("Error in filters: " + excp.message)
                    else:
                        try:
                            await send_message(
                                update.effective_message,
                                "This message couldn't be sent as it's incorrectly formatted.",
                            )
                        except BadRequest as excp:
                            LOGGER.exception("Error in filters: " + excp.message)
                        LOGGER.warning(
                            "Message %s could not be parsed", str(filt.reply)
                        )
                        LOGGER.exception(
                            "Could not parse filter %s in chat %s",
                            str(filt.keyword),
                            str(chat.id),
                        )

            else:
                    # LEGACY - all new filters will have has_markdown set to True.
                try:
                    reply_text = replace_dynamic_placeholders(filt.reply, message, None)
                    await send_message(update.effective_message, reply_text)
                except BadRequest as excp:
                    LOGGER.exception("Error in filters: " + excp.message)
            break

@cutiepii_cmd(command=["removeallfilters", "stopall"], filters=Filters.ChatType.GROUPS, rate_limit_calls=2, rate_limit_window=300, add_error_handler=True)
async def rmall_filters(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    
    # Check permissions
    is_anon = message and message.sender_chat and message.sender_chat.id == chat.id
    
    has_rights = False
    if user and user.id in SUDO_USERS:
        has_rights = True
    elif is_anon:
        has_rights = True
    elif user:
        try:
            member = await chat.get_member(user.id)
            if member.status == "creator":
                has_rights = True
            elif member.status == "administrator":
                required_perms = [
                    "can_change_info",
                    "can_delete_messages",
                    "can_invite_users",
                    "can_restrict_members",
                    "can_pin_messages",
                    "can_promote_members",
                ]
                has_rights = all(getattr(member, perm, False) is True for perm in required_perms)
        except Exception:
            pass

    if not has_rights:
        await update.effective_message.reply_text(
            "Only the chat owner or an administrator with all rights can clear all filters at once."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Stop all filters", callback_data="filters_rmall"
                    )
                ],
                [InlineKeyboardButton(text="Cancel", callback_data="filters_cancel")],
            ]
        )
        await update.effective_message.reply_text(
            f"Are you sure you would like to stop ALL filters in {escape_markdown(chat.title)}? This action cannot be undone.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )

@cutiepii_callback(pattern=r"filters_.*")
@loggable
async def rmall_callback(update, context) -> str:
    query = update.callback_query
    chat = update.effective_chat
    msg = update.effective_message
    user = query.from_user
    
    try:
        member = await chat.get_member(user.id)
    except Exception:
        await query.answer("Error checking your permissions.", show_alert=True)
        return ""

    has_rights = False
    if user.id in SUDO_USERS:
        has_rights = True
    elif member.status == "creator":
        has_rights = True
    elif member.status == "administrator":
        required_perms = [
            "can_change_info",
            "can_delete_messages",
            "can_invite_users",
            "can_restrict_members",
            "can_pin_messages",
            "can_promote_members",
        ]
        has_rights = all(getattr(member, perm, False) is True for perm in required_perms)

    if query.data == "filters_rmall":
        if has_rights:
            allfilters = sql.get_chat_triggers(chat.id)
            if not allfilters:
                await msg.edit_text("No filters in this chat, nothing to stop!")
                return ""

            count = 0
            filterlist = []
            for x in allfilters:
                count += 1
                filterlist.append(x)

            for i in filterlist:
                sql.remove_filter(chat.id, i)

            await msg.edit_text(f"Cleaned {count} filters in {escape(chat.title)}")

            log_message = (
                f"<b>{escape(chat.title or chat.id)}:</b>\n"
                f"#CLEAREDALLFILTERS\n"
                f"<b>Admin:</b> {mention_html(user.id, escape(user.first_name))}"
            )
            return log_message

        else:
            await query.answer("Only the chat owner or an administrator with all rights can clear all filters.", show_alert=True)
            return ""

    elif query.data == "filters_cancel":
        if has_rights:
            await msg.edit_text("Clearing of all filters has been cancelled.")
            return ""
        else:
            await query.answer("Only the chat owner or an administrator with all rights can cancel this.", show_alert=True)
            return ""


@cutiepii_callback(pattern=r"filter_overwrite_.*")
@loggable
async def filter_overwrite_callback(update, context) -> str:
    query = update.callback_query
    chat = update.effective_chat
    msg = update.effective_message
    user = query.from_user
    
    parts = query.data.split("_")
    action = parts[2]  # "yes" or "no"
    target_chat_id = int(parts[3])
    target_user_id = int(parts[4])
    
    if user.id != target_user_id:
        await query.answer("You did not initiate this filter creation request.", show_alert=True)
        return ""
        
    pending_key = f"{target_chat_id}_{target_user_id}"
    pending_data = PENDING_FILTERS.get(pending_key)
    
    if not pending_data:
        await query.answer("No pending request found.", show_alert=True)
        await msg.edit_text("This request has expired or is no longer valid.")
        return ""
        
    if action == "yes":
        keyword = pending_data['keyword']
        text = pending_data['text']
        file_type = pending_data['file_type']
        file_id = pending_data['file_id']
        buttons = pending_data['buttons']
        chat_name = pending_data['chat_name']
        
        for handler in dispatcher.handlers.get(HANDLER_GROUP, []):
            if handler.filters == (keyword, target_chat_id):
                dispatcher.remove_handler(handler, HANDLER_GROUP)
                
        sql.new_add_filter(target_chat_id, keyword, text, file_type, file_id, buttons)
        
        await msg.edit_text(
            "Saved filter '{}' in *{}*!".format(escape_markdown(keyword), escape_markdown(chat_name)),
            parse_mode=ParseMode.MARKDOWN
        )
        
        PENDING_FILTERS.pop(pending_key, None)
        
        logmsg = (
            f"<b>{escape(chat.title or chat.id)}:</b>\n"
            f"#ADDFILTER (Overwrite)\n"
            f"<b>Admin:</b> {mention_html(user.id, escape(user.first_name))}\n"
            f"<b>Note:</b> {keyword}"
        )
        return logmsg
        
    else:  # "no"
        await msg.edit_text("Filter overwrite request cancelled.")
        PENDING_FILTERS.pop(pending_key, None)
        return ""


# NOT ASYNC NOT A HANDLER
async def get_exception(excp, filt, chat):
    if excp.message == "Unsupported url protocol":
        return "You seem to be trying to use the URL protocol which is not supported. Telegram does not support key for multiple protocols, such as tg: //. Please try again!"
    elif excp.message == "Reply message not found" or excp.message == "Message can't be deleted":
        return "noreply"
    else:
        LOGGER.warning("Message %s could not be parsed", str(filt.reply))
        LOGGER.exception(
            "Could not parse filter %s in chat %s", str(filt.keyword), str(chat.id)
        )
        return " This data could not be sent because it is incorrectly formatted."


# NOT ASYNC NOT A HANDLER
async def addnew_filter(update, chat_id, keyword, text, file_type, file_id, buttons):
    msg = update.effective_message
    totalfilt = sql.get_chat_triggers(chat_id)
    if len(totalfilt) >= 900:  # Idk why i made this like function....
        msg.reply_text("This group has reached its max filters limit of 900.")
        return False
    else:
        sql.new_add_filter(chat_id, keyword, text, file_type, file_id, buttons)
        return True


def __stats__():
    return "- {} filters, across {} chats.".format(sql.num_filters(), sql.num_chats())


async def __import_data__(chat_id, data):
    # set chat filters
    filters = data.get("filters", {})
    for trigger in filters:
        sql.add_to_blacklist(chat_id, trigger)


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


async def __chat_settings__(chat_id, _):
    cust_filters = sql.get_chat_triggers(chat_id)
    return "There are `{}` custom filters here.".format(len(cust_filters))

__help__ = True

__mod_name__ = "Filters"
