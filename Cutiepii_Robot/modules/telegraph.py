import os
import html
import base64
import mimetypes
import httpx

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegraph import Telegraph

from Cutiepii_Robot import dispatcher, LOGGER, IMGBB_API_KEY
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd

babe = "Cutiepii_Robot"
telegraph = Telegraph(domain='graph.org')
try:
    r = telegraph.create_account(short_name=babe)
    auth_url = r["auth_url"]
except Exception as e:
    auth_url = None
    LOGGER.warning(f"Telegraph account setup failed: {e}")


def _is_image_file(file_path: str) -> bool:
    mime_type, _ = mimetypes.guess_type(file_path)
    return bool(mime_type and mime_type.startswith("image/"))


async def upload_to_catbox(file_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    file_name = os.path.basename(file_path)
    async with httpx.AsyncClient(timeout=60) as client:
        with open(file_path, "rb") as f:
            files = {"fileToUpload": (file_name, f, mime_type)}
            data = {"reqtype": "fileupload"}
            response = await client.post("https://catbox.moe/user/api.php", data=data, files=files)
            if response.status_code == 200:
                return response.text.strip()
            raise Exception(f"Catbox server error: status {response.status_code}")


async def upload_to_telegraph(file_path: str) -> str:
    async with httpx.AsyncClient(timeout=60) as client:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = await client.post("https://telegra.ph/upload", files=files)
            if response.status_code == 200:
                res_data = response.json()
                if isinstance(res_data, list) and len(res_data) > 0:
                    return f"https://telegra.ph{res_data[0]['src']}"
                raise Exception("Telegraph response format invalid")
            raise Exception(f"Telegraph server error: status {response.status_code}")


async def upload_to_imgbb(file_path: str) -> str:
    if not IMGBB_API_KEY:
        raise Exception("IMGBB API key is not configured")

    with open(file_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.imgbb.com/1/upload",
            data={"key": IMGBB_API_KEY, "image": image_b64},
        )
        if response.status_code != 200:
            raise Exception(f"ImgBB server error: status {response.status_code}")

        res_data = response.json()
        if not res_data.get("success"):
            error_msg = res_data.get("error", {}).get("message", "Unknown ImgBB error")
            raise Exception(error_msg)

        return res_data["data"]["url"]


async def upload_media(file_path: str) -> str:
    file_size = os.path.getsize(file_path)
    is_image = _is_image_file(file_path)
    errors = []

    if file_size < 5 * 1024 * 1024:
        try:
            return await upload_to_telegraph(file_path)
        except Exception as e:
            errors.append(f"Telegraph: {e}")
            LOGGER.warning(f"Telegraph upload failed: {e}")

    if is_image and IMGBB_API_KEY:
        try:
            return await upload_to_imgbb(file_path)
        except Exception as e:
            errors.append(f"ImgBB: {e}")
            LOGGER.warning(f"ImgBB upload failed: {e}")

    try:
        return await upload_to_catbox(file_path)
    except Exception as e:
        errors.append(f"Catbox: {e}")
        LOGGER.warning(f"Catbox upload failed: {e}")

    raise Exception("All upload providers failed. " + " | ".join(errors[-3:]))


@cutiepii_cmd(command="tgm")
async def tgm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not message.reply_to_message:
        await message.reply_text("Reply to a photo, video, audio, voice, animation, or document to upload it.")
        return

    reply = message.reply_to_message
    media_file = None

    if reply.photo:
        media_file = reply.photo[-1]
    elif reply.video:
        media_file = reply.video
    elif reply.audio:
        media_file = reply.audio
    elif reply.voice:
        media_file = reply.voice
    elif reply.animation:
        media_file = reply.animation
    elif reply.document:
        media_file = reply.document

    if not media_file:
        await message.reply_text("Reply to a photo, video, audio, voice, animation, or document to upload it.")
        return

    status = await message.reply_text("`Downloading file...`", parse_mode=ParseMode.MARKDOWN)

    try:
        file_obj = await context.bot.get_file(media_file.file_id)
        local_path = f"temp_upload_{media_file.file_id}"
        await file_obj.download_to_drive(custom_path=local_path)

        await status.edit_text("`Uploading to the API...`", parse_mode=ParseMode.MARKDOWN)

        public_link = await upload_media(local_path)

        if os.path.exists(local_path):
            os.remove(local_path)

        share_url = f"https://telegram.me/share/url?url={public_link}"
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Share Link", url=share_url)]
        ])

        await status.edit_text(
            f"✅ <b>File uploaded successfully</b>: <a href='{public_link}'>Link</a>",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )

    except Exception as e:
        LOGGER.exception(f"Error in /tgm: {e}")
        await status.edit_text(
            f"❌ Failed to upload media: <code>{html.escape(str(e)[:200])}</code>",
            parse_mode=ParseMode.HTML,
        )


@cutiepii_cmd(command="tgt")
async def tgt_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    content = ""
    title = f"Uploaded by {message.from_user.first_name}"

    if message.reply_to_message:
        if message.reply_to_message.text:
            content = message.reply_to_message.text
        elif message.reply_to_message.caption:
            content = message.reply_to_message.caption

    if not content and context.args:
        content = " ".join(context.args)

    if not content:
        await message.reply_text("Please reply to a text message or provide text after /tgt to upload.")
        return

    status = await message.reply_text("`Uploading text to Telegraph...`", parse_mode=ParseMode.MARKDOWN)

    try:
        formatted_content = content.replace("\n", "<br>")

        page = telegraph.create_page(
            title=title,
            html_content=formatted_content
        )

        public_link = f"https://graph.org/{page['path']}"
        share_url = f"https://telegram.me/share/url?url={public_link}"

        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Share Link", url=share_url)]
        ])

        await status.edit_text(
            f"✅ <b>Text uploaded successfully</b>: <a href='{public_link}'>Link</a>",
            parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
    except Exception as e:
        LOGGER.exception(f"Error in /tgt: {e}")
        await status.edit_text(f"❌ Failed to upload text: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)


@cutiepii_cmd(command="up")
async def up_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    url = ""
    if message.reply_to_message and message.reply_to_message.text:
        url = message.reply_to_message.text.strip()
    elif context.args:
        url = context.args[0].strip()

    if not url:
        await message.reply_text("Reply to a direct download link or provide it as an argument to upload it to Telegram.")
        return

    status = await message.reply_text("`Downloading from link...`", parse_mode=ParseMode.MARKDOWN)
    local_path = None

    try:
        file_name = url.split("/")[-1].split("?")[0]
        if not file_name or len(file_name) > 100:
            file_name = "downloaded_file"

        local_path = f"temp_up_{message.message_id}_{file_name}"

        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("GET", url, follow_redirects=True) as response:
                if response.status_code != 200:
                    await status.edit_text(f"❌ Failed to download file. Status code: {response.status_code}")
                    return
                with open(local_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)

        await status.edit_text("`Uploading to Telegram...`", parse_mode=ParseMode.MARKDOWN)

        if os.path.exists(local_path):
            with open(local_path, "rb") as f:
                await message.reply_document(
                    document=f,
                    caption=f"Uploaded By <b>@{context.bot.username}</b>",
                    parse_mode=ParseMode.HTML
                )
            os.remove(local_path)
            await status.delete()
        else:
            await status.edit_text("Failed to download file.")

    except Exception as e:
        LOGGER.exception(f"Error in /up: {e}")
        await status.edit_text(f"❌ Failed to upload: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass


@cutiepii_cmd(command=["transfersh", "transfer"])
async def transfersh_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not message.reply_to_message:
        await message.reply_text("Reply to a file/media message to upload it to Transfer.sh.")
        return

    reply = message.reply_to_message
    media_file = None
    file_name = "file"

    if reply.photo:
        media_file = reply.photo[-1]
        file_name = "photo.jpg"
    elif reply.video:
        media_file = reply.video
        file_name = reply.video.file_name or "video.mp4"
    elif reply.audio:
        media_file = reply.audio
        file_name = reply.audio.file_name or "audio.mp3"
    elif reply.voice:
        media_file = reply.voice
        file_name = "voice.ogg"
    elif reply.animation:
        media_file = reply.animation
        file_name = reply.animation.file_name or "animation.gif"
    elif reply.document:
        media_file = reply.document
        file_name = reply.document.file_name or "document"

    if not media_file:
        await message.reply_text("Reply to a valid media file/document to upload.")
        return

    status = await message.reply_text("`Downloading file...`", parse_mode=ParseMode.MARKDOWN)
    local_path = f"temp_tsh_{message.message_id}_{file_name}"

    try:
        file_obj = await context.bot.get_file(media_file.file_id)
        await file_obj.download_to_drive(custom_path=local_path)

        await status.edit_text("`Uploading to Transfer.sh...`", parse_mode=ParseMode.MARKDOWN)

        url = "https://transfer.sh/"
        async with httpx.AsyncClient(timeout=180) as client:
            with open(local_path, "rb") as f:
                response = await client.put(f"{url}{file_name}", content=f)
                if response.status_code == 200:
                    download_link = response.text.strip()
                else:
                    raise Exception(f"Server error: status {response.status_code}")

        if os.path.exists(local_path):
            os.remove(local_path)

        await status.edit_text(
            f"✅ <b>File uploaded successfully to Transfer.sh</b>\n\n"
            f"<b>Link:</b> <a href='{download_link}'>{download_link}</a>\n"
            f"<i>The link will be saved for 14 days.</i>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
    except Exception as e:
        LOGGER.exception(f"Error in /transfersh: {e}")
        await status.edit_text(f"❌ Failed to upload to Transfer.sh: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass


__mod_name__ = "Telegraph"

__help__ = True
