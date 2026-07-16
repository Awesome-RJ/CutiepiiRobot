import os
import html
import base64
import asyncio
import httpx
from io import BytesIO
from PIL import Image
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from Cutiepii_Robot import LOGGER
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd

LEXICA_UPSCALE_URLS = (
    "https://lexica.qewertyy.dev/upscale",
    "https://api.qewertyy.dev/upscale",
)


def _sanitize_error(error: Exception) -> str:
    text = str(error)
    if "<!doctype html" in text.lower() or "<html" in text.lower():
        return "Upscaling server is offline or unreachable."
    return text[:200]


def _is_valid_image(data: bytes) -> bool:
    if not data or len(data) < 12:
        return False
    head = data[:64].lstrip().lower()
    if head.startswith(b"<!doctype") or head.startswith(b"<html") or head.startswith(b"{"):
        return False
    return (
        data.startswith(b"\x89PNG\r\n\x1a\n")
        or data.startswith(b"\xff\xd8\xff")
        or (data.startswith(b"RIFF") and b"WEBP" in data[:16])
    )


def _pil_upscale(image_bytes: bytes, scale: int = 2) -> bytes:
    with Image.open(BytesIO(image_bytes)) as img:
        new_size = (img.width * scale, img.height * scale)
        upscaled = img.resize(new_size, Image.Resampling.LANCZOS)
        output = BytesIO()
        upscaled.save(output, format="PNG")
        return output.getvalue()


async def _lexica_upscale(image_bytes: bytes) -> bytes:
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    headers = {
        "User-Agent": "Cutiepii_Robot",
        "Content-Type": "application/json",
        "Accept": "image/*,application/octet-stream",
    }

    last_status = None
    async with httpx.AsyncClient(timeout=120) as client:
        for url in LEXICA_UPSCALE_URLS:
            try:
                response = await client.post(
                    url,
                    json={"format": "binary", "image_data": image_b64},
                    headers=headers,
                )
                last_status = response.status_code
                if response.status_code == 200 and _is_valid_image(response.content):
                    return response.content
            except httpx.HTTPError as e:
                last_status = getattr(getattr(e, "response", None), "status_code", None)
                LOGGER.debug("Upscale request failed for %s: %s", url, _sanitize_error(e))

    detail = f"status {last_status}" if last_status else "no response"
    raise Exception(f"Upscale service unavailable ({detail})")


@cutiepii_cmd(command=["upscale", "enhance"])
async def upscale_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    if not message.reply_to_message:
        await message.reply_text("Reply to an image to upscale it.")
        return

    reply = message.reply_to_message

    photo_file = None
    if reply.photo:
        photo_file = reply.photo[-1]
    elif reply.document and reply.document.mime_type in ("image/png", "image/jpg", "image/jpeg", "image/webp"):
        photo_file = reply.document

    if not photo_file:
        await message.reply_text("Reply to a valid image (photo or PNG/JPG document) to upscale it.")
        return

    status = await message.reply_text("`Upscaling your image...`", parse_mode=ParseMode.MARKDOWN)
    local_path = f"temp_upscale_{photo_file.file_id}"

    try:
        file_obj = await context.bot.get_file(photo_file.file_id)
        await file_obj.download_to_drive(custom_path=local_path)

        with open(local_path, "rb") as f:
            image_bytes = f.read()

        upscale_mode = "AI"
        try:
            upscaled_bytes = await _lexica_upscale(image_bytes)
        except Exception as e:
            LOGGER.debug("AI upscale unavailable, using local fallback: %s", _sanitize_error(e))
            upscaled_bytes = await asyncio.to_thread(_pil_upscale, image_bytes)
            upscale_mode = "Local 2x"

        if not _is_valid_image(upscaled_bytes):
            raise Exception("Upscale produced invalid image data")

        upscaled_file = f"upscaled_{message.message_id}.png"
        with open(upscaled_file, "wb") as f:
            f.write(upscaled_bytes)

        with open(upscaled_file, "rb") as f:
            await message.reply_document(
                document=f,
                caption=f"✨ <b>Image upscaled successfully!</b>\n<i>Mode:</i> {upscale_mode}",
                parse_mode=ParseMode.HTML,
            )

        if os.path.exists(upscaled_file):
            os.remove(upscaled_file)
        await status.delete()

    except Exception as e:
        LOGGER.error("Upscale failed: %s", _sanitize_error(e))
        await status.edit_text(
            "❌ <b>Failed to upscale image.</b>\n"
            "The upscaling service may be temporarily unavailable. Please try again later.",
            parse_mode=ParseMode.HTML,
        )
    finally:
        if os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass


__mod_name__ = "Upscale"

__help__ = True
