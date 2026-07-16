import html
import asyncio
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from telethon.tl.functions.channels import EditBannedRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsKicked, ChannelParticipantsBanned
from telethon.errors import FloodWaitError

from Cutiepii_Robot import telethn, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd
from Cutiepii_Robot.modules.helper_funcs.chat_status import connection_status
from Cutiepii_Robot.modules.helper_funcs.admin_status import (
    bot_admin_check,
    user_admin_check,
    AdminPerms,
)

@cutiepii_cmd(command="unmuteall")
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
async def unmute_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message

    progress_message = await message.reply_text(
        f"🔍 <b>Finding muted users in</b> <code>{html.escape(chat.title)}</code>...",
        parse_mode=ParseMode.HTML
    )

    try:
        muted_users = []
        async for member in telethn.iter_participants(chat.id, filter=ChannelParticipantsBanned, aggressive=True):
            muted_users.append(member.id)

        if not muted_users:
            await progress_message.edit_text("<b>No muted members found in this chat.</b>", parse_mode=ParseMode.HTML)
            return

        await progress_message.edit_text(
            f"🔍 <b>Found</b> <code>{len(muted_users)}</code> <b>muted members in</b> <code>{html.escape(chat.title)}</code>.\n"
            "<b>Now unmuting them all...</b>",
            parse_mode=ParseMode.HTML
        )

        unmuted_count = 0
        rights = ChatBannedRights(
            until_date=0,
            send_messages=False,
        )

        for user_id in muted_users:
            try:
                await telethn(EditBannedRequest(chat.id, user_id, rights))
                unmuted_count += 1
            except FloodWaitError as ex:
                LOGGER.warning(f"FloodWait: sleeping for {ex.seconds} seconds")
                await asyncio.sleep(ex.seconds)
                try:
                    await telethn(EditBannedRequest(chat.id, user_id, rights))
                    unmuted_count += 1
                except Exception:
                    pass
            except Exception:
                pass

        await progress_message.edit_text(
            f"✅ <b>Successfully unmuted</b> <code>{unmuted_count}</code> <b>users!</b>",
            parse_mode=ParseMode.HTML
        )
        
        # Log to log channel
        import Cutiepii_Robot.modules.sql.log_channel_sql as log_sql
        log_channel = log_sql.get_chat_log_channel(chat.id)
        if log_channel:
            admin_user = update.effective_user
            admin_mention = f"<a href='tg://user?id={admin_user.id}'>{html.escape(admin_user.first_name)}</a>"
            log_txt = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNMUTEALL\n"
                f"👮 <b>Admin:</b> {admin_mention}\n"
                f"🔊 <b>Unmuted users:</b> <code>{unmuted_count}</code>"
            )
            try:
                await context.bot.send_message(log_channel, log_txt, parse_mode=ParseMode.HTML)
            except Exception as e:
                LOGGER.error(f"Failed to send unmuteall log: {e}")

    except Exception as e:
        LOGGER.exception(f"Error in unmuteall: {e}")
        await progress_message.edit_text(f"An error occurred: {str(e)}")


@cutiepii_cmd(command="unbanall")
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
async def unban_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message

    progress_message = await message.reply_text(
        f"🔍 <b>Finding banned users in</b> <code>{html.escape(chat.title)}</code>...",
        parse_mode=ParseMode.HTML
    )

    try:
        banned_users = []
        async for member in telethn.iter_participants(chat.id, filter=ChannelParticipantsKicked, aggressive=True):
            banned_users.append(member.id)

        if not banned_users:
            await progress_message.edit_text("<b>No banned members found in this chat.</b>", parse_mode=ParseMode.HTML)
            return

        await progress_message.edit_text(
            f"🔍 <b>Found</b> <code>{len(banned_users)}</code> <b>banned members in</b> <code>{html.escape(chat.title)}</code>.\n"
            "<b>Now unbanning them all...</b>",
            parse_mode=ParseMode.HTML
        )

        unbanned_count = 0
        rights = ChatBannedRights(until_date=0, view_messages=False)

        for user_id in banned_users:
            try:
                await telethn(EditBannedRequest(chat.id, user_id, rights))
                unbanned_count += 1
            except FloodWaitError as ex:
                LOGGER.warning(f"FloodWait: sleeping for {ex.seconds} seconds")
                await asyncio.sleep(ex.seconds)
                try:
                    await telethn(EditBannedRequest(chat.id, user_id, rights))
                    unbanned_count += 1
                except Exception:
                    pass
            except Exception:
                pass

        await progress_message.edit_text(
            f"✅ <b>Successfully unbanned</b> <code>{unbanned_count}</code> <b>users!</b>",
            parse_mode=ParseMode.HTML
        )
        
        # Log to log channel
        import Cutiepii_Robot.modules.sql.log_channel_sql as log_sql
        log_channel = log_sql.get_chat_log_channel(chat.id)
        if log_channel:
            admin_user = update.effective_user
            admin_mention = f"<a href='tg://user?id={admin_user.id}'>{html.escape(admin_user.first_name)}</a>"
            log_txt = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#UNBANALL\n"
                f"👮 <b>Admin:</b> {admin_mention}\n"
                f"🔓 <b>Unbanned users:</b> <code>{unbanned_count}</code>"
            )
            try:
                await context.bot.send_message(log_channel, log_txt, parse_mode=ParseMode.HTML)
            except Exception as e:
                LOGGER.error(f"Failed to send unbanall log: {e}")

    except Exception as e:
        LOGGER.exception(f"Error in unbanall: {e}")
        await progress_message.edit_text(f"An error occurred: {str(e)}")

__mod_name__ = "Mass Action"

__help__ = True
