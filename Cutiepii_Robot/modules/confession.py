"""
BSD 2-Clause License
Confession System Module
"""

import html
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from telegram.constants import ParseMode

from Cutiepii_Robot import dispatcher, LOGGER, SUDO_USERS, OWNER_ID
import Cutiepii_Robot.modules.sql.confession_sql as sql
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd, cutiepii_conversation, cutiepii_msg, cutiepii_precheckout
from Cutiepii_Robot.modules.helper_funcs.admin_status import user_admin_check, AdminPerms

CHOOSE_TARGET, CONFESS_CONTENT = range(2)


async def confess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    
    if chat.type != "private":
        bot_info = await context.bot.get_me()
        button = [[InlineKeyboardButton("Configure Confession", url=f"https://t.me/{bot_info.username}?start=confess")]]
        await message.reply_text(
            "<b>Private Message Required</b>\nAnonymous confessions can only be configured and sent via Private Messages (PM) for privacy reasons.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(button)
        )
        return ConversationHandler.END

    user = update.effective_user
    strikes = sql.get_strikes(user.id)
    if strikes >= 5:
        await message.reply_text(
            "<b>Access Denied</b>\nYou have been blocked from sending confessions due to reaching 5 report strikes.\n"
            "Please appeal in the support group to reset your strikes.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

    await message.reply_text(
        "<b>Anonymous Confession Wizard</b>\n\n"
        "Please provide the username (starting with @) or user/chat ID of the recipient "
        "(e.g., <code>@Awesome_RJ</code> or <code>5378543429</code> or a group username like <code>@GirlsBoyXD</code>):",
        parse_mode=ParseMode.HTML
    )
    return CHOOSE_TARGET


async def choose_target_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    target = message.text.strip()
    
    target_id = None
    target_name = target
    
    if target.startswith("@"):
        from Cutiepii_Robot.modules.users import get_user_id
        target_id = await get_user_id(target)
        if not target_id:
            try:
                chat = await context.bot.get_chat(target)
                target_id = chat.id
                target_name = chat.title or chat.first_name
            except Exception:
                pass
    else:
        try:
            target_id = int(target)
        except ValueError:
            pass
            
    if not target_id:
        await message.reply_text(
            "<b>Error</b>\nCould not resolve recipient. Please verify the username or ID and try again.\n"
            "Or type <code>/cancel</code> to exit the wizard.",
            parse_mode=ParseMode.HTML
        )
        return CHOOSE_TARGET

    if sql.is_confessions_blocked(target_id):
        await message.reply_text(
            "<b>Confessions Blocked</b>\nThis recipient (user or group) has blocked anonymous confessions.\n"
            "Wizard ended.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END

    try:
        chat_info = await context.bot.get_chat(target_id)
        is_group = chat_info.type in ["group", "supergroup"]
    except Exception:
        is_group = False

    if is_group:
        is_official = False
        if chat_info.username and chat_info.username.lower() == "girlsboyxd":
            is_official = True
            
        if not is_official:
            try:
                member = await context.bot.get_chat_member(target_id, update.effective_user.id)
                if member.status in ["left", "kicked"]:
                    await message.reply_text(
                        "<b>Membership Required</b>\nYou must be a member of the target group to post confessions to it.\n"
                        "Join the group and try again. Wizard ended.",
                        parse_mode=ParseMode.HTML
                    )
                    return ConversationHandler.END
            except Exception:
                await message.reply_text(
                    "<b>Verification Failed</b>\nCould not verify your membership in the target group. Make sure the bot is an administrator in that group. Wizard ended.",
                    parse_mode=ParseMode.HTML
                )
                return ConversationHandler.END

    context.user_data["confess_target_id"] = target_id
    context.user_data["confess_target_name"] = target_name
    context.user_data["confess_target_is_group"] = is_group

    await message.reply_text(
        f"<b>Target Set:</b> {html.escape(str(target_name))} [<code>{target_id}</code>]\n\n"
        "Please send the message or media (photo, video, voice note, sticker, etc.) you want to confess anonymously:",
        parse_mode=ParseMode.HTML
    )
    return CONFESS_CONTENT


async def confess_content_state(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    sender = update.effective_user
    
    target_id = context.user_data.get("confess_target_id")
    target_name = context.user_data.get("confess_target_name")
    
    if not target_id:
        await message.reply_text("<b>Error</b>\nSomething went wrong. Please start again with <code>/confess</code>.", parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    confession_id = sql.add_confession(sender.id, target_id)

    bot_info = await context.bot.get_me()
    keyboard = [
        [
            InlineKeyboardButton("Report Confession", url=f"https://t.me/{bot_info.username}?start=report_{confession_id}"),
            InlineKeyboardButton("Reveal Sender", url=f"https://t.me/{bot_info.username}?start=reveal_{confession_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    sent_msg = None
    caption_prefix = "<b>New Anonymous Confession Received</b>\n\n"
    
    try:
        if message.text:
            sent_msg = await context.bot.send_message(
                chat_id=target_id,
                text=f"{caption_prefix}{html.escape(message.text)}",
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        elif message.photo:
            photo_file_id = message.photo[-1].file_id
            caption = f"{caption_prefix}{html.escape(message.caption)}" if message.caption else caption_prefix
            sent_msg = await context.bot.send_photo(
                chat_id=target_id,
                photo=photo_file_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        elif message.video:
            caption = f"{caption_prefix}{html.escape(message.caption)}" if message.caption else caption_prefix
            sent_msg = await context.bot.send_video(
                chat_id=target_id,
                video=message.video.file_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        elif message.voice:
            caption = f"{caption_prefix}{html.escape(message.caption)}" if message.caption else caption_prefix
            sent_msg = await context.bot.send_voice(
                chat_id=target_id,
                voice=message.voice.file_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        elif message.audio:
            caption = f"{caption_prefix}{html.escape(message.caption)}" if message.caption else caption_prefix
            sent_msg = await context.bot.send_audio(
                chat_id=target_id,
                audio=message.audio.file_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        elif message.document:
            caption = f"{caption_prefix}{html.escape(message.caption)}" if message.caption else caption_prefix
            sent_msg = await context.bot.send_document(
                chat_id=target_id,
                document=message.document.file_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        elif message.sticker:
            await context.bot.send_message(
                chat_id=target_id,
                text=caption_prefix,
                parse_mode=ParseMode.HTML
            )
            sent_msg = await context.bot.send_sticker(
                chat_id=target_id,
                sticker=message.sticker.file_id,
                reply_markup=reply_markup
            )
        elif message.animation:
            caption = f"{caption_prefix}{html.escape(message.caption)}" if message.caption else caption_prefix
            sent_msg = await context.bot.send_animation(
                chat_id=target_id,
                animation=message.animation.file_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=reply_markup
            )
        else:
            await message.reply_text("<b>Unsupported Format</b>\nUnsupported message format. Please send text or standard media.", parse_mode=ParseMode.HTML)
            return CONFESS_CONTENT

    except Exception as e:
        await message.reply_text(f"<b>Delivery Failure</b>\nFailed to deliver confession: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)
        return ConversationHandler.END

    if sent_msg:
        sql.update_confession_message(confession_id, sent_msg.message_id)

    await message.reply_text("<b>Delivery Successful</b>\nYour anonymous confession has been delivered successfully!", parse_mode=ParseMode.HTML)
    return ConversationHandler.END


async def cancel_confess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("<b>Cancelled</b>\nConfession wizard cancelled.", parse_mode=ParseMode.HTML)
    return ConversationHandler.END


# ==========================================
# Commands: Block / Unblock Confessions
# ==========================================

@cutiepii_cmd(command=["blockconfessions", "blockconfess"])
async def block_confess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    
    if chat.type == "private":
        sql.block_confessions(user.id)
        await message.reply_text("<b>Confessions Blocked</b>\nYou will no longer receive anonymous confessions in private messages.", parse_mode=ParseMode.HTML)
    else:
        # Group chat: check admin status
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status not in ["administrator", "creator"]:
            await message.reply_text("<b>Action Denied</b>\nYou need to be an administrator to execute this command.", parse_mode=ParseMode.HTML)
            return
        sql.block_confessions(chat.id)
        await message.reply_text("<b>Confessions Blocked</b>\nAnonymous confessions are now blocked from being posted in this group.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command=["unblockconfessions", "unblockconfess"])
async def unblock_confess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    
    if chat.type == "private":
        sql.unblock_confessions(user.id)
        await message.reply_text("<b>Confessions Allowed</b>\nYou can now receive anonymous confessions in private messages.", parse_mode=ParseMode.HTML)
    else:
        # Group chat: check admin status
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status not in ["administrator", "creator"]:
            await message.reply_text("<b>Action Denied</b>\nYou need to be an administrator to execute this command.", parse_mode=ParseMode.HTML)
            return
        sql.unblock_confessions(chat.id)
        await message.reply_text("<b>Confessions Allowed</b>\nAnonymous confessions can now be posted in this group.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="resetreports")
async def reset_reports_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    args = context.args
    
    is_sudo = user.id in SUDO_USERS or user.id == OWNER_ID
    if not is_sudo:
        await message.reply_text("<b>Action Denied</b>\nYou do not have permission to execute this command.", parse_mode=ParseMode.HTML)
        return
        
    if not args:
        await message.reply_text("<b>Invalid Command Usage</b>\nUsage: <code>/resetreports [user_id]</code>", parse_mode=ParseMode.HTML)
        return
        
    try:
        target_user_id = int(args[0])
    except ValueError:
        await message.reply_text("<b>Invalid Argument</b>\nPlease provide a valid numeric user ID.", parse_mode=ParseMode.HTML)
        return
        
    success = sql.reset_strikes(target_user_id)
    if success:
        await message.reply_text(f"<b>Strikes Reset</b>\nReport strikes for user <code>{target_user_id}</code> have been reset to 0.", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("<b>Error</b>\nUser strikes record not found.", parse_mode=ParseMode.HTML)


# ==========================================
# Deep Link Intercept Handlers
# ==========================================

async def handle_report_deeplink(update: Update, context: ContextTypes.DEFAULT_TYPE, arg: str):
    message = update.effective_message
    user = update.effective_user
    
    try:
        confession_id = int(arg.split("_")[1])
    except (IndexError, ValueError):
        await message.reply_text("<b>Error</b>\nInvalid report link.", parse_mode=ParseMode.HTML)
        return
        
    conf = sql.get_confession(confession_id)
    if not conf:
        await message.reply_text("<b>Error</b>\nConfession not found.", parse_mode=ParseMode.HTML)
        return
        
    eligible = False
    if conf.receiver_id == user.id:
        eligible = True
    elif conf.receiver_id < 0:
        try:
            member = await context.bot.get_chat_member(conf.receiver_id, user.id)
            if member.status not in ["left", "kicked"]:
                eligible = True
        except Exception:
            pass
            
    if not eligible:
        await message.reply_text("<b>Action Denied</b>\nYou are not eligible to report this confession.", parse_mode=ParseMode.HTML)
        return
        
    keyboard = [
        [
            InlineKeyboardButton("Confirm Report", callback_data=f"report_conf:{confession_id}"),
            InlineKeyboardButton("Cancel", callback_data="report_cancel")
        ]
    ]
    await message.reply_text(
        "<b>Report Confession</b>\n\n"
        "Are you sure you want to report this anonymous confession as inappropriate?\n"
        "Reporting will issue a strike warning to the sender. Senders with 5 strikes are blocked.",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_reveal_deeplink(update: Update, context: ContextTypes.DEFAULT_TYPE, arg: str):
    message = update.effective_message
    user = update.effective_user
    
    try:
        confession_id = int(arg.split("_")[1])
    except (IndexError, ValueError):
        await message.reply_text("<b>Error</b>\nInvalid reveal link.", parse_mode=ParseMode.HTML)
        return
        
    conf = sql.get_confession(confession_id)
    if not conf:
        await message.reply_text("<b>Error</b>\nConfession not found.", parse_mode=ParseMode.HTML)
        return
        
    eligible = False
    if conf.receiver_id == user.id:
        eligible = True
    elif conf.receiver_id < 0:
        try:
            member = await context.bot.get_chat_member(conf.receiver_id, user.id)
            if member.status not in ["left", "kicked"]:
                eligible = True
        except Exception:
            pass
            
    if not eligible:
        await message.reply_text("<b>Action Denied</b>\nYou are not eligible to reveal this confession.", parse_mode=ParseMode.HTML)
        return
        
    if conf.is_revealed:
        try:
            sender_info = await context.bot.get_chat(conf.sender_id)
            sender_name = sender_info.first_name
            sender_username = f"@{sender_info.username}" if sender_info.username else "No Username"
        except Exception:
            sender_name = "User"
            sender_username = "N/A"
            
        await message.reply_text(
            "<b>Sender Identity Revealed</b>\n\n"
            f"- <b>Name:</b> {html.escape(sender_name)}\n"
            f"- <b>Username:</b> {sender_username}\n"
            f"- <b>User ID:</b> <code>{conf.sender_id}</code>",
            parse_mode=ParseMode.HTML
        )
        return
        
    prices = [LabeledPrice("Reveal Sender Identity", 5)]
    
    await context.bot.send_invoice(
        chat_id=user.id,
        title="Reveal Confession Sender",
        description="Pay 5 Telegram Stars to reveal the identity of this anonymous confession sender.",
        payload=f"reveal_{confession_id}",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="reveal-identity"
    )


# ==========================================
# Callback Handlers & Payment Callbacks
# ==========================================

@cutiepii_callback(pattern=r"^(report_conf:|report_cancel)")
async def report_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    if query.data.startswith("report_conf:"):
        confession_id = int(query.data.split(":")[1])
        conf = sql.get_confession(confession_id)
        
        if not conf:
            await query.answer("Confession not found.", show_alert=True)
            return
            
        strikes = sql.add_strike(conf.sender_id)
        await query.answer("Confession reported")
        await query.message.edit_text(
            f"<b>Report Confirmed</b>\nConfession reported successfully. Sender has been issued a warning strike. Total strikes: <code>{strikes}/5</code>.",
            parse_mode=ParseMode.HTML
        )
        
        try:
            if strikes >= 5:
                await context.bot.send_message(
                    chat_id=conf.sender_id,
                    text="<b>Confession Service Blocked</b>\n\n"
                         "You have reached 5 report strikes for inappropriate confessions.\n"
                         "You are now blocked from using the confession service. Appeal in the support group to get reset.",
                    parse_mode=ParseMode.HTML
                )
            else:
                await context.bot.send_message(
                    chat_id=conf.sender_id,
                    text="<b>Report Warning Strike Issued</b>\n\n"
                         "One of your anonymous confessions was reported as inappropriate.\n"
                         f"You have been issued a strike. Current strikes: {strikes}/5. Reaching 5 strikes will block your service.",
                    parse_mode=ParseMode.HTML
                )
        except Exception:
            pass
            
    elif query.data == "report_cancel":
        await query.answer()
        await query.message.edit_text("Report cancelled.")


@cutiepii_precheckout()
async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("reveal_"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Something went wrong.")


@cutiepii_msg(pattern=filters.SUCCESSFUL_PAYMENT)
async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    payload = payment.invoice_payload
    
    if payload.startswith("reveal_"):
        try:
            confession_id = int(payload.split("_")[1])
        except ValueError:
            return
            
        sql.reveal_confession(confession_id)
        conf = sql.get_confession(confession_id)
        if conf:
            try:
                sender_info = await context.bot.get_chat(conf.sender_id)
                sender_name = sender_info.first_name
                sender_username = f"@{sender_info.username}" if sender_info.username else "No Username"
            except Exception:
                sender_name = "User"
                sender_username = "N/A"
                
            await update.message.reply_text(
                "<b>Payment Successful: Identity Revealed</b>\n\n"
                f"- <b>Name:</b> {html.escape(sender_name)}\n"
                f"- <b>Username:</b> {sender_username}\n"
                f"- <b>User ID:</b> <code>{conf.sender_id}</code>",
                parse_mode=ParseMode.HTML
            )


# Conversation Handler for Confess Wizard
confess_wizard = ConversationHandler(
    entry_points=[
        CommandHandler("confess", confess_cmd),
        MessageHandler(filters.Regex("^/start confess$"), confess_cmd)
    ],
    states={
        CHOOSE_TARGET: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, choose_target_state)
        ],
        CONFESS_CONTENT: [
            MessageHandler(filters.ALL & ~filters.COMMAND, confess_content_state)
        ]
    },
    fallbacks=[
        CommandHandler("cancel", cancel_confess),
        MessageHandler(filters.Regex("^/cancel$"), cancel_confess)
    ]
)

# Register handlers to dispatcher dynamically when imported
cutiepii_conversation(confess_wizard)

__help__ = True
__mod_name__ = "Confession"
