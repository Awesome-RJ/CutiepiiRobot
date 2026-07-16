import json

from enum import Enum
from cachetools import TTLCache
from time import perf_counter, time
from typing import List, Any, Dict
from Cutiepii_Robot.modules.sql.moderators_sql import is_modd

from telegram import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message, Update, ChatMember
from telegram.constants import ParseMode
# JSONDict is just Dict[str, Any] - use Dict[str, Any] directly
JSONDict = Dict[str, Any]

from Cutiepii_Robot import OWNER_ID, DEV_USERS, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, REDIS, dispatcher

# stores admin in memory for 10 min.
ADMINS_CACHE = TTLCache(maxsize = 512, ttl = (60 * 30), timer=perf_counter)

# stores bot admin status in memory for 10 min.
BOT_ADMIN_CACHE = TTLCache(maxsize = 512, ttl = (60 * 10), timer=perf_counter)

SUDO_USERS = SUDO_USERS + DEV_USERS

WHITELIST_USERS = WHITELIST_USERS + SUDO_USERS

SUPPORT_USERS = SUPPORT_USERS + SUDO_USERS

class AdminPerms(Enum):
	CAN_RESTRICT_MEMBERS = 'can_restrict_members'
	CAN_PROMOTE_MEMBERS = 'can_promote_members'
	CAN_INVITE_USERS = 'can_invite_users'
	CAN_DELETE_MESSAGES = 'can_delete_messages'
	CAN_CHANGE_INFO = 'can_change_info'
	CAN_PIN_MESSAGES = 'can_pin_messages'
	IS_ANONYMOUS = 'is_anonymous'


def anon_reply_markup(cb_id: str) -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(
			[
				[
					InlineKeyboardButton(
							text = 'Prove Identity',
							callback_data = cb_id
					)
				]
			]
	)


anon_reply_text = "<b>Anonymous Admin</b>\nYou appear to be an anonymous administrator. Please click the button below to prove your identity."


async def edit_anon_msg(msg: Message, text: str):
	"""
	edit anon check message and remove the button
	"""
	await msg.edit_text(text, parse_mode = ParseMode.HTML, reply_markup = None)


async def user_is_not_admin_errmsg(msg: Message, permission: AdminPerms = None, cb: CallbackQuery = None):
	if permission:
		errmsg = f"<b>Action Denied</b>\nYou are missing the required permission: <code>{permission.value}</code>"
	else:
		errmsg = "<b>Action Denied</b>\nYou do not have the necessary administrator permissions to use this command."
	if cb:
		return await cb.answer(errmsg.replace("<b>", "").replace("</b>", "").replace("<code>", "").replace("</code>", ""), show_alert = True)
	return await msg.reply_text(errmsg, parse_mode = ParseMode.HTML)

async def button_expired_error(u: Update):
	errmsg = "<b>Error</b>\nThis button has expired."
	if u.callback_query:
		await u.callback_query.answer(errmsg.replace("<b>", "").replace("</b>", ""), show_alert = True)
		await u.effective_message.delete()
		return
	return await u.effective_message.edit_text(errmsg, parse_mode = ParseMode.HTML)

def get_admin_item(chat_id: int) -> Dict[int, JSONDict]:
	"""
	Retrieve admin list from Redis.
	DEPRECATED: Use ADMINS_CACHE (TTLCache) directly instead.
	"""
	data = REDIS.get(f"admin{chat_id}")
	if data:
		return json.loads(data)
	else:
		raise KeyError


def get_bot_admin_item(chat_id: int) -> ChatMember:
	"""
	Retrieve bot admin status from Redis.
	DEPRECATED: Use BOT_ADMIN_CACHE (TTLCache) directly instead.
	Note: Requires a live Bot object for de_json deserialization.
	"""
	data = REDIS.get(f"bot_admin{chat_id}")
	if data:
		return ChatMember.de_json(data=json.loads(data), bot=dispatcher.bot)
	else:
		raise KeyError


def set_admin_item(chat_id: int, data: Dict[int, ChatMember]) -> None:
	"""
	Persist admin list to Redis.
	DEPRECATED: Use ADMINS_CACHE (TTLCache) directly instead.
	"""
	REDIS.set(f"admin{chat_id}", json.dumps(data))


def set_bot_admin_item(chat_id: int, data: ChatMember) -> None:
	"""
	Persist bot admin status to Redis.
	DEPRECATED: Use BOT_ADMIN_CACHE (TTLCache) directly instead.
	"""
	REDIS.set(f"bot_admin{chat_id}", data.to_json())


def get_callback(chat_id: int, message_id: int):
	return json.loads(REDIS.get(f"cb{message_id}{chat_id}"))


def set_callback(chat_id: int, message_id: int, data) -> None:
	REDIS.set(f"cb{message_id}{chat_id}", json.dumps(data))

anon_callbacks = {}
