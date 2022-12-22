import html
import contextlib
import Cutiepii_Robot.modules.sql.welcome_sql as sql

from typing import Optional
from datetime import timedelta

from pytimeparse.timeparse import timeparse

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler
from telegram.constants import ParseMode
from telegram.helpers import mention_html

from Cutiepii_Robot.modules.log_channel import loggable

from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status
# from Cutiepii_Robot.modules.cron_jobs import j
from Cutiepii_Robot import LOGGER, CUTIEPII_PTB
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    bot_admin_check,
    AdminPerms,
)

# store job id in a dict to be able to cancel them later
RUNNING_RAIDS = {}  # {chat_id:job_id, ...}


def get_time(time: str) -> int:
    try:
        return timeparse(time)
    except BaseException:
        return 0


def get_readable_time(time: int) -> str:
    t = f"{timedelta(seconds=time)}".split(":")
    if time == 86400:
        return "1 day"
    return f"{t[0]} hour(s)" if time >= 3600 else f"{t[1]} minutes"


@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def setRaid(update: Update, context: CallbackContext) -> Optional[str]:
    args = context.args
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    if chat.type == "private":
        await context.bot.sendMessage(chat.id,
                                      "This command is not available in PMs.")
        return
    stat, time, acttime = sql.getRaidStatus(chat.id)
    readable_time = get_readable_time(time)
    if len(args) == 0:
        if stat:
            text = 'Raid mode is currently <code>Enabled</code>\nWould you like to <code>Disable</code> raid?'
            keyboard = [[
                InlineKeyboardButton(
                    "Disable Raid Mode",
                    callback_data=f"disable_raid={chat.id}={time}",
                ),
                InlineKeyboardButton("Cancel Action",
                                     callback_data="cancel_raid=1"),
            ]]

        else:
            text = f"Raid mode is currently <code>Disabled</code>\nWould you like to <code>Enable</code> " \
                   f"raid for {readable_time}?"
            keyboard = [[
                InlineKeyboardButton(
                    "Enable Raid Mode",
                    callback_data=f"enable_raid={chat.id}={time}",
                ),
                InlineKeyboardButton("Cancel Action",
                                     callback_data="cancel_raid=0"),
            ]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await msg.reply_text(text,
                             parse_mode=ParseMode.HTML,
                             reply_markup=reply_markup)

    elif args[0] == "off":
        if stat:
            sql.setRaidStatus(chat.id, False, time, acttime)
            #            j.scheduler.remove_job(RUNNING_RAIDS.pop(chat.id))
            text = "Raid mode has been <code>Disabled</code>, members that join will no longer be kicked."
            await msg.reply_text(text, parse_mode=ParseMode.HTML)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#RAID\n"
                f"Disabled\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")

    else:
        args_time = args[0].lower()
        if time := get_time(args_time):
            readable_time = get_readable_time(time)
            if 300 <= time < 86400:
                text = f"Raid mode is currently <code>Disabled</code>\nWould you like to <code>Enable</code> " \
                       f"raid for {readable_time}? "
                keyboard = [[
                    InlineKeyboardButton(
                        "Enable Raid",
                        callback_data=f"enable_raid={chat.id}={time}",
                    ),
                    InlineKeyboardButton("Cancel Action",
                                         callback_data="cancel_raid=0"),
                ]]

                reply_markup = InlineKeyboardMarkup(keyboard)
                await msg.reply_text(text,
                                     parse_mode=ParseMode.HTML,
                                     reply_markup=reply_markup)
            else:
                await msg.reply_text(
                    "You can only set time between 5 minutes and 1 day",
                    parse_mode=ParseMode.HTML)

        else:
            await msg.reply_text(
                "Unknown time given, give me something like 5m or 1h",
                parse_mode=ParseMode.HTML)


@connection_status
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def enable_raid_cb(update: Update,
                         ctx: CallbackContext) -> Optional[str]:
    args = await update.callback_query.data.replace("enable_raid=",
                                                    "").split("=")
    chat = update.effective_chat
    user = update.effective_user
    chat_id = args[0]
    time = int(args[1])
    readable_time = get_readable_time(time)
    _, t, acttime = sql.getRaidStatus(chat_id)
    sql.setRaidStatus(chat_id, True, time, acttime)
    await update.effective_message.edit_text(
        f"Raid mode has been <code>Enabled</code> for {readable_time}.",
        parse_mode=ParseMode.HTML)
    LOGGER.info("enabled raid mode in {} for {}".format(
        chat_id, readable_time))
    with contextlib.suppress(KeyError):
        oldRaid = RUNNING_RAIDS.pop(int(chat_id))
#        j.scheduler.remove_job(oldRaid)  # check if there was an old job

    def disable_raid(_):
        sql.setRaidStatus(chat_id, False, t, acttime)
        LOGGER.info(f"disbled raid mode in {chat_id}")
        ctx.bot.send_message(chat_id,
                             "Raid mode has been automatically disabled!")


#    raid = j.run_once(disable_raid, time)

    RUNNING_RAIDS[int(chat_id)] = raid.job.id
    return (f"<b>{html.escape(chat.title)}:</b>\n"
            f"#RAID\n"
            f"Enabled for {readable_time}\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")


@connection_status
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def disable_raid_cb(update: Update) -> Optional[str]:
    args = await update.callback_query.data.replace("disable_raid=",
                                                    "").split("=")
    chat = update.effective_chat
    user = update.effective_user
    chat_id = args[0]
    time = args[1]
    _, _, acttime = sql.getRaidStatus(chat_id)
    sql.setRaidStatus(chat_id, False, time, acttime)
    #    j.scheduler.remove_job(RUNNING_RAIDS.pop(int(chat_id)))
    await update.effective_message.edit_text(
        'Raid mode has been <code>Disabled</code>, newly joining members will no longer be kicked.',
        parse_mode=ParseMode.HTML,
    )
    logmsg = (f"<b>{html.escape(chat.title)}:</b>\n"
              f"#RAID\n"
              f"Disabled\n"
              f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
    return logmsg


@connection_status
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
async def disable_raid_cb(update: Update):
    args = update.callback_query.data.split("=")
    what = args[0]
    await update.effective_message.edit_text(
        f"Action cancelled, Raid mode will stay <code>{'Enabled' if what == 1 else 'Disabled'}</code>.",
        parse_mode=ParseMode.HTML)


@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def raidtime(update: Update, context: CallbackContext) -> Optional[str]:
    what, time, acttime = sql.getRaidStatus(update.effective_chat.id)
    args = context.args
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not args:
        await msg.reply_text(
            f"Raid mode is currently set to {get_readable_time(time)}\nWhen toggled, the raid mode will last "
            f"for {get_readable_time(time)} then turn off automatically",
            parse_mode=ParseMode.HTML)
        return
    args_time = args[0].lower()
    if time := get_time(args_time):
        readable_time = get_readable_time(time)
        if 300 <= time < 86400:
            text = f"Raid mode is currently set to {readable_time}\nWhen toggled, the raid mode will last for " \
                   f"{readable_time} then turn off automatically"
            await msg.reply_text(text, parse_mode=ParseMode.HTML)
            sql.setRaidStatus(chat.id, what, time, acttime)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#RAID\n"
                f"Set Raid mode time to {readable_time}\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
        await msg.reply_text(
            "You can only set time between 5 minutes and 1 day",
            parse_mode=ParseMode.HTML)
    else:
        await msg.reply_text(
            "Unknown time given, give me something like 5m or 1h",
            parse_mode=ParseMode.HTML)


@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@loggable
async def raidactiontime(update: Update,
                         context: CallbackContext) -> Optional[str]:
    what, t, time = sql.getRaidStatus(update.effective_chat.id)
    args = context.args
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not args:
        await msg.reply_text(
            f"Raid action time is currently set to {get_readable_time(time)}\nWhen toggled, the members that "
            f"join will be temp banned for {get_readable_time(time)}",
            parse_mode=ParseMode.HTML)
        return
    args_time = args[0].lower()
    if time := get_time(args_time):
        readable_time = get_readable_time(time)
        if 300 <= time < 86400:
            text = f"Raid action time is currently set to {get_readable_time(time)}\nWhen toggled, the members that" \
                   f" join will be temp banned for {readable_time}"
            await msg.reply_text(text, parse_mode=ParseMode.HTML)
            sql.setRaidStatus(chat.id, what, t, time)
            return (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#RAID\n"
                f"Set Raid mode action time to {readable_time}\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
        await msg.reply_text(
            "You can only set time between 5 minutes and 1 day",
            parse_mode=ParseMode.HTML)
    else:
        await msg.reply_text(
            "Unknown time given, give me something like 5m or 1h",
            parse_mode=ParseMode.HTML)


CUTIEPII_PTB.add_handler(CommandHandler("raid", setRaid))
CUTIEPII_PTB.add_handler(
    CallbackQueryHandler(enable_raid_cb, pattern=r"enable_raid="))
CUTIEPII_PTB.add_handler(
    CallbackQueryHandler(disable_raid_cb, pattern=r"disable_raid="))
CUTIEPII_PTB.add_handler(
    CallbackQueryHandler(disable_raid_cb, pattern=r"cancel_raid="))
CUTIEPII_PTB.add_handler(CommandHandler("raidtime", raidtime))
CUTIEPII_PTB.add_handler(CommandHandler("raidactiontime", raidactiontime))

__mod_name__ = "AntiRaid"
