"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.
"""

import os
import html
import shutil
import tempfile
from PIL import Image
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, filters

from Cutiepii_Robot import dispatcher, LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd, cutiepii_msg

# Active PDF sessions stored in-memory
# format: {user_id: {"dir": temp_dir_path, "images": [image_paths]}}
PDF_SESSIONS = {}


# ========================================
# Helper functions
# ========================================

async def compile_pdf_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict, user_id: int):
    """Stitches collected images into a PDF and sends it back to the user."""
    message = update.effective_message
    
    if not session or not session.get("images"):
        await message.reply_text("<b>No Images</b>\nYou have not sent any images yet. Please send images first or use <code>/cancel</code> to abort.", parse_mode=ParseMode.HTML)
        return

    await message.reply_chat_action("upload_document")

    image_list = []
    for img_path in session["images"]:
        try:
            img = Image.open(img_path)
            # PDF requires RGB mode
            if img.mode != "RGB":
                img = img.convert("RGB")
            image_list.append(img)
        except Exception as e:
            LOGGER.warning(f"[PDF]: Error opening image {img_path}: {e}")

    if not image_list:
        await message.reply_text("<b>Error</b>\nCould not process any of the images sent. Please try sending clean photos or documents.", parse_mode=ParseMode.HTML)
        # Cleanup
        shutil.rmtree(session["dir"], ignore_errors=True)
        if user_id in PDF_SESSIONS:
            del PDF_SESSIONS[user_id]
        return

    try:
        pdf_path = os.path.join(session["dir"], f"converted_{user_id}.pdf")
        # Stitch all images into a single PDF
        image_list[0].save(pdf_path, save_all=True, append_images=image_list[1:])

        with open(pdf_path, "rb") as f:
            await message.reply_document(
                document=f,
                filename="converted_images.pdf",
                caption="<b>Converted PDF Document</b>",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        await message.reply_text(f"<b>Error</b>\nAn error occurred while compiling your PDF: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)
    finally:
        # Cleanup session data
        shutil.rmtree(session["dir"], ignore_errors=True)
        if user_id in PDF_SESSIONS:
            del PDF_SESSIONS[user_id]


# ========================================
# Command Handlers
# ========================================

@cutiepii_cmd(command="pdf", group=470)
async def pdf_converter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    # Case A: Reply to an image (photo or image document)
    if message.reply_to_message:
        reply = message.reply_to_message
        photo = reply.photo[-1] if reply.photo else None
        document = reply.document if reply.document and reply.document.mime_type and reply.document.mime_type.startswith("image/") else None
        
        file_id = None
        if photo:
            file_id = photo.file_id
        elif document:
            file_id = document.file_id

        if not file_id:
            await message.reply_text("<b>Invalid Target</b>\nPlease reply to an image (photo or document) to convert it to PDF.", parse_mode=ParseMode.HTML)
            return

        await message.reply_chat_action("upload_document")
        
        # Download and convert
        temp_dir = tempfile.mkdtemp()
        try:
            tg_file = await context.bot.get_file(file_id)
            img_path = os.path.join(temp_dir, "temp_img.jpg")
            await tg_file.download_to_drive(img_path)

            img = Image.open(img_path)
            if img.mode != "RGB":
                img = img.convert("RGB")

            pdf_path = os.path.join(temp_dir, "converted.pdf")
            img.save(pdf_path, "PDF")

            with open(pdf_path, "rb") as f:
                await message.reply_document(
                    document=f,
                    filename="converted_image.pdf",
                    caption="<b>Converted PDF Document</b>",
                    parse_mode=ParseMode.HTML
                )
        except Exception as e:
            await message.reply_text(f"<b>Error</b>\nAn error occurred while converting the image: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
        return

    # Case B: Multi-image session-based conversion
    if user.id in PDF_SESSIONS:
        # If user types /pdf during an active session, we treat it as "done" and compile
        await compile_pdf_and_send(update, context, PDF_SESSIONS[user.id], user.id)
    else:
        # Start new session
        temp_dir = tempfile.mkdtemp(prefix=f"pdf_{user.id}_")
        PDF_SESSIONS[user.id] = {
            "dir": temp_dir,
            "images": []
        }
        await message.reply_text(
            "<b>PDF Creation Session Started</b>\n\n"
            "Please send the images (either as photos or documents) you want to include in the PDF. "
            "When you are finished, type <code>/pdf</code> again or send <code>/done</code> to compile and receive your PDF document.\n\n"
            "<i>To cancel the session at any time, send <code>/cancel</code>.</i>",
            parse_mode=ParseMode.HTML
        )


@cutiepii_cmd(command="done", group=471)
async def pdf_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id in PDF_SESSIONS:
        await compile_pdf_and_send(update, context, PDF_SESSIONS[user.id], user.id)
    else:
        await update.effective_message.reply_text("<b>No Session</b>\nYou do not have an active PDF session. Type <code>/pdf</code> to start one.", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="cancel", group=472)
async def pdf_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if user.id in PDF_SESSIONS:
        session = PDF_SESSIONS[user.id]
        shutil.rmtree(session["dir"], ignore_errors=True)
        del PDF_SESSIONS[user.id]
        await message.reply_text("<b>Session Cancelled</b>\nThe PDF session has been cancelled and all temporary images have been deleted.", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("<b>No Session</b>\nYou do not have an active PDF session.", parse_mode=ParseMode.HTML)


# ========================================
# Message Handler (Collect Images during session)
# ========================================

@cutiepii_msg(filters.PHOTO | filters.Document.ALL, group=473)
async def pdf_image_collector(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user

    if not user or user.id not in PDF_SESSIONS:
        return

    session = PDF_SESSIONS[user.id]
    photo = message.photo[-1] if message.photo else None
    document = message.document if message.document and message.document.mime_type and message.document.mime_type.startswith("image/") else None

    file_id = None
    if photo:
        file_id = photo.file_id
    elif document:
        file_id = document.file_id

    if not file_id:
        return

    try:
        # Download image into session temp dir
        tg_file = await context.bot.get_file(file_id)
        img_path = os.path.join(session["dir"], f"img_{len(session['images']) + 1}.jpg")
        await tg_file.download_to_drive(img_path)
        
        session["images"].append(img_path)
        
        await message.reply_text(
            f"<b>Page {len(session['images'])} Added</b>\n\n"
            f"Send more images, or type <code>/pdf</code> or <code>/done</code> to compile your PDF.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await message.reply_text(f"<b>Error</b>\nFailed to process image: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)


__help__ = True

__mod_name__ = "PDF"
