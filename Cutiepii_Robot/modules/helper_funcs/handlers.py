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
import asyncio
import telegram.ext as tg
import Cutiepii_Robot.modules.sql.blacklistusers_sql as sql

from telegram import Update
from telegram.ext import MessageHandler, filters
# Import from specific modules for pyrate_limiter
# Try different import paths based on version
try:
    # Try v3.7+ API structure
    from pyrate_limiter.abstracts.rate import RequestRate, Duration
    from pyrate_limiter.limiter import Limiter
    from pyrate_limiter.buckets.in_memory_bucket import MemoryListBucket
    from pyrate_limiter.exceptions import BucketFullException
except ImportError:
    try:
        # Try v2.x API structure (direct imports)
        from pyrate_limiter import (
            Duration,
            RequestRate,
            Limiter,
            MemoryListBucket,
        )
        from pyrate_limiter.exceptions import BucketFullException
    except ImportError:
        # If all imports fail, create minimal dummy classes to prevent errors
        # The rate limiting code is currently disabled anyway
        class Duration:
            CUSTOM = 15
            MINUTE = 60
            HOUR = 3600
            DAY = 86400
        
        class RequestRate:
            def __init__(self, *args, **kwargs):
                pass
        
        class Limiter:
            def __init__(self, *args, **kwargs):
                pass
        
        class MemoryListBucket:
            pass
        
        class BucketFullException(Exception):
            pass
from Cutiepii_Robot import DEV_USERS, OWNER_ID, SUDO_USERS, WHITELIST_USERS, SUPPORT_USERS

try:
    from Cutiepii_Robot import CUSTOM_CMD
except:
    CUSTOM_CMD = False

CMD_STARTERS = CUSTOM_CMD or ("/", "!", "?", ".", "~", "+")


class AntiSpam:
    def __init__(self):
        self.whitelist = (
            (DEV_USERS or [])
            + (SUDO_USERS or [])
            + (WHITELIST_USERS or [])
            + (SUPPORT_USERS or [])
        )
        # Values are HIGHLY experimental, its recommended you pay attention to our commits as we will be adjusting the values over time with what suits best.
        Duration.CUSTOM = 15  # Custom duration, 15 seconds
        self.sec_limit = RequestRate(6, Duration.CUSTOM)  # 6 / Per 15 Seconds
        self.min_limit = RequestRate(20, Duration.MINUTE)  # 20 / Per minute
        self.hour_limit = RequestRate(100, Duration.HOUR)  # 100 / Per hour
        self.daily_limit = RequestRate(1000, Duration.DAY)  # 1000 / Per day
        self.limiter = Limiter(
            self.sec_limit,
            self.min_limit,
            self.hour_limit,
            self.daily_limit,
            bucket_class=MemoryListBucket,
        )

    @staticmethod
    def check_user(user):
        """
        Return True if user is to be ignored else False
        """
        return bool(sql.is_user_blacklisted(user))
        '''try: # this should be enabled but it disables the bot
            self.limiter.try_acquire(user)
            return False
        except BucketFullException:
            return True'''

SpamChecker = AntiSpam()
MessageHandlerChecker = AntiSpam()


class CustomCommandHandler(tg.CommandHandler):
    def __init__(self, command, callback, **kwargs):
        if "admin_ok" in kwargs:
            del kwargs["admin_ok"]
        if "run_async" in kwargs:
            del kwargs["run_async"]
        if "pass_args" in kwargs:
            del kwargs["pass_args"]  # Removed in v20+ - args are automatically available via context.args
        if "pass_chat_data" in kwargs:
            del kwargs["pass_chat_data"]  # Removed in v20+
        if "pass_user_data" in kwargs:
            del kwargs["pass_user_data"]  # Removed in v20+
        super().__init__(command, callback, **kwargs)

    async def check_update(self, update):
        if not isinstance(update, Update) or not update.effective_message:
            return
        message = update.effective_message

        try:
            user_id = update.effective_user.id
        except Exception:
            user_id = None

        raw_text = message.text or message.caption
        if raw_text and len(raw_text) > 1:
            fst_word = raw_text.split(None, 1)[0]
            if len(fst_word) > 1 and any(
                fst_word.startswith(start) for start in CMD_STARTERS
            ):
                args = raw_text.split()[1:]
                command = fst_word[1:].split("@")
                command.append(
                    update.get_bot().username
                )  # in case the command was sent without a username

                if not (
                    command[0].lower() in self.commands
                    and (len(command) <= 1 or command[1].lower() == update.get_bot().username.lower())
                ):
                    return None

                if SpamChecker.check_user(user_id):
                    return None

                filter_result = self.filters.check_update(update)
                if asyncio.iscoroutine(filter_result):
                    filter_result = await filter_result
                if filter_result:
                    return args, filter_result
                return False
        return None


class CustomMessageHandler(MessageHandler):
    def __init__(self, pattern, callback, friendly="", **kwargs):
        if "run_async" in kwargs:
            del kwargs["run_async"]
        super().__init__(pattern, callback, **kwargs)
        self.friendly = friendly or pattern
    async def check_update(self, update):
        if isinstance(update, Update) and update.effective_message:
            try:
                user_id = update.effective_user.id
            except Exception:
                user_id = None

            filter_result = self.filters.check_update(update)
            if asyncio.iscoroutine(filter_result):
                filter_result = await filter_result
            if filter_result:
                if SpamChecker.check_user(user_id):
                    return None
                return True
        return False
