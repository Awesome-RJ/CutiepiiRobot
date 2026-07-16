import html
import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.helpers import mention_html
from telegram.error import TelegramError

from Cutiepii_Robot import (
    SUDO_USERS,
    DEV_USERS,
    SUPPORT_USERS,
    WHITELIST_USERS,
    TIGER_USERS,
    OWNER_ID,
)
from Cutiepii_Robot.modules.helper_funcs.chat_status import whitelist_plus, dev_plus, sudo_plus, support_plus
from Cutiepii_Robot.modules.helper_funcs.extraction import extract_user
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.sql import super_users_sql as sql
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd

LOGGER = logging.getLogger(__name__)

# Populate lists from database on import
try:
    for royal in sql.get_superusers("sudos"):
        if royal.user_id not in SUDO_USERS:
            SUDO_USERS.append(royal.user_id)
    for support in sql.get_superusers("supports"):
        if support.user_id not in SUPPORT_USERS:
            SUPPORT_USERS.append(support.user_id)
    for wl in sql.get_superusers("whitelists"):
        if wl.user_id not in WHITELIST_USERS:
            WHITELIST_USERS.append(wl.user_id)
    for tiger in sql.get_superusers("tigers"):
        if tiger.user_id not in TIGER_USERS:
            TIGER_USERS.append(tiger.user_id)
except Exception as e:
    LOGGER.error(f"Error loading superusers from DB: {e}")

def check_user_id(user_id: int, bot) -> str | None:
    if not user_id:
        return "Nice try... Nope! Provide me a valid User ID."
    elif user_id == bot.id:
        return "This does not work that way."
    else:
        return None

@cutiepii_cmd(command='addsudo')
@dev_plus
@loggable
async def addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)
    
    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except TelegramError as e:
        await message.reply_text(f"Error fetching user: {e}")
        return ""

    rt = ""
    if user_id in SUDO_USERS:
        await message.reply_text("This member is already a Sudo user.")
        return ""

    if user_id in SUPPORT_USERS:
        rt += "Promoted from Support to Sudo.\n"
        SUPPORT_USERS.remove(user_id)

    if user_id in TIGER_USERS:
        rt += "Promoted from Tiger to Sudo.\n"
        TIGER_USERS.remove(user_id)

    if user_id in WHITELIST_USERS:
        rt += "Promoted from Whitelist to Sudo.\n"
        WHITELIST_USERS.remove(user_id)

    sql.set_superuser_role(user_id, "sudos")
    SUDO_USERS.append(user_id)

    await message.reply_text(
        rt + f"Successfully promoted {html.escape(user_member.first_name)} to Sudo!"
    )

    log_message = (
        f"#SUDO\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != "private":
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message

@cutiepii_cmd(command='addsupport')
@sudo_plus
@loggable
async def addsupport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)
    
    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except TelegramError as e:
        await message.reply_text(f"Error fetching user: {e}")
        return ""

    rt = ""
    if user_id in SUDO_USERS:
        await message.reply_text("This user is a Sudo user, they already have higher permissions!")
        return ""

    if user_id in SUPPORT_USERS:
        await message.reply_text("This member is already a Support user.")
        return ""

    if user_id in TIGER_USERS:
        rt += "Promoted from Tiger to Support.\n"
        TIGER_USERS.remove(user_id)

    if user_id in WHITELIST_USERS:
        rt += "Promoted from Whitelist to Support.\n"
        WHITELIST_USERS.remove(user_id)

    sql.set_superuser_role(user_id, "supports")
    SUPPORT_USERS.append(user_id)

    await message.reply_text(
        rt + f"Successfully promoted {html.escape(user_member.first_name)} to Support!"
    )

    log_message = (
        f"#SUPPORT\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != "private":
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message

@cutiepii_cmd(command='addtiger')
@sudo_plus
@loggable
async def addtiger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)
    
    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except TelegramError as e:
        await message.reply_text(f"Error fetching user: {e}")
        return ""

    rt = ""
    if user_id in SUDO_USERS or user_id in SUPPORT_USERS:
        await message.reply_text("This user already has higher permissions!")
        return ""

    if user_id in TIGER_USERS:
        await message.reply_text("This member is already a Tiger user.")
        return ""

    if user_id in WHITELIST_USERS:
        rt += "Promoted from Whitelist to Tiger.\n"
        WHITELIST_USERS.remove(user_id)

    sql.set_superuser_role(user_id, "tigers")
    TIGER_USERS.append(user_id)

    await message.reply_text(
        rt + f"Successfully promoted {html.escape(user_member.first_name)} to Tiger!"
    )

    log_message = (
        f"#TIGER\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != "private":
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message

@cutiepii_cmd(command='addwhitelist')
@sudo_plus
@loggable
async def addwhitelist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)
    
    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except TelegramError as e:
        await message.reply_text(f"Error fetching user: {e}")
        return ""

    if user_id in SUDO_USERS or user_id in SUPPORT_USERS or user_id in TIGER_USERS:
        await message.reply_text("This user already has higher permissions!")
        return ""

    if user_id in WHITELIST_USERS:
        await message.reply_text("This member is already a Whitelist user.")
        return ""

    sql.set_superuser_role(user_id, "whitelists")
    WHITELIST_USERS.append(user_id)

    await message.reply_text(
        f"Successfully promoted {html.escape(user_member.first_name)} to Whitelist!"
    )

    log_message = (
        f"#WHITELIST\n"
        f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
        f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
    )

    if chat.type != "private":
        log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

    return log_message

@cutiepii_cmd(command='removesudo')
@dev_plus
@loggable
async def removesudo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)
    
    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except TelegramError as e:
        await message.reply_text(f"Error fetching user: {e}")
        return ""

    if user_id in SUDO_USERS:
        SUDO_USERS.remove(user_id)
        sql.remove_superuser(user_id)

        await message.reply_text(f"Successfully demoted {html.escape(user_member.first_name)} to normal user.")

        log_message = (
            f"#UNSUDO\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != "private":
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        await message.reply_text("This user is not a Sudo user!")
        return ""

@cutiepii_cmd(command='removesupport')
@sudo_plus
@loggable
async def removesupport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)
    
    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except TelegramError as e:
        await message.reply_text(f"Error fetching user: {e}")
        return ""

    if user_id in SUPPORT_USERS:
        SUPPORT_USERS.remove(user_id)
        sql.remove_superuser(user_id)

        await message.reply_text(f"Successfully demoted {html.escape(user_member.first_name)} to normal user.")

        log_message = (
            f"#UNSUPPORT\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != "private":
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        await message.reply_text("This user is not a Support user!")
        return ""

@cutiepii_cmd(command='removetiger')
@sudo_plus
@loggable
async def removetiger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)
    
    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except TelegramError as e:
        await message.reply_text(f"Error fetching user: {e}")
        return ""

    if user_id in TIGER_USERS:
        TIGER_USERS.remove(user_id)
        sql.remove_superuser(user_id)

        await message.reply_text(f"Successfully demoted {html.escape(user_member.first_name)} to normal user.")

        log_message = (
            f"#UNTIGER\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != "private":
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        await message.reply_text("This user is not a Tiger user!")
        return ""

@cutiepii_cmd(command='removewhitelist')
@sudo_plus
@loggable
async def removewhitelist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    bot, args = context.bot, context.args
    user_id = await extract_user(message, args)
    
    reply = check_user_id(user_id, bot)
    if reply:
        await message.reply_text(reply)
        return ""

    try:
        user_member = await bot.get_chat(user_id)
    except TelegramError as e:
        await message.reply_text(f"Error fetching user: {e}")
        return ""

    if user_id in WHITELIST_USERS:
        WHITELIST_USERS.remove(user_id)
        sql.remove_superuser(user_id)

        await message.reply_text(f"Successfully removed {html.escape(user_member.first_name)} from Whitelist.")

        log_message = (
            f"#UNWHITELIST\n"
            f"<b>Admin:</b> {mention_html(user.id, html.escape(user.first_name))}\n"
            f"<b>User:</b> {mention_html(user_member.id, html.escape(user_member.first_name))}"
        )

        if chat.type != "private":
            log_message = f"<b>{html.escape(chat.title)}:</b>\n" + log_message

        return log_message
    else:
        await message.reply_text("This user is not a Whitelist user!")
        return ""

nations_text = """The bot has custom authentication levels:
\n<b>Dev (Developers)</b> - Users who have complete server access and can execute, edit, or modify bot code.
\n<b>God (Owner)</b> - The bot owner, who has complete, absolute access.
\n<b>Sudo Users</b> - Have super-user access. They can globally ban users, manage lower user levels, and act as bot admins.
\n<b>Support Users</b> - Have permission to globally ban scammers and bad users.
\n<b>Tiger Users</b> - Reserved specialized access.
\n<b>Whitelist Users</b> - Users exempted from spam limits and automated filters.
"""

@cutiepii_cmd(command='nations')
async def nations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        nations_text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )

@cutiepii_cmd(command='whitelistlist')
@whitelist_plus
async def whitelistlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    if not WHITELIST_USERS:
        await update.effective_message.reply_text("No Whitelisted users found.", parse_mode=ParseMode.HTML)
        return
    reply = "<b>Whitelist users:</b>\n"
    for each_user in WHITELIST_USERS:
        user_id = int(each_user)
        try:
            user = await bot.get_chat(user_id)
            reply += f"❍ {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            reply += f"❍ <code>{user_id}</code>\n"
    await update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)

@cutiepii_cmd(command='tigers')
@whitelist_plus
async def tigerlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    if not TIGER_USERS:
        await update.effective_message.reply_text("No Tiger users found.", parse_mode=ParseMode.HTML)
        return
    reply = "<b>Tiger users:</b>\n"
    for each_user in TIGER_USERS:
        user_id = int(each_user)
        try:
            user = await bot.get_chat(user_id)
            reply += f"❍ {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            reply += f"❍ <code>{user_id}</code>\n"
    await update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)

@cutiepii_cmd(command='supportlist')
@whitelist_plus
async def supportlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    if not SUPPORT_USERS:
        await update.effective_message.reply_text("No Support users found.", parse_mode=ParseMode.HTML)
        return
    reply = "<b>Support users:</b>\n"
    for each_user in SUPPORT_USERS:
        user_id = int(each_user)
        try:
            user = await bot.get_chat(user_id)
            reply += f"❍ {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            reply += f"❍ <code>{user_id}</code>\n"
    await update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)

@cutiepii_cmd(command='sudolist')
@whitelist_plus
async def sudolist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    true_sudo = list(set(SUDO_USERS) - set(DEV_USERS))
    if not true_sudo:
        await update.effective_message.reply_text("No sudo users found.", parse_mode=ParseMode.HTML)
        return
    reply = "<b>Sudo users:</b>\n"
    for each_user in true_sudo:
        user_id = int(each_user)
        try:
            user = await bot.get_chat(user_id)
            reply += f"❍ {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            reply += f"❍ <code>{user_id}</code>\n"
    await update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)

@cutiepii_cmd(command='devlist')
@whitelist_plus
async def devlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    true_dev = list(set(DEV_USERS) - {OWNER_ID})
    if not true_dev:
        await update.effective_message.reply_text("No Dev users found.", parse_mode=ParseMode.HTML)
        return
    reply = "<b>Dev users:</b>\n"
    for each_user in true_dev:
        user_id = int(each_user)
        try:
            user = await bot.get_chat(user_id)
            reply += f"❍ {mention_html(user_id, user.first_name)}\n"
        except TelegramError:
            reply += f"❍ <code>{user_id}</code>\n"
    await update.effective_message.reply_text(reply, parse_mode=ParseMode.HTML)

def get_help(chat):
    return (
        "Manage bot authentication level lists dynamically:\n\n"
        "❍ `/nations`: View the details of permission levels.\n"
        "❍ `/sudolist`: List Sudo users.\n"
        "❍ `/supportlist`: List Support users.\n"
        "❍ `/tigers`: List Tiger users.\n"
        "❍ `/whitelistlist`: List Whitelist users.\n"
        "❍ `/devlist`: List Dev users.\n\n"
        "<b>Admin commands:</b>\n"
        "❍ `/addsudo`: Promote user to Sudo (Dev only).\n"
        "❍ `/removesudo`: Demote user from Sudo (Dev only).\n"
        "❍ `/addsupport`: Promote user to Support (Sudo+ only).\n"
        "❍ `/removesupport`: Demote user from Support (Sudo+ only).\n"
        "❍ `/addtiger`: Promote user to Tiger (Sudo+ only).\n"
        "❍ `/removetiger`: Demote user from Tiger (Sudo+ only).\n"
        "❍ `/addwhitelist`: Promote user to Whitelist (Sudo+ only).\n"
        "❍ `/removewhitelist`: Demote user from Whitelist (Sudo+ only)."
    )

__mod_name__ = "Disasters"
