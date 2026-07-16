import html
from typing import Optional

from telegram import Update, ChatMemberUpdated
from telegram.constants import ParseMode
from telegram.ext import ChatMemberHandler, ContextTypes
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility

import Cutiepii_Robot.modules.sql.log_channel_sql as logsql
from Cutiepii_Robot import dispatcher
from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepiichatmember

import Cutiepii_Robot.modules.sql.logger_sql as sql


# Module to extract and log (optional: send to chat) status changes in chat members using ChatMemberUpdated
# https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/chatmemberbot.py

async def extract_status_change(chat_member_update: ChatMemberUpdated):
    try:
        status_change = chat_member_update.difference().get("status")
    except AttributeError:  # no change in status
        status_change = None

    try:
        title_change = chat_member_update.difference().get("custom_title")
    except AttributeError:  # no change in title
        title_change = None

    return status_change, title_change


async def do_announce(chat):  # announce to chat or only to log channel?
    return bool(chat.type != "channel" and sql.does_chat_log(chat.id))


def safe_mention_html(user):
    if not user:
        return "Unknown"
    name = getattr(user, "full_name", None) or getattr(user, "first_name", None) or f"User {user.id}"
    return f'<a href="tg://user?id={user.id}">{html.escape(name)}</a>'


@cutiepiichatmember()
@loggable
async def chatmemberupdates(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    chat = update.effective_chat
    message = update.effective_message
    log_setting = logsql.get_chat_setting(chat.id)
    if not log_setting:
        logsql.set_chat_setting(chat.id, True, True, True, True, True)
        log_setting = logsql.get_chat_setting(chat.id)
        
    result = await extract_status_change(update.chat_member)
    status_change, title_change = result

    if title_change is not None and status_change is None:  # extract title changes for admins
        oldtitle, newtitle = title_change
        cause_name = safe_mention_html(update.chat_member.from_user)
        member_name = safe_mention_html(update.chat_member.new_chat_member.user)
        if oldtitle != newtitle:

            if str(update.chat_member.from_user.id) == str(bot.id):  # bot action
                return ''  # we handle these in their respective modules
            else:

                if oldtitle is None:
                    if await do_announce(chat):
                        await update.effective_chat.send_message(
                            f"{member_name}'s title was set by {cause_name}.\nold title: {oldtitle}\nnew title: '<code>{newtitle}</code>'",
                            parse_mode=ParseMode.HTML,
                        )
                    log_message = (
                        f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#ADMIN\nTitle set\n"
                        f"<b>By Admin:</b> {cause_name}\n"
                        f"<b>To Admin:</b> {member_name}\n"
                        f"<b>Old Title:</b> {oldtitle}\n"
                        f"<b>New Title:</b> '<code>{newtitle}</code>'"
                    )
                    return log_message

                elif newtitle is None:
                    if await do_announce(chat):
                        await update.effective_chat.send_message(
                            f"{member_name}'s title was removed by {cause_name}.\nold title: '<code>{oldtitle}</code"
                            f">'\nnew title: {newtitle}",
                            parse_mode=ParseMode.HTML,
                        )
                    log_message = (
                        f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#ADMIN\nTitle removed\n"
                        f"<b>By Admin:</b> {cause_name}\n"
                        f"<b>To Admin:</b> {member_name}\n"
                        f"<b>Old Title:</b> '<code>{oldtitle}</code>'\n"
                        f"<b>New Title:</b> {newtitle}"
                    )
                    return log_message

                else:
                    if await do_announce(chat):
                        await update.effective_chat.send_message(
                            f"{member_name}'s title was changed by {cause_name}.\nold title: '<code>{oldtitle}</code"
                            f">'\nnew title: '<code>{newtitle}</code>'",
                            parse_mode=ParseMode.HTML,
                        )
                    log_message = (
                        f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#ADMIN\nTitle changed\n"
                        f"<b>By Admin:</b> {cause_name}\n"
                        f"<b>To Admin:</b> {member_name}\n"
                        f"<b>Old Title:</b> '<code>{oldtitle}</code>'\n"
                        f"<b>New Title:</b> '<code>{newtitle}</code>'"
                    )
                    return log_message

    if status_change is not None:  # exctract chat changes
        status = ','.join(status_change)
        oldstat = str(status.split(",")[0])
        newstat = str(status.split(",")[1])

        if str(update.chat_member.from_user.id) == str(bot.id):
            return ''  # we handle these in their respective modules same as before
        else:

            cause_name = safe_mention_html(update.chat_member.from_user)
            member_name = safe_mention_html(update.chat_member.new_chat_member.user)

            if oldstat == "administrator" and newstat == "member":
                if await do_announce(chat):
                    await update.effective_chat.send_message(
                        f"{member_name} was demoted by {cause_name}.",
                        parse_mode=ParseMode.HTML,
                    )

                if not log_setting.log_action:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#ADMIN\n<b>Demoted</b>\n"
                    f"<b>Admin:</b> {cause_name}\n"
                    f"<b>User:</b> {member_name}"
                )
                return log_message

            if oldstat == "administrator" and newstat == "kicked":
                if await do_announce(chat):
                    await update.effective_chat.send_message(
                        f"{member_name} was demoted and removed by {cause_name}.",
                        parse_mode=ParseMode.HTML,
                    )

                if not log_setting.log_action:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#BANNED\n"
                    f"#ADMIN\n<b>Demoted</b>\n"
                    f"<b>Admin:</b> {cause_name}\n"
                    f"<b>User:</b> {member_name}"
                )
                return log_message

            if oldstat == "administrator" and newstat == "left":

                if not log_setting.log_action:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#ADMIN\n<b>Left</b>\n"
                    f"<b>Admin:</b> {cause_name}\n"
                    f"<b>User:</b> {member_name}"
                )
                return log_message

            if oldstat != "administrator" and newstat == "administrator":
                if title_change is not None:
                    oldtitle, newtitle = title_change
                    if oldtitle != newtitle:
                        if await do_announce(chat):
                            await update.effective_chat.send_message(
                                f"{member_name} was promoted by {cause_name} with the title <code>{newtitle}</code>.",
                                parse_mode=ParseMode.HTML,
                            )

                        if not log_setting.log_action:
                            return ""

                        log_message = (
                            f"<b>{html.escape(chat.title)}:</b>\n"
                            f"#ADMIN\n<b>Promoted</b>\n"
                            f"<b>Admin:</b> {cause_name}\n"
                            f"<b>User:</b> {member_name}\n"
                            f"<b>Title:</b> '<code>{newtitle}</code>'"
                        )
                        return log_message

                else:
                    if await do_announce(chat):
                        await update.effective_chat.send_message(
                            f"{member_name} was promoted by {cause_name}.",
                            parse_mode=ParseMode.HTML,
                        )

                    if not log_setting.log_action:
                        return ""

                    log_message = (
                        f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#ADMIN\n<b>Promoted</b>\n"
                        f"<b>Admin:</b> {cause_name}\n"
                        f"<b>User:</b> {member_name}"
                    )
                    return log_message

            if oldstat != "restricted" and newstat == "restricted":
                if await do_announce(chat):
                    await update.effective_chat.send_message(
                        f"{member_name} was muted by {cause_name}.",
                        parse_mode=ParseMode.HTML,
                    )

                if not log_setting.log_action:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#MUTED\n"
                    f"<b>Admin:</b> {cause_name}\n"
                    f"<b>User:</b> {member_name}"
                )
                return log_message

            if oldstat == "restricted" and newstat != "restricted":
                if await do_announce(chat):
                    await update.effective_chat.send_message(
                        f"{member_name} was unmuted by {cause_name}.",
                        parse_mode=ParseMode.HTML,
                    )

                if not log_setting.log_action:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#UNMUTED\n"
                    f"<b>Admin:</b> {cause_name}\n"
                    f"<b>User:</b> {member_name}"
                )
                return log_message

        if str(update.chat_member.from_user.id) == str(bot.id):
            cause_name = safe_mention_html(message.from_user)
        else:
            cause_name = safe_mention_html(update.chat_member.from_user)

        if oldstat != "kicked" and newstat == "kicked":
            if await do_announce(chat):
                await update.effective_chat.send_message(
                    f"{member_name} was banned by {cause_name}.",
                    parse_mode=ParseMode.HTML,
                )

            if not log_setting.log_action:
                return ""

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#BANNED\n"
                f"<b>Admin:</b> {cause_name}\n"
                f"<b>User:</b> {member_name}"
            )
            return log_message

        if oldstat == "kicked" and newstat != "kicked":
            if await do_announce(chat):
                await update.effective_chat.send_message(
                    f"{member_name} was unbanned by {cause_name}.",
                    parse_mode=ParseMode.HTML,
                )

            if not log_setting.log_action:
                return ""

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNBANNED\n"
                f"<b>Admin:</b> {cause_name}\n"
                f"<b>User:</b> {member_name}"
            )
            return log_message

        if oldstat == "kicked" and newstat == "member":
            if await do_announce(chat):
                await update.effective_chat.send_message(
                    f"{member_name} was unbanned and added by {cause_name}.",
                    parse_mode=ParseMode.HTML,
                )

            if not log_setting.log_action:
                return ""

            log_message = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNBANNED\n"
                f"#WELCOME\n"
                f"<b>Admin:</b> {cause_name}\n"
                f"<b>User:</b> {member_name}"
            )
            return log_message

        if oldstat == ("left" or "kicked") and newstat == "member":
            if member_name == cause_name:

                if not log_setting.log_joins:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#WELCOME\n"
                    f"<b>User:</b> {member_name}\n"
                    f"<b>ID</b>: <code>{update.chat_member.new_chat_member.user.id}</code>"
                )
                return log_message

            else:
                if not log_setting.log_joins:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#WELCOME\n"
                    f"<b>User:</b> {member_name}\n"
                    f"<b>Added by:</b> {cause_name}\n"
                    f"<b>ID</b>: <code>{update.chat_member.new_chat_member.user.id}</code>"
                )
                return log_message

        if oldstat == ("member" or "administrator") and newstat == "left":
            if member_name == cause_name:

                if not log_setting.log_leave:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#GOODBYE\n"
                    f"<b>User:</b> {member_name}\n"
                    f"<b>ID</b>: <code>{update.chat_member.new_chat_member.user.id}</code>"
                )
                return log_message

            else:

                if not log_setting.log_leave:
                    return ""

                log_message = (
                    f"<b>{html.escape(chat.title)}:</b>\n"
                    f"#REMOVED\n"
                    f"<b>User:</b> {member_name}\n"
                    f"<b>Removed by:</b> {cause_name}\n"
                    f"<b>ID</b>: <code>{update.chat_member.new_chat_member.user.id}</code>"
                )
                return log_message


# Handler is registered automatically via @cutiepiichatmember decorator