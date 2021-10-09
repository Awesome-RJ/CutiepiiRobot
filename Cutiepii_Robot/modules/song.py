"""
MIT License

Copyright (C) 2021 Awesome-RJ

This file is part of @Cutiepii_Robot (Telegram Bot)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import asyncio
import time
import os
import json

from telethon.tl.types import DocumentAttributeAudio
from Cutiepii_Robot.events import register
from Cutiepii_Robot.utils.progress import progress
from youtube_dl import YoutubeDL
from youtube_dl.utils import (DownloadError, ContentTooShortError,

                              ExtractorError, GeoRestrictedError,
                              MaxDownloadsReached, PostProcessingError,
                              UnavailableVideoError, XAttrMetadataError)
try:
   from youtubesearchpython import SearchVideos 

except:
	os.system("pip install pip install youtube-search-python")
	from youtubesearchpython import SearchVideos 

#@register(pattern="^/song (.*)")
async def download_video(v_url):

   lazy = v_url
   sender = await lazy.get_sender()
   me = await lazy.client.get_me()

   if sender.id != me.id:
      rkp = await lazy.reply("`processing...`")
   else:
      rkp = await lazy.edit("`processing...`")
   url = v_url.pattern_match.group(1)
   if not url:
        return await rkp.edit("`Error \nusage song <song name>`")
   search = SearchVideos(url, offset = 1, mode = "json", max_results = 1)
   test = search.result()
   p = json.loads(test)
   q = p.get('search_result')
   try:
      url = q[0]['link']
   except:
   	return await rkp.edit("`failed to find`")
   type = "audio"
   await rkp.edit("`Preparing to download...`")
   if type == "audio":
       opts = {
           'format':
           'bestaudio',
           'addmetadata':
           True,
           'key':
           'FFmpegMetadata',
           'writethumbnail':
           True,
           'prefer_ffmpeg':
           True,
           'geo_bypass':
           True,
           'nocheckcertificate':
           True,
           'postprocessors': [{
               'key': 'FFmpegExtractAudio',
               'preferredcodec': 'mp3',
               'preferredquality': '320',
           }],
           'outtmpl':
           '%(id)s.mp3',
           'quiet':
           True,
           'logtostderr':
           False
       }
       video = False
       song = True
   try:
       await rkp.edit("`Fetching data, please wait..`")
       with YoutubeDL(opts) as rip:
           rip_data = rip.extract_info(url)
   except DownloadError as DE:
       await rkp.edit(f"`{str(DE)}`")
       return
   except ContentTooShortError:
       await rkp.edit("`The download content was too short.`")
       return
   except GeoRestrictedError:
       await rkp.edit(
           "`Video is not available from your geographic location due to geographic restrictions imposed by a website.`"
       )
       return
   except MaxDownloadsReached:
       await rkp.edit("`Max-downloads limit has been reached.`")
       return
   except PostProcessingError:
       await rkp.edit("`There was an error during post processing.`")
       return
   except UnavailableVideoError:
       await rkp.edit("`Media is not available in the requested format.`")
       return
   except XAttrMetadataError as XAME:
       await rkp.edit(f"`{XAME.code}: {XAME.msg}\n{XAME.reason}`")
       return
   except ExtractorError:
       await rkp.edit("`There was an error during info extraction.`")
       return
   except Exception as e:
       await rkp.edit(f"{str(type(e)): {str(e)}}")
       return
   c_time = time.time()
   if song:
       await rkp.edit(f"`Preparing to upload song:`\
        \n**{rip_data['title']}**\
        \nby *{rip_data['uploader']}*")
       await v_url.client.send_file(
           v_url.chat_id,
           f"{rip_data['id']}.mp3",
           supports_streaming=True,
           attributes=[
               DocumentAttributeAudio(duration=int(rip_data['duration']),
                                      title=str(rip_data['title']),
                                      performer=str(rip_data['uploader']))
           ],
           progress_callback=lambda d, t: asyncio.get_event_loop(
           ).create_task(
               progress(d, t, v_url, c_time, "Uploading..",
                        f"{rip_data['title']}.mp3")))
       os.remove(f"{rip_data['id']}.mp3")
   elif video:
       await rkp.edit(f"`Preparing to upload song :`\
        \n**{rip_data['title']}**\
        \nby *{rip_data['uploader']}*")
       await v_url.client.send_file(
           v_url.chat_id,
           f"{rip_data['id']}.mp4",
           supports_streaming=True,
           caption=url,
           progress_callback=lambda d, t: asyncio.get_event_loop(
           ).create_task(
               progress(d, t, v_url, c_time, "Uploading..",
                        f"{rip_data['title']}.mp4")))
       os.remove(f"{rip_data['id']}.mp4")

__mod_name__ = "Music"
