import asyncio
from functools import wraps
from typing import Optional, Callable, Any
from threading import RLock

from telegram import Chat, Update, ChatMember
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CallbackQueryHandler, ApplicationHandlerStop
from telegram.error import Forbidden, TelegramError

from Cutiepii_Robot import dispatcher, LOGGER
from Cutiepii_Robot.modules.sql.moderators_sql import is_modd
from Cutiepii_Robot.modules.helper_funcs.decorators import cutiepii_callback

from Cutiepii_Robot.modules.helper_funcs.admin_status_helpers import (
	ADMINS_CACHE,
	BOT_ADMIN_CACHE,
	SUDO_USERS,
	AdminPerms,
	anon_reply_markup as arm,
	anon_reply_text as art,
	anon_callbacks as a_cb,
	user_is_not_admin_errmsg as u_na_errmsg,
	edit_anon_msg as eam,
	button_expired_error as bxp,
	get_admin_item,
	set_admin_item,
	get_bot_admin_item,
	set_bot_admin_item
)

# Attributes that exist on ChatMemberAdministrator (PTB v20+); ChatMemberMember has none.
# Excludes e.g. can_send_messages which is on ChatPermissions, not ChatMember.
_VALID_MEMBER_PERMS = frozenset(
	{"can_restrict_members", "can_promote_members", "can_invite_users", "can_delete_messages",
	 "can_change_info", "can_pin_messages", "is_anonymous"}
)


async def bot_is_admin(chat: Chat, perm: Optional[AdminPerms] = None) -> bool:
	"""Check if bot is admin in chat, optionally with specific permission"""
	try:
		if chat.type == "private":
			return True
		# all_members_are_administrators was removed in PTB v20+

		bot_member = await get_bot_member(chat.id)

		if perm:
			# ChatMemberMember lacks permission attributes in PTB v20+
			return hasattr(bot_member, perm.value) and getattr(bot_member, perm.value)

		return bot_member.status == "administrator"  # bot can't be owner
	except Exception as e:
		LOGGER.error(f"[AdminStatus] Error checking bot admin status: {e}")
		return False


async def get_bot_member(chat_id: int) -> ChatMember:
	"""Get bot's ChatMember object from cache or API"""
	try:
		# Check cache first
		if chat_id in BOT_ADMIN_CACHE:
			return BOT_ADMIN_CACHE[chat_id]
		
		# Fetch from API (PTB v20+ uses async get_chat_member)
		mem = await dispatcher.bot.get_chat_member(chat_id, dispatcher.bot.id)
		BOT_ADMIN_CACHE[chat_id] = mem
		return mem
		
	except (Forbidden, TelegramError) as e:
		LOGGER.warning(f"[AdminStatus] Failed to get bot member for chat {chat_id}: {e}")
		# Return None - caller should handle this appropriately
		# Alternative: Return ghost member with no permissions (commented for PTB v20+ compatibility)
		# bot_user = await dispatcher.bot.get_me()
		# ghost = ChatMember(
		# 	user=bot_user,
		# 	status='member',
		# 	can_be_edited=False,
		# 	is_anonymous=False,
		# 	can_manage_chat=False,
		# 	can_delete_messages=False,
		# 	can_manage_video_chats=False,
		# 	can_restrict_members=False,
		# 	can_promote_members=False,
		# 	can_change_info=False,
		# 	can_invite_users=False,
		# 	can_post_messages=False,
		# 	can_edit_messages=False,
		# 	can_pin_messages=False,
		# 	can_manage_topics=False,
		# 	can_send_messages=False,
		# )
		# return ghost
		return None


# Decorator to check if bot is admin with optional permission check
# Usage: @bot_admin_check() or @bot_admin_check(AdminPerms.CAN_DELETE_MESSAGES)
def bot_admin_check(permission: Optional[AdminPerms] = None) -> Callable:
	"""Decorator to check if bot is admin, optionally with specific permission"""
	def wrapper(func: Callable) -> Callable:
		@wraps(func)
		async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs) -> Any:
			nonlocal permission
			chat = update.effective_chat
			
			try:
				if chat.type == "private":
					return await func(update, context, *args, **kwargs)
				# all_members_are_administrators was removed in PTB v20+
				
				bot_id = dispatcher.bot.id

				# Try to get from cache
				try:
					bot_member = BOT_ADMIN_CACHE[chat.id]
				except KeyError:
					# If not in cache, get from API and save to cache (PTB v20+ async)
					bot_member = await dispatcher.bot.get_chat_member(chat.id, bot_id)
					BOT_ADMIN_CACHE[chat.id] = bot_member

				# ChatMemberMember = bot is not admin; never access permission attributes on it
				if type(bot_member).__name__ == "ChatMemberMember":
					await update.effective_message.reply_text(
						"<b>Action Denied</b>\nI must be an administrator to perform this action.",
						parse_mode=ParseMode.HTML
					)
					return None

				# If a permission is required, check for it
				if permission:
					if permission.value in _VALID_MEMBER_PERMS:
						try:
							if getattr(bot_member, permission.value, None):
								return await func(update, context, *args, **kwargs)
						except Exception:
							pass
					
					await update.effective_message.reply_text(
						f"<b>Action Denied</b>\nI require the '{permission.value.replace('_', ' ')}' permission to perform this action.",
						parse_mode=ParseMode.HTML
					)
					return None

				# If no specific permission is required, check for admin-ship only
				if getattr(bot_member, "status", None) == "administrator":
					return await func(update, context, *args, **kwargs)
				else:
					await update.effective_message.reply_text(
						"<b>Action Denied</b>\nI must be an administrator to perform this action.",
						parse_mode=ParseMode.HTML
					)
					return None
					
			except Exception as e:
				LOGGER.error(f"[AdminStatus] Error in bot_admin_check: {e}")
				await update.effective_message.reply_text(
					"<b>Error</b>\nAn error occurred while checking bot administrator permissions.",
					parse_mode=ParseMode.HTML
				)
				return None

		return wrapped
	return wrapper


async def user_is_admin(
	update: Update,
	user_id: int,
	channels: bool = False,  # if True, returns True if user is anonymous
	allow_moderators: bool = False,  # if True, returns True if user is a moderator
	perm: Optional[AdminPerms] = None  # if not None, returns True if user has the specified permission
) -> bool:
	"""Check if user is admin in chat"""
	try:
		# Support both user_is_admin(update, user_id) and user_is_admin(chat, user_id) from admin.py
		chat = update.effective_chat if hasattr(update, 'effective_chat') else update
		message = getattr(update, 'effective_message', None)
		
		# Private chats and sudo users always return True
		if chat.type == "private" or user_id in SUDO_USERS:
			return True

		# Check for anonymous admin (channel)
		if channels and message and (message.sender_chat is not None and message.sender_chat.type != "channel"):
			return True

		# Check moderators if allowed
		if allow_moderators and is_modd(chat.id, user_id):
			return True

		member: Optional[ChatMember] = await get_mem_from_cache(user_id, chat.id)

		if not member:  # not in cache so not an admin
			return False

		# Check specific permission if required
		if perm:
			try:
				the_perm = perm.value
			except AttributeError:
				if isinstance(perm, str) and perm.upper() in AdminPerms.__members__:
					the_perm = getattr(AdminPerms, perm.upper()).value
				else:
					LOGGER.warning(f"[AdminStatus] Invalid permission: {perm}")
					return False
			try:
				# ChatMemberMember has no permission attributes (can_send_messages etc); any getattr can raise
				if the_perm not in _VALID_MEMBER_PERMS:
					return getattr(member, "status", None) == "creator"
				val = getattr(member, the_perm, None)
				if val is not None:
					return bool(val) or getattr(member, "status", None) == "creator"
				return getattr(member, "status", None) == "creator"
			except AttributeError:
				# Regular member (ChatMemberMember) or missing attr; treat as no permission
				return False

		# Check if user is admin
		try:
			return member.status in ["administrator", "creator"]
		except AttributeError:
			return False
		
	except Exception as e:
		LOGGER.error(f"[AdminStatus] Error checking user admin status: {e}")
		return False


RLOCK = RLock()


async def get_mem_from_cache(user_id: int, chat_id: int) -> Optional[ChatMember]:
	"""Get user's ChatMember object from cache or API (PTB v20+ async)"""
	with RLOCK:
		try:
			# Check cache first
			if chat_id in ADMINS_CACHE:
				for member in ADMINS_CACHE[chat_id]:
					if member.user.id == user_id:
						return member
				return None  # User not in admin list
			
			# Fetch from API (PTB v20+ get_chat_administrators is async)
			try:
				admins = await dispatcher.bot.get_chat_administrators(chat_id)
				ADMINS_CACHE[chat_id] = list(admins)
				
				for member in admins:
					if member.user.id == user_id:
						return member
				return None
				
			except Forbidden:
				LOGGER.warning(f"[AdminStatus] Bot not authorized in chat {chat_id}")
				return None
			except TelegramError as e:
				LOGGER.error(f"[AdminStatus] Error fetching admins for chat {chat_id}: {e}")
				return None
				
		except Exception as e:
			LOGGER.error(f"[AdminStatus] Error in get_mem_from_cache: {e}")
			return None

# Decorator to check if user is admin
# Usage: @user_admin_check() or @user_admin_check(AdminPerms.CAN_DELETE_MESSAGES, allow_mods=True)
def user_admin_check(permission: Optional[AdminPerms] = None, allow_mods: bool = False, noreply: bool = False) -> Callable:
	"""Decorator to check if user is admin, optionally with specific permission"""
	def wrapper(func: Callable) -> Callable:
		@wraps(func)
		async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs) -> Any:
			nonlocal permission
			try:
				if update.effective_chat.type == 'private':
					res = func(update, context, *args, **kwargs)
					if asyncio.iscoroutine(res):
						return await res
					return res
				
				message = update.effective_message

				# Handle anonymous admin
				if update.effective_message.sender_chat and not update.effective_message.is_automatic_forward:
					callback_id = f'anonCB/{message.chat.id}/{message.message_id}/{permission.value if permission else "None"}'
					a_cb[(message.chat.id, message.message_id)] = (
						(update, context),
						func, (message, args)
					)
					await message.reply_text(
						text=art,
						reply_markup=arm(callback_id)
					)
					return None

				# Check if user is admin
				user_id = message.from_user.id if not noreply else update.effective_user.id
				if await user_is_admin(
					update,
					user_id,
					allow_moderators=allow_mods,
					perm=permission
				):
					res = func(update, context, *args, **kwargs)
					if asyncio.iscoroutine(res):
						return await res
					return res

				return await u_na_errmsg(message, permission, update.callback_query)
				
			except ApplicationHandlerStop:
				raise
			except Exception as e:
				import traceback
				LOGGER.error(f"[AdminStatus] Error in user_admin_check: {e}\n{traceback.format_exc()}")
				return None

		return wrapped
	return wrapper


# Decorator to check user is NOT admin
def user_not_admin_check(func: Callable) -> Callable:
	"""Decorator to ensure user is not an admin"""
	@wraps(func)
	async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs) -> Any:
		try:
			message = update.effective_message
			user = message.sender_chat or update.effective_user
			
			if (message.is_automatic_forward
					or (message.sender_chat and message.sender_chat.type != "channel")
					or not user):
				return None
			
			if not await user_is_admin(update, user.id, channels=True):
				result = func(update, context, *args, **kwargs)
				if asyncio.iscoroutine(result):
					return await result
				return result
			
			return None
		except ApplicationHandlerStop:
			raise
		except Exception as e:
			LOGGER.error(f"[AdminStatus] Error in user_not_admin_check: {e}")
			return None
	return wrapped


class AnonymousAdminMessage:
	def __init__(self, original_message, real_user):
		self._original_message = original_message
		self._real_user = real_user

	def __getattr__(self, name):
		return getattr(self._original_message, name)

	@property
	def from_user(self):
		return self._real_user

	@property
	def sender_chat(self):
		return None


class AnonymousAdminUpdate:
	def __init__(self, original_update, real_user):
		self._original_update = original_update
		self._real_user = real_user
		self._wrapped_message = AnonymousAdminMessage(original_update.message, real_user) if original_update.message else None

	def __getattr__(self, name):
		return getattr(self._original_update, name)

	@property
	def effective_user(self):
		return self._real_user

	@property
	def effective_sender_chat(self):
		return None

	@property
	def message(self):
		return self._wrapped_message

	@property
	def effective_message(self):
		return self._wrapped_message


@cutiepii_callback(pattern="anonCB")
async def perm_callback_check(upd: Update, _: ContextTypes.DEFAULT_TYPE) -> Any:
	"""Handle anonymous admin permission callback"""
	try:
		callback = upd.callback_query
		chat_id = int(callback.data.split('/')[1])
		message_id = int(callback.data.split('/')[2])
		perm = callback.data.split('/')[3]
		user_id = callback.from_user.id
		msg = upd.effective_message

		# Check if user has required permission
		is_admin = await user_is_admin(upd, user_id, perm=perm if perm != 'None' else None)

		if not is_admin:
			await eam(
				msg,
				"You need to be an admin to perform this action!"
				if perm == 'None'
				else f"You lack the permission: `{perm}`!"
			)
			return None

		# Get callback data
		cb = a_cb.pop((chat_id, message_id), None)
		if not cb:
			await eam(msg, "This message is no longer valid.")
			return None

		await msg.delete()

		# Wrap the original update to correctly identify the real user and bypass anon sender chat
		wrapped_update = AnonymousAdminUpdate(cb[0][0], upd.effective_user)

		return await cb[1](wrapped_update, cb[0][1])  # return func(wrapped_update, context)
		
	except Exception as e:
		LOGGER.error(f"[AdminStatus] Error in perm_callback_check: {e}")
		return None


async def update_admins_cache(chat_id: int) -> None:
	"""Update admin cache for a chat"""
	try:
		# Directly refresh the admin list from the API and update ADMINS_CACHE
		admins = await dispatcher.bot.get_chat_administrators(chat_id)
		ADMINS_CACHE[chat_id] = list(admins)
		# Also refresh the bot's own member record
		bot_member = await dispatcher.bot.get_chat_member(chat_id, dispatcher.bot.id)
		BOT_ADMIN_CACHE[chat_id] = bot_member
		LOGGER.info(f"[AdminStatus] Updated admin cache for chat {chat_id}")
	except Exception as e:
		LOGGER.error(f"[AdminStatus] Error updating admin cache for chat {chat_id}: {e}")


# Callback handler is registered via cutiepii_callback decorator
