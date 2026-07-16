import html

from telegram import Update
from telegram.ext import ContextTypes
CallbackContext = ContextTypes.DEFAULT_TYPE  # Alias for backward compatibility
from telegram.helpers import mention_html

from Cutiepii_Robot.modules.log_channel import loggable
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd

import Cutiepii_Robot.modules.sql.logger_sql as sql

from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    user_admin_check,
    AdminPerms,
)

@cutiepii_cmd(command="announce", pass_args=True)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@loggable
async def announcestat(update: Update, context: CallbackContext) -> str:
    args = context.args
    if len(args) > 0:
        u = update.effective_user
        message = update.effective_message
        chat = update.effective_chat
        user = update.effective_user
        if args[0].lower() in ["on", "yes", "true"]:
            sql.enable_chat_log(update.effective_chat.id)
            await update.effective_message.reply_text(
                "I've enabled announcements in this group. Now any admin actions in your group will be announced."
            )
            logmsg = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#ANNOUNCE_TOGGLED\n"
                f"Admin actions announcement has been <b>enabled</b>\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name) if not message.sender_chat else message.sender_chat.title}\n "
            )
            return logmsg
        elif args[0].lower() in ["off", "no", "false"]:
            sql.disable_chat_log(update.effective_chat.id)
            await update.effective_message.reply_text(
                "I've disabled announcements in this group. Now admin actions in your group will not be announced."
            )
            logmsg = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#ANNOUNCE_TOGGLED\n"
                f"Admin actions announcement has been <b>disabled</b>\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name) if not message.sender_chat else message.sender_chat.title}\n "
            )
            return logmsg
    else:
        await update.effective_message.reply_text(
            "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
            "Your current setting is: {}\n"
            "When True, any admin actions in your group will be announced."
            "When False, admin actions in your group will not be announced.".format(
                sql.does_chat_log(update.effective_chat.id))
        )
        return ''


async def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)

__mod_name__ = "Announce"

__help__ = True