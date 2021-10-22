"""
MIT License
Copyright (C) 2021 @NksamaX
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

import pytgcalls

from pyrogram import filters
from Cutiepii_Robot import pgram , musicbot


calls = pytgcalls.GroupCallFactory(musicbot).get_group_call()


@pgram.on_message(filters.command('play'))
async def play(_,message):
  try:
    await musicbot.start()
  except:
    pass
  reply = message.reply_to_message
  if reply:
    fk = await message.reply('Downloading....')
    path = await reply.download()
    await calls.join(message.chat.id)
    await calls.start_audio(path , repeat=False)
    await fk.edit('playing...')

    
@pgram.on_message(filters.command('vplay'))
async def vplay(_,message):
  try:
    await musicbot.start()
  except:
    pass
  reply = message.reply_to_message
  if reply:
    path = await reply.download()
    await calls.join(message.chat.id)
    await calls.start_video(path , repeat=False)
    await fk.edit('playing...')

@pgram.on_message(filters.command('leavevc'))
async def leavevc(_,message):
  await calls.stop()
  await calls.leave_current_group_call()

    
@pgram.on_message(filters.command('pause'))
async def pause(_,message):
  await calls.pause_stream()
