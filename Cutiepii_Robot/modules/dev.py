"""
BSD 2-Clause License

Copyright (C) 2017-2019, Paul Larsen
Copyright (c) 2021-2026, Awesome-RJ, <https://github.com/Awesome-RJ>
Copyright (c) 2021-2026, Yūki - Black Knights Union, <https://github.com/Awesome-RJ/CutiepiiRobot>

All rights reserved.

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

from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback, cutiepii_cmd
import re
import os
import subprocess
import sys
import asyncio
import shlex
from typing import Optional
from contextlib import suppress
from statistics import mean
from time import monotonic as time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.error import Forbidden
from telethon import events

from Cutiepii_Robot import dispatcher, DEV_USERS, telethn, OWNER_ID, ALLOW_CHATS, LOGGER
from Cutiepii_Robot.modules.helper_funcs.chat_status import dev_plus


@cutiepii_callback(pattern=r"leavechat_cb_")
async def leave_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback for leave chat confirmation"""
    try:
        callback = update.callback_query
        
        if callback.from_user.id not in DEV_USERS:
            await callback.answer(text="This action is not authorized.", show_alert=True)
            return
        
        match = re.match(r"leavechat_cb_\((.+?)\)", callback.data)
        if not match:
            await callback.answer(text="Invalid callback data.", show_alert=True)
            return
        
        chat_id = int(match.group(1))
        await context.bot.leave_chat(chat_id=chat_id)
        await callback.answer(text="Left the chat.")
        
        LOGGER.info(f"[Dev] Bot left chat {chat_id} by {callback.from_user.id}")
        
    except Exception as e:
        LOGGER.error(f"[Dev] Error in leave_cb: {e}")
        await callback.answer(text="Error occurred while leaving the chat.", show_alert=True)


@dev_plus
@cutiepii_cmd(command="lockdown")
async def allow_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle group lockdown mode (developer only)"""
    try:
        args = context.args
        message = update.effective_message
        
        if not args:
            state = "Lockdown is " + ("disabled" if ALLOW_CHATS else "enabled")
            await message.reply_text(f"<b>Lockdown Settings</b>\nCurrent state: {state}", parse_mode=ParseMode.HTML)
            return
        
        arg = args[0].lower()
        if arg in ["off", "no"]:
            # ALLOW_CHATS = True means lockdown is OFF
            ALLOW_CHATS = True
            await message.reply_text("<b>Lockdown Disabled</b>\nThe bot is now allowed to join new groups.", parse_mode=ParseMode.HTML)
        elif arg in ["yes", "on"]:
            # ALLOW_CHATS = False means lockdown is ON
            ALLOW_CHATS = False
            await message.reply_text("<b>Lockdown Enabled</b>\nThe bot will not join new groups.", parse_mode=ParseMode.HTML)
        else:
            await message.reply_text("<b>Usage:</b>\n<code>/lockdown &lt;yes/no&gt;</code> or <code>&lt;on/off&gt;</code>", parse_mode=ParseMode.HTML)
            return
        
        LOGGER.info(f"[Dev] Lockdown toggled to {arg} by {update.effective_user.id}")
        
    except Exception as e:
        LOGGER.error(f"[Dev] Error in allow_groups: {e}")
        await update.effective_message.reply_text("An error occurred while toggling lockdown.")


class Store:
    """Store for tracking event statistics"""
    def __init__(self, func):
        self.func = func
        self.calls = []
        self.time = time()
        self.lock = asyncio.Lock()

    def average(self):
        """Calculate average calls per second"""
        return round(mean(self.calls), 2) if self.calls else 0

    def __repr__(self):
        return f"<Store func={self.func.__name__}, average={self.average()}>"

    async def __call__(self, event):
        """Track event calls"""
        async with self.lock:
            if not self.calls:
                self.calls = [0]
            if time() - self.time > 1:
                self.time = time()
                self.calls.append(1)
            else:
                self.calls[-1] += 1
        await self.func(event)


async def nothing(event):
    """Placeholder function for event tracking"""
    pass


# Initialize event trackers
messages = Store(nothing)
inline_queries = Store(nothing)
callback_queries = Store(nothing)

# Register event handlers
telethn.add_event_handler(messages, events.NewMessage())
telethn.add_event_handler(inline_queries, events.InlineQuery())
telethn.add_event_handler(callback_queries, events.CallbackQuery())


@telethn.on(events.NewMessage(pattern=r"/getstats", from_users=OWNER_ID))
async def getstats(event):
    """Get bot statistics (owner only)"""
    try:
        await event.reply(
            "<b>Event Statistics</b>\n\n"
            f"<b>Average Messages:</b> <code>{messages.average()}/s</code>\n"
            f"<b>Average Callback Queries:</b> <code>{callback_queries.average()}/s</code>\n"
            f"<b>Average Inline Queries:</b> <code>{inline_queries.average()}/s</code>",
            parse_mode="html"
        )
        LOGGER.info(f"[Dev] Stats requested by owner")
    except Exception as e:
        LOGGER.error(f"[Dev] Error in getstats: {e}")


@dev_plus
@cutiepii_cmd(command="install")
async def pip_install(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Install Python packages (developer only) - USE WITH CAUTION"""
    try:
        message = update.effective_message
        args = context.args
        
        if not args:
            await message.reply_text(
                "<b>Usage:</b>\n<code>/install &lt;package_name&gt;</code>\n\n"
                "<b>Warning:</b> This command installs packages directly onto the host system. "
                "Ensure you only install trusted dependencies.",
                parse_mode=ParseMode.HTML
            )
            return
        
        # Security: Validate package names (alphanumeric, hyphens, underscores only)
        package_names = []
        for arg in args:
            if not re.match(r'^[a-zA-Z0-9_\-\.]+$', arg):
                await message.reply_text(
                    f"<b>Error:</b> Invalid package name: <code>{html.escape(arg)}</code>\n"
                    "Package names must be alphanumeric, including hyphens/underscores/dots.",
                    parse_mode=ParseMode.HTML
                )
                return
            package_names.append(arg)
        
        await message.reply_text(
            f"<b>Package Manager</b>\nInstalling packages: <code>{', '.join(html.escape(p) for p in package_names)}</code>\n"
            "This may take a moment...",
            parse_mode=ParseMode.HTML
        )
        
        # Use subprocess.run with list of arguments (NOT shell=True for security)
        cmd = [sys.executable, "-m", "pip", "install"] + package_names
        
        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                check=False
            )
            
            stdout = process.stdout
            stderr = process.stderr
            reply = ""
            
            if stdout:
                reply += f"<b>Stdout:</b>\n<code>{html.escape(stdout[:3000])}</code>\n"  # Limit output
            if stderr:
                reply += f"<b>Stderr:</b>\n<code>{html.escape(stderr[:1000])}</code>\n"
            
            if process.returncode == 0:
                reply += "\n<b>Installation Successful</b>"
            else:
                reply += f"\n<b>Installation Failed</b> (Exit code: <code>{process.returncode}</code>)"
            
            await message.reply_text(text=reply, parse_mode=ParseMode.HTML)
            LOGGER.info(f"[Dev] Package installed: {package_names} by {update.effective_user.id}")
            
        except subprocess.TimeoutExpired:
            await message.reply_text("<b>Error:</b> Installation timed out (120s limit).", parse_mode=ParseMode.HTML)
        except Exception as e:
            LOGGER.error(f"[Dev] Error installing package: {e}")
            await message.reply_text(f"<b>Error:</b> An error occurred during installation: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)
            
    except Exception as e:
        LOGGER.error(f"[Dev] Error in pip_install: {e}")
        await update.effective_message.reply_text("An error occurred during package installation.")


@dev_plus
@cutiepii_cmd(command="leave")
async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Leave a chat (developer only)"""
    try:
        message = update.effective_message
        args = context.args
        
        if args:
            # Leave specified chat
            try:
                chat_id = int(args[0])
            except ValueError:
                await message.reply_text("<b>Error:</b> Invalid chat ID. Must be a numeric value.", parse_mode=ParseMode.HTML)
                return
            
            leave_msg = " ".join(args[1:]) if len(args) > 1 else "Goodbye!"
            
            try:
                await context.bot.send_message(chat_id, leave_msg)
                await context.bot.leave_chat(chat_id)
                await message.reply_text(f"<b>Success:</b> Left chat <code>{chat_id}</code>.", parse_mode=ParseMode.HTML)
                LOGGER.info(f"[Dev] Left chat {chat_id} by {update.effective_user.id}")
            except TelegramError as e:
                await message.reply_text(f"<b>Error:</b> Failed to leave chat: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)
        else:
            # Leave current chat with confirmation
            chat = update.effective_chat
            leave_button = [[
                InlineKeyboardButton(
                    text="Leave Chat",
                    callback_data=f"leavechat_cb_({chat.id})"
                )
            ]]
            await message.reply_text(
                f"<b>Leave Confirmation</b>\nAre you sure you want to leave <b>{html.escape(chat.title)}</b>?\n"
                "Press the button below to confirm.",
                reply_markup=InlineKeyboardMarkup(leave_button),
                parse_mode=ParseMode.HTML
            )
            
    except Exception as e:
        LOGGER.error(f"[Dev] Error in leave: {e}")
        await update.effective_message.reply_text("An error occurred while processing leave command.")


@dev_plus
@cutiepii_cmd(command="gitpull")
async def gitpull(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pull latest changes from git repository (developer only)"""
    try:
        message = update.effective_message
        
        await message.reply_text("<b>Git Pull</b>\nPulling latest changes from the git repository...", parse_mode=ParseMode.HTML)
        
        # Use subprocess.run without shell=True for security
        try:
            process = subprocess.run(
                ["git", "pull"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False
            )
            
            output = process.stdout + "\n" + process.stderr
            
            if process.returncode == 0:
                await message.reply_text(
                    "<b>Git Pull Successful</b>\n\n"
                    f"<code>{html.escape(output[:3000])}</code>\n\n"
                    "<b>Notice:</b> A reboot is required to apply the changes.\n"
                    "Use <code>/reboot</code> to restart the bot.",
                    parse_mode=ParseMode.HTML
                )
                LOGGER.info(f"[Dev] Git pull executed by {update.effective_user.id}")
            else:
                await message.reply_text(
                    f"<b>Git Pull Failed</b> (Exit code: <code>{process.returncode}</code>)\n\n"
                    f"<code>{html.escape(output[:2000])}</code>",
                    parse_mode=ParseMode.HTML
                )
                
        except subprocess.TimeoutExpired:
            await message.reply_text("<b>Error:</b> Git pull operation timed out (60s limit).", parse_mode=ParseMode.HTML)
        except FileNotFoundError:
            await message.reply_text("<b>Error:</b> Git binary was not found. Please ensure Git is installed.", parse_mode=ParseMode.HTML)
        except Exception as e:
            LOGGER.error(f"[Dev] Error in gitpull: {e}")
            await message.reply_text(f"<b>Error:</b> An error occurred during git pull: <code>{html.escape(str(e))}</code>", parse_mode=ParseMode.HTML)
            
    except Exception as e:
        LOGGER.error(f"[Dev] Error in gitpull: {e}")
        await update.effective_message.reply_text("An error occurred during git pull.")


@dev_plus
@cutiepii_cmd(command="reboot")
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Restart the bot (developer only) - USE WITH CAUTION"""
    try:
        message = update.effective_message
        
        await message.reply_text(
            "<b>Rebooting</b>\n"
            "Restarting the bot... All processes will be terminated and a new instance will start. This may take a few moments.",
            parse_mode=ParseMode.HTML
        )
        
        LOGGER.warning(f"[Dev] Bot restart initiated by {update.effective_user.id}")
        
        # For Unix/Linux systems
        if sys.platform != "win32":
            try:
                # Proper restart for Unix systems
                os.execv(sys.executable, [sys.executable, "-m", "Cutiepii_Robot"])
            except Exception as e:
                LOGGER.error(f"[Dev] Unix restart failed: {e}")
                # Fallback: Kill current process (supervisor/systemd should restart)
                sys.exit(1)
        else:
            # For Windows
            try:
                # Try to use restart.bat if it exists
                if os.path.exists("restart.bat"):
                    subprocess.Popen(["restart.bat"], shell=True)
                    sys.exit(0)
                else:
                    # Direct restart
                    python = sys.executable
                    os.execl(python, python, *sys.argv)
            except Exception as e:
                LOGGER.error(f"[Dev] Windows restart failed: {e}")
                sys.exit(1)
                
    except Exception as e:
        LOGGER.error(f"[Dev] Error in restart: {e}")
        await update.effective_message.reply_text("An error occurred during restart attempt.")


# Register handlers


__mod_name__ = "Dev"
__handlers__ = [
]
