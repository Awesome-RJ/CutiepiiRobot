from enum import IntEnum
import html
import re
from typing import List, Tuple, Optional

from telegram import ChatPermissions, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode, ChatMemberStatus
from telegram.error import BadRequest
from telegram.ext import ContextTypes, filters
from telegram.helpers import mention_html
import Cutiepii_Robot.modules.sql.blacklist_sql as sql
from Cutiepii_Robot import SUDO_USERS, LOGGER, REDIS
from Cutiepii_Robot.modules.sql.approve_sql import is_approved
from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_text
from Cutiepii_Robot.modules.helper_funcs.misc import split_message
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.warns import warn
from Cutiepii_Robot.modules.helper_funcs.string_handling import extract_time
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, cutiepii_join_request, cutiepii_msg
from Cutiepii_Robot.modules.helper_funcs.alternate import send_message, typing_action

def is_blacklist_delete(chat_id: int) -> bool:
    val = REDIS.get(f"blacklist_delete_{chat_id}")
    if val is None:
        return True
    return val.decode() == "true"

def set_blacklist_delete(chat_id: int, status: bool):
    REDIS.set(f"blacklist_delete_{chat_id}", "true" if status else "false")

def trigger_to_regex(trigger: str) -> re.Pattern:
    temp = trigger
    temp = temp.replace("**", "___DOUBLE_STAR___")
    temp = temp.replace("*", "___SINGLE_STAR___")
    temp = temp.replace("?", "___QUESTION___")
    escaped = re.escape(temp)
    escaped = escaped.replace("___DOUBLE_STAR___", ".*")
    escaped = escaped.replace("___SINGLE_STAR___", r"[^\s]+")
    escaped = escaped.replace("___QUESTION___", r"[^\s]")
    pattern = r"( |^|[^\w])" + escaped + r"( |$|[^\w])"
    return re.compile(pattern, re.IGNORECASE)

from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
    user_not_admin_check,
    user_is_admin,
)

BLACKLIST_GROUP = -3


class BlacklistActions(IntEnum):
    default = 0
    delete = 1
    warn = 2
    mute = 3
    kick = 4
    ban = 5


@cutiepii_cmd(command=["blacklist", "blacklists", "blocklist", "blocklists", "blacklisted"], admin_ok=True, rate_limit_calls=30, rate_limit_window=60, add_error_handler=True)
@connection_status
@user_admin_check()
@typing_action
async def blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    args = context.args

    filter_list = "<b>🚫 Blacklist Settings for {}</b>\n\n".format(html.escape(chat.title))

    getmode, getvalue = sql.get_blacklist_setting(chat.id)
    bl_type = "Do nothing"
    match getmode:
        case 1:
            bl_type = "Delete"
        case 2:
            bl_type = "Warn"
        case 3:
            bl_type = "Mute"
        case 4:
            bl_type = "Kick"
        case 5:
            bl_type = "Ban"
        case 6:
            bl_type = "Temporarily Ban for {}".format(getvalue)
        case 7:
            bl_type = "Temporarily Mute for {}".format(getvalue)

    filter_list += "📋 <b>Current blacklist mode:</b> {}\n".format(bl_type)
    all_blacklisted = sql.get_chat_blacklist(chat.id)
    filter_list += "\n📝 <b>Current blacklisted words (<i>{}</i>):</b>\n".format(len(all_blacklisted))
    for i in all_blacklisted:
        trigger = i[0]
        action = BlacklistActions(i[1]).name
        filter_list += "  - <code>{}</code> - <i>Action:</i> {}\n".format(html.escape(trigger), action)

    buttons = [
        [InlineKeyboardButton("➕ Add Word", url=f"t.me/{context.bot.username}?start=addblacklist_{chat.id}"),
         InlineKeyboardButton("🔧 Settings", callback_data="blacklist_settings")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="blacklist_refresh"),
         InlineKeyboardButton("ℹ️ Help", callback_data="blacklist_help")],
        [InlineKeyboardButton("❌ Close", callback_data="blacklist_close")]
    ]

    split_text = split_message(filter_list)
    for text in split_text:
        if len(all_blacklisted) == 0:
            await send_message(
                update.effective_message,
                "🚫 <b>Blacklist Words</b>\n\n"
                "No blacklisted words in <b>{}</b>!\n\n"
                "<i>Use /addblacklist to add words.</i>".format(chat.title),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
            return
        await send_message(update.effective_message, text, parse_mode=ParseMode.HTML,
                         reply_markup=InlineKeyboardMarkup(buttons) if text == split_text[-1] else None)


@cutiepii_cmd(command=["addblacklist", "addblocklist", "blacklist"], rate_limit_calls=10, rate_limit_window=60, add_error_handler=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@typing_action
async def add_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    args = context.args

    # Check if this is just showing blacklists (i.e. /blacklist command without arguments and not as reply)
    command_name = update.effective_message.text.split()[0][1:].split("@")[0].lower()
    if command_name in ["blacklist", "blacklists", "blocklist", "blocklists"] and not args and not msg.reply_to_message:
        await blacklist(update, context)
        return

    chat_name = html.escape(chat.title)

    if msg.reply_to_message:
        reply = msg.reply_to_message
        if reply.sticker:
            trigger_text = f"stickerpack:{reply.sticker.set_name}"
            if args:
                arg_str = " ".join(args)
                trigger, action, custom_val = await extract_bl_and_action(arg_str)
                stored_trigger = trigger_text
                if custom_val:
                    stored_trigger += f"|||{custom_val}"
                action_value = action.value if hasattr(action, 'value') else int(action)
                sql.add_to_blacklist(chat.id, stored_trigger, action_value)
                act_name = action.name if hasattr(action, 'name') else str(action)
                await msg.reply_text(f"Added blacklist for stickerpack: <code>{reply.sticker.set_name}</code> with <b>{act_name}</b> action!", parse_mode=ParseMode.HTML)
            else:
                sql.add_to_blacklist(chat.id, trigger_text, BlacklistActions.default.value)
                await msg.reply_text(f"Added blacklist for stickerpack: <code>{reply.sticker.set_name}</code>!", parse_mode=ParseMode.HTML)
            return
        elif reply.text or reply.caption:
            text_to_blacklist = reply.text or reply.caption
            trigger_text = text_to_blacklist.strip()
            if args:
                arg_str = " ".join(args)
                trigger, action, custom_val = await extract_bl_and_action(arg_str)
                stored_trigger = trigger_text
                if custom_val:
                    stored_trigger += f"|||{custom_val}"
                action_value = action.value if hasattr(action, 'value') else int(action)
                sql.add_to_blacklist(chat.id, stored_trigger, action_value)
                act_name = action.name if hasattr(action, 'name') else str(action)
                await msg.reply_text(f"Added blacklist trigger: <code>{html.escape(trigger_text)}</code> with <b>{act_name}</b> action!", parse_mode=ParseMode.HTML)
            else:
                sql.add_to_blacklist(chat.id, trigger_text, BlacklistActions.default.value)
                await msg.reply_text(f"Added blacklist trigger: <code>{html.escape(trigger_text)}</code>!", parse_mode=ParseMode.HTML)
            return

    if args:
        text = msg.text.split(None, 1)[1]
        to_blacklist: List[str] = list({trigger.strip() for trigger in text.split("\n") if trigger.strip()})

        for trigger in to_blacklist:
            bl, action, custom_val = await extract_bl_and_action(trigger)
            stored_trigger = bl
            if custom_val:
                stored_trigger += f"|||{custom_val}"
            action_value = action.value if hasattr(action, 'value') else int(action)
            if not sql.add_to_blacklist(chat.id, stored_trigger, action_value):
                await msg.reply_text("<b>Action Denied</b>\nThe maximum threshold of 100 blacklist triggers has been reached for this chat.", parse_mode=ParseMode.HTML)
                return
            act = action.name if hasattr(action, 'name') else str(action)

        if len(to_blacklist) == 1:
            reply = "Added blacklist trigger: <code>{}</code> with <b>{}</b> action!"
            await send_message(
                update.effective_message,
                reply.format(html.escape(bl), act),
                parse_mode=ParseMode.HTML,
            )
        else:
            reply = "Added blacklist <code>{}</code> in chat: <b>{}</b>!"
            await send_message(
                update.effective_message,
                reply.format(len(to_blacklist), chat_name),
                parse_mode=ParseMode.HTML,
            )
    else:
        await send_message(
            update.effective_message,
            "Tell me which words/stickers you would like to add to the blacklist (or reply to a message/sticker).",
        )


async def extract_bl_and_action(text: str) -> Tuple[str, BlacklistActions, Optional[str]]:
    if not text or "{" not in text or "}" not in text:
        return text, BlacklistActions.default, None

    try:
        start_idx = text.rindex("{")
        end_idx = text.rindex("}")
        action_part = text[start_idx + 1: end_idx].strip()
        parts = action_part.split(None, 1)
        action_name = parts[0].lower()
        custom_val = parts[1] if len(parts) > 1 else None

        action_map = {
            "off": BlacklistActions.default,
            "del": BlacklistActions.delete,
            "delete": BlacklistActions.delete,
            "warn": BlacklistActions.warn,
            "mute": BlacklistActions.mute,
            "kick": BlacklistActions.kick,
            "ban": BlacklistActions.ban,
            "tban": 6,
            "tmute": 7
        }

        if action_name in action_map:
            clean_trigger = text[:start_idx].strip()
            if (clean_trigger.startswith('"') and clean_trigger.endswith('"')) or \
               (clean_trigger.startswith("'") and clean_trigger.endswith("'")):
                clean_trigger = clean_trigger[1:-1].strip()
            action_type = action_map[action_name]
            return clean_trigger, action_type, custom_val
    except ValueError:
        pass

    return text, BlacklistActions.default, None


@cutiepii_cmd(command=["unblacklist", "unblocklist", "whitelist"], rate_limit_calls=10, rate_limit_window=60, add_error_handler=True)
@typing_action
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def unblacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    args = context.args

    chat_id = chat.id
    chat_name = html.escape(chat.title)

    if args:
        text = msg.text.split(None, 1)[1]
        to_unblacklist = list({trigger.strip() for trigger in text.split("\n") if trigger.strip()})

        successful = 0
        allfilters = sql.get_chat_blacklist(chat_id)

        for trigger in to_unblacklist:
            for item in list(allfilters):
                db_trigger = item[0]
                db_clean = db_trigger.split("|||", 1)[0]
                if db_clean.lower() == trigger.lower() or db_trigger.lower() == trigger.lower():
                    success = sql.rm_from_blacklist(chat_id, db_trigger)
                    if success:
                        successful += 1

        if len(to_unblacklist) == 1:
            if successful:
                await send_message(
                    update.effective_message,
                    "Removed <code>{}</code> from blacklist in <b>{}</b>!".format(
                        html.escape(to_unblacklist[0]), chat_name
                    ),
                    parse_mode=ParseMode.HTML,
                )
            else:
                await send_message(
                    update.effective_message, "This is not a blacklist trigger!"
                )

        elif successful == len(to_unblacklist):
            await send_message(
                update.effective_message,
                "Removed <code>{}</code> from blacklist in <b>{}</b>!".format(
                    successful, chat_name
                ),
                parse_mode=ParseMode.HTML,
            )

        elif not successful:
            await send_message(
                update.effective_message,
                "None of these triggers exist so it can't be removed.",
                parse_mode=ParseMode.HTML,
            )

        else:
            await send_message(
                update.effective_message,
                "Removed <code>{}</code> from blacklist. {} did not exist, "
                "so were not removed.".format(
                    successful, len(to_unblacklist) - successful
                ),
                parse_mode=ParseMode.HTML,
            )
    else:
        await send_message(
            update.effective_message,
            "Tell me which words you would like to remove from blacklist!",
        )


@cutiepii_cmd(command=["blacklistmode", "blocklistmode", "setblacklistmode", "setblocklistmode"], rate_limit_calls=5, rate_limit_window=60, add_error_handler=True)
@typing_action
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@loggable
async def blacklist_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):  # sourcery no-metrics
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = context.args

    chat_id = chat.id

    if args:
        if args[0].lower() in ["off", "nothing", "no"]:
            settypeblacklist = "do nothing"
            sql.set_blacklist_strength(chat_id, 0, "0")
        elif args[0].lower() in ["del", "delete"]:
            settypeblacklist = "will delete blacklisted message"
            sql.set_blacklist_strength(chat_id, 1, "0")
        elif args[0].lower() == "warn":
            settypeblacklist = "warn the sender"
            sql.set_blacklist_strength(chat_id, 2, "0")
        elif args[0].lower() == "mute":
            settypeblacklist = "mute the sender"
            sql.set_blacklist_strength(chat_id, 3, "0")
        elif args[0].lower() == "kick":
            settypeblacklist = "kick the sender"
            sql.set_blacklist_strength(chat_id, 4, "0")
        elif args[0].lower() == "ban":
            settypeblacklist = "ban the sender"
            sql.set_blacklist_strength(chat_id, 5, "0")
        elif args[0].lower() == "tban":
            if len(args) == 1:
                teks = """It looks like you tried to set time value for blacklist but you didn't specified time; Try, `/blacklistmode tban <timevalue>`.

Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                await send_message(update.effective_message, teks, parse_mode=ParseMode.MARKDOWN)
                return ""
            restime = await extract_time(msg, args[1])
            if not restime:
                teks = """Invalid time value!
Example of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                await send_message(update.effective_message, teks, parse_mode=ParseMode.MARKDOWN)
                return ""
            settypeblacklist = "temporarily ban for {}".format(args[1])
            sql.set_blacklist_strength(chat_id, 6, str(args[1]))
        elif args[0].lower() == "tmute":
            if len(args) == 1:
                teks = """It looks like you tried to set time value for blacklist but you didn't specified  time; try, `/blacklistmode tmute <timevalue>`.

Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                await send_message(update.effective_message, teks, parse_mode=ParseMode.MARKDOWN)
                return ""
            restime = await extract_time(msg, args[1])
            if not restime:
                teks = """Invalid time value!
Examples of time value: 4m = 4 minutes, 3h = 3 hours, 6d = 6 days, 5w = 5 weeks."""
                await send_message(update.effective_message, teks, parse_mode=ParseMode.MARKDOWN)
                return ""
            settypeblacklist = "temporarily mute for {}".format(args[1])
            sql.set_blacklist_strength(chat_id, 7, str(args[1]))
        else:
            await send_message(
                update.effective_message,
                "I only understand: off/del/warn/ban/kick/mute/tban/tmute!",
            )
            return ""
        text = "Changed blacklist mode: `{}`!".format(settypeblacklist)
        await send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
        return (
            "<b>{}:</b>\n"
            "<b>Admin:</b> {}\n"
            "Changed the blacklist mode. will {}.".format(
                html.escape(chat.title),
                mention_html(user.id, user.first_name),
                settypeblacklist,
            )
        )
    else:
        getmode, getvalue = sql.get_blacklist_setting(chat.id)
        bl_type = "Do nothing"
        match getmode:
            case 1:
                bl_type = "Delete"
            case 2:
                bl_type = "Warn"
            case 3:
                bl_type = "Mute"
            case 4:
                bl_type = "Kick"
            case 5:
                bl_type = "Ban"
            case 6:
                bl_type = "Temporarily Ban for {}".format(getvalue)
            case 7:
                bl_type = "Temporarily Mute for {}".format(getvalue)
        text = "Current blacklistmode: *{}*.".format(bl_type)
        await send_message(update.effective_message, text, parse_mode=ParseMode.MARKDOWN)
    return ""


@cutiepii_cmd(command="blocklistdelete", admin_ok=True, rate_limit_calls=10, rate_limit_window=60)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
async def blocklist_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    args = context.args
    if args:
        val = args[0].lower()
        if val in ["on", "yes", "true"]:
            set_blacklist_delete(chat.id, True)
            await update.effective_message.reply_text("<b>Blacklist Settings Updated</b>\nEnabled deletion of blacklisted messages.", parse_mode=ParseMode.HTML)
        elif val in ["off", "no", "false"]:
            set_blacklist_delete(chat.id, False)
            await update.effective_message.reply_text("<b>Blacklist Settings Updated</b>\nDisabled deletion of blacklisted messages.", parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text("<b>Invalid Argument</b>\nPlease specify either <code>on</code> or <code>off</code>.", parse_mode=ParseMode.HTML)
    else:
        is_del = is_blacklist_delete(chat.id)
        status = "enabled" if is_del else "disabled"
        await update.effective_message.reply_text(f"<b>Blacklist Settings</b>\nDeletion of blacklisted messages is currently <code>{status}</code>.", parse_mode=ParseMode.HTML)


@cutiepii_msg(((filters.TEXT | filters.COMMAND | filters.Sticker.ALL | filters.PHOTO) & filters.ChatType.GROUPS),
        group=BLACKLIST_GROUP)
@user_not_admin_check
async def del_blacklist(update: Update, context: ContextTypes.DEFAULT_TYPE):  # sourcery no-metrics
    chat = update.effective_chat
    message = update.effective_message
    user = message.sender_chat or update.effective_user
    bot = context.bot
    if is_approved(chat.id, user.id):
        return

    to_match = await extract_text(message)
    is_sticker = message.sticker is not None

    getmode, default_val = sql.get_blacklist_setting(chat.id)
    chat_filters = sql.get_chat_blacklist(chat.id)
    should_delete = is_blacklist_delete(chat.id)

    for item in chat_filters:
        trigger_str = str(item[0])
        parts = trigger_str.split("|||", 1)
        trigger = parts[0]
        custom_val = parts[1] if len(parts) > 1 else None

        action_strength = int(item[1]) if int(item[1]) > 0 else getmode
        if action_strength == 0:
            continue

        val_to_use = custom_val if custom_val else default_val
        matched = False

        if trigger.startswith("sticker:"):
            if is_sticker:
                emoji_to_match = trigger[len("sticker:"):]
                if message.sticker.emoji == emoji_to_match:
                    matched = True
        elif trigger.startswith("stickerpack:"):
            if is_sticker:
                pack_to_match = trigger[len("stickerpack:"):]
                if message.sticker.set_name == pack_to_match:
                    matched = True
        elif trigger.startswith("exact:"):
            word_to_match = trigger[len("exact:"):]
            if to_match and to_match.strip().lower() == word_to_match.lower():
                matched = True
        elif trigger.startswith("prefix:"):
            word_to_match = trigger[len("prefix:"):]
            if to_match and to_match.strip().lower().startswith(word_to_match.lower()):
                matched = True
        else:
            if to_match:
                regex = trigger_to_regex(trigger)
                if regex.search(to_match):
                    matched = True

        if matched:
            try:
                if should_delete and action_strength > 0:
                    try:
                        await message.delete()
                    except BadRequest as e:
                        if e.message != "Message to delete not found":
                            raise

                match action_strength:
                    case 1:
                        return
                    case 2:
                        reason = val_to_use if val_to_use != "0" else "Using blacklisted trigger"
                        await warn(
                            update.effective_user,
                            update,
                            reason,
                            message,
                            update.effective_user,
                        )
                        return
                    case 3:
                        await bot.restrict_chat_member(
                            chat.id,
                            update.effective_user.id,
                            permissions=ChatPermissions(can_send_messages=False),
                        )
                        await bot.send_message(
                            chat.id,
                            f"Muted {user.first_name} for using blacklisted word/sticker!",
                        )
                        return
                    case 4:
                        res = await chat.unban_member(update.effective_user.id)
                        if res:
                            await bot.send_message(
                                chat.id,
                                f"Kicked {user.first_name} for using blacklisted word/sticker!",
                            )
                        return
                    case 5:
                        await chat.ban_member(user.id)
                        await bot.send_message(
                            chat.id,
                            f"Banned {user.first_name} for using blacklisted word/sticker!",
                        )
                        return
                    case 6:
                        bantime = await extract_time(message, val_to_use)
                        await chat.ban_member(user.id, until_date=bantime)
                        await bot.send_message(
                            chat.id,
                            f"Banned {user.first_name} until '{val_to_use}' for using blacklisted word/sticker!",
                        )
                        return
                    case 7:
                        mutetime = await extract_time(message, val_to_use)
                        await bot.restrict_chat_member(
                            chat.id,
                            user.id,
                            until_date=mutetime,
                            permissions=ChatPermissions(can_send_messages=False),
                        )
                        await bot.send_message(
                            chat.id,
                            f"Muted {user.first_name} until '{val_to_use}' for using blacklisted word/sticker!",
                        )
                        return
            except BadRequest as excp:
                if excp.message != "Message to delete not found":
                    LOGGER.exception("Error while handling blacklist trigger.")
            break


@cutiepii_cmd(command=["removeallblacklists", "removeallblocklists", "unblacklistall"], filters=filters.ChatType.GROUPS, rate_limit_calls=2, rate_limit_window=300, add_error_handler=True)
async def rmall_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    member = await chat.get_member(user.id)
    if member.status != ChatMemberStatus.OWNER and user.id not in SUDO_USERS:
        await update.effective_message.reply_text(
            "Only the chat owner can clear all blacklists at once."
        )
    else:
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Remove all Blacklists", callback_data="blacklists_rmall"
                    )
                ],
                [InlineKeyboardButton(text="Cancel", callback_data="blacklists_cancel")],
            ]
        )
        await update.effective_message.reply_text(
            f"Are you sure you would like to stop ALL blacklists in {chat.title}? This action cannot be undone.",
            reply_markup=buttons,
            parse_mode=ParseMode.MARKDOWN,
        )


@cutiepii_callback(pattern=r"blacklists_.*")
@loggable
async def rmall_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    query = update.callback_query
    chat = update.effective_chat
    msg = update.effective_message
    member = await chat.get_member(query.from_user.id)
    user = query.from_user
    if query.data == "blacklists_rmall":
        if member.status == ChatMemberStatus.OWNER or query.from_user.id in SUDO_USERS:
            allfilters = sql.get_chat_blacklist(chat.id)
            if not allfilters:
                await msg.edit_text("No blacklists in this chat, nothing to stop!")
                return ""

            count = 0
            filterlist = []
            for x in allfilters:
                count += 1
                filterlist.append(x)
            for i in filterlist:
                sql.rm_from_blacklist(chat.id, i[0])

            await msg.edit_text(f"Cleaned {count} bl in {chat.title}")

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#CLEAREDALLBLACKLISTS\n"
                f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}"
            )
            return log_message

        if member.status == ChatMemberStatus.ADMINISTRATOR:
            await query.answer("Only owner of the chat can do this.")
            return ""

        if member.status == ChatMemberStatus.MEMBER:
            await query.answer("You need to be admin to do this.")
            return ""
    elif query.data == "blacklists_cancel":
        if member.status == ChatMemberStatus.OWNER or query.from_user.id in SUDO_USERS:
            await msg.edit_text("Clearing of all filters has been cancelled.")
            return ""
        if member.status == ChatMemberStatus.ADMINISTRATOR:
            await query.answer("Only owner of the chat can do this.")
            return ""
        if member.status == ChatMemberStatus.MEMBER:
            await query.answer("You need to be admin to do this.")
            return ""


async def __import_data__(chat_id, data):
    # set chat blacklist
    blacklist = data.get("blacklist", {})
    for trigger in blacklist:
        sql.add_to_blacklist(chat_id, trigger)


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


async def __chat_settings__(chat_id, user_id):
    blacklisted = sql.num_blacklist_chat_filters(chat_id)
    return "There are {} blacklisted words.".format(blacklisted)


def __stats__():
    return "- {} blacklist triggers, across {} chats.".format(
        sql.num_blacklist_filters(), sql.num_blacklist_filter_chats()
    )


__help__ = True


# Callback handler for blacklist module buttons
@cutiepii_callback(pattern=r"^blacklist_")
async def blacklist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, data: str = None):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    query = update.callback_query
    await query.answer()
    if data is None:
        data = query.data
    chat = update.effective_chat
    user = update.effective_user
    
    # Check if user is admin
    if not await user_is_admin(update, user.id):
        await query.answer("⚠️ You need to be an admin to use this!", show_alert=True)
        return
    
    if data == "blacklist_close":
        await query.message.delete()
        return
    
    if data == "blacklist_help":
        help_text = """
<b>ℹ️ Blacklist System Help</b>

<b>What is blacklist?</b>
Automatically deletes messages containing blacklisted words.

<b>Available Actions:</b>
- Delete - Just delete the message
- Warn - Warn the user
- Mute - Silence the user
- Kick - Remove from group
- Ban - Permanently ban

<b>Quick Commands:</b>
❍ /blacklist - View blacklisted words
❍ /addblacklist - Add words
❍ /unblacklist - Remove words
❍ /blacklistmode - Change action

<i>Admins are ignored by blacklists!</i>
        """
        buttons = [
            [InlineKeyboardButton("« Back", callback_data="blacklist_refresh"),
             InlineKeyboardButton("❌ Close", callback_data="blacklist_close")]
        ]
        await query.message.edit_text(help_text, parse_mode=ParseMode.HTML,
                                     reply_markup=InlineKeyboardMarkup(buttons))
        return
    
    if data == "blacklist_refresh" or data == "blacklist_settings":
        filter_list = "<b>🚫 Blacklist Settings for {}</b>\n\n".format(html.escape(chat.title))
        getmode, getvalue = sql.get_blacklist_setting(chat.id)
        bl_type = "Do nothing"
        match getmode:
            case 1:
                bl_type = "Delete"
            case 2:
                bl_type = "Warn"
            case 3:
                bl_type = "Mute"
            case 4:
                bl_type = "Kick"
            case 5:
                bl_type = "Ban"
            case 6:
                bl_type = "Temporarily Ban for {}".format(getvalue)
            case 7:
                bl_type = "Temporarily Mute for {}".format(getvalue)

        filter_list += "📋 <b>Current blacklist mode:</b> {}\n".format(bl_type)
        all_blacklisted = list(sql.get_chat_blacklist(chat.id))
        filter_list += "\n📝 <b>Current blacklisted words (<i>{}</i>):</b>\n".format(len(all_blacklisted))
        
        for i in all_blacklisted[:20]:  # Limit to 20 for message size
            trigger = i[0]
            action = BlacklistActions(i[1]).name
            filter_list += "  - <code>{}</code> - <i>{}</i>\n".format(html.escape(trigger), action)
        
        if len(all_blacklisted) > 20:
            filter_list += f"\n<i>... and {len(all_blacklisted) - 20} more words</i>"

        buttons = [
            [InlineKeyboardButton("🔧 Settings", callback_data="blacklist_mode_settings")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="blacklist_refresh"),
             InlineKeyboardButton("ℹ️ Help", callback_data="blacklist_help")],
            [InlineKeyboardButton("❌ Close", callback_data="blacklist_close")]
        ]

        if len(all_blacklisted) == 0:
            filter_list = "🚫 <b>Blacklist Words</b>\n\nNo blacklisted words in <b>{}</b>!\n\n<i>Use /addblacklist to add words.</i>".format(chat.title)
        
        await query.message.edit_text(filter_list, parse_mode=ParseMode.HTML,
                                     reply_markup=InlineKeyboardMarkup(buttons))
        return
    
    if data == "blacklist_mode_settings":
        getmode, getvalue = sql.get_blacklist_setting(chat.id)
        buttons = [
            [InlineKeyboardButton("❌ Delete Only", callback_data="blacklist_setmode_1")],
            [InlineKeyboardButton("⚠️ Warn", callback_data="blacklist_setmode_2"),
             InlineKeyboardButton("🔇 Mute", callback_data="blacklist_setmode_3")],
            [InlineKeyboardButton("👢 Kick", callback_data="blacklist_setmode_4"),
             InlineKeyboardButton("🚫 Ban", callback_data="blacklist_setmode_5")],
            [InlineKeyboardButton("« Back", callback_data="blacklist_refresh"),
             InlineKeyboardButton("❌ Close", callback_data="blacklist_close")]
        ]
        await query.message.edit_text(
            "<b>🔧 Select Blacklist Action Mode</b>\n\n"
            f"<b>Current mode:</b> {getmode}\n\n"
            "Choose what action to take when blacklisted words are sent:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
    
    if data.startswith("blacklist_setmode_"):
        mode = int(data.split("_")[-1])
        sql.set_blacklist_strength(chat.id, mode, "0")
        await query.answer("✅ Blacklist mode updated!", show_alert=True)
        await blacklist_callback(update, context, data="blacklist_refresh")
        return
async def check_user_profile_blacklist(chat_id, user, user_bio=None, bot=None):
    chat_filters = sql.get_chat_blacklist(chat_id)
    if not chat_filters:
        return False, None, None, None

    bio = user_bio
    if not bio and bot:
        try:
            chat_member_chat = await bot.get_chat(user.id)
            bio = getattr(chat_member_chat, "bio", "") or getattr(chat_member_chat, "description", "")
        except Exception:
            bio = ""

    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    username = user.username or ""

    match_targets = []
    if full_name:
        match_targets.append(full_name)
    if first_name:
        match_targets.append(first_name)
    if last_name:
        match_targets.append(last_name)
    if username:
        match_targets.append(username)
        match_targets.append(f"@{username}")
    if bio:
        match_targets.append(bio)

    getmode, default_val = sql.get_blacklist_setting(chat_id)

    for item in chat_filters:
        trigger_str = str(item[0])
        parts = trigger_str.split("|||", 1)
        trigger = parts[0]
        custom_val = parts[1] if len(parts) > 1 else None

        action_strength = int(item[1]) if int(item[1]) > 0 else getmode
        if action_strength == 0:
            continue

        matched = False
        if trigger.startswith("sticker:") or trigger.startswith("stickerpack:"):
            continue

        clean_trigger = trigger
        if trigger.startswith("exact:"):
            clean_trigger = trigger[len("exact:"):]
            for target in match_targets:
                if target.strip().lower() == clean_trigger.lower():
                    matched = True
                    break
        elif trigger.startswith("prefix:"):
            clean_trigger = trigger[len("prefix:"):]
            for target in match_targets:
                if target.strip().lower().startswith(clean_trigger.lower()):
                    matched = True
                    break
        else:
            regex = trigger_to_regex(clean_trigger)
            for target in match_targets:
                if regex.search(target):
                    matched = True
                    break

        if matched:
            return True, clean_trigger, action_strength, (custom_val if custom_val else default_val)

    return False, None, None, None


@cutiepii_join_request()
async def blacklist_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.chat_join_request
    if not request:
        return
    chat = request.chat
    user = request.from_user
    bot = context.bot

    matched, trigger, action, val = await check_user_profile_blacklist(
        chat.id, user, user_bio=getattr(request, "bio", None), bot=bot
    )
    if matched:
        try:
            await bot.decline_chat_join_request(chat_id=chat.id, user_id=user.id)
            LOGGER.info(f"[BLACKLIST JOIN PROTECTION] Declined join request from {user.first_name} ({user.id}) in chat {chat.title} due to trigger '{trigger}'")
        except Exception as e:
            LOGGER.error(f"Error declining join request: {e}")


@cutiepii_msg(filters.StatusUpdate.NEW_CHAT_MEMBERS & filters.ChatType.GROUPS, group=BLACKLIST_GROUP - 1)
async def blacklist_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    if not message or not message.new_chat_members:
        return
    bot = context.bot

    for user in message.new_chat_members:
        if is_approved(chat.id, user.id):
            continue

        matched, trigger, action, val = await check_user_profile_blacklist(chat.id, user, bot=bot)
        if matched:
            try:
                match action:
                    case 1 | 4:
                        await chat.unban_member(user.id)
                    case 2 | 5:
                        await chat.ban_member(user.id)
                    case 3:
                        await bot.restrict_chat_member(
                            chat.id,
                            user.id,
                            permissions=ChatPermissions(can_send_messages=False),
                        )
                    case 6:
                        bantime = await extract_time(message, val)
                        await chat.ban_member(user.id, until_date=bantime)
                    case 7:
                        mutetime = await extract_time(message, val)
                        await bot.restrict_chat_member(
                            chat.id,
                            user.id,
                            until_date=mutetime,
                            permissions=ChatPermissions(can_send_messages=False),
                        )
                
                if is_blacklist_delete(chat.id):
                    try:
                        await message.delete()
                    except Exception:
                        pass

                LOGGER.info(f"[BLACKLIST JOIN PROTECTION] Removed new member {user.first_name} ({user.id}) in chat {chat.title} (Action: {action}) due to trigger '{trigger}'")
            except Exception as e:
                LOGGER.error(f"Error handling blacklisted new member: {e}")


__mod_name__ = "Blacklists"
