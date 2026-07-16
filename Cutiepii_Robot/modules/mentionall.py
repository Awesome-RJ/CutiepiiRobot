import html
import asyncio
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.error import BadRequest
from telethon.tl.types import ChannelParticipantCreator, ChannelParticipantAdmin
from telethon.tl.functions.channels import GetParticipantRequest

from Cutiepii_Robot import dispatcher, telethn, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, cutiepii_msg

# Emojis for etagall
EMOJIS = [
    "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇", "🙂", "🙃", "😉", "😌", "😍", "🥰",
    "😘", "😗", "😙", "😚", "😋", "😛", "😝", "😜", "🤪", "🤨", "🧐", "🤓", "😎", "🤩", "🥳", "😏",
    "😒", "😞", "😔", "😟", "😕", "🙁", "☹️", "😣", "😖", "😫", "😩", "🥺", "😢", "😭", "😤", "😠",
    "😡", "🤬", "🤯", "😳", "🥵", "🥶", "😱", "😨", "😰", "😥", "😓", "🤗", "🤔", "🤭", "🤫", "🤥",
    "😶", "😐", "😑", "😬", "🙄", "😯", "😦", "😧", "😮", "😲", "🥱", "😴", "🤤", "😪", "😵", "🤐",
    "🥴", "🤢", "🤮", "🤧", "😷", "🤒", "🤕", "🤑", "🤠", "😈", "👿", "👹", "👺", "💀", "☠️", "👻",
    "👽", "👾", "🤖", "🎃", "😺", "😸", "😹", "😻", "😼", "😽", "🙀", "😿", "😾"
]

ACTIVE_TAGALLS = set()


async def check_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == chat.PRIVATE:
        return True
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def start_tagall_process(update: Update, context: ContextTypes.DEFAULT_TYPE, use_emojis: bool, custom_text: str):
    chat = update.effective_chat
    message = update.effective_message
    
    if chat.type == chat.PRIVATE:
        await message.reply_text("❌ This command can only be used in groups and channels.")
        return

    if not await check_admin(update, context):
        await message.reply_text("❌ Only admins can mention all!")
        return

    if chat.id in ACTIVE_TAGALLS:
        await message.reply_text("⚠️ There is already an active tagall process running in this chat. Send /cancel to stop it.")
        return

    ACTIVE_TAGALLS.add(chat.id)
    
    status_msg = await message.reply_text(
        "🔄 <b>Mentioning all users...</b>\nProgress: Starting...",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛑 Stop", callback_data=f"tagall_stop_{chat.id}")]
        ])
    )

    try:
        total_users = 0
        try:
            participants = await telethn.get_participants(chat.id, limit=1)
            total_users = getattr(participants, 'total', 100)
        except Exception:
            total_users = 100

        usrnum = 0
        usrtxt = ""
        total_processed = 0

        async for usr in telethn.iter_participants(chat.id):
            if chat.id not in ACTIVE_TAGALLS:
                break

            if usr.bot or usr.deleted:
                continue

            total_processed += 1
            usrnum += 1

            if use_emojis:
                emoji = random.choice(EMOJIS)
                usrtxt += f"<a href='tg://user?id={usr.id}'>{emoji}</a> "
            else:
                usrtxt += f"<a href='tg://user?id={usr.id}'>{html.escape(usr.first_name)}</a> "

            if usrnum == 5:
                txt = f"{usrtxt}\n\n{html.escape(custom_text)}"
                if message.reply_to_message:
                    try:
                        await message.reply_to_message.reply_text(txt, parse_mode=ParseMode.HTML)
                    except Exception:
                        await context.bot.send_message(chat.id, txt, parse_mode=ParseMode.HTML)
                else:
                    await context.bot.send_message(chat.id, txt, parse_mode=ParseMode.HTML)

                try:
                    await status_msg.edit_text(
                        f"🔄 <b>Mentioning all users...</b>\n"
                        f"Progress: Mentioned {total_processed} of {total_users} users.",
                        parse_mode=ParseMode.HTML,
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🛑 Stop", callback_data=f"tagall_stop_{chat.id}")]
                        ])
                    )
                except Exception:
                    pass

                await asyncio.sleep(1.5)
                usrnum = 0
                usrtxt = ""

        if usrnum > 0 and chat.id in ACTIVE_TAGALLS:
            txt = f"{usrtxt}\n\n{html.escape(custom_text)}"
            if message.reply_to_message:
                try:
                    await message.reply_to_message.reply_text(txt, parse_mode=ParseMode.HTML)
                except Exception:
                    await context.bot.send_message(chat.id, txt, parse_mode=ParseMode.HTML)
            else:
                await context.bot.send_message(chat.id, txt, parse_mode=ParseMode.HTML)

        if chat.id in ACTIVE_TAGALLS:
            ACTIVE_TAGALLS.remove(chat.id)
            await status_msg.edit_text(f"✅ <b>Mentioning completed.</b>\nTotal mentioned: {total_processed} users.", parse_mode=ParseMode.HTML)
        else:
            await status_msg.edit_text(f"🛑 <b>Mentioning stopped.</b>\nTotal mentioned: {total_processed} users.", parse_mode=ParseMode.HTML)

    except Exception as e:
        ACTIVE_TAGALLS.discard(chat.id)
        LOGGER.exception(f"Error in tagall: {e}")
        try:
            await status_msg.edit_text(f"❌ <b>An error occurred during tagall:</b>\n<code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)
        except Exception:
            pass


@cutiepii_cmd(command=["tagall", "tall", "call", "all", "mentionall", "etagall", "everyone"])
async def tagall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    text = message.text.split()[0].lower()
    
    use_emojis = "etagall" in text
    
    custom_text = "Hey! Wake up! 📣"
    if context.args:
        custom_text = " ".join(context.args)
    elif message.reply_to_message and (message.reply_to_message.text or message.reply_to_message.caption):
        custom_text = message.reply_to_message.text or message.reply_to_message.caption
        
    await start_tagall_process(update, context, use_emojis, custom_text)


@cutiepii_cmd(command=["cancel", "stoptagall", "stoptall"])
async def tagall_cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    
    if not await check_admin(update, context):
        await message.reply_text("❌ Only admins can stop tagall!")
        return
        
    if chat.id in ACTIVE_TAGALLS:
        ACTIVE_TAGALLS.remove(chat.id)
        await message.reply_text("🛑 <b>Tagall stopped.</b>", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("No active tagall process found in this chat.")


@cutiepii_callback(pattern=r"^tagall_stop_")
async def tagall_stop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    chat_id = int(query.data.split("_")[2])
    user = query.from_user
    
    try:
        member = await context.bot.get_chat_member(chat_id, user.id)
        is_admin = member.status in ("administrator", "creator")
    except Exception:
        is_admin = False
        
    if not is_admin:
        await query.answer("❌ Only admins can stop tagall!", show_alert=True)
        return
        
    if chat_id in ACTIVE_TAGALLS:
        ACTIVE_TAGALLS.remove(chat_id)
        await query.answer("Tagall stopped successfully.")
    else:
        await query.answer("No active tagall process found.")


@cutiepii_msg(pattern=filters.ChatType.GROUPS & filters.Regex(r"(?i)^@(all|eall)"), group=11)
async def tagall_regex_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    text = message.text.strip()
    
    if text.lower().startswith("@eall"):
        use_emojis = True
        custom_text = text[5:].strip()
    else:
        use_emojis = False
        custom_text = text[4:].strip()
        
    if not custom_text:
        custom_text = "Hey! Wake up! 📣"
        
    await start_tagall_process(update, context, use_emojis, custom_text)



__mod_name__ = "Tag All"

__help__ = True
