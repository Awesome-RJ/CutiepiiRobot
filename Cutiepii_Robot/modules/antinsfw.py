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
import html
from telegram import Update, ChatMember
from telegram.ext import ContextTypes, MessageHandler, filters
from telegram.error import BadRequest

from Cutiepii_Robot import dispatcher, REDIS, LOGGER, arq
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_cmd, cutiepii_msg
from Cutiepii_Robot.modules.log_channel import loggable


async def is_nsfw_enabled(chat_id: int) -> bool:
    """Check if NSFW filter is enabled for a chat"""
    return REDIS.get(f"antinsfw_{chat_id}") == "true"


async def enable_nsfw(chat_id: int):
    """Enable NSFW filter for a chat"""
    REDIS.set(f"antinsfw_{chat_id}", "true")


async def disable_nsfw(chat_id: int):
    """Disable NSFW filter for a chat"""
    REDIS.delete(f"antinsfw_{chat_id}")


@cutiepii_msg(pattern=(filters.PHOTO | filters.Document.IMAGE) & filters.ChatType.GROUPS, group=10)
@loggable
async def check_nsfw_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check images for NSFW content"""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    
    if not await is_nsfw_enabled(chat.id):
        return None
    
    # Skip if user is admin
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            return None
    except BadRequest:
        pass
    
    # Get photo
    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document and message.document.mime_type and message.document.mime_type.startswith('image'):
        file_id = message.document.file_id
    else:
        return None
    
    log_text = None
    try:
        # Download image
        file = await context.bot.get_file(file_id)
        file_path = await file.download_to_drive()
        
        # Check using ARQ NSFW detection
        if arq:
            try:
                res = await arq.nsfw_scan(file=file_path)
                if res.ok and res.result.is_nsfw:
                    await message.delete()
                    
                    # Fetch settings
                    mode = REDIS.get(f"antinsfw_mode_{chat.id}") or "delete"
                    log_group = REDIS.get(f"antinsfw_log_{chat.id}") == "true"
                    
                    if mode == "warn":
                        try:
                            from Cutiepii_Robot.modules.warns import warn
                            await warn(user, update, "Automated NSFW Content Detection", message)
                        except Exception as e:
                            LOGGER.error(f"[ANTINSFW]: Failed to warn user: {e}")
                            
                    elif mode == "mute":
                        try:
                            from telegram import ChatPermissions
                            await chat.restrict_member(user.id, permissions=ChatPermissions(can_send_messages=False))
                            warn_msg = await context.bot.send_message(
                                chat.id,
                                f"<b>NSFW Content Detected</b>\n{user.mention_html()} has been muted permanently for sending NSFW content.",
                                parse_mode='HTML'
                            )
                            if not log_group:
                                async def delete_warn(job_context):
                                    try:
                                        await warn_msg.delete()
                                    except Exception:
                                        pass
                                context.job_queue.run_once(delete_warn, 10)
                        except Exception as e:
                            LOGGER.error(f"[ANTINSFW]: Failed to mute user: {e}")
                            
                    elif mode == "kick":
                        try:
                            await chat.ban_member(user.id)
                            await chat.unban_member(user.id)
                            warn_msg = await context.bot.send_message(
                                chat.id,
                                f"<b>NSFW Content Detected</b>\n{user.mention_html()} has been kicked for sending NSFW content.",
                                parse_mode='HTML'
                            )
                            if not log_group:
                                async def delete_warn(job_context):
                                    try:
                                        await warn_msg.delete()
                                    except Exception:
                                        pass
                                context.job_queue.run_once(delete_warn, 10)
                        except Exception as e:
                            LOGGER.error(f"[ANTINSFW]: Failed to kick user: {e}")
                            
                    elif mode == "ban":
                        try:
                            await chat.ban_member(user.id)
                            warn_msg = await context.bot.send_message(
                                chat.id,
                                f"<b>NSFW Content Detected</b>\n{user.mention_html()} has been banned for sending NSFW content.",
                                parse_mode='HTML'
                            )
                            if not log_group:
                                async def delete_warn(job_context):
                                    try:
                                        await warn_msg.delete()
                                    except Exception:
                                        pass
                                context.job_queue.run_once(delete_warn, 10)
                        except Exception as e:
                            LOGGER.error(f"[ANTINSFW]: Failed to ban user: {e}")
                            
                    else: # delete / default
                        warn_msg = await context.bot.send_message(
                            chat.id,
                            f"<b>NSFW Content Removed</b>\n{user.mention_html()}, NSFW content has been detected and removed. Please maintain appropriate content in this group.",
                            parse_mode='HTML'
                        )
                        if not log_group:
                            async def delete_warn(job_context):
                                try:
                                    await warn_msg.delete()
                                except Exception:
                                    pass
                            context.job_queue.run_once(delete_warn, 10)
                            
                    log_text = (
                        f"<b>{html.escape(chat.title)}:</b>\n"
                        f"#NSFW_CONTENT\n"
                        f"<b>Action:</b> {mode.capitalize()}\n"
                        f"<b>User:</b> {user.mention_html()}\n"
                        f"<b>User ID:</b> <code>{user.id}</code>"
                    )
            except Exception as e:
                LOGGER.warning(f"[ANTINSFW]: NSFW scan failed: {e}")
        
        # Clean up
        import os
        if os.path.exists(file_path):
            os.remove(file_path)
            
    except Exception as e:
        LOGGER.warning(f"[ANTINSFW]: Image download or scan failed: {e}")
        
    return log_text


@cutiepii_cmd(command="antinsfw", filters=filters.ChatType.GROUPS)
async def antinsfw_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enable/disable NSFW filter, set actions, and toggle group logging"""
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    args = context.args
    
    # Check if user is admin
    member = await context.bot.get_chat_member(chat.id, user.id)
    if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
        await message.reply_text("<b>Action Denied</b>\nYou do not have administrator privileges to run this command.", parse_mode='HTML')
        return
    
    status = "enabled" if await is_nsfw_enabled(chat.id) else "disabled"
    mode = REDIS.get(f"antinsfw_mode_{chat.id}") or "delete"
    log_status = "enabled" if REDIS.get(f"antinsfw_log_{chat.id}") == "true" else "disabled"
    
    if not args:
        await message.reply_text(
            f"<b>NSFW Filter Settings</b>\n"
            f"• <b>Status:</b> {status.capitalize()}\n"
            f"• <b>Action Mode:</b> {mode.capitalize()}\n"
            f"• <b>Group Chat Logging:</b> {log_status.capitalize()}\n\n"
            f"<b>Commands:</b>\n"
            f"• <code>/antinsfw [on|off]</code>: Enable/disable NSFW filter\n"
            f"• <code>/antinsfw mode [delete|warn|mute|kick|ban]</code>: Set detection action\n"
            f"• <code>/antinsfw log [on|off]</code>: Toggle persistent log in group chat",
            parse_mode='HTML'
        )
        return
        
    action = args[0].lower()
    
    if action in ["on", "yes", "enable"]:
        await enable_nsfw(chat.id)
        await message.reply_text(
            "<b>NSFW Filter Updated</b>\nNSFW filter has been enabled. Incoming media will be scanned and removed if inappropriate content is detected.",
            parse_mode='HTML'
        )
    elif action in ["off", "no", "disable"]:
        await disable_nsfw(chat.id)
        await message.reply_text("<b>NSFW Filter Updated</b>\nNSFW filter has been disabled.", parse_mode='HTML')
        
    elif action == "mode":
        if len(args) < 2:
            await message.reply_text("<b>Usage:</b>\n<code>/antinsfw mode [delete|warn|mute|kick|ban]</code>", parse_mode='HTML')
            return
        new_mode = args[1].lower()
        if new_mode in ["delete", "del", "warn", "mute", "kick", "ban"]:
            if new_mode == "del":
                new_mode = "delete"
            REDIS.set(f"antinsfw_mode_{chat.id}", new_mode)
            await message.reply_text(f"<b>NSFW Filter Updated</b>\nAction mode set to: <b>{new_mode.capitalize()}</b>.", parse_mode='HTML')
        else:
            await message.reply_text("<b>Invalid Mode</b>\nChoose one of: <code>delete</code>, <code>warn</code>, <code>mute</code>, <code>kick</code>, <code>ban</code>.", parse_mode='HTML')
            
    elif action == "log":
        if len(args) < 2:
            await message.reply_text("<b>Usage:</b>\n<code>/antinsfw log [on|off]</code>", parse_mode='HTML')
            return
        val = args[1].lower()
        if val in ["on", "yes", "enable", "true"]:
            REDIS.set(f"antinsfw_log_{chat.id}", "true")
            await message.reply_text("<b>NSFW Filter Updated</b>\nGroup chat logging has been enabled. Log messages will remain in the group.", parse_mode='HTML')
        elif val in ["off", "no", "disable", "false"]:
            REDIS.set(f"antinsfw_log_{chat.id}", "false")
            await message.reply_text("<b>NSFW Filter Updated</b>\nGroup chat logging has been disabled. Warning messages will be auto-deleted after 10 seconds.", parse_mode='HTML')
        else:
            await message.reply_text("<b>Usage:</b>\n<code>/antinsfw log [on|off]</code>", parse_mode='HTML')
    else:
        await message.reply_text("<b>Usage:</b>\n<code>/antinsfw [on|off]</code>\n<code>/antinsfw mode [delete|warn|mute|kick|ban]</code>\n<code>/antinsfw log [on|off]</code>", parse_mode='HTML')


# Handler registration


__mod_name__ = "Anti-NSFW"
__help__ = True
