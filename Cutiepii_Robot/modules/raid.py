import html
import Cutiepii_Robot.modules.sql.welcome_sql as sql

from typing import Optional
from datetime import timedelta

from pytimeparse.timeparse import timeparse

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, ChatPermissions
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, filters
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility
from telegram.helpers import mention_html

from Cutiepii_Robot.modules.log_channel import loggable

from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd
from Cutiepii_Robot.modules.cron_jobs import j
from Cutiepii_Robot import LOGGER, REDIS
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
    return "{} hour(s)".format(t[0]) if time >= 3600 else "{} minutes".format(t[1])


@cutiepii_cmd(command="raid", pass_args=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
async def setRaid(update: Update, context: CallbackContext) -> Optional[str]:
    args = context.args
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    if chat.type == "private":
        context.bot.sendMessage(chat.id, "<b>Action Denied</b>\nThis command can only be used in group chats.", parse_mode=ParseMode.HTML)
        return
    stat, time, acttime = sql.getRaidStatus(chat.id)
    readable_time = get_readable_time(time)
    if len(args) == 0:
        if stat:
            text = '<b>Raid Mode Status</b>\nRaid mode is currently <b>Enabled</b>.\n\nWould you like to <b>Disable</b> raid mode?'
            keyboard = [[
                InlineKeyboardButton("Disable Raid", callback_data="disable_raid={}={}".format(chat.id, time)),
                InlineKeyboardButton("Cancel", callback_data="cancel_raid=1"),
            ]]
        else:
            text = f"<b>Raid Mode Status</b>\nRaid mode is currently <b>Disabled</b>.\n\nWould you like to <b>Enable</b> raid mode for {readable_time}?"
            keyboard = [[
                InlineKeyboardButton("Enable Raid", callback_data="enable_raid={}={}".format(chat.id, time)),
                InlineKeyboardButton("Cancel", callback_data="cancel_raid=0"),
            ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)

    elif args[0] == "off":
        if stat:
            sql.setRaidStatus(chat.id, False, time, acttime)
            j.scheduler.remove_job(RUNNING_RAIDS.pop(int(chat.id)))
            text = "<b>Raid Mode Disabled</b>\nRaid mode has been disabled. Newly joining members will no longer be kicked."
            msg.reply_text(text, parse_mode=ParseMode.HTML)
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
                text = f"<b>Raid Mode Status</b>\nRaid mode is currently <b>Disabled</b>.\n\nWould you like to <b>Enable</b> raid mode for {readable_time}?"
                keyboard = [[
                    InlineKeyboardButton("Enable Raid", callback_data="enable_raid={}={}".format(chat.id, time)),
                    InlineKeyboardButton("Cancel", callback_data="cancel_raid=0"),
                ]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                msg.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
            else:
                msg.reply_text("<b>Error</b>\nYou can only set the raid duration between 5 minutes and 1 day.", parse_mode=ParseMode.HTML)

        else:
            msg.reply_text("<b>Error</b>\nInvalid duration format specified. Use formats like <code>5m</code> or <code>1h</code>.", parse_mode=ParseMode.HTML)


@cutiepii_callback(pattern="enable_raid=")
@connection_status
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True, noreply=True)
@loggable
async def enable_raid_cb(update: Update, ctx: CallbackContext) -> Optional[str]:
    args = update.callback_query.data.replace("enable_raid=", "").split("=")
    chat = update.effective_chat
    user = update.effective_user
    chat_id = args[0]
    time = int(args[1])
    readable_time = get_readable_time(time)
    _, t, acttime = sql.getRaidStatus(chat_id)
    sql.setRaidStatus(chat_id, True, time, acttime)
    update.effective_message.edit_text(f"<b>Raid Mode Enabled</b>\nRaid mode has been enabled for {readable_time}.",
                                       parse_mode=ParseMode.HTML)
    LOGGER.info("enabled raid mode in {} for {}".format(chat_id, readable_time))
    try:
        oldRaid = RUNNING_RAIDS.pop(int(chat_id))
        j.scheduler.remove_job(oldRaid)  # check if there was an old job
    except KeyError:
        pass

    def disable_raid(_):
        sql.setRaidStatus(chat_id, False, t, acttime)
        LOGGER.info("disbled raid mode in {}".format(chat_id))
        ctx.bot.send_message(chat_id, "<b>Raid Mode</b>\nRaid mode has been automatically disabled.", parse_mode=ParseMode.HTML)

    raid = j.run_once(disable_raid, time)
    RUNNING_RAIDS[int(chat_id)] = raid.job.id
    return (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#RAID\n"
        f"Enabled for {readable_time}\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
    )


@cutiepii_callback(pattern="disable_raid=")
@connection_status
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True, noreply=True)
@loggable
async def disable_raid_cb(update: Update, _: CallbackContext) -> Optional[str]:
    args = update.callback_query.data.replace("disable_raid=", "").split("=")
    chat = update.effective_chat
    user = update.effective_user
    chat_id = args[0]
    time = args[1]
    _, _, acttime = sql.getRaidStatus(chat_id)
    sql.setRaidStatus(chat_id, False, time, acttime)
    j.scheduler.remove_job(RUNNING_RAIDS.pop(int(chat_id)))
    update.effective_message.edit_text(
        '<b>Raid Mode Disabled</b>\nRaid mode has been disabled. Newly joining members will no longer be kicked.',
        parse_mode=ParseMode.HTML,
    )
    logmsg = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#RAID\n"
        f"Disabled\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
    )
    return logmsg


@cutiepii_callback(pattern="cancel_raid=")
@connection_status
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True, noreply=True)
async def disable_raid_cb(update: Update, _: CallbackContext):
    args = update.callback_query.data.split("=")
    what = args[0]
    update.effective_message.edit_text(
        f"<b>Action Cancelled</b>\nRaid mode status remains unchanged.",
        parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="raidtime")
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
async def raidtime(update: Update, context: CallbackContext) -> Optional[str]:
    what, time, acttime = sql.getRaidStatus(update.effective_chat.id)
    args = context.args
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not args:
        msg.reply_text(
            f"<b>Raid Duration Status</b>\nRaid duration is currently set to <code>{get_readable_time(time)}</code>.\n\nWhen enabled, raid mode will automatically turn off after this duration.",
            parse_mode=ParseMode.HTML)
        return
    args_time = args[0].lower()
    if time := get_time(args_time):
        readable_time = get_readable_time(time)
        if 300 <= time < 86400:
            text = f"<b>Raid Duration Updated</b>\nRaid duration has been set to <code>{readable_time}</code>."
            msg.reply_text(text, parse_mode=ParseMode.HTML)
            sql.setRaidStatus(chat.id, what, time, acttime)
            return (f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#RAID\n"
                    f"Set Raid mode time to {readable_time}\n"
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
        else:
            msg.reply_text("<b>Error</b>\nYou can only set the raid duration between 5 minutes and 1 day.", parse_mode=ParseMode.HTML)
    else:
        msg.reply_text("<b>Error</b>\nInvalid duration format specified. Use formats like <code>5m</code> or <code>1h</code>.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="raidactiontime", pass_args=True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods = True)
@loggable
async def raidtime(update: Update, context: CallbackContext) -> Optional[str]:
    what, t, time = sql.getRaidStatus(update.effective_chat.id)
    args = context.args
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not args:
        msg.reply_text(
            f"<b>Raid Temporary Ban Duration</b>\nRaid action temporary ban duration is currently set to <code>{get_readable_time(time)}</code>.",
            parse_mode=ParseMode.HTML)
        return
    args_time = args[0].lower()
    if time := get_time(args_time):
        readable_time = get_readable_time(time)
        if 300 <= time < 86400:
            text = f"<b>Raid Temporary Ban Duration Updated</b>\nTemporary ban duration for newly joining members has been set to <code>{readable_time}</code>."
            msg.reply_text(text, parse_mode=ParseMode.HTML)
            sql.setRaidStatus(chat.id, what, t, time)
            return (f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#RAID\n"
                    f"Set Raid mode action time to {readable_time}\n"
                    f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n")
        else:
            msg.reply_text("<b>Error</b>\nYou can only set the duration between 5 minutes and 1 day.", parse_mode=ParseMode.HTML)
    else:
        msg.reply_text("<b>Error</b>\nInvalid duration format specified. Use formats like <code>5m</code> or <code>1h</code>.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="raidmode", filters=filters.ChatType.GROUPS)
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, allow_mods=True)
async def raidmode_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if not args:
        val = REDIS.get(f"raidmode:{chat.id}")
        val = val.decode("utf-8") if val else "false"
        status = "ON" if val == "true" else "OFF"
        await message.reply_text(f"<b>Raid Mode Status</b>\nRaid Mode is currently: <code>{status}</code>", parse_mode=ParseMode.HTML)
        return

    action = args[0].lower().strip()
    if action in ["on", "yes", "enable"]:
        REDIS.set(f"raidmode:{chat.id}", "true")
        await message.reply_text("<b>Raid Mode Enabled</b>\nRaid mode has been enabled. Newly joining members will be restricted immediately.", parse_mode=ParseMode.HTML)
    elif action in ["off", "no", "disable"]:
        REDIS.set(f"raidmode:{chat.id}", "false")
        await message.reply_text("<b>Raid Mode Disabled</b>\nRaid mode has been disabled.", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("<b>Usage</b>\nUse <code>/raidmode [ON|OFF]</code> to toggle raid mode settings.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="lockdown", filters=filters.ChatType.GROUPS)
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, allow_mods=True)
async def lockdown_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    args = context.args

    if not args:
        val = REDIS.get(f"lockdown:{chat.id}")
        val = val.decode("utf-8") if val else "false"
        status = "ON" if val == "true" else "OFF"
        await message.reply_text(f"<b>Lockdown Status</b>\nLockdown is currently: <code>{status}</code>", parse_mode=ParseMode.HTML)
        return

    action = args[0].lower().strip()
    if action in ["on", "yes", "enable"]:
        REDIS.set(f"lockdown:{chat.id}", "true")
        await context.bot.set_chat_permissions(
            chat.id, ChatPermissions(can_send_messages=False)
        )
        await message.reply_text("<b>Lockdown Enabled</b>\nLockdown has been enabled. Members are restricted from sending messages or media.", parse_mode=ParseMode.HTML)
    elif action in ["off", "no", "disable"]:
        REDIS.set(f"lockdown:{chat.id}", "false")
        await context.bot.set_chat_permissions(
            chat.id, ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        await message.reply_text("<b>Lockdown Disabled</b>\nLockdown has been disabled. Members can now send messages and media.", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("<b>Usage</b>\nUse <code>/lockdown [ON|OFF]</code> to toggle lockdown settings.", parse_mode=ParseMode.HTML)


__help__ = True

__mod_name__ = "Raid Mode"
