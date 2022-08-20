from datetime import datetime

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from Cutiepii_Robot import pgram, OWNER_ID, OWNER_USERNAME, SUPPORT_CHAT
from Cutiepii_Robot.utils.errors import capture_err


def content(msg: Message) -> [None, str]:
    text_to_return = msg.text

    if msg.text is None:
        return None
    if " " not in text_to_return:
        return None
    try:
        return msg.text.split(None, 1)[1]
    except IndexError:
        return None


@pgram.on_message(filters.command("bug"))
@capture_err
async def bug(_, msg: Message):
    if msg.chat.username:
        chat_username = (f"@{msg.chat.username} / `{msg.chat.id}`")
    else:
        chat_username = (f"Private Group / `{msg.chat.id}`")

    bugs = content(msg)
    user_id = msg.from_user.id
    mention = (
        f"[{msg.from_user.first_name}](tg://user?id={str(msg.from_user.id)}" +
        ")")

    datetimes_fmt = "%d-%m-%Y"
    datetimes = datetime.utcnow().strftime(datetimes_fmt)

    bug_report = f"""
**#BUG : ** **@{OWNER_USERNAME}**
**From User : ** **{mention}**
**User ID : ** **{user_id}**
**Group : ** **{chat_username}**
**Bug Report : ** **{bugs}**
**Event Stamp : ** **{datetimes}**"""

    if msg.chat.type == ChatType.PRIVATE:
        await msg.reply_text("❎ <b>This command only works in groups.</b>")
        return

    if user_id == OWNER_ID:
        if bugs:
            await msg.reply_text(
                "❎ <b>How can be owner bot reporting bug??</b>", )
            return
        await msg.reply_text("Owner noob!")
    elif bugs:
        await msg.reply_text(
            f"<b>Bug Report : {bugs}</b>\n\n"
            "✅ <b>The bug was successfully reported to the support group!</b>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Close",
                                       callback_data="close_reply")]]),
        )

        thumb = "https://i.pinimg.com/564x/f2/47/8b/f2478ba4e193470ebcdf61a2ad0f33ce.jpg"

        await pgram.send_photo(
            SUPPORT_CHAT,
            photo=thumb,
            caption=f"{bug_report}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("➡ View Bug", url=f"{msg.link}")],
                 [
                     InlineKeyboardButton("❌ Close",
                                          callback_data="close_send_photo")
                 ]]))
    else:
        await msg.reply_text("❎ <b>No bug to Report!</b>")


@pgram.on_callback_query(filters.regex("close_reply"))
async def close_reply(CallbackQuery):
    await CallbackQuery.message.delete()


@pgram.on_callback_query(filters.regex("close_send_photo"))
async def close_send_photo(_, CallbackQuery):
    is_Admin = await pgram.get_chat_member(CallbackQuery.message.chat.id,
                                           CallbackQuery.from_user.id)
    if not is_Admin.can_delete_messages:
        return await CallbackQuery.answer("You're not allowed to close this.",
                                          show_alert=True)
    await CallbackQuery.message.delete()


__mod_name__ = "Bug"
