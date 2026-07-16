"""
Enhanced decorators for Cutiepii Robot
Provides improved command handling, caching, rate limiting, and error handling
"""

import traceback
import html
import requests
import functools
import time
import asyncio
from typing import Optional, Union, List, Callable, Any, Dict
from collections import defaultdict

from telethon import events
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler, InlineQueryHandler, ChatMemberHandler
from telegram.ext import filters
MessageFilter = filters.BaseFilter  # Alias for backward compatibility
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from Cutiepii_Robot import LOGGER, telethn, OWNER_ID, BOT_USERNAME, dispatcher as d
from Cutiepii_Robot.modules.helper_funcs.handlers import CustomCommandHandler, CustomMessageHandler


# Global registry for module handlers to support dynamic unloading
MODULE_HANDLERS = defaultdict(list)


# ===========================
# Rate Limiting
# ===========================

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.user_timestamps: Dict[int, List[float]] = defaultdict(list)
        self.cleanup_interval = 3600  # Cleanup every hour
        self.last_cleanup = time.time()
    
    def is_rate_limited(self, user_id: int, max_calls: int = 30, time_window: int = 60) -> bool:
        """
        Check if user has exceeded rate limit
        
        Args:
            user_id: Telegram user ID
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds
        
        Returns:
            True if rate limited, False otherwise
        """
        current_time = time.time()
        
        # Cleanup old timestamps periodically
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_old_timestamps()
            self.last_cleanup = current_time
        
        # Get user's recent timestamps
        timestamps = self.user_timestamps[user_id]
        
        # Remove timestamps outside the time window
        timestamps = [ts for ts in timestamps if current_time - ts < time_window]
        self.user_timestamps[user_id] = timestamps
        
        # Check if rate limited
        if len(timestamps) >= max_calls:
            return True
        
        # Add current timestamp
        timestamps.append(current_time)
        return False
    
    def _cleanup_old_timestamps(self):
        """Remove old user data to prevent memory leaks"""
        current_time = time.time()
        users_to_remove = []
        
        for user_id, timestamps in self.user_timestamps.items():
            # Remove timestamps older than 1 hour
            recent_timestamps = [ts for ts in timestamps if current_time - ts < 3600]
            if not recent_timestamps:
                users_to_remove.append(user_id)
            else:
                self.user_timestamps[user_id] = recent_timestamps
        
        for user_id in users_to_remove:
            del self.user_timestamps[user_id]


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(max_calls: int = 30, time_window: int = 60):
    """
    Decorator to add rate limiting to handlers
    
    Args:
        max_calls: Maximum number of calls per time window
        time_window: Time window in seconds
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id if update.effective_user else 0
            
            if rate_limiter.is_rate_limited(user_id, max_calls, time_window):
                try:
                    await update.effective_message.reply_text(
                        "<b>Rate Limit Exceeded</b>\nYou are sending commands too quickly. Please wait a moment and try again.",
                        parse_mode=ParseMode.HTML
                    )
                except Exception:
                    pass
                return
            
            return await func(update, context, *args, **kwargs)
        
        return wrapper
    return decorator


# ===========================
# Simple Cache Decorator
# ===========================

class SimpleCache:
    """Simple in-memory cache for function results"""
    
    def __init__(self, ttl: int = 300):
        self.cache: Dict[str, tuple] = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if still valid"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """Cache a value"""
        self.cache[key] = (value, time.time())
    
    def clear(self):
        """Clear all cached values"""
        self.cache.clear()


def cached(ttl: int = 300):
    """
    Simple cache decorator
    
    Args:
        ttl: Time to live in seconds
    """
    cache = SimpleCache(ttl)
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator


# ===========================
# Error Handling Decorator
# ===========================

def error_handler(func: Callable) -> Callable:
    """
    Decorator to add comprehensive error handling.
    Handles both sync and async callbacks to avoid "object NoneType can't be used in 'await'" and unawaited coroutines.
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        from Cutiepii_Robot.modules.sql import SESSION
        try:
            result = func(update, context, *args, **kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result
        except Exception as e:
            from telegram.error import BadRequest, RetryAfter, TimedOut
            if isinstance(e, TimedOut):
                LOGGER.warning(f"Timeout occurred in {func.__name__}. Retrying once after 1 second...")
                await asyncio.sleep(1)
                try:
                    result = func(update, context, *args, **kwargs)
                    if asyncio.iscoroutine(result):
                        return await result
                    return result
                except Exception as retry_err:
                    LOGGER.error(f"Error on retrying {func.__name__} after timeout: {retry_err}")
                return

            if isinstance(e, RetryAfter):
                LOGGER.warning(f"Flood control hit in {func.__name__}. Retrying after {e.retry_after} seconds.")
                await asyncio.sleep(e.retry_after)
                try:
                    result = func(update, context, *args, **kwargs)
                    if asyncio.iscoroutine(result):
                        return await result
                    return result
                except Exception as retry_err:
                    LOGGER.error(f"Error on retrying {func.__name__}: {retry_err}")
                return

            if isinstance(e, BadRequest) and "Message is not modified" in str(e):
                try:
                    if update.callback_query:
                        await update.callback_query.answer()
                except Exception:
                    pass
                return
            LOGGER.error(f"Error in {func.__name__}: {e}")
            LOGGER.error(traceback.format_exc())
            
            try:
                await update.effective_message.reply_text(
                    "<b>Error</b>\nAn error occurred while processing your request. Please try again later.",
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass
        finally:
            SESSION.remove()
    
    return wrapper


# ===========================
# Command Handler Class
# ===========================

class Cutiepii_TG_Handler:
    """Enhanced Telegram handler with improved features"""
    
    def __init__(self, dispatcher):
        self._dispatcher = dispatcher
    
    def _register_handler(self, func, h, group=0):
        module_name = func.__module__
        MODULE_HANDLERS[module_name].append((h, group))
    
    def command(
        self,
        command: Union[str, List[str]],
        filters: Optional[MessageFilter] = None,
        admin_ok: bool = False,
        group: Optional[Union[int, str]] = 40,
        rate_limit_calls: int = 0,
        rate_limit_window: int = 60,
        add_error_handler: bool = True,
        can_disable: bool = False,
        **kwargs
    ):
        """
        Enhanced command decorator with rate limiting and error handling.
        
        Args:
            command (str or list): Command name(s) to register (e.g. "start" or ["start", "help"])
            filters (BaseFilter, optional): Message filters to restrict when this command is triggered.
            admin_ok (bool): Allow admins to bypass command if disabled. Defaults to False.
            group (int, optional): Priority handler group. Defaults to 40.
            rate_limit_calls (int): Max calls allowed per window. Defaults to 0 (no limit).
            rate_limit_window (int): Time window in seconds for rate limiting. Defaults to 60.
            add_error_handler (bool): Wrap callback with automatic error reporting. Defaults to True.
            can_disable (bool): Allow the command to be toggled/disabled via modules manager. Defaults to False.
        """
        def _command(func):
            handler_func = func
            if add_error_handler:
                handler_func = error_handler(handler_func)
            
            if rate_limit_calls > 0:
                handler_func = rate_limit(rate_limit_calls, rate_limit_window)(handler_func)
            
            handler_kwargs = kwargs.copy()
            if "pass_args" in handler_kwargs:
                del handler_kwargs["pass_args"]
            if "pass_chat_data" in handler_kwargs:
                del handler_kwargs["pass_chat_data"]
            if "pass_user_data" in handler_kwargs:
                del handler_kwargs["pass_user_data"]
            if "can_disable" in handler_kwargs:
                del handler_kwargs["can_disable"]
            
            try:
                if can_disable:
                    from Cutiepii_Robot.modules.disable import DisableAbleCommandHandler
                    h = DisableAbleCommandHandler(
                        command, handler_func, filters=filters, admin_ok=admin_ok, **handler_kwargs
                    )
                    self._dispatcher.add_handler(h, group)
                else:
                    h = CustomCommandHandler(command, handler_func, filters=filters, **handler_kwargs)
                    self._dispatcher.add_handler(h, group)
                
                self._register_handler(func, h, group)
                
                cmd_str = command if isinstance(command, str) else ", ".join(command)
                LOGGER.debug(
                    f"[CUTIEPII CMD] Loaded handler /{cmd_str} for {func.__name__} in group {group}"
                )
            except Exception as e:
                LOGGER.error(f"Error loading handler {command}: {e}")
            
            return func
        
        return _command
    
    def message(
        self,
        pattern: Optional[str] = None,
        group: Optional[Union[int, str]] = 60,
        friendly=None,
        add_error_handler: bool = True,
        can_disable: bool = False,
        **kwargs
    ):
        """
        Enhanced message handler decorator.
        
        Args:
            pattern (BaseFilter, optional): Filter triggers (e.g. filters.TEXT or custom filters).
            group (int, optional): Priority handler group. Defaults to 60.
            friendly (str, optional): A descriptive name for the handler when listing/disabling.
            add_error_handler (bool): Wrap callback with automatic error reporting. Defaults to True.
            can_disable (bool): Allow the message handler to be toggled/disabled. Defaults to False.
        """
        def _message(func):
            handler_func = func
            if add_error_handler:
                handler_func = error_handler(handler_func)
            
            handler_kwargs = kwargs.copy()
            if "can_disable" in handler_kwargs:
                del handler_kwargs["can_disable"]
            
            try:
                if can_disable:
                    from Cutiepii_Robot.modules.disable import DisableAbleMessageHandler
                    h = DisableAbleMessageHandler(pattern, handler_func, friendly=friendly, **handler_kwargs)
                    self._dispatcher.add_handler(h, group)
                else:
                    h = CustomMessageHandler(pattern, handler_func, **handler_kwargs)
                    self._dispatcher.add_handler(h, group)
                
                self._register_handler(func, h, group)
                
                LOGGER.debug(
                    f"[CUTIEPII MSG] Loaded filter {pattern} for {func.__name__} in group {group}"
                )
            except Exception as e:
                LOGGER.error(f"Error loading message handler {pattern}: {e}")
            
            return func
        
        return _message
    
    def callbackquery(
        self,
        pattern: Optional[str] = None,
        run_async: bool = True,
        group: int = 0,
        **kwargs
    ):
        """
        Callback query handler decorator.
        
        Args:
            pattern (str or Pattern, optional): Regular expression pattern to match callback data query.
            run_async (bool): Run callback block asynchronously. Defaults to True.
            group (int): Priority handler group. Defaults to 0.
        """
        def _callbackquery(func):
            handler_func = error_handler(func)
            
            h = CallbackQueryHandler(pattern=pattern, callback=handler_func, block=not run_async, **kwargs)
            self._dispatcher.add_handler(h, group)
            self._register_handler(func, h, group)
            LOGGER.debug(
                f"[CUTIEPII CALLBACK] Loaded handler {pattern} for {func.__name__} in group {group}"
            )
            return func
        
        return _callbackquery
    
    def inlinequery(
        self,
        pattern: Optional[str] = None,
        chat_types: Optional[List[str]] = None,
        run_async: bool = True,
        group: int = 0,
        **kwargs
    ):
        """
        Inline query handler decorator.
        
        Args:
            pattern (str or Pattern, optional): Regular expression pattern to match inline query.
            chat_types (list, optional): List of chat types (e.g. ["sender", "private", "group"]) to restrict.
            run_async (bool): Run callback block asynchronously. Defaults to True.
            group (int): Priority handler group. Defaults to 0.
        """
        def _inlinequery(func):
            handler_func = error_handler(func)
            
            h = InlineQueryHandler(pattern=pattern, callback=handler_func, chat_types=chat_types, block=not run_async, **kwargs)
            self._dispatcher.add_handler(h, group)
            self._register_handler(func, h, group)
            LOGGER.debug(
                f"[CUTIEPII INLINE] Loaded handler {pattern} for {func.__name__} in group {group} | CHAT TYPES: {chat_types}"
            )
            return func
        
        return _inlinequery

    def chatmember(
        self,
        chat_member_types: int = ChatMemberHandler.CHAT_MEMBER,
        run_async: bool = True,
        group: int = 0,
        **kwargs
    ):
        """
        Chat member handler decorator.
        
        Args:
            chat_member_types (int): Type of updates (e.g. MY_CHAT_MEMBER or CHAT_MEMBER). Defaults to CHAT_MEMBER.
            run_async (bool): Run callback block asynchronously. Defaults to True.
            group (int): Priority handler group. Defaults to 0.
        """
        def _chatmember(func):
            handler_func = error_handler(func)
            
            h = ChatMemberHandler(
                callback=handler_func,
                chat_member_types=chat_member_types,
                block=not run_async,
                **kwargs
            )
            self._dispatcher.add_handler(h, group)
            self._register_handler(func, h, group)
            LOGGER.debug(
                f"[CUTIEPII CHATMEMBER] Loaded handler for {func.__name__} in group {group}"
            )
            return func
        
        return _chatmember

    def chatjoinrequest(
        self,
        run_async: bool = True,
        group: int = 0,
        **kwargs
    ):
        """
        Chat join request handler decorator.
        
        Args:
            run_async (bool): Run callback block asynchronously. Defaults to True.
            group (int): Priority handler group. Defaults to 0.
        """
        def _chatjoinrequest(func):
            from telegram.ext import ChatJoinRequestHandler
            handler_func = error_handler(func)
            
            h = ChatJoinRequestHandler(
                callback=handler_func,
                block=not run_async,
                **kwargs
            )
            self._dispatcher.add_handler(h, group)
            self._register_handler(func, h, group)
            LOGGER.debug(
                f"[CUTIEPII CHATJOINREQUEST] Loaded handler for {func.__name__} in group {group}"
            )
            return func
        
        return _chatjoinrequest

    def businessconnection(
        self,
        run_async: bool = True,
        group: int = 0,
        **kwargs
    ):
        """
        Business connection handler decorator.
        
        Args:
            run_async (bool): Run callback block asynchronously. Defaults to True.
            group (int): Priority handler group. Defaults to 0.
        """
        def _businessconnection(func):
            from telegram.ext import BusinessConnectionHandler
            handler_func = error_handler(func)
            
            h = BusinessConnectionHandler(
                callback=handler_func,
                block=not run_async,
                **kwargs
            )
            self._dispatcher.add_handler(h, group)
            self._register_handler(func, h, group)
            LOGGER.debug(
                f"[CUTIEPII BUSINESS] Loaded handler for {func.__name__} in group {group}"
            )
            return func
        
        return _businessconnection

    def chatboost(
        self,
        run_async: bool = True,
        group: int = 0,
        **kwargs
    ):
        """
        Chat boost handler decorator.
        
        Args:
            run_async (bool): Run callback block asynchronously. Defaults to True.
            group (int): Priority handler group. Defaults to 0.
        """
        def _chatboost(func):
            from telegram.ext import ChatBoostHandler
            handler_func = error_handler(func)
            
            h = ChatBoostHandler(
                callback=handler_func,
                block=not run_async,
                **kwargs
            )
            self._dispatcher.add_handler(h, group)
            self._register_handler(func, h, group)
            LOGGER.debug(
                f"[CUTIEPII BOOST] Loaded handler for {func.__name__} in group {group}"
            )
            return func
        
        return _chatboost

    def precheckoutquery(
        self,
        group: int = 0,
        **kwargs
    ):
        """
        Pre-checkout query handler decorator.
        
        Args:
            group (int): Priority handler group. Defaults to 0.
        """
        def _precheckoutquery(func):
            from telegram.ext import PreCheckoutQueryHandler
            handler_func = error_handler(func)
            
            h = PreCheckoutQueryHandler(
                callback=handler_func,
                **kwargs
            )
            self._dispatcher.add_handler(h, group)
            self._register_handler(func, h, group)
            LOGGER.debug(
                f"[CUTIEPII PRECHECKOUT] Loaded handler for {func.__name__} in group {group}"
            )
            return func
        
        return _precheckoutquery

    def messagereaction(
        self,
        run_async: bool = True,
        group: int = 0,
        **kwargs
    ):
        """
        Message reaction handler decorator.
        
        Args:
            run_async (bool): Run callback block asynchronously. Defaults to True.
            group (int): Priority handler group. Defaults to 0.
        """
        def _messagereaction(func):
            from telegram.ext import MessageReactionHandler
            handler_func = error_handler(func)
            
            h = MessageReactionHandler(
                callback=handler_func,
                block=not run_async,
                **kwargs
            )
            self._dispatcher.add_handler(h, group)
            self._register_handler(func, h, group)
            LOGGER.debug(
                f"[CUTIEPII REACTION] Loaded handler for {func.__name__} in group {group}"
            )
            return func
        
        return _messagereaction

    def conversation(
        self,
        conversation_handler,
        group: int = 0
    ):
        """Register a conversation handler directly"""
        self._dispatcher.add_handler(conversation_handler, group)
        import sys
        try:
            frame = sys._getframe(1)
            module_name = frame.f_globals.get('__name__')
            if module_name:
                MODULE_HANDLERS[module_name].append((conversation_handler, group))
        except Exception:
            pass


# Create global handler instances
handler = Cutiepii_TG_Handler(d)
cutiepii_cmd = handler.command
cutiepii_msg = handler.message
cutiepii_callback = handler.callbackquery
cutiepii_inline = handler.inlinequery
cutiepii_chatmember = handler.chatmember
cutiepiichatmember = handler.chatmember
cutiepii_join_request = handler.chatjoinrequest
cutiepii_business_connection = handler.businessconnection
cutiepii_chat_boost = handler.chatboost
cutiepii_precheckout = handler.precheckoutquery
cutiepii_message_reaction = handler.messagereaction
cutiepii_conversation = handler.conversation


# ===========================
# Telethon Decorator
# ===========================

def register(**args):
    """
    Enhanced Telethon event handler decorator
    """
    pattern = args.get('pattern', None)
    disable_edited = args.get('disable_edited', False)
    groups_only = args.get('groups_only', False)
    no_args = args.get('no_args', False)
    raw = args.get('raw', False)
    
    if pattern is not None:
        if raw:
            reg = "(?i)[/!>]"
            args['pattern'] = reg + pattern
        else:
            reg = "(?i)[/!>]"
            reg += pattern
            if no_args:
                reg += "($|@{}$)".format(BOT_USERNAME)
            else:
                reg += "( |@{} )?(.*)".format(BOT_USERNAME)
            args['pattern'] = reg
    
    # Clean up custom args
    for key in ['disable_edited', 'no_args', 'raw', 'groups_only']:
        if key in args:
            del args[key]
    
    def decorator(func):
        async def wrapper(check):
            # Skip edited messages in channels
            if check.edit_date and check.is_channel and not check.is_group:
                return
            
            # Check group requirement
            if groups_only and not check.is_group:
                await check.respond("⚠️ This command can only be used in groups")
                return
            
            from Cutiepii_Robot.modules.sql import SESSION
            try:
                try:
                    await func(check)
                except events.StopPropagation:
                    raise events.StopPropagation
                except KeyboardInterrupt:
                    pass
                except BaseException as error:
                    # Enhanced error handling
                    error_text = html.escape(str(check.text))
                    
                    tb_list = traceback.format_exception(None, error, error.__traceback__)
                    tb = "".join(tb_list)
                    
                    pretty_message = (
                        "Telethon Exception\n\n"
                        f"User: {check.from_id or 'None'}\n"
                        f"Chat: {check.chat.title or ''} ({check.chat_id or ''})\n"
                        f"Message: {error_text}\n\n"
                        f"Traceback:\n{tb}"
                    )
                    
                    try:
                        # Try to post to nekobin
                        response = requests.post(
                            "https://nekobin.com/api/documents",
                            json={"content": pretty_message},
                            timeout=5
                        )
                        key = response.json().get("result", {}).get("key")
                        
                        if key:
                            url = f"https://nekobin.com/{key}.py"
                            await check.client.send_message(
                                OWNER_ID,
                                f"<b>Telethon Exception:</b>\n<code>{error_text[:100]}</code>",
                                buttons=[[InlineKeyboardButton("View Error", url=url)]],
                                parse_mode="html",
                            )
                        else:
                            raise Exception("No key returned")
                            
                    except Exception:
                        # Fallback: send as file
                        try:
                            with open("telethon_error.txt", "w+", encoding="utf-8") as f:
                                f.write(pretty_message)
                            
                            await check.client.send_file(
                                OWNER_ID,
                                "telethon_error.txt",
                                caption=f"<b>Telethon Exception:</b>\n<code>{error_text[:100]}</code>",
                                parse_mode="html",
                            )
                        except Exception as send_error:
                            LOGGER.error(f"Failed to send error report: {send_error}")
                    
                    LOGGER.error(f"Telethon error in {func.__name__}: {error}")
                    LOGGER.error(pretty_message)
            finally:
                SESSION.remove()
        
        # Register handlers
        if not disable_edited:
            telethn.add_event_handler(wrapper, events.MessageEdited(**args))
        telethn.add_event_handler(wrapper, events.NewMessage(**args))
        
        LOGGER.debug(f"[TLTHNCMD] Loaded handler {pattern} for {func.__name__}")
        
        return wrapper
    
    return decorator


# ===========================
# Utility Decorators
# ===========================

def async_timing(func: Callable) -> Callable:
    """Decorator to measure async function execution time"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        elapsed = time.time() - start_time
        LOGGER.debug(f"[TIMING] {func.__name__} took {elapsed:.2f}s")
        return result
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    Retry decorator for async functions
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        LOGGER.warning(
                            f"[RETRY] {func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        LOGGER.error(
                            f"[RETRY] {func.__name__} failed after {max_attempts} attempts"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


# Export all
__all__ = [
    'cutiepii_cmd',
    'cutiepii_msg',
    'cutiepii_callback',
    'cutiepii_inline',
    'cutiepii_chatmember',
    'cutiepiichatmember',
    'cutiepii_join_request',
    'register',
    'rate_limit',
    'cached',
    'error_handler',
    'async_timing',
    'retry',
    'RateLimiter',
    'SimpleCache',
]
