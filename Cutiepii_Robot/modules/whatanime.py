"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import aiohttp
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd


@cutiepii_cmd(command="whatanime")
async def whatanime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Find anime from an image using trace.moe API"""
    message = update.effective_message
    
    if not message.reply_to_message:
        await message.reply_text("Reply to an image or GIF to search for anime!")
        return
    
    reply = message.reply_to_message
    
    if not (reply.photo or reply.animation or reply.document):
        await message.reply_text("Please reply to an image, GIF, or video!")
        return
    
    msg = await message.reply_text("Searching anime... Please wait...")
    
    try:
        # Get file
        if reply.photo:
            file = await context.bot.get_file(reply.photo[-1].file_id)
        elif reply.animation:
            file = await context.bot.get_file(reply.animation.file_id)
        elif reply.document:
            if not reply.document.mime_type.startswith('image'):
                await msg.edit_text("Please send an image file!")
                return
            file = await context.bot.get_file(reply.document.file_id)
        else:
            await msg.edit_text("Unsupported file type!")
            return
        
        # Download file
        file_path = await file.download_to_drive()
        
        # Read file as bytes
        with open(file_path, 'rb') as f:
            image_data = f.read()
        
        # Search using trace.moe API
        async with aiohttp.ClientSession() as session:
            form_data = aiohttp.FormData()
            form_data.add_field('image', image_data, filename='image.jpg')
            
            async with session.post('https://api.trace.moe/search', data=form_data) as resp:
                if resp.status != 200:
                    await msg.edit_text("API error! Please try again later.")
                    return
                
                result = await resp.json()

        if not isinstance(result, dict) or not result.get('result'):
            await msg.edit_text("No anime found! Try with a clearer image.")
            return

        results_list = result['result']
        if not results_list or not isinstance(results_list[0], dict):
            await msg.edit_text("No anime found! Try with a clearer image.")
            return

        # Get best match
        match = results_list[0]

        # Format response (API may return anilist as int ID or as dict with title)
        anime_title = match.get('filename', 'Unknown')
        anilist = match.get('anilist', {})
        if not isinstance(anilist, dict):
            anilist = {}
        title = anilist.get('title', {})
        if not isinstance(title, dict):
            title = {}

        english = title.get('english', '')
        romaji = title.get('romaji', '')
        native = title.get('native', '')

        episode = match.get('episode', 'Unknown')
        similarity = round(match.get('similarity', 0) * 100, 2)
        from_time = match.get('from', 0)
        to_time = match.get('to', 0)
        
        # Convert time to minutes:seconds
        def format_time(seconds):
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins:02d}:{secs:02d}"
        
        text = f"<b>Anime Found!</b>\n\n"
        if english:
            text += f"<b>Title (English):</b> {english}\n"
        if romaji:
            text += f"<b>Title (Romaji):</b> {romaji}\n"
        if native:
            text += f"<b>Title (Native):</b> {native}\n"
        
        text += f"<b>Episode:</b> {episode}\n"
        text += f"<b>Similarity:</b> {similarity}%\n"
        text += f"<b>Scene Timestamp:</b> {format_time(from_time)} - {format_time(to_time)}\n"
        
        # Get video preview if available
        video = match.get('video')
        
        if video and similarity > 85:
            # Send video preview
            await msg.delete()
            await message.reply_video(
                video,
                caption=text,
                parse_mode=ParseMode.HTML
            )
        else:
            # Send text only
            image_url = match.get('image')
            if image_url:
                await msg.delete()
                await message.reply_photo(
                    image_url,
                    caption=text,
                    parse_mode=ParseMode.HTML
                )
            else:
                await msg.edit_text(text, parse_mode=ParseMode.HTML)
        
        # Clean up downloaded file
        import os
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        await msg.edit_text(f"Error: {str(e)}\n\nPlease try again later.")


__mod_name__ = "WhatAnime"
__help__ = True
