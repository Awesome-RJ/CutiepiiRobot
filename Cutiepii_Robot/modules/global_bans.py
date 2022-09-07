import html
import time
from datetime import datetime
from io import BytesIO

from telegram import Update, Bot
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from telegram.ext import CallbackContext, CommandHandler, filters, MessageHandler
from telegram.helpers import mention_html

import Cutiepii_Robot.modules.sql.global_bans_sql as sql
from Cutiepii_Robot import (
    SUPPORT_USERS,
    DEV_USERS,
    GBAN_LOGS,
    OWNER_ID,
    STRICT_GBAN,
    SUPPORT_CHAT,
    TIGER_USERS,
    WHITELIST_USERS,
    CUTIEPII_PTB,
    SUDO_USERS,
)
from Cutiepii_Robot.modules.helper_funcs.chat_status import (
    is_user_admin,
    support_plus,
    bot_admin,
)
from Cutiepii_Robot.modules.helper_funcs.anonymous import user_admin

from Cutiepii_Robot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from Cutiepii_Robot.modules.helper_funcs.misc import send_to_list
from Cutiepii_Robot.modules.sql.users_sql import get_user_com_chats

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
    "Can't remove chat owner",
}

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
    "Peer_id_invalid",
    "User not found",
}


@support_plus
async def gban(update: Update, context: CallbackContext) -> None:
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect..",
        )
        return

    if (user_id) in DEV_USERS:
        await message.reply_text("That user is a Destroyers", )
        return

    if (user_id) in SUDO_USERS:
        await message.reply_text(
            "I spy, with my little eye... a Shadow Slayer! Why are you guys turning on each other?",
        )
        return

    if (user_id) in SUPPORT_USERS:
        await message.reply_text(
            "OOOH someone's trying to gban a Guardian! *Grabs Popcorn*", )
        return

    if (user_id) in TIGER_USERS:
        await message.reply_text(
            "That's a Light Shooters! They cannot be banned!")
        return

    if (user_id) in WHITELIST_USERS:
        await message.reply_text(
            "That's a Villain! They have a immune for ban and gban!")
        return

    if user_id == bot.id:
        await message.reply_text("You uhh...want me to punch myself?")
        return

    if user_id in [777000, 1087968824]:
        await message.reply_text(
            "Fool! You can't attack Telegram's native tech!")
        return

    try:
        user_chat = await bot.get_chat(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            await message.reply_text("I can't seem to find this user.")
            return ""
        return

    if user_chat.type != "private":
        await message.reply_text("That's not a user!")
        return

    if gban_db.is_user_gbanned(user_id):

        if not reason:
            await message.reply_text(
                "This user is already gbanned; I'd change the reason, but you haven't given me one...",
            )
            return

        if old_reason := gban_db.update_gban_reason(
                user_id,
                user_chat.username or user_chat.first_name,
                reason,
        ):
            await message.reply_text(
                f"This user is already gbanned, for the following reason:\n<code>{html.escape(old_reason)}</code>\nI've gone and updated it with your new reason!",
                parse_mode=ParseMode.HTML,
            )

        else:
            await message.reply_text(
                "This user is already gbanned, but had no reason set; I've gone and updated it!",
            )

        return

    await message.reply_text("On it!")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if ChatType.PRIVATE:
        chat_origin = f"<b>{html.escape(chat.title)} ({chat.id})</b>\n"
    else:
        chat_origin = f"<b>{chat.id}</b>\n"

    log_message = (
        f"#GBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Banned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Banned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>")

    if reason:
        if chat.type == chat.SUPERGROUP and chat.username:
            log_message += f'\n<b>Reason:</b> <a href="https://telegram.me/{chat.username}/{message.message_id}">{reason}</a>'
        else:
            log_message += f"\n<b>Reason:</b> <code>{reason}</code>"

    if GBAN_LOGS:
        try:
            log = await bot.send_message(GBAN_LOGS,
                                         log_message,
                                         parse_mode=ParseMode.HTML)
        except BadRequest:
            log = await bot.send_message(
                GBAN_LOGS,
                log_message +
                "\n\nFormatting has been disabled due to an unexpected error.",
            )

    else:
        send_to_list(bot, SUDO_USERS + SUPPORT_USERS, log_message, html=True)

    gban_db.gban_user(user_id, user_chat.username or user_chat.first_name,
                      reason)

    chats = get_user_com_chats(user_id)
    gbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            await bot.ban_chat_member(chat_id, user_id)
            gbanned_chats += 1

        except BadRequest as excp:
            if excp.message not in GBAN_ERRORS:
                await message.reply_text(
                    f"Could not gban due to: {excp.message}")
                if GBAN_LOGS:
                    await bot.send_message(
                        GBAN_LOGS,
                        f"Could not gban due to {excp.message}",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    send_to_list(
                        bot,
                        SUDO_USERS + SUPPORT_USERS,
                        f"Could not gban due to: {excp.message}",
                    )
                sql.ungban_user(user_id)
                return
        except TelegramError:
            pass

    if GBAN_LOGS:
        log.edit_text(
            f"{log_message}\n<b>Chats affected:</b> <code>{gbanned_chats}</code>",
            parse_mode=ParseMode.HTML,
        )

    else:
        send_to_list(
            bot,
            SUDO_USERS + SUPPORT_USERS,
            f"Gban complete! (User banned in <code>{gbanned_chats}</code> chats)",
            html=True,
        )

    end_time = time.time()
    gban_time = round((end_time - start_time), 2)

    if gban_time > 60:
        gban_time = round((gban_time / 60), 2)
    await message.reply_text("Done! Gbanned.", parse_mode=ParseMode.HTML)
    try:
        await bot.send_message(
            user_id,
            "#EVENT"
            "You have been marked as Malicious and as such have been banned from any future groups we manage."
            f"\n<b>Reason:</b> <code>{html.escape(user['reason'])}</code>"
            f"</b>Appeal Chat:</b> @{SUPPORT_CHAT}",
            parse_mode=ParseMode.HTML,
        )
    except:
        pass  # bot probably blocked by user


@support_plus
async def ungban(update: Update,
                 context: CallbackContext) -> None:  # sourcery no-metrics
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id = extract_user(message, args)

    if not user_id:
        await message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect.."
        )
        return

    user_chat = await bot.get_chat(user_id)
    if user_chat.type != "private":
        await message.reply_text("That's not a user!")
        return

    if not sql.is_user_gbanned(user_id):
        await message.reply_text("This user is not gbanned!")
        return

    await message.reply_text(
        f"I'll give {user_chat.first_name} a second chance, globally.")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if ChatType.PRIVATE:
        chat_origin = f"<b>{html.escape(chat.title)} ({chat.id})</b>\n"
    else:
        chat_origin = f"<b>{chat.id}</b>\n"

    log_message = (
        f"#UNGBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Unbanned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Unbanned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>")

    if GBAN_LOGS:
        try:
            log = await bot.send_message(GBAN_LOGS,
                                         log_message,
                                         parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = await bot.send_message(
                GBAN_LOGS,
                log_message +
                "\n\nFormatting has been disabled due to an unexpected error.",
            )
    else:
        send_to_list(bot, SUDO_USERS + SUPPORT_USERS, log_message, html=True)

    chats = get_user_com_chats(user_id)
    ungbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status == "kicked":
                await bot.unban_chat_member(chat_id, user_id)
                ungbanned_chats += 1

        except BadRequest as excp:
            if excp.message not in UNGBAN_ERRORS:
                await message.reply_text(
                    f"Could not un-gban due to: {excp.message}")
                if GBAN_LOGS:
                    await bot.send_message(
                        GBAN_LOGS,
                        f"Could not un-gban due to: {excp.message}",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    await bot.send_message(
                        OWNER_ID, f"Could not un-gban due to: {excp.message}")
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    if GBAN_LOGS:
        log.edit_text(
            f"{log_message}\n<b>Chats affected:</b> {ungbanned_chats}",
            parse_mode=ParseMode.HTML,
        )

    else:
        send_to_list(bot, SUDO_USERS + SUPPORT_USERS, "un-gban complete!")

    end_time = time.time()
    ungban_time = round((end_time - start_time), 2)

    if ungban_time > 60:
        ungban_time = round((ungban_time / 60), 2)
        await message.reply_text(
            f"Person has been un-gbanned. Took {ungban_time} min")
    else:
        await message.reply_text(
            f"Person has been un-gbanned. Took {ungban_time} sec")


@support_plus
async def gbanlist(update: Update, context: CallbackContext) -> None:
    banned_users = sql.get_gban_list()

    if not banned_users:
        await update.effective_message.reply_text(
            "There aren't any gbanned users! You're kinder than I expected...",
        )
        return

    banfile = "Screw these guys.\n"
    for user in banned_users:
        banfile += f"[x] {user['name']} - {user['_id']}\n"
        if user["reason"]:
            banfile += f"Reason: {user['reason']}\n"

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="gbanlist.txt",
            caption="Here is the list of currently gbanned users.",
        )


async def check_and_ban(update, user_id, should_message=True):
    if sql.is_user_gbanned(user_id):
        await update.effective_chat.ban_member(user_id)
        if should_message:
            text = (f"<b>Alert</b>: this user is globally banned.\n"
                    f"<code>*bans them from here*</code>.\n"
                    f"<b>Appeal chat</b>: @{SUPPORT_CHAT}\n"
                    f"<b>User ID</b>: <code>{user_id}</code>")
            user = sql.get_gbanned_user(user_id)
            if user.reason:
                text += f"\n<b>Ban Reason:</b> <code>{html.escape(user.reason)}</code>"
            await update.effective_message.reply_text(
                text, parse_mode=ParseMode.HTML)


@bot_admin
async def enforce_gban(update: Update, context: CallbackContext) -> None:
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    bot = context.bot
    if sql.does_chat_gban(update.effective_chat.id):
        user = update.effective_user
        chat = update.effective_chat
        msg = update.effective_message

        if user and not await is_user_admin(update, user_id, member):
            await check_and_ban(update, user.id)
            return

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                await check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user
            if user and not await is_user_admin(update, user_id, member):
                await check_and_ban(update, user.id, should_message=False)


@user_admin
async def gbanstat(update: Update, context: CallbackContext) -> None:
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            await update.effective_message.reply_text(
                "» Antispam is now enabled\n"
                "I am now protecting your group from potential remote threats!",
            )
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            await update.effective_message.reply_text(
                "» Antispan is now disabled")
    else:
        await update.effective_message.reply_text(
            f"Give me some arguments to choose a setting! on/off, yes/no!\n\nYour current setting is: {sql.does_chat_gban(update.effective_chat.id)}\nWhen True, any gbans that happen will also happen in your group. When False, they won't, leaving you at the possible mercy of spammers."
        )


async def clear_gbans(bot: Bot, update: Update):
    banned = sql.get_gban_list()
    deleted = 0
    for user in banned:
        id = user["user_id"]
        await asyncio.sleep(0.1)  # Reduce floodwait
        try:
            acc = await bot.get_chat(id)
            if not acc.first_name:
                deleted += 1
                sql.ungban_user(id)
        except BadRequest:
            deleted += 1
            sql.ungban_user(id)
    await update.effective_message.reply_text(
        f"Done! `{deleted}` deleted accounts were removed from the gbanlist.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def check_gbans(bot: Bot, update: Update):
    banned = sql.get_gban_list()
    deleted = 0
    for user in banned:
        id = user["user_id"]
        await asyncio.sleep(0.1)  # Reduce floodwait
        try:
            acc = await bot.get_chat(id)
            if not acc.first_name:
                deleted += 1
        except BadRequest:
            deleted += 1
    if deleted:
        await update.effective_message.reply_text(
            f"`{deleted}` deleted accounts found in the gbanlist! Run /cleangb to remove them from the database!",
            parse_mode=ParseMode.MARKDOWN,
        )

    else:
        await update.effective_message.reply_text(
            "No deleted accounts in the gbanlist!")


def __stats__():
    return f"➛ {sql.num_gbanned_users()} gbanned users."


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)
    text = "Gbanned: <b>{}</b>"
    if user_id in [777000, 1087968824]:
        return ""
    if user_id == 1241223850:
        return ""
    if (user_id) in SUDO_USERS + TIGER_USERS + WHITELIST_USERS:
        return ""
    if is_gbanned:
        text = text.format("Yes")
        user = sql.get_gbanned_user(user_id)
        if user["reason"]:
            text += f"\n<b>Reason:</b> <code>{html.escape(user['reason'])}</code>"
        text += f"\n<b>Appeal Chat:</b> @{SUPPORT_CHAT}"
    else:
        text = text.format("???")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"This chat is enforcing *gbans*: `{sql.does_chat_gban(chat_id)}`."


__help__ = f"""
*Admins only:*
➛ /antispam <on/off/yes/no>*:* Will toggle our antispam tech or return your current settings.

Anti-Spam, used by bot devs to ban spammers across all groups. This helps protect \
you and your groups by removing spam flooders as quickly as possible.
*Note:* Users can appeal gbans or report spammers at @{SUPPORT_CHAT}
"""

CUTIEPII_PTB.add_handler(CommandHandler("gban", gban))
CUTIEPII_PTB.add_handler(CommandHandler("ungban", ungban))
CUTIEPII_PTB.add_handler(CommandHandler("gbanlist", gbanlist))
CUTIEPII_PTB.add_handler(
    CommandHandler("antispam", gbanstat, filters=filters.ChatType.GROUPS))
CUTIEPII_PTB.add_handler(
    CommandHandler("checkgb", check_gbans, filters=filters.User(OWNER_ID)))
CUTIEPII_PTB.add_handler(
    CommandHandler("cleangb", clear_gbans, filters=filters.User(OWNER_ID)))
CUTIEPII_PTB.add_handler(
    MessageHandler((filters.ALL & filters.ChatType.GROUPS), enforce_gban))

__mod_name__ = "Anti-Spam"
