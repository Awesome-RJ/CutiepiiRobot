"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.
"""
from Cutiepii_Robot.modules.helper_funcs.decorators import register


import os
import random
import re
import shutil
import subprocess
import tempfile
import requests
from telethon import events
from telethon.tl.functions.messages import SendMediaRequest
from telethon.tl.types import (
    InputMediaUploadedPhoto,
    InputMediaUploadedDocument,
    DocumentAttributeVideo,
    InputDocument,
)
from telegram.constants import ParseMode

from Cutiepii_Robot import telethn, application, LOGGER
from Cutiepii_Robot.events import register


# ========================================
# Helper Functions
# ========================================

def get_video_duration_and_size(video_path):
    """Retrieves duration, width, and height of video via ffprobe."""
    duration, w, h = 5, 1280, 720
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration:stream=width,height", "-of", "default=noprint_wrappers=1",
            video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        for line in result.stdout.splitlines():
            if "duration" in line:
                duration = int(float(line.split("=")[1]))
            elif "width" in line:
                w = int(line.split("=")[1])
            elif "height" in line:
                h = int(line.split("=")[1])
    except Exception as e:
        LOGGER.warning(f"[LIVEPHOTO]: ffprobe error: {e}")
    return duration, w, h


def extract_first_frame(video_path, output_image_path):
    """Extracts the first frame of a video using ffmpeg."""
    try:
        cmd = [
            "ffmpeg", "-y", "-i", video_path, "-vframes", "1", "-f", "image2", output_image_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except Exception as e:
        LOGGER.error(f"[LIVEPHOTO]: ffmpeg extract error: {e}")
        return False


def download_url(url, dest_path, max_size=10 * 1024 * 1024):
    """Downloads a URL to a local destination with a size limit check."""
    try:
        r = requests.get(url, stream=True, timeout=25)
        if r.status_code != 200:
            return False, f"Failed to download file (HTTP status: {r.status_code})"
        
        total_size = 0
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    total_size += len(chunk)
                    if total_size > max_size:
                        return False, "File exceeds the 10 MB limit."
                    f.write(chunk)
        return True, None
    except Exception as e:
        return False, str(e)


# ========================================
# Command Handler
# ========================================

@register(pattern="^/livephoto(?:@Cutiepii_Robot)?(.*)")
async def live_photo_cmd(event):
    if event.fwd_from:
        return

    reply = await event.get_reply_message()
    args = event.pattern_match.group(1).strip()
    chat = await event.get_input_chat()

    # Determine input sources
    video_input = None
    cover_input = None

    if reply and reply.video:
        video_input = "reply"
    elif args:
        parts = args.split("|")
        video_input = parts[0].strip()
        if len(parts) > 1:
            cover_input = parts[1].strip()
    
    if not video_input:
        await event.reply(
            "📸 <b>Live Photo Generator</b>\n\n"
            "<b>Usage:</b>\n"
            "❍ Reply to a video with <code>/livephoto</code>\n"
            "❍ <code>/livephoto [video URL / file_id]</code>\n"
            "❍ <code>/livephoto [video URL / file_id] | [cover URL / file_id]</code>\n\n"
            "<i>Note: Video must be ≤ 10 seconds and ≤ 10 MB.</i>",
            parse_mode="html"
        )
        return

    # Create temporary directory for downloads
    temp_dir = tempfile.mkdtemp(prefix="livephoto_")
    video_path = os.path.join(temp_dir, "video.mp4")
    cover_path = os.path.join(temp_dir, "cover.jpg")

    status_msg = await event.reply("⏳ <i>Processing your live photo, please wait...</i>", parse_mode="html")

    try:
        # Download Video
        if video_input == "reply":
            await event.client.download_media(reply.media, video_path)
        elif video_input.startswith("http://") or video_input.startswith("https://"):
            success, err = download_url(video_input, video_path)
            if not success:
                await status_msg.edit(f"❌ <b>Download Failed:</b> {err}", parse_mode="html")
                return
        else:
            # Assume file_id
            try:
                bot_file = await application.bot.get_file(video_input)
                await bot_file.download_to_drive(video_path)
            except Exception as e:
                await status_msg.edit(f"❌ <b>Failed to resolve video file_id:</b> {e}", parse_mode="html")
                return

        # Validate video size
        video_size = os.path.getsize(video_path)
        if video_size > 10 * 1024 * 1024:
            await status_msg.edit("❌ <b>Error:</b> Video size exceeds 10 MB limit.")
            return

        # Fetch video attributes
        duration, w, h = get_video_duration_and_size(video_path)
        if duration > 10:
            await status_msg.edit(f"❌ <b>Error:</b> Video duration ({duration}s) exceeds 10 seconds limit.")
            return

        # Download or Extract Cover
        if cover_input:
            if cover_input.startswith("http://") or cover_input.startswith("https://"):
                success, err = download_url(cover_input, cover_path)
                if not success:
                    await status_msg.edit(f"❌ <b>Download Cover Failed:</b> {err}", parse_mode="html")
                    return
            else:
                try:
                    bot_file = await application.bot.get_file(cover_input)
                    await bot_file.download_to_drive(cover_path)
                except Exception as e:
                    await status_msg.edit(f"❌ <b>Failed to resolve cover file_id:</b> {e}", parse_mode="html")
                    return
        else:
            # Extract first frame
            extracted = extract_first_frame(video_path, cover_path)
            if not extracted or not os.path.exists(cover_path):
                await status_msg.edit("❌ <b>Error:</b> Failed to extract video's cover frame.")
                return

        # 1. Upload video
        uploaded_video = await event.client.upload_file(video_path)

        # 2. Upload video as a temporary document to obtain standard Document object
        media_doc = await event.client(SendMediaRequest(
            peer=chat,
            media=InputMediaUploadedDocument(
                file=uploaded_video,
                mime_type="video/mp4",
                attributes=[DocumentAttributeVideo(duration=duration, w=w, h=h)]
            ),
            message="",
            random_id=random.randint(0, 2**31 - 1)
        ))

        # Retrieve Document object from sent message details
        video_document = None
        if hasattr(media_doc, "updates"):
            for u in media_doc.updates:
                if hasattr(u, "message") and u.message.media and hasattr(u.message.media, "document"):
                    video_document = u.message.media.document
                    # Immediately delete helper video message
                    try:
                        await event.client.delete_messages(chat, u.message.id)
                    except Exception:
                        pass
                    break

        if not video_document:
            await status_msg.edit("❌ <b>Error:</b> Failed to obtain video document ID.")
            return

        input_doc = InputDocument(
            id=video_document.id,
            access_hash=video_document.access_hash,
            file_reference=video_document.file_reference
        )

        # 3. Upload cover photo
        uploaded_photo = await event.client.upload_file(cover_path)

        # 4. Construct Live Photo
        live_photo_media = InputMediaUploadedPhoto(
            file=uploaded_photo,
            live_photo=True,
            video=input_doc
        )

        # 5. Send Live Photo and delete status message
        await event.client(SendMediaRequest(
            peer=chat,
            media=live_photo_media,
            message="📸 <b>Live Photo</b>",
            random_id=random.randint(0, 2**31 - 1)
        ))
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit(f"❌ <b>An error occurred:</b> {e}", parse_mode="html")
    finally:
        # Cleanup downloads
        shutil.rmtree(temp_dir, ignore_errors=True)


__help__ = True

__mod_name__ = "Live Photo"
