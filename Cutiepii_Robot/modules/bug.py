from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode, ChatType
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, filters

from Cutiepii_Robot import dispatcher, OWNER_ID, OWNER_USERNAME, SUPPORT_CHAT
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd


def content(text: str) -> [None, str]:
    if text is None:
        return None
    if " " not in text:
        return None
    try:
        return text.split(None, 1)[1]
    except IndexError:
        return None


@cutiepii_cmd(command="bug", filters=filters.ChatType.GROUPS)
async def bug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.username:
        chat_username = f"@{chat.username} / `{chat.id}`"
    else:
        chat_username = f"Private Group / `{chat.id}`"

    bugs = content(msg.text)
    user_id = user.id
    mention = f"[{user.first_name}](tg://user?id={user_id})"

    datetimes_fmt = "%d-%m-%Y"
    datetimes = datetime.utcnow().strftime(datetimes_fmt)

    bug_report = f"""
**#BUG : ** **@{OWNER_USERNAME}**
**From User : ** **{mention}**
**User ID : ** **{user_id}**
**Group : ** **{chat_username}**
**Bug Report : ** **{bugs}**
**Event Stamp : ** **{datetimes}**"""

    if user_id == OWNER_ID:
        if bugs:
            await msg.reply_text(
                "❎ <b>How can be owner bot reporting bug??</b>",
                parse_mode=ParseMode.HTML
            )
            return
        else:
            await msg.reply_text("Owner noob!")
    elif bugs:
        await msg.reply_text(
            f"<b>Bug Report : {html.escape(bugs)}</b>\n\n"
            "✅ <b>The bug was successfully reported to the support group!</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Close", callback_data="close_reply")]]
            ),
        )
 
        thumb = "https://i.pinimg.com/564x/f2/47/8b/f2478ba4e193470ebcdf61a2ad0f33ce.jpg"
 
        await context.bot.send_photo(
            SUPPORT_CHAT,
            photo=thumb,
            caption=bug_report,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "➡ View Bug", url=f"https://t.me/{chat.username}/{msg.message_id}" if chat.username else f"https://t.me/c/{str(chat.id)[4:]}/{msg.message_id}")
                    ],
                    [
                        InlineKeyboardButton(
                            "❌ Close", callback_data="close_send_photo")
                    ]
                ]
            )
        )
    else:
        await msg.reply_text("❎ <b>No bug to Report!</b>", parse_mode=ParseMode.HTML)
        

@cutiepii_callback(pattern="^close_reply$")
async def close_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.delete()


@cutiepii_callback(pattern="^close_send_photo$")
async def close_send_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    chat = query.message.chat
    
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if not getattr(member, "can_delete_messages", False) and user.id != OWNER_ID:
            return await query.answer(
                "You're not allowed to close this.", show_alert=True
            )
        else:
            await query.message.delete()
    except Exception:
        await query.answer("Failed to delete message.", show_alert=True)



__mod_name__ = "Bug"
